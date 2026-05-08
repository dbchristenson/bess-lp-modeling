# Battery Energy Storage for Data Center Grid Flexibility: A Quantitative Analysis of Dublin's I-SEM Market

# Table of Contents

# Executive Summary

# Methodology
Our model evaluates whether a representative Google DeepMind data center in Dublin could reduce its electricity costs by installing a battery energy storage system (BESS) and participating in Ireland's demand response programs. Using synthetic hourly electricity prices calibrated to real I-SEM market data, the model determines the optimal battery size and hour-by-hour charging schedule that minimizes the facility's total annual electricity costs.

**Three scenarios are compared:**

| Scenario | Description |
|---|---|
| **Grid-Only** | Baseline — data center draws a constant 10 MW from the grid with no battery |
| **Grid + BESS** | Battery performs energy arbitrage: charges when electricity is cheap, discharges when it is expensive |
| **Grid + BESS + DR** | Battery also earns revenue from EirGrid's capacity market and peak-hour energy arbitrage |

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

For BESS cost assumptions, the model runs two cost scenarios: the original thesis estimates (NREL ATB 2025) and updated estimates reflecting recent battery price declines (BNEF 2025 CapEx with inflation-adjusted OpEx). The updated scenario is used for scenario comparison and policy recommendations.

### Revenues
The model considers two revenue streams: **energy arbitrage** and **flexible resource capacity payments**.

Energy arbitrage reduces costs by charging the battery when electricity prices are low—including during negative price events caused by wind curtailment—and discharging during expensive peak hours to avoid high spot prices.

Capacity payments come from EirGrid's capacity auction market, which compensates large flexible loads that can reduce their grid draw during system stress events. These participants are called demand side units (DSUs). While DSUs can take several forms (curtailed loads, batteries, virtual power plants), our model registers only the battery—not the data center load itself—as the DSU. Revenue assumptions are based on EirGrid's 2025–2026 capacity auction rates.

Additional detail on the mathematical formulation of the objective function and full model results can be found in the appendix and accompanying deliverables.

# Results

# Regulatory and Policy Considerations

# Bibliography

# Appendix