# Project 3 — Climate & Energy Transition Dashboard

## Overview

**▶ Live: [shangyuz-sustainable-finance.streamlit.app](https://shangyuz-sustainable-finance.streamlit.app)**

A live Streamlit dashboard covering four sections useful on a sustainable
finance desk — built on Our World in Data's CC BY 4.0 datasets, plus a bundled
EU carbon price series that is indicative only (see [DATA.md](../DATA.md)).

## Sections

| # | Section | Data source |
|---|---------|------------|
| 1 | **EU Carbon Price** | Bundled EUA weekly history — *indicative, uncited* (see [DATA.md](../DATA.md)) |
| 2 | **Energy Transition** | OWID energy dataset (electricity mix) + OWID CO2 dataset |
| 3 | **Country Climate Scorecard** | OWID energy + CO2 — ranked CO₂ per capita & renewables |
| 4 | **Portfolio Carbon Calculator** | Illustrative — assumed sector intensities, not sourced figures |

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
| `data/eua_prices.csv` | Weekly EUA prices 2018–2026 — **indicative only**, see [DATA.md](../DATA.md) |
| `.streamlit/config.toml` | Green theme configuration |
| `requirements.txt` | Python dependencies |

The calculations live in `transforms.py` so they can be tested without a network
connection or a running Streamlit app. `app.py` keeps only I/O and layout.

## Methodology notes

- **WACI** = Σ (portfolio weight × sector carbon intensity), the metric the TCFD
  recommends. It is only comparable to a benchmark when weights
  total 100%: at 90% the figure is scaled down by the shortfall, which reads as a
  lower-carbon portfolio when it is really an incomplete one. The app shows the
  rescaled figure when weights don't sum to 100.
- **CO₂** is territorial (production-based) emissions from fossil fuels and
  industry, not consumption-based.
- **The calculator is illustrative.** Its sector intensities are assumed round
  numbers, not taken from a specific publication, date or emissions boundary, and
  holding names do not affect the result — each holding takes its sector's
  assumed intensity. It applies no "high-" or "low-carbon" label, because there
  is no documented benchmark for one. A real WACI needs company-level emissions
  and revenue.
- **The EU carbon price series is indicative and uncited** (see DATA.md); it is
  not a reference price and should not be quoted as one.

## Deploying to Streamlit Community Cloud

Verified ready. Two things about Cloud are worth knowing because both fail
*silently* rather than erroring, and `tests/test_deployment.py` now guards them:

1. **Cloud's working directory is the repository root, not this folder.** Streamlit
   resolves `.streamlit/config.toml` relative to the working directory, so a theme
   that lives only here is ignored on Cloud. There is now a copy at the repo root,
   and a test asserts the two stay identical.
2. **`from transforms import ...` still resolves**, because Streamlit puts the main
   script's own directory on `sys.path`. Verified by executing the app with the
   repo root as the working directory.

Resource use is comfortable: the two OWID downloads total ~24MB and the cached
frames occupy ~12MB in memory, against Cloud's 1GB limit. First load takes a few
seconds while the data downloads; it is then cached for 24h.

**Steps:**

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **New app** → **Deploy a public app from a repo**.
3. Repository `ShangyuZ/Sustainable-finance-portfolio`, branch `main`.
4. **Main file path:** `project3-climate-dashboard/app.py` *(not `app.py`)*.
5. Deploy. No secrets or API keys are needed — every data source is public.
6. Put the resulting URL in the Live Link section below and in the root README.

If the build fails on dependencies, point Cloud at
`project3-climate-dashboard/requirements.txt` under Advanced settings; the root
`requirements.txt` also covers the app's imports.

## Status

- [x] EU Carbon Price chart with policy event annotations
- [x] Energy Transition — renewable share, CO₂ (total and per capita), energy mix
- [x] Country Climate Scorecard — rankings, scatter, decarbonisation rate
- [x] Portfolio Carbon Intensity Calculator (WACI)
- [x] Unit tests for all pure transforms; CI smoke-test renders every section
- [x] Deployment preconditions verified and guarded by tests
- [x] Deployed to Streamlit Community Cloud

## Live Link

🔗 **[shangyuz-sustainable-finance.streamlit.app](https://shangyuz-sustainable-finance.streamlit.app)**

Public, no sign-in required. The first load after a period of inactivity takes a
few seconds: Community Cloud suspends idle apps, and the dashboard then downloads
~24MB of OWID data, which is cached for 24h thereafter.

---
*Part of the [Sustainable Finance Portfolio](../README.md)*
