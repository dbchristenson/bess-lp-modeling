"""
Generate Excel workbook from BESS + DR optimization results.

Reads results.pkl exported by build_model.py and produces Excel workbook.

Run: uv run python build_workbook.py
"""

import pickle
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_XLSX = SCRIPT_DIR / "BESS_DR_Model_Results.xlsx"
RESULTS_PKL = SCRIPT_DIR / "results.pkl"

T = 8760
YEAR = 2023
D_MW = 10.0
CARBON_INTENSITY = 225

BESS_UPDATED = {
    "label": "NREL ATB 2024 Adv.",
    "c_P_cap": 221.4,
    "c_E_cap": 239.6,
    "c_P_opex": 5.5,
    "c_E_opex": 6.0,
}

WACC = 0.08
LT_BESS = 15
AF_BESS = WACC * (1 + WACC) ** LT_BESS / ((1 + WACC) ** LT_BESS - 1)

P_OPTIONS = [2, 4, 6, 8, 10]
TAU_OPTIONS = [1, 2, 4]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HEADER_FONT = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)
NUM_FMT_EUR = '#,##0'
NUM_FMT_EUR_DEC = '#,##0.00'
NUM_FMT_PCT = '0.0%'


def hour_index_to_datetime(h):
    return datetime(YEAR, 1, 1) + timedelta(hours=int(h))


def build_calendar():
    months = np.empty(T, dtype=int)
    hours = np.empty(T, dtype=int)
    dows = np.empty(T, dtype=int)
    days = np.empty(T, dtype=int)
    for h in range(T):
        dt = hour_index_to_datetime(h)
        months[h] = dt.month
        hours[h] = dt.hour
        dows[h] = dt.weekday()
        days[h] = h // 24
    return months, hours, dows, days


def style_header_row(ws, row, ncols):
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = BORDER


def style_data_cell(ws, row, col, fmt=None):
    cell = ws.cell(row=row, column=col)
    cell.border = BORDER
    cell.alignment = Alignment(horizontal="center")
    if fmt:
        cell.number_format = fmt


def auto_width(ws):
    for col_cells in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col_cells[0].column)
        for cell in col_cells:
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_len + 4, 30)


# ---------------------------------------------------------------------------
# Sheet Writers
# ---------------------------------------------------------------------------

def write_summary_sheet(wb, summary):
    ws = wb.create_sheet("Summary")
    headers = ["Metric"] + list(summary.keys())
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    style_header_row(ws, 1, len(headers))

    metrics = list(next(iter(summary.values())).keys())
    for r, metric in enumerate(metrics, 2):
        ws.cell(row=r, column=1, value=metric)
        ws.cell(row=r, column=1).border = BORDER
        ws.cell(row=r, column=1).font = Font(bold=True)
        for c, scenario in enumerate(summary.keys(), 2):
            val = summary[scenario][metric]
            ws.cell(row=r, column=c, value=val if val != "N/A" else "N/A")
            fmt = NUM_FMT_EUR_DEC if isinstance(val, float) else None
            style_data_cell(ws, r, c, fmt)
    auto_width(ws)


def write_assumptions_sheet(wb):
    ws = wb.create_sheet("Assumptions")
    headers = ["Parameter", "Thesis Value", "Updated Value", "Unit", "Source"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    style_header_row(ws, 1, len(headers))

    rows = [
        ("DC Load", 10, 10, "MW", "Group agreement"),
        ("Grid Connection (MIC)", 20, 20, "MW", "2× DC load for BESS charging headroom"),
        ("Grid CO₂ Intensity", 225, 225, "gCO₂/kWh", "SEAI"),
        ("TOU Tariff — Day", 65.03, 65.03, "EUR/MWh", "Thesis Table 3.2"),
        ("TOU Tariff — Peak", 66.40, 66.40, "EUR/MWh", "Thesis Table 3.2"),
        ("TOU Tariff — Night", 53.53, 53.53, "EUR/MWh", "Thesis Table 3.2"),
        ("Grid Subscription Fee", 4_403_376, 4_403_376, "EUR/yr", "Thesis Table 3.3"),
        ("BESS Power CapEx", 675, 221.4, "EUR/kW", "NREL ATB 2025 / NREL ATB 2024 Adv."),
        ("BESS Energy CapEx", 165.6, 239.6, "EUR/kWh", "NREL ATB 2025 / NREL ATB 2024 Adv."),
        ("BESS Power O&M", 16.9, 5.5, "EUR/kW-yr", "NREL ATB 2025 / NREL ATB 2024 Adv."),
        ("BESS Energy O&M", 4.11, 6.0, "EUR/kWh-yr", "NREL ATB 2025 / NREL ATB 2024 Adv."),
        ("Round-Trip Efficiency", "95%", "95%", "", "Thesis Table 3.7"),
        ("BESS Lifetime", 15, 15, "years", "Thesis Table 3.7"),
        ("WACC", "8%", "8%", "", "Thesis assumption"),
        ("Capital Recovery Factor", round(AF_BESS, 5), round(AF_BESS, 5), "", "Computed"),
        ("Initial SoC", "50%", "50%", "of E_BESS", "Thesis assumption"),
        ("Spot Price Source", "Synthetic", "Synthetic", "", "Calibrated to 2023 I-SEM stats"),
    ]
    for r, row_data in enumerate(rows, 2):
        for c, val in enumerate(row_data, 1):
            ws.cell(row=r, column=c, value=val)
            style_data_cell(ws, r, c)
    auto_width(ws)


def write_baseline_sheet(wb, spot, tou):
    ws = wb.create_sheet("Baseline")
    headers = ["Month", "Hours", "Avg Spot (EUR/MWh)", "Avg TOU (EUR/MWh)",
               "Import (MWh)", "Energy Cost (EUR)", "Emissions (tCO₂)"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    style_header_row(ws, 1, len(headers))

    months_arr = build_calendar()[0]
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    for m in range(12):
        mask = months_arr == (m + 1)
        n_hours = int(mask.sum())
        avg_spot = float(np.mean(spot[mask]))
        avg_tou = float(np.mean(tou[mask]))
        import_mwh = D_MW * n_hours
        energy_cost = D_MW * float(np.sum((spot + tou)[mask]))
        emissions = import_mwh * CARBON_INTENSITY / 1000

        row = m + 2
        vals = [month_names[m], n_hours, avg_spot, avg_tou, import_mwh, energy_cost, emissions]
        for c, val in enumerate(vals, 1):
            ws.cell(row=row, column=c, value=val)
            fmt = NUM_FMT_EUR_DEC if c in (3, 4) else NUM_FMT_EUR if c in (5, 6) else None
            style_data_cell(ws, row, c, fmt)
    auto_width(ws)


def write_bess_sizing_sheet(wb, bess_results_thesis, bess_results_updated, baseline_cost):
    ws = wb.create_sheet("BESS Sizing")
    headers = ["Config", "P (MW)", "τ (h)", "E (MWh)",
               "Annual BESS Cost (€) [Thesis]", "Total Cost (€) [Thesis]", "Savings (€) [Thesis]",
               "Annual BESS Cost (€) [Updated]", "Total Cost (€) [Updated]", "Savings (€) [Updated]",
               "Payback (yr) [Updated]"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    style_header_row(ws, 1, len(headers))

    best_updated_key = min(bess_results_updated, key=lambda k: bess_results_updated[k]["total_cost"])

    row = 2
    for P in P_OPTIONS:
        for tau in TAU_OPTIONS:
            key = (P, tau)
            if key not in bess_results_thesis:
                continue
            rt = bess_results_thesis[key]
            ru = bess_results_updated[key]
            E = P * tau
            savings_t = baseline_cost - rt["total_cost"]
            savings_u = baseline_cost - ru["total_cost"]
            capex_u = BESS_UPDATED["c_P_cap"] * P * 1000 + BESS_UPDATED["c_E_cap"] * E * 1000
            payback_u = capex_u / savings_u if savings_u > 0 else float("inf")

            vals = [f"{P}MW/{E}MWh", P, tau, E,
                    rt["bess_annual_cost"], rt["total_cost"], savings_t,
                    ru["bess_annual_cost"], ru["total_cost"], savings_u,
                    payback_u if payback_u != float("inf") else "N/A"]
            for c, val in enumerate(vals, 1):
                ws.cell(row=row, column=c, value=val)
                fmt = NUM_FMT_EUR if c >= 5 and isinstance(val, (int, float)) else None
                style_data_cell(ws, row, c, fmt)

            if key == best_updated_key:
                highlight = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
                for c in range(1, len(headers) + 1):
                    ws.cell(row=row, column=c).fill = highlight
            row += 1
    auto_width(ws)


def write_dispatch_sheet(wb, spot, tou, dispatch):
    ws = wb.create_sheet("Optimal Dispatch")
    headers = ["Hour", "Date", "Spot (EUR/MWh)", "TOU (EUR/MWh)",
               "Grid Import (MW)", "Charge (MW)", "Discharge (MW)", "SoC (MWh)", "Hourly Cost (EUR)"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    style_header_row(ws, 1, len(headers))

    for t in range(T):
        row = t + 2
        dt = hour_index_to_datetime(t)
        cost = dispatch["grid_import"][t] * (spot[t] + tou[t])
        vals = [t, dt.strftime("%Y-%m-%d %H:%M"), spot[t], tou[t],
                dispatch["grid_import"][t], dispatch["charge"][t],
                dispatch["discharge"][t], dispatch["soc"][t], cost]
        for c, val in enumerate(vals, 1):
            ws.cell(row=row, column=c, value=val)


def write_dr_sheet(wb, dr_result):
    ws = wb.create_sheet("DR Analysis")
    headers = ["Event #", "Day of Year", "Date", "Start Hour",
               "Duration (h)", "Baseline Import (MW)", "Actual Import (MW)",
               "Curtailed (MWh)", "Capacity Claim (MW)"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    style_header_row(ws, 1, len(headers))

    events = dr_result["events"]
    for idx, ev in enumerate(events):
        row = idx + 2
        dt = hour_index_to_datetime(ev["start_hour"])
        actual_import = D_MW - ev["curtailed_MWh"] / ev["duration_h"] if ev["duration_h"] > 0 else D_MW

        vals = [idx + 1, ev["day"], dt.strftime("%Y-%m-%d"),
                dt.strftime("%H:%M"), ev["duration_h"],
                ev["baseline_import_MW"], actual_import,
                ev["curtailed_MWh"], ev["capacity_claim_MW"]]
        for c, val in enumerate(vals, 1):
            ws.cell(row=row, column=c, value=val)
            fmt = NUM_FMT_EUR_DEC if c >= 6 else None
            style_data_cell(ws, row, c, fmt)

    total_row = len(events) + 2
    ws.cell(row=total_row, column=1, value="TOTAL")
    ws.cell(row=total_row, column=1).font = Font(bold=True)
    ws.cell(row=total_row, column=8, value=sum(e["curtailed_MWh"] for e in events))
    for c in range(1, 10):
        style_data_cell(ws, total_row, c, NUM_FMT_EUR_DEC if c >= 8 else None)

    summary_row = total_row + 2
    ws.cell(row=summary_row, column=1, value="Annual DSU Revenue Model")
    ws.cell(row=summary_row, column=1).font = Font(bold=True)
    enrolled = dr_result.get("enrolled_capacity_MW", 0)
    eligible = dr_result.get("dsu_eligible", False)
    labels = [
        ("Enrolled Capacity (MW)", enrolled),
        ("DSU Eligible (≥4 MW)", "Yes" if eligible else "No"),
        ("EirGrid Capacity Payment (€)", dr_result.get("annual_cap_payment", 0)),
        ("Total DR Revenue (€)", dr_result["dr_revenue"]),
        ("Annual Peak Discharge (MWh)", dr_result.get("annual_peak_discharge_MWh", 0)),
        ("BESS Deficit (€)", dr_result["bess_deficit"]),
        ("Net (€)", dr_result["dr_net"]),
    ]
    for i, (label, val) in enumerate(labels):
        r = summary_row + 1 + i
        ws.cell(row=r, column=1, value=label)
        ws.cell(row=r, column=2, value=val)
        if not isinstance(val, str):
            style_data_cell(ws, r, 2, NUM_FMT_EUR_DEC)

    auto_width(ws)


def write_cost_comparison_sheet(wb, spot, tou, dispatch):
    ws = wb.create_sheet("Cost Comparison")
    headers = ["Month", "Grid-Only Cost (€)", "BESS Import Cost (€)",
               "Savings (€)", "Savings (%)",
               "Grid-Only Emissions (tCO₂)", "BESS Emissions (tCO₂)", "Emissions Saved (tCO₂)"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    style_header_row(ws, 1, len(headers))

    months_arr = build_calendar()[0]
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    for m in range(12):
        mask = months_arr == (m + 1)
        total_price = spot + tou
        baseline_cost = D_MW * float(np.sum(total_price[mask]))
        bess_cost = float(np.sum(dispatch["grid_import"][mask] * total_price[mask]))
        savings = baseline_cost - bess_cost
        pct = savings / baseline_cost if baseline_cost > 0 else 0
        base_em = D_MW * int(mask.sum()) * CARBON_INTENSITY / 1000
        bess_em = float(np.sum(dispatch["grid_import"][mask])) * CARBON_INTENSITY / 1000

        row = m + 2
        vals = [month_names[m], baseline_cost, bess_cost, savings, pct,
                base_em, bess_em, base_em - bess_em]
        for c, val in enumerate(vals, 1):
            ws.cell(row=row, column=c, value=val)
            fmt = NUM_FMT_PCT if c == 5 else (NUM_FMT_EUR if c in (2, 3, 4) else NUM_FMT_EUR_DEC)
            style_data_cell(ws, row, c, fmt)
    auto_width(ws)


def write_beta_sweep_sheet(wb, beta_sweep, baseline_cost):
    ws = wb.create_sheet("Beta Sensitivity")

    headers = ["Beta", "Discount Formula", "Optimal P (MW)", "Optimal E (MWh)",
               "Adj. DR Revenue (EUR)", "Adj. Net Cost (EUR)", "Savings vs Grid-Only (EUR)"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    style_header_row(ws, 1, len(headers))

    for r, entry in enumerate(beta_sweep["sweep_results"], 2):
        beta = entry["beta"]
        bk = entry["best_key"]
        cfg = entry["configs"][bk]
        vals = [
            beta,
            f"1 - {beta:.2f} * (P / 10)",
            cfg["P_MW"],
            cfg["E_MWh"],
            cfg["adjusted_dr_revenue"],
            cfg["adjusted_net_cost"],
            baseline_cost - cfg["adjusted_net_cost"],
        ]
        for c, val in enumerate(vals, 1):
            ws.cell(row=r, column=c, value=val)
            fmt = NUM_FMT_EUR_DEC if c == 1 else (NUM_FMT_EUR if c >= 5 and isinstance(val, (int, float)) else None)
            style_data_cell(ws, r, c, fmt)

    gap_row = len(beta_sweep["sweep_results"]) + 4
    ws.cell(row=gap_row, column=1, value="Adjusted Net Cost by Config and Beta")
    ws.cell(row=gap_row, column=1).font = Font(bold=True, size=12)

    header_row = gap_row + 1
    beta_values = beta_sweep["beta_values"]
    ws.cell(row=header_row, column=1, value="Config")
    for j, beta in enumerate(beta_values):
        ws.cell(row=header_row, column=j + 2, value=f"β={beta:.2f}")
    style_header_row(ws, header_row, len(beta_values) + 1)

    data_row = header_row + 1
    for P in P_OPTIONS:
        for tau in TAU_OPTIONS:
            key = (P, tau)
            E = P * tau
            ws.cell(row=data_row, column=1, value=f"{P}MW/{E}MWh")
            style_data_cell(ws, data_row, 1)
            for j, entry in enumerate(beta_sweep["sweep_results"]):
                if key in entry["configs"]:
                    val = entry["configs"][key]["adjusted_net_cost"]
                    ws.cell(row=data_row, column=j + 2, value=val)
                    style_data_cell(ws, data_row, j + 2, NUM_FMT_EUR)
            data_row += 1

    auto_width(ws)


# ---------------------------------------------------------------------------
# Workbook Assembly
# ---------------------------------------------------------------------------

def generate_workbook(summary, spot, tou, bess_results_thesis, bess_results_updated,
                      baseline, optimal_dispatch, dr_result, baseline_cost, beta_sweep=None):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    write_summary_sheet(wb, summary)
    write_assumptions_sheet(wb)
    write_baseline_sheet(wb, spot, tou)
    write_bess_sizing_sheet(wb, bess_results_thesis, bess_results_updated, baseline_cost)
    write_dispatch_sheet(wb, spot, tou, optimal_dispatch)
    write_dr_sheet(wb, dr_result)
    write_cost_comparison_sheet(wb, spot, tou, optimal_dispatch)

    if beta_sweep is not None:
        write_beta_sweep_sheet(wb, beta_sweep, baseline_cost)

    wb.save(OUTPUT_XLSX)
    print(f"  Workbook saved: {OUTPUT_XLSX}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading results from", RESULTS_PKL)
    with open(RESULTS_PKL, "rb") as f:
        results = pickle.load(f)

    spot = results["spot"]
    tou = results["tou"]
    baseline = results["baseline"]
    optimal_dispatch = results["optimal_dispatch"]
    dr_result = results["dr_result"]
    summary = results["summary"]
    bess_results_thesis = results["bess_results_thesis"]
    bess_results_updated = results["bess_results_updated"]

    beta_sweep = results.get("beta_sweep")

    print("Generating Excel workbook...")
    generate_workbook(summary, spot, tou, bess_results_thesis, bess_results_updated,
                      baseline, optimal_dispatch, dr_result, baseline["total_cost"],
                      beta_sweep=beta_sweep)

    print(f"Done. Workbook saved to {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
