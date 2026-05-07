# Prompt

I have an assignment about modeling how a data center in Dublin acting as a DR resource can monetize it. The goals for the assignment are:


Model how a representative Dublin data center could participate as a flexible grid resource — via load shifting, battery storage, or AI workload scheduling.

Use historical or synthetic hourly price and wind generation data to simulate operational and emissions outcomes.

Quantify cost savings, emissions reductions, and potential market revenues from flexible operation.

Develop a policy or market proposal (e.g., “Flexible Load Tariff” or “AI-as-Grid-Resource Pilot”) that aligns corporate and national energy objectives.


To make things easier (not as complicated as the masters thesis source) we are planning on only investigating a scenario where we install a new BESS at the data center and model the revenues generated, pay-back period, emissions saving etc. I want to use some of the modeling in the paper, but currently it's too complicated (with the addition of BTM, etc). It would be better for the assignment to just model how the batteries will charge, when they will discharge, money earned etc.

Do you think the formulations in this paper could be dumbed down to achieve this? What sections of the paper would be necessary to feed to an LLM to help model this? I want to use Claude code to model, but the paper is probably too large to efficiently pass. I need to find a way to compress the information by getting a summary or maybe just pointing at specific pages

# Response

Yes, the formulations in the paper can absolutely be simplified to model just a Battery Energy Storage System (BESS) and Demand Response (DR) participation. The author built the Mixed-Integer Linear Programming (MILP) model in a highly modular way, which means you can simply drop the variables and constraints related to Solar PV, Onshore Wind, and Small Modular Reactors (SMRs).
To "dumb down" the model, you would simplify the energy balance equation so that the data center's demand is met purely by grid imports and battery discharging, while charging comes only from the grid.
To get an LLM like Claude to build this simplified model for you, you only need to feed it a few specific sections of the paper. Here are the exact pages and sections you should point to:
1. The Mathematical Constraints (Pages 22–24)
Section 3.4.1 (Objective Function, Page 22): You only need the formulas for Grid Import/Export and BESS CapEx/OpEx. You can instruct the LLM to ignore the PV, Wind, and SMR terms.
Section 3.4.3 (BESS Operation, Page 24): Equations 3.12, 3.13, and 3.14 dictate exactly how the battery charges, discharges, and tracks its State-of-Charge (SoC).
Section 3.4.3 (Energy Balance, Page 24): Equations 3.15 and 3.16. You can instruct the LLM to drop the gPV, gW, and gSMR terms from Equation 3.15.
2. Demand Response Rules & Formulas (Pages 34–35)
Section 4.2.1 (DR Modeling Assumptions): This section is crucial for your assignment. It explains the specific constraints needed to simulate a DR event, including the "one-hour headroom reserve" which forces the battery to hold enough charge immediately before an event.
Section 4.2.1 (DR Revenue Calculations): Page 35 contains the exact mathematical formulas for calculating DR Capacity Payments and Energy Payments, as well as how to calculate the "5-of-10" baseline.
3. The Input Data (Pages 25 & 28)
Section 3.5.1 (Grid Data, Page 25): Tables 3.1, 3.2, and 3.3 provide the time-of-use tariffs, grid carbon intensity, and capacity charges you need to simulate costs and emissions.
Section 3.5.6 (BESS Data, Page 28): Table 3.7 provides the capital costs, fixed O&M, round-trip efficiency (95%), and lifetime parameters for the battery.