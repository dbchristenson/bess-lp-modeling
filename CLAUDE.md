# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Assignment 3 for ISEN 495 (MSES, Spring 2026). Team project modeling a **10 MW Dublin data center with BESS** participating in demand response on Ireland's I-SEM grid. The student's role is **modeler** — responsible for data tables, visualizations, and quantitative outputs (not the policy/regulatory writing).

Deliverables: data tables and scenario analysis supporting a 4-6 page technical report + policy note.

## Modeling Approach

The model is a **simplified version** of the MILP in `milp_eirgrid_dc_model_thesis.pdf` (Ljungblom, Chalmers 2025). That thesis models a 5 MW DC with PV, wind, SMR, and BESS. We strip it down to **grid imports + BESS only** — no on-site generation (PV, wind, SMR terms dropped).

The simplified energy balance: data center demand is met by grid imports and battery discharging; battery charges from grid only.

### Key Thesis Sections to Reference

- **Objective function** (p. 22, Section 3.4.1): Keep grid import/export costs and BESS CapEx/OpEx terms; drop PV, Wind, SMR terms.
- **BESS operation** (p. 24, Section 3.4.3): Equations 3.12-3.14 govern charge, discharge, and state-of-charge tracking.
- **Energy balance** (p. 24, Eqs. 3.15-3.16): Drop gPV, gW, gSMR terms from Eq. 3.15.
- **DR modeling** (pp. 34-35, Section 4.2.1): DR event constraints, one-hour headroom reserve, capacity/energy payment formulas, "5-of-10" baseline calculation.
- **Input data tables**: TOU tariffs, grid carbon intensity, capacity charges (p. 25, Tables 3.1-3.3); BESS costs, 95% round-trip efficiency, lifetime params (p. 28, Table 3.7).

### Key Parameters (from group agreement)

- 10 MW data center (thesis used 5 MW)
- BESS sized to capture curtailed wind energy (11% of EirGrid wind is curtailed)
- Revenue streams: sell to aggregator, avoid peak-load charges
- DC commits to funding new transmission for BESS energy delivery during peaks

## Conventions

Inherits from parent `CLAUDE.md`:
- APA 7th edition citations
- Government/regulatory primary sources (CSO, CRU, EirGrid)
- Python scripts run via `uv run`; install deps with `uv pip install`
