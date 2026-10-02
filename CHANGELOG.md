# Changelog

All notable changes to this portfolio are documented here.

---

## [v0.9.2] — 2026-10-02 — Remove contradictory disclaimers of the greenium estimate

### Fixed

Four places still said no greenium estimate was claimed, after v0.9.0 published
one. Reported by a reader of the brief, who spotted that §4 gives −1.50bps while
§5 listed "No greenium estimate is claimed" as a limitation.

- `brief/Green_Bond_Market_Brief.md` §5 — now states the real limitation: the
  estimate is **German sovereign only** and does not generalise to corporates,
  other sovereigns, or primary-market pricing.
- `project1-green-bond-analysis/README.md` — the greenium bullet still deferred to
  the literature and disclaimed an estimate; it now leads with the measured
  −1.50bps.
- `scripts/process_data.py` — the "STATUS: framework and sources only" note is
  written **into sheet 7 of the Excel model**, so a reader opening the workbook saw
  the contradiction where no text search would find it. Now a "RESULT" note
  carrying the estimate, its standard error, and the reproduction commands.
- `scripts/greenium.py` module docstring.

### Changed

- The guard that was supposed to prevent this is replaced. It pinned one exact
  sentence (`"I make no empirical claim here"`), so the same claim reworded in
  another section passed. It now matches the *property* — any unqualified
  disclaimer of an estimate — across the brief, three READMEs, both scripts, and
  **the generated workbook's cells**, which is the surface that hid four vendor
  references for months.
- The qualification check is **sentence-scoped**. A first attempt checked whole
  cells, which let a long workbook note disclaim an estimate in one sentence and
  be excused by "German sovereign only" three sentences later. Mutation testing
  caught it; both mutations now fail the suite.
- A paired test asserts the qualified caveat is still present, so the fix cannot
  swing the other way into overclaiming.
- 255 → **262 tests**.

---

## [v0.9.1] — 2026-10-02 — Dashboard deployed

### Added

- The climate dashboard is live at
  **https://shangyuz-sustainable-finance.streamlit.app** — public, no sign-in.
  The live link and both document PDFs are now surfaced at the top of the root
  README, which is where a first-time visitor actually looks.
- `tests/test_deployment.py` gained guards for the published links: the live URL
  must appear in both READMEs (so one cannot go stale while the other is
  updated), the deployment status box must be ticked, and every PDF linked from
  the root README must exist — a broken link on the landing page is worse than no
  link.

### Note

An earlier check reported the app as private. That was wrong: the diagnostic used
a cookie-less request, which loops forever on Streamlit's session handshake even
for public apps. Re-tested with a cookie jar it returns HTTP 200 with no login
wall. The sharing setting had been correct all along.

- 252 → **255 tests**.

---

## [v0.9.0] — 2026-10-02 — The greenium, measured; SLL structuring memo

### Added — an actual greenium estimate

The portfolio previously specified a greenium methodology and claimed no result.
It now has one, from the issuer's own published data.

- **`scripts/fetch_bund_yields.py`** — downloads the twin-bond pairs and daily
  yields from the Deutsche Finanzagentur. The twin pairing is **derived, not
  asserted**: for each green security the script collects the conventional ISINs
  the issuer's factsheet links to, fetches each, and keeps the one whose coupon
  and maturity match *exactly*. A green bond with no exact match is reported and
  skipped — an approximate pair would reintroduce the matching error the twin
  structure exists to remove. All nine outstanding green Federal securities
  matched. Each factsheet embeds its full daily price and yield history as
  Highcharts JSON, which is the data source; fetched HTML is cached on disk.
- **The result**: pooled greenium **−1.50bps** (HAC SE 0.052, t = −28.7) across
  **8,094 paired daily observations**, September 2020 to October 2026, negative on
  99.8% of days, per-pair means −0.65bps to −2.40bps and all negative. No maturity
  pattern (correlation 0.11), so it is a label effect rather than a term-structure
  artefact.
- **Two findings worth more than the level.** First, the HAC correction is not
  cosmetic: on this data it **triples** the standard error, taking the
  t-statistic from −94 to −28.7. On a shorter sample that factor is the difference
  between a finding and an artefact. Second, the greenium has **compressed about
  80% since 2021** — −4.71bps then, −0.76bps in 2025 — which is consistent with a
  maturing market and sharpens the portfolio's thesis: at under 1bp the label
  carries no funding incentive worth restructuring for.
- `data/green_twin_pairs.csv` (9 coupon- and maturity-matched pairs) and
  `data/bund_yields.csv` (17,656 daily observations across 18 securities) are
  committed, so the estimate reproduces without network access.
- **`tests/test_greenium_result.py`** — pins the published estimate against the
  committed data, so the figures in the brief and FINDINGS.md cannot drift.
  Verified by mutation: shifting the green legs by 10bps fails six of its tests.

### Added — Project 2 structuring memo

- **`memo/SLL_Structuring_Memo.md`** + generated PDF. A credit-committee-style
  document that recommends structuring the facility as sustainability-linked
  **but not presenting the ratchet as the commercial rationale**, and takes a view
  on the KPI set rather than describing it: KPI 3 measures process (audit
  *coverage*) not outcome, and the renewable SPT can be met largely through
  procurement. Both accepted with stated conditions. Includes ranked integrity
  risks, six conditions precedent, and an explicit list of what the analysis does
  not claim.

### Changed

- `build_brief.py` generalised into a document-agnostic Markdown→PDF renderer:
  title and footer derive from the document's own H1, so one renderer serves both
  the brief and the memo.
- The brief's §4 replaced its "no empirical claim" disclaimer with the measured
  result, its uncertainty and the time trend. Its test now requires the estimate
  to be reported *with* a standard error and t-statistic — a point estimate
  without uncertainty is not a result.
- CI lints the fetcher and rebuilds both documents.
- 238 → **252 tests**.

---

## [v0.8.0] — 2026-10-02 — Audit write-up, greenium estimator, investment brief

### Added

- **`FINDINGS.md`** — what the October audit found, with mechanisms and
  quantified consequences, plus the argument the three projects add up to. The
  portfolio previously read as three parallel exercises; the thesis is that
  labelled debt splits into use-of-proceeds and performance-linked families, and
  the performance-linked family has a pricing problem (small incentive, scales
  with drawdown, gated by a fixed verification cost). The root README is reframed
  around it.
- **`scripts/greenium.py`** — greenium estimator built on sovereign green *twin*
  bonds, where the green and conventional legs share coupon, maturity and issuer,
  so the yield difference is the greenium by construction with no matching model.
  Inference is **Newey-West HAC corrected**: a daily yield spread is strongly
  autocorrelated, so the iid standard error understates uncertainty and an
  uncorrected t-test manufactures significance. Reports the per-pair distribution,
  the share of days actually negative, and whether each pair is an exact twin —
  a non-twin estimate must not read like a clean one.
  **No empirical estimate is claimed**: no yield data is committed and the fetch
  has not been run. 34 tests verify the estimator against synthetic series with a
  known true greenium.
- **`data/green_twin_pairs.example.csv`** — pair-registry template. Deliberately
  unpopulated: the estimator refuses to run while any row contains `FILL_ME`, and
  CI asserts that refusal, so the repo cannot publish numbers for securities that
  do not exist.
- **The investment brief** (`brief/Green_Bond_Market_Brief.md` + generated PDF) —
  three pages of analysis plus methodology and references, arguing that the
  $650bn headline conceals a European sovereign funding programme with a small
  private tail. Markdown is the source of truth; `scripts/build_brief.py` renders
  the PDF. Every headline figure is re-derived from the committed dataset and
  asserted in `tests/test_brief.py`, so the document cannot drift from the data.
- **Deployment preconditions verified and guarded** (`tests/test_deployment.py`).

### Fixed

- **Streamlit Cloud would have dropped the dashboard theme silently.** Streamlit
  resolves `.streamlit/config.toml` relative to the *working directory*, and Cloud
  runs from the repository root — so a config living only in
  `project3-climate-dashboard/` is never read. Added a root-level copy, with a
  test asserting the two stay identical.
- Three figures in the brief were wrong on first draft and caught by the figure
  tests: 2022 volume read $140.4bn against a true $140.3bn, its average deal size
  $831m against $830m, and the Social theme's volume share 4.3% against 4.2%. All
  three came from **double rounding** — formatting an already-2dp-rounded
  aggregate to 1dp. The tests now compare against raw sums.

### Changed

- CI additionally rebuilds the brief, asserts the greenium template refuses to
  estimate, and lints the two new modules.
- 183 → **238 tests**.

---

## [v0.7.0] — 2026-10-02 — Project 2: realistic RCF economics

### Added

- `project2-sll-structuring/scripts/sll.py` — facility economics as pure,
  unit-tested functions: ratchet grid, utilisation, commitment fee, break-even.
- `project2-sll-structuring/scripts/build_model.py` — generates the workbook, so
  Project 2 is reproducible for the same reason Project 1 now is. The `.xlsx` was
  previously committed with no script that produced it.
- **Utilisation and commitment fee.** The model priced the £650m RCF as fully
  drawn with no commitment fee. Both assumptions flatter the structure: the
  ratchet applies only to the drawn margin, so at 60% utilisation the best-case
  saving falls from £487.5k to **£292.5k**; and the undrawn balance carries a
  commitment fee (~35% of margin, 42bps here) worth £1.09m a year at that
  utilisation — several times the entire ratchet saving, and previously ignored.
- **Break-even analysis.** The ratchet saving scales with drawdown while the
  verification cost is fixed, so there is a utilisation below which the best
  possible ESG outcome does not cover the cost of proving it: **20.5%**. For an
  RCF held as an undrawn liquidity backstop — the normal use — the pricing
  benefit is therefore negligible, and the case for the SLL has to rest on
  signalling rather than cost of capital. That is a recognised criticism of the
  instrument and the model now makes it explicit.
- Two new sheets: "4. Utilisation Sensitivity" and "5. Economics & Caveats", the
  latter listing what the model deliberately does not claim.
- 58 tests for the SLL layer, including one that evaluates the workbook's Excel
  formulas and asserts they match the Python model cell by cell — a
  formula-driven workbook that silently disagrees with the code is worse than no
  workbook, because a reader has no reason to doubt it.
- `requirements-dev.txt`.

### Fixed

- The carbon glide path was hardcoded values, so editing the baseline or SPT left
  the interim targets stale. It is now interpolated from the two endpoints in
  Excel formulas.
- The scenario table used literal conditions (`IF(3=3,…)`) rather than referencing
  the row, so the rows could not be copied or extended.
- 2027 glide-path value displayed as 240.2 rather than 240.25.

### Changed

- CI lints and rebuilds both Excel models, and runs on a Python 3.11 + 3.13 matrix.

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
