# Assignment Prompt from Professor

Focus: Quantitative modeling + qualitative policy design for flexibility and optimization

Context: Ireland’s Integrated Single Electricity Market (I-SEM) faces increasing volatility due to high renewable penetration and inflexible loads from data centers. EirGrid projects that achieving 80% renewable electricity by 2030 will require significant demand-side flexibility. Dublin’s data centers — with large, schedulable computing loads — represent untapped potential for providing ancillary services, demand response, and time-shifting.

Assignment: Building on the case in Assignment 2a, students will:

1. Model how a representative Dublin data center could participate as a flexible grid resource — via load shifting, battery storage, or AI workload scheduling.
2. Use historical or synthetic hourly price and wind generation data to simulate operational and emissions outcomes.
3. Quantify cost savings, emissions reductions, and potential market revenues from flexible operation.
4. Develop a policy or market proposal (e.g., “Flexible Load Tariff” or “AI-as-Grid-Resource Pilot”) that aligns corporate and national energy objectives.

Deliverable:

A 4–6 page technical report with data tables and scenario analysis.
A short policy note summarizing the regulatory and economic implications for Ireland’s 2030 Climate Action Plan.

# Personal Context

I am the group's modeler. I am not really going to be in charge of the policy, regulatory scenarios. I am here to provide the data, visualizations, and tables that will support assignment requirements #1, #2, and #3

# Group Notes

Below are some notes that I took from my group meeting about the variables/positions that we agreed on.

## Meeting 1
- Dublin data center model
    - Battery plan -> 11% of Eirgrid wind energy is curtailed and harms renewable energy goals
        - Batteries are charged using the wind energy
        - Volatility will go up as Eirgrid switches to more renewables which makes BESS financially viable
        - Batteries at the time of the report were expensive and less good. Since the data was gathered, battery prices and performance has improved to make BESS financially viable sooner than 2028 (breakeven in the report)
    - Data center promises to pay for new transmission to get the BESS energy where it needs to go during peak hours

- 10 MW data center
- ? How much BESS storage do we need
    - Come up with reasonable assumption for battery/KW price
    - Multiple ways to monetize
        - Sell to aggregator
        - Avoid peak load


## Meeting 2
- Corporate Strategy
    - This data center is a Google deepmind data center with mostly curtailable loads in the event that the BESS storage fails.
    - This specification also allows us to have less diesel generators on-site for backup, reducing emissions
- There seems to be less negative pricing occuring then our initial expectations. The data was synthetically generated, is this an issue of the deviations in spot price being based on sample statistics which might overly average all spot prices?
    - If this is the case, it might help the case for the energy arbitrage to have more negative pricing events that the BESS can take advantage of
- The assumption for BESS OPEX seems to be currently that it has become cheaper since the thesis was written. I do not really know if that would be the case. I am more comfortable assuming that OPEX has actually increased marginally due to the rising cost of labor. Assumptively we can just say that OPEX increases with rate of inflation.
- Figure 7 does not look like its fully working. The regions of breakeven are all vertical, but because we have the capacity payment and also the avoided load payments graphed on the x and y, the break even regions should be a diagonal gradient right? Needs to be fixed.
- Figures 2 and 3 for dispatch are a bit difficult to read. Its hard to make sense that red = charge and green = dispatch. I think a better selection of color scheme/more clear visualization can be used here.