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

Ireland's I-SEM spot market exhibits strong temporal price variation that creates a clear opportunity for battery arbitrage. Figure 1 shows average hourly spot prices across 2023: evening peaks regularly exceed €140/MWh during winter months, while overnight and spring/summer hours — particularly April through August — frequently fall below €20/MWh and occasionally turn negative. These negative prices coincide with periods of high wind output that the grid cannot absorb; in 2023, approximately 11% of Ireland's wind generation was curtailed (Climate Jargon Buster, n.d.). A co-located BESS can capture this otherwise wasted energy and discharge it during peak hours, converting a grid liability into facility savings.

**Figure 1.** Average Hourly I-SEM Spot Price Heatmap, 2023

The model evaluates fifteen BESS configurations spanning five power ratings (2, 4, 6, 8, and 10 MW) and three duration classes (1-, 2-, and 4-hour storage). For each configuration, an LP minimizes annual energy import costs subject to charge/discharge and state-of-charge constraints. The optimizer selects a 10 MW / 20 MWh system (2-hour duration) as the cost-minimizing configuration. At 10 MW the battery can fully offset the data center's load during discharge hours, and the 2-hour duration balances sufficient energy capacity for daily arbitrage cycling against the higher per-MWh capital cost of longer-duration systems. This configuration also maximizes the DSU enrollment capacity at the full 10 MW, capturing the largest possible capacity payment from EirGrid.

Figure 2 summarizes the annual cost impact of this optimal BESS under each scenario. Against the Grid-Only baseline of €17.31M/yr, energy arbitrage alone saves €1.02M/yr — but the annualized BESS capital and operating costs total €0.99M/yr, leaving a net arbitrage margin of only €0.03M/yr. Software licensing, component degradation, and price volatility could easily erode this margin, making arbitrage alone too risky to justify the investment. Adding EirGrid DSU capacity payments of €1.14M/yr transforms the economics: the combined BESS + DR scenario achieves net savings of €1.17M/yr, reducing total annual costs to €16.14M/yr — a 6.7% reduction.

**Figure 2.** Cost Impact vs. Grid-Only Baseline (Waterfall)

These savings are distributed throughout the year. Figure 3 shows monthly electricity cost reductions ranging from 5.0% in January to 11.3% in May, with the largest gains in spring and early summer when the spread between off-peak and peak prices is widest due to high wind availability.

**Figure 3.** Monthly Electricity Cost — Grid-Only vs. BESS

The payback analysis in Figure 4 underscores the importance of demand response revenue. Under discounted cash flow at 8% WACC, the BESS-only scenario barely reaches payback at 14.2 years — the end of the battery's assumed 15-year lifetime — with a marginal NPV of €+0.20M. The BESS + DR scenario, by contrast, achieves discounted payback in just 4.3 years and delivers an NPV of €+10.0M. Without EirGrid's annual DSU capacity payments, BESS investment in the Irish market remains economically marginal; with them, it becomes compelling.

**Figure 4.** BESS Investment Payback — Simple and Discounted

From an emissions perspective, the net impact is approximately neutral. BESS round-trip losses increase annual emissions by 246 tCO₂ relative to the grid-only baseline of 19,710 tCO₂/yr, while DR-dispatched hours displace 230 tCO₂ of oil-fired peaker generation (at 800 gCO₂/kWh versus the 225 gCO₂/kWh grid average), yielding a net change of +16 tCO₂ — effectively carbon-neutral. The emissions case for BESS thus rests not on facility-level reductions but on the systemic value of enabling higher renewable penetration by absorbing curtailed wind.

**Figure 5.** Emissions Impact — BESS & Demand Response

# Regulatory and Policy Considerations

**Layer 2: Peaker Displacement Contract (PDC).** When EirGrid activates a demand response event, the facility draws on its BESS to serve load rather than importing from the grid. Under the PDC, each verified DR event hour earns the facility an additional payment reflecting the social cost of the peaker generation avoided. Our model assumes 20 events per year totaling 400 MWh of curtailed demand. At an emission factor of 800 gCO₂/kWh for oil-fired peaker dispatch, the midpoint of the United Nations Economic Commission for Europe (UNECE) lifecycle assessment range — against a grid average of 225 gCO₂/kWh (SEAI), each curtailed MWh avoids 575 gCO₂. Applied to our modeled DR volume, this yields approximately 230 tonnes of CO₂ avoided annually per facility. For context, Moneypoint generated roughly 2 TWh running on heavy fuel oil in 2025; our single facility's curtailment represents a small but verifiable slice of that displacement. At an EU ETS carbon value of €63/tonne, the implied social benefit is approximately €14,490 per facility per year. Scaled across five pilot participants, verified avoided emissions reach 1,150 tonnes annually, a modest but auditable baseline from which a formal PDC payment structure can be built. The PDC payment would be set at a fraction of the full carbon value, sufficient to incentivize participation while remaining within the bounds of the avoided cost.

# Bibliography

Cole, W., & Karmakar, A. (2023). *Cost projections for utility-scale battery storage: 2023 update* (NREL/TP-6A40-85332). National Renewable Energy Laboratory. https://www.nrel.gov/docs/fy23osti/85332.pdf

EirGrid. (n.d.). *Demand side management*. https://www.eirgrid.ie/industry/becoming-customer/demand-side-management

EirGrid. (2024, September). *EirGrid statement of charges 2024/2025* (v1.0). https://www.eirgrid.com

Ljungblom, L. (2025). *Optimal planning of data centers with on-site generation and storage* [Master's thesis, Chalmers University of Technology].

National Renewable Energy Laboratory. (2025). *Utility-scale battery storage*. Annual Technology Baseline. https://atb.nrel.gov/electricity/2024/commercial_battery_storage

SEAI. (n.d.). *Conversion factors*. SEAI Statistics. https://www.seai.ie/data-and-insights/seai-statistics/conversion-factors

SEMO. (2025, July). *Final capacity auction results: 2025/26 T-1* (FCAR2526T-1). https://www.sem-o.com/sites/semo/files/2025-07/FCAR2526T-1.pdf

# Appendix