# Battery Energy Storage for Data Center Grid Flexibility: A Quantitative Analysis of Dublin's I-SEM Market

# Table of Contents

# Executive Summary

# Methodology
Our model evaluates whether a representative Google DeepMind data center in Dublin could reduce its electricity costs by installing a battery energy storage system (BESS) and participating in Ireland's demand response programs. Using synthetic hourly electricity prices calibrated to real I-SEM market data, the model determines the optimal battery size and hour-by-hour charging schedule that minimizes the facility's total annual electricity costs. The model and some inputs are taken and updated from a paper by Lukas Ljungblom, *"Optimal Planning of Data Centers with On-Site Generation and Storage"*.

**Three scenarios are compared:**

| Scenario | Description |
|---|---|
| **Grid-Only** | Baseline — data center draws a constant 10 MW from the grid with no battery |
| **Grid + BESS** | Battery performs energy arbitrage: charges when electricity is cheap, discharges when it is expensive |
| **Grid + BESS + DR** | Battery also earns revenue from EirGrid's capacity market as a demand side unit (DSU) |

## Assumptions
- The data center draws a constant 10 MW load and has a 20 MW grid connection, leaving headroom for battery charging
- Google DeepMind workloads are not mission-critical, so the data center can curtail its load if the battery is unavailable
- The BESS has a 15-year lifetime, 95% round-trip efficiency, and costs are discounted at an 8% weighted average cost of capital (WACC)
- The BESS capacity is always awarded in EirGrid's capacity auction, making it eligible for annual demand side unit (DSU) payments up to 10 MW

## Modeling
The systems we modeled are easily divided into two categories: **costs** and **revenues**.

### Costs
The model accounts for four cost components that together form the facility's **annualized lifecycle cost (ALCC)**:

1. **Grid subscription fee** — a fixed annual charge of approximately €4.4M for maintaining the 10 MW grid connection, paid regardless of how much electricity is consumed.
2. **Energy import costs** — variable costs for each MWh drawn from the grid, equal to the I-SEM spot price plus a time-of-use (TOU) network tariff. TOU rates are highest during weekday peak hours (17:00–19:00) and lowest overnight and on weekends.
3. **BESS capital expenditure (CapEx)** — the upfront cost of the battery system, spread over its 15-year lifetime using a standard annuity factor at 8% WACC. CapEx scales with both the battery's power rating (MW) and its energy capacity (MWh).
4. **BESS operating expenditure (OpEx)** — annual maintenance and operating costs, also scaling with battery power and energy capacity. These costs are adjusted upward from thesis values to reflect inflation and rising labor costs in Ireland.

For BESS cost assumptions, the model runs two cost scenarios: the original thesis estimates (NREL ATB 2025, Moderate) and the NREL ATB 2024 Advanced scenario, which reflects aggressive but plausible cost reductions in battery technology. All ATB costs are reported in 2022 USD and converted to EUR at a rate of 0.95 EUR/USD. The updated scenario is used for scenario comparison and policy recommendations.

### Revenues and Savings
The model captures value through two mechanisms: **energy arbitrage** (cost reduction) and **DSU capacity payments** (revenue).

Energy arbitrage is embedded in the BESS optimization itself. The battery charges when electricity prices are low — including during negative price events caused by wind curtailment — and discharges during expensive peak hours, reducing the facility's net import costs. This benefit appears in all BESS scenarios automatically.

Capacity payments are additional revenue available only in the DR scenario. EirGrid's capacity auction market compensates large flexible loads that can reduce their grid draw during system stress events. These participants are called demand side units (DSUs). While DSUs can take several forms (curtailed loads, batteries, virtual power plants), our model registers only the battery — not the data center load itself — as the DSU. Revenue assumptions are based on the capacity-weighted average clearing price from EirGrid's 2025–2026 T-1 auction results.

Additional detail on the mathematical formulation of the objective function and full model results can be found in the appendix and accompanying deliverables.

# Results

# Regulatory and Policy Considerations

# Bibliography

Cole, W., & Karmakar, A. (2023). *Cost projections for utility-scale battery storage: 2023 update* (NREL/TP-6A40-85332). National Renewable Energy Laboratory. https://www.nrel.gov/docs/fy23osti/85332.pdf

EirGrid. (n.d.). *Demand side management*. https://www.eirgrid.ie/industry/becoming-customer/demand-side-management

EirGrid. (2024, September). *EirGrid statement of charges 2024/2025* (v1.0). https://www.eirgrid.com

Ljungblom, L. (2025). *Optimal planning of data centers with on-site generation and storage* [Master's thesis, Chalmers University of Technology].

National Renewable Energy Laboratory. (2025). *Utility-scale battery storage*. Annual Technology Baseline. https://atb.nrel.gov/electricity/2024/commercial_battery_storage

SEAI. (n.d.). *Conversion factors*. SEAI Statistics. https://www.seai.ie/data-and-insights/seai-statistics/conversion-factors

SEMO. (2025, July). *Final capacity auction results: 2025/26 T-1* (FCAR2526T-1). https://www.sem-o.com/sites/semo/files/2025-07/FCAR2526T-1.pdf

# Appendix