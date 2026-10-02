# Project 3 — Climate & Energy Transition Dashboard

## Overview

A live Streamlit dashboard covering four sections useful on a sustainable
finance desk — built entirely on freely licensed, open datasets.

## Sections

| # | Section | Data source |
|---|---------|------------|
| 1 | **EU Carbon Price** | Bundled EUA weekly price history (public sources) |
| 2 | **Energy Transition** | OWID energy dataset (electricity mix) + OWID CO2 dataset |
| 3 | **Country Climate Scorecard** | OWID energy + CO2 — ranked CO₂ per capita & renewables |
| 4 | **Portfolio Carbon Calculator** | TCFD-aligned sector benchmarks (public) |

## Quick Start

```bash
cd project3-climate-dashboard
pip install -r requirements.txt
streamlit run app.py
```

No API keys needed. The dashboard loads live OWID data on first run (cached for
24h) and uses the bundled `data/eua_prices.csv` for carbon prices.

## A note on the two OWID datasets

OWID publishes energy and emissions as **separate** datasets. The electricity-mix
columns (`renewables_share_elec`, `fossil_share_elec`, …) are in the
[energy dataset](https://github.com/owid/energy-data); the emissions columns
(`co2`, `co2_per_capita`) are only in the
[CO2 dataset](https://github.com/owid/co2-data). The app loads both and merges on
`(country, year)`.

This matters: reading `co2_per_capita` off the energy dataset returns nothing
silently, because the column simply isn't there. That is what previously left the
CO₂ tab and the whole Country Climate Scorecard showing "column not found".

## Two things that are easy to get wrong here

Both are now unit-tested in `../tests/test_transforms.py`:

**Electricity shares are nested.** `renewables_share_elec` already contains
hydro, wind and solar. Charting all of them together double-counts — for Norway
that produced a pie summing to 198%. The app shows fossil / renewables / nuclear
as the top-level split (which sums to 100%) and breaks renewables down separately.

**The newest year is not the right reference year.** OWID's latest year covers
only a partial set of reporters — in the energy dataset, ~90 countries with no
emissions data at all. Keying a cross-country ranking to `max(year)` yields an
empty table. The scorecard instead picks the most recent year with at least 40
countries reporting every metric it needs, and states which year that is.

## Architecture

| File | Description |
|------|-------------|
| `app.py` | Streamlit UI, data loading and caching |
| `transforms.py` | Pure calculations — no Streamlit, no network, unit-tested |
| `data/eua_prices.csv` | Weekly EUA spot prices 2018–2026 |
| `.streamlit/config.toml` | Green theme configuration |
| `requirements.txt` | Python dependencies |

The calculations live in `transforms.py` so they can be tested without a network
connection or a running Streamlit app. `app.py` keeps only I/O and layout.

## Methodology notes

- **WACI** = Σ (portfolio weight × sector carbon intensity benchmark), the
  TCFD-aligned definition. It is only comparable to a benchmark when weights
  total 100%: at 90% the figure is scaled down by the shortfall, which reads as a
  lower-carbon portfolio when it is really an incomplete one. The app shows the
  rescaled figure when weights don't sum to 100.
- **CO₂** is territorial (production-based) emissions from fossil fuels and
  industry, not consumption-based.
- Sector intensity benchmarks are sector averages, so the WACI is indicative;
  company-level precision needs company-level disclosures (CDP).

## Status

- [x] EU Carbon Price chart with policy event annotations
- [x] Energy Transition — renewable share, CO₂ (total and per capita), energy mix
- [x] Country Climate Scorecard — rankings, scatter, decarbonisation rate
- [x] Portfolio Carbon Intensity Calculator (WACI)
- [x] Unit tests for all pure transforms; CI smoke-test renders every section
- [ ] Deployment to Streamlit Community Cloud

## Live Link

🔗 *Coming on deployment*

---
*Part of the [Sustainable Finance Portfolio](../README.md)*
