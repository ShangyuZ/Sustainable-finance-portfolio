# Changelog

All notable changes to this portfolio are documented here.

---

## [v0.6.0] — 2026-10-02 — Reproducibility, data-quality layer, dashboard repairs

This release is mostly corrections. Several things the earlier changelog claimed
were done turned out not to be, and two of the four dashboard sections were not
working at all. Details below rather than glossed over, because the point of the
changelog is to be able to trust it.

### Fixed — portfolio-level claim that was false

- **Bloomberg/Refinitiv references were still live inside
  `Green_Bond_Market_Analysis.xlsx`**, despite v0.2.0 claiming they were "removed
  throughout" and the root README stating none are used *anywhere*. Four cells
  carried them, including "This sheet is designed to be populated using
  Bloomberg/Refinitiv data available via UCL library access" and "Visit a UCL
  Bloomberg terminal". A text search of the repo could never have found these —
  they were inside the zipped workbook. The greenium sheet is rebuilt around
  sovereign green "twin" bonds (Finanzagentur, AFT, UK DMO), which is both free
  and a cleaner identification strategy, since a green Bund and its conventional
  twin share coupon, maturity and issuer by construction. CI now fails the build
  if a vendor reference reappears in any file *or* any spreadsheet cell.

### Fixed — Project 3 dashboard: two of four sections were dead

- **`co2` and `co2_per_capita` do not exist in the OWID energy dataset.** They
  live only in OWID's separate CO2 dataset. The "CO₂ Emissions" tab and the
  entire "Country Climate Scorecard" — the headline v0.3.0 feature — therefore
  fell through to "column not found" and `st.stop()` every time they were opened.
  The app now loads both datasets and merges on `(country, year)`.
- **Energy mix pie double-counted nested shares.** `renewables_share_elec`
  already contains hydro, wind and solar, so plotting all of them in one pie
  summed to 134% for the UK, 181% for Brazil and **198% for Norway**. Now split
  into a fossil/renewables/nuclear pie (sums to 100%) plus a separate renewables
  breakdown.
- **Scorecard keyed its ranking to `max(year)`.** OWID's newest year covers only
  partial reporters (energy dataset: ~90 countries, zero emissions overlap), so
  even after the merge above the table would have been empty. It now selects the
  most recent year with at least 40 countries reporting every required metric,
  and displays which year that is.
- **`top_n` slider crashed** when fewer than 30 countries had data: the hardcoded
  `st.slider(..., 10, len(scorecard), 30)` raises when the default exceeds the
  maximum.
- **`use_container_width` is past its removal date** (2025-12-31). Replaced with
  `width="stretch"` across all nine call sites; `streamlit` floor raised to 1.49.
- Default portfolio weights didn't sum to 100 for several holding counts (n=14
  gave 99.4%), tripping the "adjust to 100%" warning on an untouched form.
- WACI is now also reported rescaled to 100% when entered weights fall short —
  previously an under-weighted portfolio simply looked lower-carbon.
- The synthetic EUA price fallback is now labelled as illustrative in the UI
  instead of rendering silently as if it were real market data.
- Missing empty-data guard on the CO₂ tab; year sliders capped at years where the
  plotted column actually has data.

### Fixed — Project 1 was not reproducible

- **The committed workbook was never produced by the committed script.** The file
  in the repo had sheets `Summary Dashboard / Raw Data / Annual Issuance /
  Country & Sector / SLB Analysis / Greenium Analysis`; the script emitted
  `0. Dashboard … 5. Greenium Analysis`. The script also read a column
  `Amount (USD bn)` that does not exist in the data (it is `Amount_USD_bn`), and
  its input `data/cbi_newsmakers.csv` was absent from the repo entirely. The
  README described output nobody could regenerate.
- **Source data is now committed** at `project1-green-bond-analysis/data/cbi_newsmakers.csv`
  (732 records, extracted from the workbook's own Raw Data sheet), and the model
  rebuilds from it with `python scripts/process_data.py`. CI runs that rebuild.
- **Scope was internally inconsistent.** The workbook headlined "2018–2024 /
  7-year time series" and its annual table started at 2018 ($638.15bn), while its
  total said $650.0bn — an unexplained $11.90bn gap, being 2015–2017. All sheets
  now cover 2015–2024 and reconcile to $650.04bn, with the thinness of 2015–2017
  and the partial-year status of 2024 stated explicitly.
- **"Unique issuers: 69"** on the dashboard was the *country* count; unique
  issuers is 180. Both are now reported correctly and separately.

### Fixed — data quality defects that silently skewed the analysis

New `scripts/clean.py` plus sheet 1 of the workbook documents every rule:

- `Sector` encodes "not disclosed" as the string `"0"` (64 records) — previously
  rendered as a sector literally named "0" in the breakdown.
- `Sector` used 34 labels for 11 real groups (140 records affected):
  Financials/Financial/Finance/Banks/Commercial Bank/Diversified Banks/Financial
  Institution are one sector. Split across seven rows, none of them ranked;
  folded, Financials is second by volume at 7.1%.
- `Country` carried duplicate labels (42 records): USA/United States,
  UK/United Kingdom, China_HK, and the misspelt Supernational/Supranational.
  This understated the **UK ($59.34bn → $59.79bn)** and, together with a trailing
  space in `"Netherlands "`, the **Netherlands ($28.81bn → $29.58bn)**, and
  inflated the country count from an actual **64 to an apparent 69**.
- `Issuer Name` had case variants (GoodLeap/Goodleap) inflating the issuer count.
- Two source records are **deliberately left uncorrected** and flagged instead:
  Schneider Electric SE (French) is tagged to the United States, and its 2015
  deal is labelled SLB years before that market existed — which is why 2015 shows
  a 100% SLB share.

### Fixed — README claims that did not match the data

- "731 bond issuances" → **732** (the theme breakdown already summed to 732).
- "50+ countries" → **64** (and the workbook's "69" was wrong).
- "Deal **volume** grew from 10 transactions in 2018 to 238 in 2023 — a 2,280%
  increase" conflated count with volume. The +2,280% figure is deal **count**;
  USD volume over the same period grew **+950%** ($17.6bn → $184.5bn). Both are
  now reported, with the reason they differ.
- Coverage was stated as 2018–2024 in the overview and 2015–2024 in the dataset
  section. It is 2015–2024.
- The greenium **sign convention was contradictory** between artifacts — the
  script listed negative bps while the workbook's formulas treated positive as
  "greenium exists". Now stated explicitly once: (green − conventional) in bps,
  negative means a greenium.
- "Six-sheet model" → nine sheets, listed individually.

### Added

- `tests/` — **125 tests** covering normalisation, every aggregation's
  reconciliation invariants, the workbook build, merged-range validity, and the
  dashboard's pure transforms. Verified by mutation testing: reintroducing each
  original bug makes the suite fail.
- `project3-climate-dashboard/transforms.py` — pure calculations extracted from
  `app.py` so they are testable without a network connection or a Streamlit
  context.
- `project1-green-bond-analysis/scripts/clean.py` — loading, normalisation and
  aggregation, separated from Excel presentation.
- Workbook sheet **"1. Data Quality"** — every cleaning rule, records affected,
  and why it matters; plus known source issues left uncorrected.
- Workbook sheets for **Geography**, **Sector**, **Theme Evolution** (on deals
  *and* volume) and **SLB Analysis** (two penetration measures, since SLB share
  of green+SLB and of all issuance are not interchangeable).
- CI: Python 3.11 + 3.13 matrix, pyflakes over all sources and tests, pytest, a
  workbook-rebuild check, the proprietary-data guard, and a non-blocking
  dashboard smoke job that renders all four sections against live OWID data.

### Changed

- `streamlit>=1.35.0` → `>=1.49.0` (needed for `width="stretch"`).
- Geography and sector tables now rank by **USD volume** rather than deal count:
  China leads on deals (68) but is sixth by volume, which is the more meaningful
  ordering for market size.

---

## [v0.5.0] — 2026-09-30 — Project 2 Excel model, financial-impact fix

### Added
- `project2-sll-structuring/SLL_Structuring_Model.xlsx`: New four-sheet Excel model
  (Borrower Profile, KPI Tracker, SPT Calibration & Glide Path, Margin Ratchet
  Calculator). The KPI tracker and ratchet calculator are formula-driven with
  editable (yellow) input cells and live recalculation — not static tables. All
  data is the existing hypothetical Albion Industrials plc case; no real company
  data used.

### Fixed
- `project2-sll-structuring/README.md`: Corrected the Financial Impact table —
  the previous annual interest cost figures (~£8.7m/£9.2m/£9.7m) did not
  reconcile with the stated £650m facility, SONIA + 120bps margin, and 4.25%
  SONIA rate (facility × all-in rate gives ~£34.9m/£35.4m/£35.9m). The
  scenario-to-scenario delta of £490k was already correct and is unchanged;
  only the absolute cost figures were restated. New figures are cross-checked
  against the live calculator in the new Excel model.
- `project1-green-bond-analysis/README.md`: Status checklist marked "3-page
  investment brief" as complete while the Files table listed the same PDF as
  *(in progress)* and the file does not exist in the repo — checklist item
  un-checked for consistency. Also fixed a missing table-row delimiter that
  broke Markdown rendering of the Files table.

### Updated
- `project2-sll-structuring/README.md`: Checked off "Excel model" in Status;
  refreshed "Last updated" to 2026-09-30.
- `README.md`: Refreshed "Last updated" to September 2026.

---

## [v0.4.2] — 2026-07-02 — Dynamic year ranges, full docstring coverage

### Improved
- `project1/scripts/process_data.py`: `sheet_annual()` header now derived from
  actual data year range (`yr_min`–`yr_max`) instead of hardcoded `"2015–2024"`,
  so it stays accurate when the dataset is updated.
- `project1/scripts/process_data.py`: Dashboard KPI label changed from
  `"Total Deals (2015–2024)"` to `"Total Deals (2015–present)"` for the same reason.
- `project1/scripts/process_data.py`: Added docstrings to all previously
  undocumented functions (`load`, `col_header`, `sheet_geo`, `sheet_sector`,
  `sheet_theme`, `sheet_dashboard`, `main`) — module now has full docstring coverage.

---

## [v0.4.1] — 2026-07-02 — Project 2 case study: hypothetical borrower

### Improved
- `project2-sll-structuring/README.md`: Replaced "TBC" company selection with a
  fully hypothetical borrower (*Albion Industrials plc*) — illustrative revenue,
  EBITDA margin, existing debt, credit rating, and Scope 1+2 baseline, all clearly
  labelled as fictional. Removed reference to Bloomberg (proprietary data source,
  violates portfolio rules); replaced with free equivalents: Companies House,
  company IR websites, CDP disclosures, and LSE prospectuses.
- `project2-sll-structuring/README.md`: Added financial impact table (P&L effect
  of margin ratchet across three SPT scenarios), expanded SPT calibration with
  explicit benchmark sources (SBTi Industrials pathway; UK CCC 6th Carbon Budget),
  and added a Verification & Reporting section referencing SECR and REGO.

---

## [v0.4.0] — 2026-07-02 — Code quality: pandas fix, docstrings, volume YoY tracking

### Fixed
- `project3/app.py`: Replaced deprecated `Styler.applymap()` with `Styler.map()` —
  `applymap` was deprecated in pandas 2.1 and removed in pandas 3.x; this would have
  caused a hard crash on upgraded environments
- `project3/app.py`: Corrected ISO-code prefix check from `"OWI"` to `"OWID"` to
  match the inline comment and make intent explicit (functional impact is nil since
  the 3-letter length filter already excludes OWID aggregate codes, but the code
  now clearly documents why the filter exists)

### Improved
- `project1/scripts/process_data.py`: `annual_issuance()` now also computes
  `YoY_Volume_Pct` (year-on-year % change in USD bn volume) alongside the existing
  `YoY_Deals_Pct` — volume trend is a key metric for any green bond analysis
- `project1/scripts/process_data.py`: Added docstrings to `geographic()`,
  `sector()`, and `theme_evolution()` describing their output schema and sort order

### Updated
- `README.md`: refreshed "Last updated" date to July 2026

---

## [v0.3.0] — 2026-06-11 — Big update: bug fixes, new dashboard section, CI

### Fixed
- `project3/app.py`: Replaced fabricated Ember GitHub URL with bundled `data/eua_prices.csv`
  (the previous URL pointed to a non-existent repository and always fell through to synthetic data)
- `project3/app.py`: OWID region filtering now uses ISO code (`iso_code` must be 3 letters,
  not starting with `OWID`) — replaces the incomplete manual exclusion set that missed
  dozens of aggregate entries (e.g. "Central Africa", "Eastern Europe")
- `project3/app.py`: Added null-guard on EUA price load to prevent `KeyError` crash
  if data file is missing or malformed
- `project1/scripts/process_data.py`: Removed unused imports (`Path`, `Border`, `Side`)
  and unused `THEME_COLOURS` dict

### Added
- `project3/data/eua_prices.csv`: Bundled weekly EU ETS EUA price history (2018–2026)
  compiled from public sources — dashboard now works fully offline
- `project3/.streamlit/config.toml`: Green brand theme applied across the app
- **Country Climate Scorecard** (new dashboard section): Ranked table + scatter plot of
  CO₂ per capita vs renewable share + 5-year decarbonisation rate, all from OWID
- `.github/workflows/ci.yml`: GitHub Actions CI — runs syntax check and pyflakes lint
  on every push to main
- `CHANGELOG.md`: This file

---

## [v0.2.0] — 2026-06-11 — Open-source pivot

### Changed
- Removed all Bloomberg / proprietary data references throughout
- Project 2 reframed as a clearly hypothetical SLL framework (no real company data)
- Project 3 rewired to Our World in Data (CC BY) and Ember Climate (CC BY)

### Added
- `project1/scripts/process_data.py`: Python processing script for CBI data → Excel
- `project2-sll-structuring/README.md`: Full SLL structuring framework document
- `project3-climate-dashboard/`: Streamlit app scaffold
- `.gitignore`, root `requirements.txt`

---

## [v0.1.0] — 2026-03 — Initial commit

- Project 1: Green Bond Market Analysis (Excel model, README)
- Root README with portfolio overview
