"""
BESS + Demand Response Optimization Model for a 10 MW Dublin Data Center.

Simplified from Ljungblom (2025) Chalmers thesis MILP: BESS + grid imports only
(no PV, wind, or SMR). Exports results for workbook and figure generation.

Run: uv run python build_model.py
"""

import pickle
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pyomo.environ as pyo

# ---------------------------------------------------------------------------
# Phase 1: Constants, Parameters, Synthetic Data
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_PKL = SCRIPT_DIR / "results.pkl"

T = 8760  # hours in a year
YEAR = 2023  # reference year for calendar mapping

# Data center
D_MW = 10.0  # constant load (MW)
C_GRID = 20.0  # grid connection capacity (MW); 2× DC load to allow BESS charging headroom

# Grid (thesis Tables 3.1-3.3)
CARBON_INTENSITY = 225  # gCO2/kWh (SEAI)
TOU_DAY = 65.03  # EUR/MWh (08-17 weekdays)
TOU_PEAK = 66.40  # EUR/MWh (17-19 weekdays)
TOU_NIGHT = 53.53  # EUR/MWh (23-08 and weekends)
F_SUB = 4_403_376.0  # EUR/year grid subscription fee (thesis Table 3.3, 10 MW connection)

# BESS — thesis values (NREL ATB 2025, thesis Table 3.7)
BESS_THESIS = {
    "label": "NREL ATB 2025",
    "c_P_cap": 675.0,   # EUR/kW power CapEx
    "c_E_cap": 165.6,   # EUR/kWh energy CapEx
    "c_P_opex": 16.9,   # EUR/kW-yr power O&M
    "c_E_opex": 4.11,   # EUR/kWh-yr energy O&M
}

# BESS — updated estimates (BNEF 2025 CapEx + inflation-adjusted OpEx)
BESS_UPDATED = {
    "label": "BNEF 2025 CapEx + Inflation-Adj. OpEx",
    "c_P_cap": 500.0,
    "c_E_cap": 120.0,
    "c_P_opex": 17.3,   # thesis 16.9 × 1.025 (Irish CPI, rising labor costs)
    "c_E_opex": 4.21,   # thesis 4.11 × 1.025
}

ETA_RT = 0.95  # round-trip efficiency
ETA_C = 0.95   # one-way charge efficiency (discharge at 100% → 95% round-trip)
LT_BESS = 15   # years
WACC = 0.08
AF_BESS = WACC * (1 + WACC) ** LT_BESS / ((1 + WACC) ** LT_BESS - 1)  # 0.11683
S0_FRAC = 0.5  # initial SoC fraction

# BESS sizing grid
P_OPTIONS = [2, 4, 6, 8, 10]  # MW
TAU_OPTIONS = [1, 2, 4]        # hours

# Demand Side Unit (DSU) — EirGrid capacity market
DSU_MIN_MW = 4.0        # minimum enrolled capacity to participate as DSU
EIRGRID_CAP_RATE = 138  # k€/MW/yr — EirGrid average annual DSU capacity payment
ENERGY_ARB_RATE = 81.0  # EUR/MWh — avoided peak energy charge (thesis reference)

# Revenue discount factor — models auction uncertainty for larger DSU bids
P_MAX = max(P_OPTIONS)
BETA_VALUES = [round(b, 2) for b in np.arange(0.0, 0.55, 0.05)]


def hour_index_to_datetime(h):
    return datetime(YEAR, 1, 1) + timedelta(hours=int(h))


def build_calendar():
    """Return arrays of month (1-12), hour-of-day (0-23), day-of-week (0=Mon..6=Sun)."""
    months = np.empty(T, dtype=int)
    hours = np.empty(T, dtype=int)
    dows = np.empty(T, dtype=int)
    days = np.empty(T, dtype=int)  # day-of-year 0-364
    for h in range(T):
        dt = hour_index_to_datetime(h)
        months[h] = dt.month
        hours[h] = dt.hour
        dows[h] = dt.weekday()
        days[h] = h // 24
    return months, hours, dows, days


def generate_spot_prices(seed=42):
    """Synthetic hourly spot prices calibrated to 2023 I-SEM statistics."""
    rng = np.random.default_rng(seed)
    months, hours, dows, _ = build_calendar()

    base = 95.0  # EUR/MWh

    seasonal = np.zeros(T)
    for m, adj in [(12, 15), (1, 15), (2, 15), (11, 5), (3, 5),
                   (4, -10), (5, -10), (6, -10), (7, -15), (8, -15)]:
        seasonal[months == m] = adj

    daily = np.zeros(T)
    for h_range, adj in [((2, 3, 4, 5, 6), -20), ((8, 9, 10, 11, 12, 13, 14, 15, 16), 10),
                         ((17, 18, 19), 25), ((20, 21, 22), 5)]:
        for h in h_range:
            daily[hours == h] = adj

    weekend = np.where((dows >= 5), -8.0, 0.0)

    noise = rng.lognormal(mean=0, sigma=0.3, size=T)
    noise = (noise - np.mean(noise)) * 25  # center at 0, scale

    prices = base + seasonal + daily + weekend + noise

    # Inject negative prices (~5-6% of hours, preferring night + spring/autumn)
    neg_prob = np.full(T, 0.015)
    neg_prob[(hours >= 1) & (hours <= 6)] *= 3
    neg_prob[(months >= 3) & (months <= 5)] *= 2
    neg_prob[(months >= 9) & (months <= 11)] *= 1.5
    neg_mask = rng.random(T) < neg_prob
    prices[neg_mask] = rng.uniform(-80, -5, size=neg_mask.sum())

    # Cluster consecutive negative hours (wind curtailment events last several hours)
    cluster_mask = np.zeros(T, dtype=bool)
    for t in range(T - 1):
        if neg_mask[t] and not neg_mask[t + 1]:
            run_len = rng.integers(1, 3)
            for dt in range(1, run_len + 1):
                if t + dt < T and rng.random() < 0.5:
                    cluster_mask[t + dt] = True
    prices[cluster_mask] = rng.uniform(-80, -5, size=cluster_mask.sum())

    return np.clip(prices, -80, 400)


def build_tou_tariffs():
    """Return array of TOU tariff adders in EUR/MWh for each hour."""
    _, hours, dows, _ = build_calendar()
    tariffs = np.full(T, TOU_NIGHT)
    weekday = dows < 5
    tariffs[weekday & (hours >= 8) & (hours < 17)] = TOU_DAY
    tariffs[weekday & (hours >= 17) & (hours < 19)] = TOU_PEAK
    tariffs[weekday & (hours >= 19) & (hours < 23)] = TOU_DAY
    return tariffs


# ---------------------------------------------------------------------------
# Phase 2: Grid-Only Baseline
# ---------------------------------------------------------------------------

def compute_baseline(spot, tou):
    total_import_cost = D_MW * np.sum(spot + tou)  # EUR
    total_cost = F_SUB + total_import_cost
    total_emissions = D_MW * T * CARBON_INTENSITY / 1000  # tCO2 (225 g/kWh × 10 MW × 8760h)
    lcoe = total_cost / (D_MW * T)  # EUR/MWh
    return {
        "total_cost": total_cost,
        "import_cost": total_import_cost,
        "grid_fees": F_SUB,
        "emissions_tCO2": total_emissions,
        "lcoe": lcoe,
        "peak_import_MW": D_MW,
    }


# ---------------------------------------------------------------------------
# Phase 3: BESS Dispatch Optimization (LP relaxation)
# ---------------------------------------------------------------------------

def annualized_bess_cost(P, E, costs):
    capex_annual = AF_BESS * (costs["c_P_cap"] * P * 1000 + costs["c_E_cap"] * E * 1000)
    opex_annual = costs["c_P_opex"] * P * 1000 + costs["c_E_opex"] * E * 1000
    return capex_annual + opex_annual


def solve_bess_dispatch(P_BESS, E_BESS, spot, tou, verbose=False):
    """Solve LP for optimal BESS dispatch. Returns dict with results."""
    total_price = spot + tou

    model = pyo.ConcreteModel(name=f"BESS_{P_BESS}MW_{E_BESS}MWh")
    model.hours = pyo.RangeSet(0, T - 1)

    model.c = pyo.Var(model.hours, within=pyo.NonNegativeReals, bounds=(0, P_BESS))
    model.d = pyo.Var(model.hours, within=pyo.NonNegativeReals, bounds=(0, P_BESS))
    model.s = pyo.Var(model.hours, within=pyo.NonNegativeReals, bounds=(0, E_BESS))
    model.i = pyo.Var(model.hours, within=pyo.NonNegativeReals, bounds=(0, C_GRID))

    model.obj = pyo.Objective(
        expr=sum(float(total_price[t]) * model.i[t] for t in model.hours),
        sense=pyo.minimize,
    )

    S0 = S0_FRAC * E_BESS

    def balance_rule(m, t):
        return m.i[t] + m.d[t] == D_MW + m.c[t]
    model.balance = pyo.Constraint(model.hours, rule=balance_rule)

    def soc_rule(m, t):
        if t == 0:
            return m.s[t] == S0 + ETA_C * m.c[t] - m.d[t]
        return m.s[t] == m.s[t - 1] + ETA_C * m.c[t] - m.d[t]
    model.soc = pyo.Constraint(model.hours, rule=soc_rule)

    model.wrap_around = pyo.Constraint(expr=model.s[T - 1] >= S0)

    solver = pyo.SolverFactory("appsi_highs")
    solver.options["time_limit"] = 120.0
    result = solver.solve(model, tee=verbose)

    if result.solver.termination_condition != pyo.TerminationCondition.optimal:
        return None

    c_vals = np.array([pyo.value(model.c[t]) for t in range(T)])
    d_vals = np.array([pyo.value(model.d[t]) for t in range(T)])
    s_vals = np.array([pyo.value(model.s[t]) for t in range(T)])
    i_vals = np.array([pyo.value(model.i[t]) for t in range(T)])

    import_cost = float(np.sum(total_price * i_vals))
    cycles = float(np.sum(d_vals)) / E_BESS if E_BESS > 0 else 0

    return {
        "import_cost": import_cost,
        "charge": c_vals,
        "discharge": d_vals,
        "soc": s_vals,
        "grid_import": i_vals,
        "cycles": cycles,
    }


def run_bess_optimization(spot, tou, bess_costs):
    """Enumerate all BESS configs, return results dict keyed by (P, tau).

    Each config includes DR revenue (DSU capacity payment + energy arbitrage)
    so that config selection can account for the EirGrid capacity market.
    """
    results = {}
    for P in P_OPTIONS:
        for tau in TAU_OPTIONS:
            E = P * tau
            label = f"{P}MW/{E}MWh ({tau}h)"
            print(f"  Solving {label} ...", end=" ", flush=True)
            dispatch = solve_bess_dispatch(P, E, spot, tou)
            if dispatch is None:
                print("INFEASIBLE")
                continue
            bess_annual = annualized_bess_cost(P, E, bess_costs)
            total = F_SUB + bess_annual + dispatch["import_cost"]
            dr_info = compute_dr_revenue(dispatch, P, E)
            net_cost = total - dr_info["dr_revenue"]
            emissions = float(np.sum(dispatch["grid_import"])) * CARBON_INTENSITY / 1000
            results[(P, tau)] = {
                "P_MW": P,
                "tau_h": tau,
                "E_MWh": E,
                "bess_annual_cost": bess_annual,
                "import_cost": dispatch["import_cost"],
                "total_cost": total,
                "net_cost": net_cost,
                "emissions_tCO2": emissions,
                "cycles": dispatch["cycles"],
                "dispatch": dispatch,
                "dr_info": dr_info,
            }
            dsu_tag = " [DSU]" if dr_info["dsu_eligible"] else ""
            print(f"done — €{total / 1e6:.2f}M/yr (net €{net_cost / 1e6:.2f}M/yr){dsu_tag}")
    return results


# ---------------------------------------------------------------------------
# Phase 4: Demand Response Break-Even Analysis
# ---------------------------------------------------------------------------

def identify_dr_events(grid_import, n_events=20, max_consec=3):
    """Identify DR events: top import hours in 16:00-21:00 weekday window, Jun-Sep."""
    _, hours, dows, days = build_calendar()

    eligible = (
        (dows < 5)
        & (hours >= 16) & (hours < 21)
        & (build_calendar()[0] >= 6) & (build_calendar()[0] <= 9)
    )

    daily_max_import = {}
    daily_max_hour = {}
    for t in range(T):
        if not eligible[t]:
            continue
        day = days[t]
        if day not in daily_max_import or grid_import[t] > daily_max_import[day]:
            daily_max_import[day] = grid_import[t]
            daily_max_hour[day] = t

    sorted_days = sorted(daily_max_import.keys(), key=lambda d: daily_max_import[d], reverse=True)

    events = []
    selected_days = set()
    for day in sorted_days:
        if len(events) >= n_events:
            break
        consec_count = sum(1 for sd in selected_days if abs(sd - day) <= max_consec and sd != day)
        consecutive_block = any(
            all((day + offset) in selected_days for offset in range(1, max_consec + 1))
            for _ in [None]
        )
        recent = sum(1 for sd in selected_days if 0 < day - sd <= max_consec)
        if recent >= max_consec:
            continue
        events.append({
            "day": day,
            "start_hour": daily_max_hour[day],
            "duration_h": 2,
            "peak_import": daily_max_import[day],
        })
        selected_days.add(day)

    return events


def compute_5of10_baseline(grid_import, event_hour, events_set):
    """5-of-10 baseline: average of 5 highest non-event same-clock-hour imports from prior 10 days."""
    _, hours_arr, dows, days = build_calendar()
    clock_hour = hours_arr[event_hour]
    event_day = days[event_hour]

    candidates = []
    for lookback in range(1, 30):
        check_day = event_day - lookback
        if check_day < 0:
            break
        check_t = check_day * 24 + clock_hour
        if check_t < 0 or check_t >= T:
            continue
        if dows[check_t] >= 5:
            continue
        if check_t in events_set:
            continue
        candidates.append(grid_import[check_t])
        if len(candidates) >= 10:
            break

    if len(candidates) < 5:
        return np.mean(candidates) if candidates else D_MW

    candidates.sort(reverse=True)
    return np.mean(candidates[:5])


def compute_dr_revenue(dispatch, P_BESS, E_BESS):
    """Compute DSU enrolled capacity and DR revenue for a BESS configuration."""
    grid_import = dispatch["grid_import"]
    soc = dispatch["soc"]

    events = identify_dr_events(grid_import)
    events_hours = set()
    for ev in events:
        for h in range(ev["duration_h"]):
            events_hours.add(ev["start_hour"] + h)

    for ev in events:
        t_start = ev["start_hour"]
        baseline_import = compute_5of10_baseline(grid_import, t_start, events_hours)
        ev["baseline_import_MW"] = baseline_import

        curtailed_total = 0.0
        capacity_total = 0.0
        for h in range(ev["duration_h"]):
            t = t_start + h
            if t >= T:
                break
            avail_discharge = min(P_BESS, soc[t] if t > 0 else S0_FRAC * E_BESS)
            actual_import = grid_import[t]
            curtailed = max(0, baseline_import - actual_import)
            capacity_claim = min(baseline_import, avail_discharge)
            curtailed_total += curtailed
            capacity_total += capacity_claim

        ev["curtailed_MWh"] = curtailed_total
        ev["capacity_claim_MW"] = capacity_total / ev["duration_h"]

    enrolled_capacity_MW = float(np.mean([ev["capacity_claim_MW"] for ev in events]))
    dsu_eligible = enrolled_capacity_MW >= DSU_MIN_MW

    _, hours_arr, dows_arr, _ = build_calendar()
    peak_mask = (dows_arr < 5) & (hours_arr >= 16) & (hours_arr < 21)
    annual_peak_discharge_MWh = float(np.sum(dispatch["discharge"][peak_mask]))

    annual_cap_payment = EIRGRID_CAP_RATE * 1000 * enrolled_capacity_MW if dsu_eligible else 0.0
    energy_arb_revenue = ENERGY_ARB_RATE * annual_peak_discharge_MWh
    dr_revenue = annual_cap_payment + energy_arb_revenue

    return {
        "events": events,
        "enrolled_capacity_MW": enrolled_capacity_MW,
        "dsu_eligible": dsu_eligible,
        "annual_cap_payment": annual_cap_payment,
        "energy_arb_revenue": energy_arb_revenue,
        "dr_revenue": dr_revenue,
        "annual_peak_discharge_MWh": annual_peak_discharge_MWh,
    }


def discount_factor(P, beta):
    return 1.0 - beta * (P / P_MAX)


def run_beta_sweep(bess_results, beta_values=BETA_VALUES):
    sweep = []
    for beta in beta_values:
        configs = {}
        for key, val in bess_results.items():
            P = val["P_MW"]
            p = discount_factor(P, beta)
            raw_dr = val["dr_info"]["dr_revenue"]
            adj_dr = raw_dr * p
            adj_net_cost = val["total_cost"] - adj_dr
            configs[key] = {
                "P_MW": P,
                "tau_h": val["tau_h"],
                "E_MWh": val["E_MWh"],
                "total_cost": val["total_cost"],
                "raw_dr_revenue": raw_dr,
                "discount_factor": p,
                "adjusted_dr_revenue": adj_dr,
                "adjusted_net_cost": adj_net_cost,
            }
        best_key = min(configs, key=lambda k: configs[k]["adjusted_net_cost"])
        sweep.append({
            "beta": beta,
            "configs": configs,
            "best_key": best_key,
            "best_net_cost": configs[best_key]["adjusted_net_cost"],
            "best_P_MW": configs[best_key]["P_MW"],
            "best_E_MWh": configs[best_key]["E_MWh"],
        })
    return {"beta_values": beta_values, "sweep_results": sweep}


def dr_breakeven_analysis(bess_result, baseline_cost):
    """Breakeven sweep using pre-computed DR info from BESS config selection."""
    dr_info = bess_result["dr_info"]
    enrolled_capacity_MW = dr_info["enrolled_capacity_MW"]
    dsu_eligible = dr_info["dsu_eligible"]
    annual_peak_discharge_MWh = dr_info["annual_peak_discharge_MWh"]

    cap_rates = np.linspace(0, 250, 51)      # k€/MW/yr
    energy_rates = np.linspace(0, 150, 31)    # EUR/MWh

    bess_deficit = bess_result["total_cost"] - baseline_cost

    breakeven_grid = np.zeros((len(energy_rates), len(cap_rates)))
    for j, cr in enumerate(cap_rates):
        for k, er in enumerate(energy_rates):
            cap_rev = cr * 1000 * enrolled_capacity_MW if dsu_eligible else 0.0
            energy_rev = er * annual_peak_discharge_MWh
            breakeven_grid[k, j] = cap_rev + energy_rev + bess_deficit

    return {
        **dr_info,
        "cap_rates": cap_rates,
        "energy_rates": energy_rates,
        "breakeven_grid": breakeven_grid,
        "bess_deficit": bess_deficit,
        "dr_net": bess_deficit + dr_info["dr_revenue"],
    }


# ---------------------------------------------------------------------------
# Phase 5: Scenario Summary
# ---------------------------------------------------------------------------

def build_scenario_summary(baseline, bess_result, dr_result, bess_costs):
    P = bess_result["P_MW"]
    E = bess_result["E_MWh"]
    capex = bess_costs["c_P_cap"] * P * 1000 + bess_costs["c_E_cap"] * E * 1000

    bess_savings = baseline["total_cost"] - bess_result["total_cost"]
    bess_payback = capex / bess_savings if bess_savings > 0 else float("inf")

    dr_savings = bess_savings + dr_result["dr_revenue"]
    dr_payback = capex / dr_savings if dr_savings > 0 else float("inf")
    dr_total_cost = bess_result["total_cost"] - dr_result["dr_revenue"]

    return {
        "Grid-Only": {
            "ALCC (M€/yr)": baseline["total_cost"] / 1e6,
            "LCOE (EUR/MWh)": baseline["lcoe"],
            "Emissions (tCO₂/yr)": baseline["emissions_tCO2"],
            "Peak Import (MW)": baseline["peak_import_MW"],
            "BESS Cycles/yr": 0,
            "Payback (years)": "N/A",
            "Annual Savings (€)": 0,
        },
        "Grid+BESS": {
            "ALCC (M€/yr)": bess_result["total_cost"] / 1e6,
            "LCOE (EUR/MWh)": bess_result["total_cost"] / (D_MW * T),
            "Emissions (tCO₂/yr)": bess_result["emissions_tCO2"],
            "Peak Import (MW)": float(np.max(bess_result["dispatch"]["grid_import"])),
            "BESS Cycles/yr": bess_result["cycles"],
            "Payback (years)": bess_payback,
            "Annual Savings (€)": bess_savings,
        },
        "Grid+BESS+DR": {
            "ALCC (M€/yr)": dr_total_cost / 1e6,
            "LCOE (EUR/MWh)": dr_total_cost / (D_MW * T),
            "Emissions (tCO₂/yr)": bess_result["emissions_tCO2"],
            "Peak Import (MW)": float(np.max(bess_result["dispatch"]["grid_import"])),
            "BESS Cycles/yr": bess_result["cycles"],
            "Payback (years)": dr_payback,
            "Annual Savings (€)": dr_savings,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("BESS + DR Optimization Model — 10 MW Dublin Data Center")
    print("=" * 60)

    # Phase 1: Generate data
    print("\n[Phase 1] Generating synthetic spot prices and TOU tariffs...")
    spot = generate_spot_prices()
    tou = build_tou_tariffs()
    print(f"  Spot prices: mean={spot.mean():.1f}, min={spot.min():.1f}, max={spot.max():.1f} EUR/MWh")
    print(f"  Negative price hours: {(spot < 0).sum()} ({(spot < 0).mean() * 100:.1f}%)")

    # Phase 2: Baseline
    print("\n[Phase 2] Computing Grid-Only baseline...")
    baseline = compute_baseline(spot, tou)
    print(f"  Total annual cost: €{baseline['total_cost'] / 1e6:.2f}M")
    print(f"  LCOE: €{baseline['lcoe']:.2f}/MWh")
    print(f"  Emissions: {baseline['emissions_tCO2']:,.0f} tCO₂/yr")

    # Phase 3: BESS optimization
    print("\n[Phase 3a] BESS optimization — Thesis costs (NREL ATB 2025)...")
    bess_results_thesis = run_bess_optimization(spot, tou, BESS_THESIS)

    print("\n[Phase 3b] BESS optimization — Updated costs (BNEF 2025)...")
    bess_results_updated = run_bess_optimization(spot, tou, BESS_UPDATED)

    # Phase 3c: Revenue discount factor sensitivity sweep
    print("\n[Phase 3c] Revenue discount factor sensitivity sweep...")
    beta_sweep = run_beta_sweep(bess_results_updated)
    for entry in beta_sweep["sweep_results"]:
        print(f"  beta={entry['beta']:.2f}: optimal={entry['best_P_MW']}MW/"
              f"{entry['best_E_MWh']}MWh, net_cost=EUR{entry['best_net_cost']/1e6:.2f}M/yr")

    # Select optimal config (updated costs, accounting for DR revenue)
    best_key = min(bess_results_updated, key=lambda k: bess_results_updated[k]["net_cost"])
    best = bess_results_updated[best_key]
    dr_info = best["dr_info"]
    print(f"\n  Optimal config (updated): {best['P_MW']}MW / {best['E_MWh']}MWh ({best_key[1]}h)")
    print(f"  Total cost (pre-DR): €{best['total_cost'] / 1e6:.2f}M/yr")
    print(f"  DR revenue: €{dr_info['dr_revenue'] / 1e6:.2f}M/yr"
          f" (DSU: {'Yes' if dr_info['dsu_eligible'] else 'No'},"
          f" enrolled: {dr_info['enrolled_capacity_MW']:.1f} MW)")
    print(f"  Net cost: €{best['net_cost'] / 1e6:.2f}M/yr")
    print(f"  Savings vs baseline: €{(baseline['total_cost'] - best['net_cost']) / 1e6:.2f}M/yr")

    # Phase 4: DR break-even sensitivity analysis
    print("\n[Phase 4] Demand Response break-even analysis...")
    dr_result = dr_breakeven_analysis(best, baseline["total_cost"])
    print(f"  Events identified: {len(dr_result['events'])}")
    print(f"  DSU capacity payment (€{EIRGRID_CAP_RATE}k/MW/yr): €{dr_result['annual_cap_payment']:,.0f}")
    print(f"  Energy arbitrage (€{ENERGY_ARB_RATE}/MWh): €{dr_result['energy_arb_revenue']:,.0f}")
    print(f"  Total DR revenue: €{dr_result['dr_revenue']:,.0f}")
    print(f"  BESS deficit vs baseline: €{dr_result['bess_deficit']:,.0f}")
    print(f"  Net with DR: €{dr_result['dr_net']:,.0f} ({'profitable' if dr_result['dr_net'] > 0 else 'not profitable'})")

    # Phase 5: Summary
    print("\n[Phase 5] Building scenario summary...")
    summary = build_scenario_summary(baseline, best, dr_result, BESS_UPDATED)
    for scenario, metrics in summary.items():
        print(f"\n  {scenario}:")
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"    {k}: {v:,.2f}")
            else:
                print(f"    {k}: {v}")

    # Phase 6: Export results for figure generation
    print("\n[Phase 6] Exporting results...")
    optimal_dispatch = best["dispatch"]
    results_data = {
        "spot": spot,
        "tou": tou,
        "baseline": baseline,
        "optimal_dispatch": optimal_dispatch,
        "best_config": {
            "P_MW": best["P_MW"],
            "E_MWh": best["E_MWh"],
            "total_cost": best["total_cost"],
            "net_cost": best["net_cost"],
            "bess_annual_cost": best["bess_annual_cost"],
            "emissions_tCO2": best["emissions_tCO2"],
            "cycles": best["cycles"],
        },
        "dr_result": dr_result,
        "summary": summary,
        "bess_results_thesis": {
            key: {"bess_annual_cost": val["bess_annual_cost"], "total_cost": val["total_cost"]}
            for key, val in bess_results_thesis.items()
        },
        "bess_results_updated": {
            key: {
                "bess_annual_cost": val["bess_annual_cost"],
                "total_cost": val["total_cost"],
                "net_cost": val["net_cost"],
                "dr_revenue": val["dr_info"]["dr_revenue"],
                "dsu_eligible": val["dr_info"]["dsu_eligible"],
            }
            for key, val in bess_results_updated.items()
        },
        "beta_sweep": beta_sweep,
        "payback_data": {
            "capex": BESS_UPDATED["c_P_cap"] * best["P_MW"] * 1000
                     + BESS_UPDATED["c_E_cap"] * best["E_MWh"] * 1000,
            "annual_opex": BESS_UPDATED["c_P_opex"] * best["P_MW"] * 1000
                           + BESS_UPDATED["c_E_opex"] * best["E_MWh"] * 1000,
            "energy_savings": baseline["import_cost"] - best["dispatch"]["import_cost"],
            "dr_revenue": dr_info["dr_revenue"],
            "wacc": WACC,
            "lifetime": LT_BESS,
            "P_MW": best["P_MW"],
            "E_MWh": best["E_MWh"],
        },
    }
    with open(RESULTS_PKL, "wb") as f:
        pickle.dump(results_data, f)
    print(f"  Results saved: {RESULTS_PKL}")

    print("\n" + "=" * 60)
    print("DONE.")
    print(f"  Results: {RESULTS_PKL}")
    print("=" * 60)


if __name__ == "__main__":
    main()
