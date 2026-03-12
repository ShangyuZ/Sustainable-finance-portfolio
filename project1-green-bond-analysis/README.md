# Project 1 — Green Bond Market Analysis

## Overview

This project analyses the global green bond market (2018–2024) using publicly 
available issuance data from the Climate Bonds Initiative. I built this model to 
understand how sustainable debt markets have evolved over the past decade — and 
specifically to examine how quickly sustainability-linked bonds are emerging as 
a structurally different instrument relative to traditional green bonds.

What surprised me most was the speed of the SLB market's growth post-2020 and 
how concentrated issuance remains geographically, despite the global narrative 
around the energy transition.

## Key Questions

- How has green bond issuance grown from 2018 to 2024?
- Which countries and sectors dominate issuance volume?
- Are sustainability-linked bonds (SLBs) displacing traditional green bonds?
- Do green bonds trade at a yield premium vs conventional bonds — the "greenium"?

## Dataset

- **Source:** Climate Bonds Initiative — News Makers dataset
- **Coverage:** 731 bond issuances across 50+ countries (2015–2024)
- **Themes covered:** Green (490 deals), SLB (108), Sustainability (109), Social (25)

## Key Findings

- Deal volume grew from 10 transactions in 2018 to 238 in 2023 — a 2,280% increase
- Green bonds account for 67% of all deals but SLBs are the fastest-growing theme, 
  growing from near zero pre-2020 to meaningful market share by 2022–2023
- China, Germany, and the USA are the top 3 countries by deal count, but sovereign 
  issuers dominate by volume — highlighting the role of government-led climate 
  financing programmes in scaling the market
- Sovereign issuance accelerated sharply after 2020 as governments increasingly 
  used green bonds to fund national climate transition plans
- Greenium: academic literature consistently finds a 2–4 bps premium in developed markets and up to 13 bps in emerging markets (Zerbib 2019; Panizza et al. 2025; Banque de France 2025). A matched-pair framework is included in the Excel model for future empirical testing

## Methodology

Data was cleaned and processed in Python using pandas. Issuance records were 
filtered to include labelled sustainable bonds only, then grouped by year, 
country, sector, and bond theme for aggregation.

The processed dataset was structured into a six-sheet Excel financial model 
built using openpyxl. Charts and summary tables were constructed to visualise:

- Annual issuance growth with year-on-year percentage change
- Geographic distribution — top 10 countries by issuance volume (USD bn)
- Sector allocation across sovereign, commercial bank, industrial, and other categories
- Bond theme evolution — Green vs SLB vs Sustainability vs Social, 2018–2024
- A greenium analysis sheet documenting academic evidence across five studies (2019–2025) and a matched-pair framework designed for empirical testing using publicly available yield data
  
## Files

| File | Description |
|------|-------------|
| `Green_Bond_Market_Analysis.xlsx` | Six-sheet financial model including market charts, summary dashboard, and greenium literature review
`Green_Bond_Market_Brief.pdf` | 3-page investment brief formatted as a bank-style research note |

## Skills Demonstrated

- Sustainable finance market analysis and investment research
- Financial data cleaning and transformation (Python / pandas)
- Financial modelling and charting in Excel (openpyxl)
- Climate finance market research and data sourcing
- Investment brief writing and structured analytical communication

## Status

- [x] Data acquisition and cleaning
- [x] Annual issuance analysis (2018–2024)
- [x] Geographic and sector breakdown
- [x] SLB vs Green bond comparison
- [x] Greenium literature review and matched-pair framework
- [x] 3-page investment brief

## References

Zerbib, O.D. (2019). *The effect of pro-environmental preferences on bond prices.* Journal of Banking & Finance, 98, 39–60.

Panizza et al. (2025). *Sovereign Green Bonds.* CEPR Discussion Paper No.20817.

Banque de France (2025). *The Green Bond Premium.* Working Paper No.1010.

---
*Part of the [Sustainable Finance Portfolio](../README.md)*
