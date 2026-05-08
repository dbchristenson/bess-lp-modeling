"""
Generate publication-quality figures from BESS + DR optimization results.

Reads results.pkl exported by build_model.py and produces PNG figures.

Run: uv run build_figures.py
"""

import pickle
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
FIGURES_DIR = SCRIPT_DIR / "figures"
RESULTS_PKL = SCRIPT_DIR / "results.pkl"

T = 8760
YEAR = 2023
D_MW = 10.0
P_OPTIONS = [2, 4, 6, 8, 10]
TAU_OPTIONS = [1, 2, 4]

DPI = 300

PAL = {
    "grid": "#4A6FA5",
    "charge": "#5C4D7D",
    "discharge": "#E9A820",
    "load": "#264653",
    "spot": "#D4A017",
    "spot_fill": "#E9C46A",
    "soc": "#7B2D8E",
    "baseline": "#8D99AE",
    "dr": "#F4A261",
    "positive": "#2A9D8F",
    "negative": "#E63946",
    "neutral": "#4A6FA5",
}


def apply_theme():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 11,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.alpha": 0.3,
            "grid.linewidth": 0.5,
            "legend.fontsize": 10,
            "legend.framealpha": 0.9,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
        }
    )


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


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def fig1_spot_price_heatmap(spot):
    months_arr, hours_arr, _, _ = build_calendar()
    heatmap = np.zeros((24, 12))
    counts = np.zeros((24, 12))
    for t in range(T):
        h, m = hours_arr[t], months_arr[t] - 1
        heatmap[h, m] += spot[t]
        counts[h, m] += 1
    heatmap /= np.maximum(counts, 1)

    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(
        heatmap,
        aspect="auto",
        cmap="RdYlBu_r",
        origin="lower",
        vmin=-10,
        vmax=160,
        interpolation="nearest",
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("Hour of Day")
    ax.set_title("Average Hourly I-SEM Spot Price (EUR/MWh), 2023")
    ax.set_xticks(range(12))
    ax.set_xticklabels(
        [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
    )
    ax.set_yticks(range(0, 24, 2))
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    cb.set_label("EUR/MWh")
    cb.outline.set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "01_spot_price_heatmap.png", dpi=DPI)
    plt.close(fig)


def _dispatch_figure(spot, dispatch, t_start, t_end, title, filename):
    sl = slice(t_start, t_end)
    n = t_end - t_start
    x = np.arange(n)

    grid_imp = dispatch["grid_import"][sl]
    load_from_grid = np.minimum(grid_imp, D_MW)
    load_from_bess = np.maximum(D_MW - grid_imp, 0)
    charging = np.maximum(grid_imp - D_MW, 0)

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(14, 7),
        height_ratios=[3, 1],
        sharex=True,
        layout="constrained",
    )

    ax1.bar(
        x,
        load_from_grid,
        color=PAL["grid"],
        alpha=0.7,
        width=0.85,
        label="Grid → Load",
    )
    ax1.bar(
        x,
        load_from_bess,
        bottom=load_from_grid,
        color=PAL["discharge"],
        alpha=0.7,
        width=0.85,
        label="Discharging to Load",
    )
    ax1.bar(
        x,
        charging,
        bottom=D_MW,
        color=PAL["charge"],
        alpha=0.7,
        width=0.85,
        label="Charging from Grid",
    )
    ax1.axhline(
        y=D_MW,
        color=PAL["load"],
        linestyle="--",
        linewidth=1.8,
        label=f"DC Load ({D_MW:.0f} MW)",
        zorder=5,
    )

    ax1.set_ylabel("Power (MW)")
    ax1.set_title(title)
    ax1.set_ylim(0, max(grid_imp) * 1.15)
    ax1.set_xlim(-0.5, n - 0.5)
    ax1.legend(loc="upper right", ncol=4, frameon=True)
    ax1.spines["bottom"].set_visible(False)
    ax1.tick_params(axis="x", length=0)

    ax2.fill_between(
        x, spot[sl], alpha=0.3, color=PAL["spot_fill"], step="mid"
    )
    ax2.step(x, spot[sl], where="mid", color=PAL["spot"], linewidth=1.5)
    ax2.set_ylabel("Spot Price\n(EUR/MWh)")
    ax2.set_xlabel("Hour")

    tick_step = 6
    ax2.set_xticks(range(0, n, tick_step))
    ax2.set_xticklabels(
        [f"{(t_start + h) % 24:02d}:00" for h in range(0, n, tick_step)],
        rotation=45,
        ha="right",
    )

    for h in range(24, n, 24):
        ax1.axvline(h - 0.5, color="#ccc", linewidth=0.8, linestyle=":")
        ax2.axvline(h - 0.5, color="#ccc", linewidth=0.8, linestyle=":")

    fig.savefig(FIGURES_DIR / filename, dpi=DPI)
    plt.close(fig)


def fig2_dispatch_winter(spot, tou, dispatch):
    months_arr, _, _, days = build_calendar()

    dec_indices = np.where(months_arr == 12)[0]
    daily_avg = {}
    for t in dec_indices:
        day = days[t]
        daily_avg.setdefault(day, []).append(spot[t])
    daily_avg = {d: np.mean(v) for d, v in daily_avg.items()}
    if not daily_avg:
        return
    peak_day = max(daily_avg, key=daily_avg.get)

    t_start = peak_day * 24
    t_end = min(t_start + 48, T)
    dt_start = hour_index_to_datetime(t_start)

    _dispatch_figure(
        spot,
        dispatch,
        t_start,
        t_end,
        f"48-Hour Dispatch — Winter Peak ({dt_start.strftime('%d %b')})",
        "02_dispatch_winter_peak.png",
    )


def fig3_dispatch_spring(spot, tou, dispatch):
    months_arr, _, _, days = build_calendar()

    apr_indices = np.where(months_arr == 4)[0]
    daily_avg = {}
    for t in apr_indices:
        day = days[t]
        daily_avg.setdefault(day, []).append(spot[t])
    daily_avg = {d: np.mean(v) for d, v in daily_avg.items()}
    if not daily_avg:
        return
    low_day = min(daily_avg, key=daily_avg.get)

    t_start = low_day * 24
    t_end = min(t_start + 48, T)
    dt_start = hour_index_to_datetime(t_start)

    _dispatch_figure(
        spot,
        dispatch,
        t_start,
        t_end,
        f"48-Hour Dispatch — Spring Low-Price ({dt_start.strftime('%d %b')})",
        "03_dispatch_spring_low.png",
    )


def fig4_cost_waterfall(baseline, bess_result, dr_result):
    fig, ax = plt.subplots(figsize=(10, 5.5))

    grid_only = baseline["total_cost"] / 1e6
    arb_savings = (
        baseline["total_cost"]
        - bess_result["total_cost"]
        + bess_result["bess_annual_cost"]
    ) / 1e6
    bess_cost = bess_result["bess_annual_cost"] / 1e6
    dr_rev = dr_result["dr_revenue"] / 1e6
    net_savings = arb_savings - bess_cost + dr_rev
    net_cost = grid_only - net_savings

    categories = [
        "Arbitrage\nSavings",
        "BESS Annual\nCost",
        "DR\nRevenue",
        "Net\nSavings",
    ]
    values = [arb_savings, -bess_cost, dr_rev, net_savings]
    colors = [
        PAL["positive"],
        PAL["negative"],
        PAL["positive"],
        PAL["neutral"],
    ]

    y_pos = np.arange(len(categories))
    ax.barh(
        y_pos,
        values,
        color=colors,
        height=0.55,
        edgecolor="white",
        linewidth=1.5,
        alpha=0.85,
    )

    ax.axhline(2.55, color="#ddd", linewidth=1)

    pad = max(abs(v) for v in values) * 0.04
    for i, (v, c) in enumerate(zip(values, colors)):
        if v >= 0:
            ax.text(
                v + pad,
                y_pos[i],
                f"+€{v:.2f}M/yr",
                va="center",
                ha="left",
                fontsize=11,
                fontweight="bold",
                color=c,
            )
        else:
            ax.text(
                pad,
                y_pos[i],
                f"−€{abs(v):.2f}M/yr",
                va="center",
                ha="left",
                fontsize=11,
                fontweight="bold",
                color=c,
            )

    ax.axvline(0, color="#333", linewidth=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("Annual Impact (M€/yr)")
    ax.set_title(f"Cost Impact vs. Grid-Only Baseline (€{grid_only:.2f}M/yr)")

    if net_savings >= 0:
        summary = (
            f"Net annual cost: €{net_cost:.2f}M/yr  "
            f"(−{net_savings / grid_only * 100:.1f}%)"
        )
    else:
        summary = (
            f"Net annual cost: €{net_cost:.2f}M/yr  "
            f"(+{-net_savings / grid_only * 100:.1f}%)"
        )
    ax.text(
        0.98,
        0.05,
        summary,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=11,
        fontweight="bold",
        bbox=dict(
            boxstyle="round,pad=0.5", facecolor="#f0f0f0", edgecolor="#ccc"
        ),
    )

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "04_cost_waterfall.png", dpi=DPI)
    plt.close(fig)


def fig5_weekly_soc(spot, dispatch, bess_E):
    months_arr = build_calendar()[0]
    jan_start = np.where(months_arr == 1)[0][0]
    week_start = jan_start + 7 * 24
    week_end = min(week_start + 168, T)
    sl = slice(week_start, week_end)
    n = week_end - week_start

    fig, ax1 = plt.subplots(figsize=(14, 5))

    x = np.arange(n)
    ax1.fill_between(x, 0, dispatch["soc"][sl], alpha=0.2, color=PAL["soc"])
    ax1.plot(
        x, dispatch["soc"][sl], color=PAL["soc"], linewidth=1.8, label="SoC"
    )
    ax1.set_ylabel("State of Charge (MWh)", color=PAL["soc"])
    ax1.set_ylim(0, bess_E * 1.1)
    ax1.tick_params(axis="y", labelcolor=PAL["soc"])
    ax1.spines["left"].set_color(PAL["soc"])
    ax1.spines["right"].set_visible(True)

    ax2 = ax1.twinx()
    ax2.plot(
        x,
        spot[sl],
        color=PAL["spot"],
        linewidth=1,
        alpha=0.55,
        label="Spot Price",
    )
    ax2.set_ylabel("Spot Price (EUR/MWh)", color=PAL["spot"])
    ax2.tick_params(axis="y", labelcolor=PAL["spot"])
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(PAL["spot"])
    ax2.spines["left"].set_visible(False)

    dt_start = hour_index_to_datetime(week_start)
    ax1.set_xlabel("Day")
    ax1.set_title(
        f"Weekly Battery SoC Profile — "
        f"{dt_start.strftime('%d %b')} to "
        f"{hour_index_to_datetime(week_end).strftime('%d %b %Y')}"
    )

    day_ticks = []
    day_labels = []
    for d in range(7):
        dt = dt_start + timedelta(days=d)
        day_ticks.append(d * 24 + 12)
        day_labels.append(dt.strftime("%a\n%d %b"))
    ax1.set_xticks(day_ticks)
    ax1.set_xticklabels(day_labels)

    for d in range(1, 7):
        ax1.axvline(d * 24, color="#ddd", linewidth=0.8, linestyle=":")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "05_weekly_soc_profile.png", dpi=DPI)
    plt.close(fig)


def fig6_bess_config_comparison(bess_results, baseline_cost):
    fig, ax = plt.subplots(figsize=(12, 6))

    tau_colors = {1: PAL["grid"], 2: PAL["dr"], 4: PAL["discharge"]}
    width = 0.25
    group_width = len(TAU_OPTIONS) * width + 0.15

    positions = []
    values = []
    bar_colors = []

    for idx_p, P in enumerate(P_OPTIONS):
        for idx_t, tau in enumerate(TAU_OPTIONS):
            key = (P, tau)
            if key not in bess_results:
                continue
            pos = idx_p * group_width + idx_t * width
            positions.append(pos)
            savings = (baseline_cost - bess_results[key]["total_cost"]) / 1e6
            values.append(savings)
            bar_colors.append(tau_colors[tau])

    ax.bar(
        positions,
        values,
        width=width,
        color=bar_colors,
        alpha=0.85,
        edgecolor="white",
        linewidth=1,
    )
    ax.axhline(
        0,
        color=PAL["baseline"],
        linewidth=2,
        linestyle="--",
        label="Grid-Only Breakeven",
    )

    center_positions = [
        idx_p * group_width + width for idx_p in range(len(P_OPTIONS))
    ]
    ax.set_xticks(center_positions)
    ax.set_xticklabels([f"{P} MW" for P in P_OPTIONS])

    legend_elements = [
        mpatches.Patch(
            facecolor=tau_colors[t], alpha=0.85, label=f"{t}h duration"
        )
        for t in TAU_OPTIONS
    ]
    legend_elements.append(
        plt.Line2D(
            [0],
            [0],
            color=PAL["baseline"],
            linestyle="--",
            linewidth=2,
            label="Breakeven",
        )
    )
    ax.legend(handles=legend_elements)

    ax.set_xlabel("BESS Power Rating")
    ax.set_ylabel("Net Annual Savings vs. Grid-Only (M€/yr)")
    ax.set_title("BESS Configuration Comparison — Net Savings")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("€%.2fM"))

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "06_bess_config_comparison.png", dpi=DPI)
    plt.close(fig)


def fig7_dr_breakeven(dr_result):
    fig, ax = plt.subplots(figsize=(10, 6))

    cap_rates = dr_result["cap_rates"]
    net_savings = dr_result["breakeven_curve"] / 1e6

    ax.plot(cap_rates, net_savings, color=PAL["grid"], linewidth=2.5, zorder=3)
    ax.axhline(0, color="#999", linewidth=1, linestyle="--", zorder=1)

    ax.fill_between(
        cap_rates, net_savings, 0,
        where=(net_savings >= 0), color=PAL["positive"], alpha=0.15,
        label="Net profitable",
    )
    ax.fill_between(
        cap_rates, net_savings, 0,
        where=(net_savings < 0), color=PAL["negative"], alpha=0.15,
        label="Net loss",
    )

    eirgrid_rate = 138
    eirgrid_idx = np.argmin(np.abs(cap_rates - eirgrid_rate))
    eirgrid_val = net_savings[eirgrid_idx]

    ax.plot(
        eirgrid_rate, eirgrid_val,
        marker="*", markersize=18,
        color="white", markeredgecolor="#333",
        markeredgewidth=1.5, zorder=5,
    )
    ax.annotate(
        f"EirGrid T-1 rate\n(€{eirgrid_rate}k/MW/yr)",
        xy=(eirgrid_rate, eirgrid_val),
        xytext=(eirgrid_rate + 30, eirgrid_val - 0.15),
        fontsize=10, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#333", lw=1.5),
        bbox=dict(
            boxstyle="round,pad=0.4",
            facecolor="white", edgecolor="#333", alpha=0.9,
        ),
    )

    ax.set_xlabel("DSU Capacity Payment (k€/MW/yr)")
    ax.set_ylabel("Net Annual Savings vs. Grid-Only (M€/yr)")
    ax.set_title("DR Break-Even Analysis — EirGrid DSU Capacity Payments")
    ax.legend(loc="lower right")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("€%.2fM"))

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "07_dr_breakeven_capacity.png", dpi=DPI)
    plt.close(fig)


def fig9_payback_period(payback_data):
    capex = payback_data["capex"]
    opex = payback_data["annual_opex"]
    savings = payback_data["energy_savings"]
    dr_rev = payback_data["dr_revenue"]
    wacc = payback_data["wacc"]
    lt = payback_data["lifetime"]
    P = payback_data["P_MW"]
    E = payback_data["E_MWh"]

    annual_bess = savings - opex
    annual_dr = annual_bess + dr_rev
    years = np.arange(0, lt + 1)

    cum_simple_bess = np.concatenate(
        [[-capex], -capex + np.cumsum(np.full(lt, annual_bess))]
    )
    cum_simple_dr = np.concatenate(
        [[-capex], -capex + np.cumsum(np.full(lt, annual_dr))]
    )

    disc = np.array([1 / (1 + wacc) ** y for y in range(1, lt + 1)])
    cum_disc_bess = np.concatenate(
        [[-capex], -capex + np.cumsum(annual_bess * disc)]
    )
    cum_disc_dr = np.concatenate(
        [[-capex], -capex + np.cumsum(annual_dr * disc)]
    )

    def find_pb(c):
        for i in range(1, len(c)):
            if c[i] >= 0 > c[i - 1]:
                return i - 1 + (-c[i - 1]) / (c[i] - c[i - 1])
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    panels = [
        (
            ax1,
            cum_simple_bess,
            cum_simple_dr,
            "Simple Payback",
            "Cumulative Cash Flow (M€)",
            False,
        ),
        (
            ax2,
            cum_disc_bess,
            cum_disc_dr,
            f"Discounted Payback (WACC = {wacc:.0%})",
            "Cumulative Discounted Cash Flow (M€)",
            True,
        ),
    ]

    for ax, cb, cd, title, ylabel, show_npv in panels:
        ax.plot(
            years,
            cb / 1e6,
            color=PAL["grid"],
            linewidth=2.5,
            marker="o",
            markersize=4,
            label="BESS Only",
            zorder=3,
        )
        ax.plot(
            years,
            cd / 1e6,
            color=PAL["dr"],
            linewidth=2.5,
            marker="s",
            markersize=4,
            label="BESS + DR",
            zorder=3,
        )
        ax.fill_between(
            years,
            np.minimum(cb, cd) / 1e6,
            0,
            where=(np.minimum(cb, cd) < 0),
            alpha=0.06,
            color=PAL["negative"],
        )
        ax.axhline(0, color="#333", linewidth=0.8, linestyle="--", alpha=0.5)

        pb_bess = find_pb(cb)
        pb_dr = find_pb(cd)

        for pb, color, y_sign in [
            (pb_dr, PAL["dr"], 1),
            (pb_bess, PAL["grid"], -1),
        ]:
            if pb is not None and pb <= lt:
                ax.plot(pb, 0, marker="D", color=color, markersize=8, zorder=5)
                ax.annotate(
                    f"{pb:.1f} yr",
                    xy=(pb, 0),
                    xytext=(-12, 30 * y_sign),
                    textcoords="offset points",
                    fontsize=10,
                    fontweight="bold",
                    color=color,
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.2),
                )

        if show_npv:
            for cum, color, v_off in [
                (cb, PAL["grid"], -24),
                (cd, PAL["dr"], 6),
            ]:
                npv = cum[-1]
                ax.annotate(
                    f"NPV: €{npv / 1e6:+.2f}M",
                    xy=(lt, npv / 1e6),
                    xytext=(-8, v_off),
                    textcoords="offset points",
                    fontsize=9,
                    color=color,
                    ha="right",
                    fontweight="bold",
                )

        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(loc="lower right")
        ax.set_xlim(0, lt)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("€%.1fM"))

    fig.suptitle(
        f"BESS Investment Payback — {P:.0f} MW / {E:.0f} MWh",
        fontsize=14,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "09_payback_period.png", dpi=DPI)
    plt.close(fig)


def fig8_monthly_cost(spot, tou, dispatch):
    months_arr = build_calendar()[0]

    baseline_monthly = np.zeros(12)
    bess_monthly = np.zeros(12)

    for t in range(T):
        m = months_arr[t] - 1
        price = spot[t] + tou[t]
        baseline_monthly[m] += D_MW * price
        bess_monthly[m] += dispatch["grid_import"][t] * price

    savings_pct = (baseline_monthly - bess_monthly) / baseline_monthly * 100

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(12)
    width = 0.35
    ax.bar(
        x - width / 2,
        baseline_monthly / 1e6,
        width,
        color=PAL["baseline"],
        alpha=0.85,
        label="Grid-Only",
        edgecolor="white",
        linewidth=1,
    )
    ax.bar(
        x + width / 2,
        bess_monthly / 1e6,
        width,
        color=PAL["grid"],
        alpha=0.85,
        label="Grid + BESS",
        edgecolor="white",
        linewidth=1,
    )

    for i in range(12):
        if savings_pct[i] > 0.1:
            y_top = max(baseline_monthly[i], bess_monthly[i]) / 1e6
            ax.text(
                x[i],
                y_top + 0.008,
                f"−{savings_pct[i]:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8,
                color=PAL["positive"],
                fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
    )
    ax.set_ylabel("Monthly Energy Cost (M€)")
    ax.set_title("Monthly Electricity Cost — Grid-Only vs. BESS")
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("€%.2fM"))

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "08_monthly_cost_comparison.png", dpi=DPI)
    plt.close(fig)


def fig10_beta_sensitivity(beta_sweep, baseline_cost):
    sweep = beta_sweep["sweep_results"]
    betas = [s["beta"] for s in sweep]
    best_P = [s["best_P_MW"] for s in sweep]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Left: optimal BESS power vs beta
    ax1.step(betas, best_P, where="mid", color=PAL["grid"], linewidth=2.5)
    ax1.scatter(betas, best_P, color=PAL["grid"], zorder=5, s=50)
    ax1.set_xlabel("Revenue Discount Factor (β)")
    ax1.set_ylabel("Optimal BESS Power Rating (MW)")
    ax1.set_title("Optimal BESS Size vs. Risk Aversion")
    ax1.set_ylim(0, max(P_OPTIONS) + 1)
    ax1.set_xlim(betas[0], betas[-1])

    # Right: net cost by BESS power across betas
    colors = plt.cm.viridis(np.linspace(0.15, 0.85, len(P_OPTIONS)))
    for idx, P in enumerate(P_OPTIONS):
        costs = []
        for s in sweep:
            p_configs = {k: v for k, v in s["configs"].items() if k[0] == P}
            best_for_P = min(p_configs, key=lambda k: p_configs[k]["adjusted_net_cost"])
            costs.append(p_configs[best_for_P]["adjusted_net_cost"] / 1e6)
        ax2.plot(betas, costs, linewidth=2, label=f"{P} MW", marker="o",
                 markersize=4, color=colors[idx])

    ax2.axhline(baseline_cost / 1e6, color=PAL["baseline"], linestyle="--",
                linewidth=1.5, label="Grid-Only")
    ax2.set_xlabel("Revenue Discount Factor (β)")
    ax2.set_ylabel("Annual Net Cost (M€/yr)")
    ax2.set_title("Net Cost by BESS Size vs. Risk Aversion")
    ax2.legend(loc="best", fontsize=9)

    fig.suptitle("Revenue Discount Sensitivity Analysis", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "10_beta_sensitivity.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)


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
    best_config = results["best_config"]
    dr_result = results["dr_result"]
    bess_configs = results["bess_results_updated"]

    FIGURES_DIR.mkdir(exist_ok=True)
    apply_theme()

    print("Generating figures...")

    print("  Fig 1: Spot price heatmap")
    fig1_spot_price_heatmap(spot)

    print("  Fig 2: 48h dispatch — winter peak")
    fig2_dispatch_winter(spot, tou, optimal_dispatch)

    print("  Fig 3: 48h dispatch — spring low-price")
    fig3_dispatch_spring(spot, tou, optimal_dispatch)

    print("  Fig 4: Cost waterfall")
    fig4_cost_waterfall(baseline, best_config, dr_result)

    print("  Fig 5: Weekly SoC profile")
    fig5_weekly_soc(spot, optimal_dispatch, best_config["E_MWh"])

    print("  Fig 6: BESS config comparison")
    fig6_bess_config_comparison(bess_configs, baseline["total_cost"])

    print("  Fig 7: DR break-even")
    fig7_dr_breakeven(dr_result)

    print("  Fig 8: Monthly cost comparison")
    fig8_monthly_cost(spot, tou, optimal_dispatch)

    print("  Fig 9: Payback period")
    fig9_payback_period(results["payback_data"])

    if "beta_sweep" in results:
        print("  Fig 10: Beta sensitivity analysis")
        fig10_beta_sensitivity(results["beta_sweep"], baseline["total_cost"])

    print(f"\nDone. Figures saved to {FIGURES_DIR}/")


if __name__ == "__main__":
    main()
