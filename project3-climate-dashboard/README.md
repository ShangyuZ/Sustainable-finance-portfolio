# Project 3 — Climate & Energy Transition Dashboard

## Overview

A live Streamlit dashboard covering four sections useful on a sustainable
finance desk — built entirely on freely licensed, open datasets.

## Sections

| # | Section | Data source |
|---|---------|------------|
| 1 | **EU Carbon Price** | Bundled EUA weekly price history (public sources) |
| 2 | **Energy Transition** | Our World in Data energy dataset (CC BY) |
| 3 | **Country Climate Scorecard** | Our World in Data — ranked CO₂ & renewables |
| 4 | **Portfolio Carbon Calculator** | TCFD sector benchmarks (public) |

## Quick Start

```bash
cd project3-climate-dashboard
pip install -r requirements.txt
streamlit run app.py
```

No API keys needed. The dashboard loads live OWID data on first run (cached for 24h)
and uses the bundled `data/eua_prices.csv` for carbon prices.

## Files

| File | Description |
|------|-------------|
| `app.py` | Main Streamlit application |
| `data/eua_prices.csv` | Weekly EUA spot prices 2018–2026 |
| `.streamlit/config.toml` | Green theme configuration |
| `requirements.txt` | Python dependencies |

## Status

- [x] EU Carbon Price chart with policy event annotations
- [x] Energy Transition — renewable share, CO₂, energy mix by country
- [x] Country Climate Scorecard — rankings, scatter, decarbonisation rate
- [x] Portfolio Carbon Intensity Calculator (WACI)
- [ ] Deployment to Streamlit Community Cloud

## Live Link

🔗 *Coming on deployment*

---
*Part of the [Sustainable Finance Portfolio](../README.md)*
