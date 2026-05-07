# BESS + Demand Response Optimization Model

A techno-economic optimization model for co-locating battery energy storage (BESS) with a **10 MW data center in Dublin**, evaluating participation in Ireland's I-SEM capacity market as a Demand Side Unit (DSU).

Built for ISEN 495 (MSES, Spring 2026) as a simplified adaptation of the [Ljungblom (2025) Chalmers thesis MILP](milp_eirgrid_dc_model_thesis.pdf), reduced to grid imports + BESS only (no on-site PV, wind, or SMR).

---

## Model Overview

The model solves an hourly LP over 8,760 hours to minimize grid import costs for a data center with battery storage, then evaluates demand response revenue under EirGrid's capacity market rules.

**Three scenarios are compared:**

| Scenario | Description |
|---|---|
| **Grid-Only** | Baseline — data center draws 10 MW flat from the grid |
| **Grid + BESS** | Battery performs energy arbitrage (charge low, discharge high) |
| **Grid + BESS + DR** | BESS also earns DSU capacity payments and peak energy arbitrage revenue |

**Key parameters:**
- 10 MW constant data center load
- 20 MW grid connection (2x headroom for BESS charging)
- BESS sizing grid: 2–10 MW power x 1/2/4 hour duration (15 configurations)
- 95% round-trip efficiency, 15-year lifetime, 8% WACC
- Two cost sets: NREL ATB 2025 (thesis) and BNEF 2025 (updated)
- Synthetic I-SEM spot prices calibrated to 2023 statistics (~6% negative price hours)
- EirGrid TOU tariffs (day/peak/night)

## Project Structure

```
assignment3/
├── build_model.py          # Optimization model (Pyomo + HiGHS solver)
├── build_figures.py         # 9 publication-quality figures
├── build_workbook.py        # Excel workbook with all results tables
├── Makefile                 # Build orchestration
├── pyproject.toml           # Dependencies and metadata
├── results.pkl              # Serialized model outputs (generated)
├── BESS_DR_Model_Results.xlsx  # Excel workbook (generated)
└── figures/                 # PNG figures (generated)
    ├── 01_spot_price_heatmap.png
    ├── 02_dispatch_winter_peak.png
    ├── 03_dispatch_spring_low.png
    ├── 04_cost_waterfall.png
    ├── 05_weekly_soc_profile.png
    ├── 06_bess_config_comparison.png
    ├── 07_dr_breakeven_contour.png
    ├── 08_monthly_cost_comparison.png
    └── 09_payback_period.png
```

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Build everything

```sh
make all
```

This runs three stages in sequence:

1. **`make model`** — Solves the LP for all 15 BESS configurations under both cost sets, selects the optimal config, runs DR break-even analysis, and exports `results.pkl`
2. **`make figures`** — Generates 9 PNG figures from the results
3. **`make workbook`** — Generates the Excel workbook with scenario summaries, hourly dispatch data, and DR event tables

### Run individually

```sh
uv run python build_model.py      # ~1-2 min (solves 30 LPs)
uv run python build_figures.py
uv run python build_workbook.py
```

### Clean generated outputs

```sh
make clean
```

## Figures

| # | Figure | What it shows |
|---|--------|---------------|
| 1 | Spot price heatmap | Hourly I-SEM prices by month and hour-of-day — seasonal and diurnal patterns |
| 2 | Winter peak dispatch | Stacked area of grid import, BESS charge/discharge during a high-price winter week |
| 3 | Spring low dispatch | Same view during a low-price spring week with negative price episodes |
| 4 | Cost waterfall | Annual cost breakdown: arbitrage savings, BESS cost, DR revenue, net savings |
| 5 | Weekly SoC profile | Battery state-of-charge over a representative week |
| 6 | BESS config comparison | Total annual cost across all 15 power/duration configurations |
| 7 | DR break-even contour | Sensitivity of profitability to capacity payment rate and energy arbitrage rate |
| 8 | Monthly cost comparison | Grid-only vs. Grid+BESS monthly electricity costs |
| 9 | Payback period | Cumulative cash flow and payback year for BESS and BESS+DR scenarios |

## Dependencies

| Package | Purpose |
|---------|---------|
| `pyomo` | Optimization modeling framework |
| `highspy` | HiGHS LP/MIP solver (via appsi interface) |
| `numpy` | Numerical arrays and data generation |
| `matplotlib` | Figure generation |
| `openpyxl` | Excel workbook generation |

## Reference

Ljungblom, E. (2025). *Optimizing Data Centre Power Systems with Battery Energy Storage: A MILP Framework for Reducing Costs, Emissions, and Grid Dependence*. Chalmers University of Technology.
