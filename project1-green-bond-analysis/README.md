# Project 1 — Green Bond Market Analysis

## Overview

This project analyses the global labelled sustainable bond market using publicly
available issuance data from the Climate Bonds Initiative. I built it to understand
how sustainable debt markets have evolved — and specifically to examine how quickly
sustainability-linked bonds are emerging as a structurally different instrument
relative to traditional green bonds.

Two things surprised me. The first was how much the answer depends on whether you
measure in deal count or in dollars: SLBs are about 15% of transactions but only
3% of volume, so the "SLB boom" is many small deals rather than a shift in where
the money goes. The second was how much of this market is simply governments —
sovereign issuers are 82% of volume. The private-sector green bond market is far
smaller than the headline numbers suggest.

## Key Questions

- How has labelled sustainable bond issuance grown, in deals and in dollars?
- Which countries and sectors dominate issuance volume?
- Are sustainability-linked bonds (SLBs) displacing traditional green bonds?
- Do green bonds trade at a yield premium vs conventional bonds — the "greenium"?

## Dataset

- **Source:** Climate Bonds Initiative — News Makers dataset
- **Coverage:** 732 bond issuances, 64 countries plus supranational issuers, 2015–2024
- **Total volume:** $650.04bn
- **Themes:** Green (490 deals), Sustainability (109), SLB (108), Social (25)

The extract is committed at [`data/cbi_newsmakers.csv`](./data/cbi_newsmakers.csv)
so the whole model rebuilds from source with one command.

### Scope notes

Two caveats matter for reading any figure below:

- **2024 is a partial year** in this extract. Its −47% volume change is the data
  cut-off, not a market contraction, and it is not a trend.
- **2015–2017 is thin** — 9 deals, $11.90bn. It is included in every total so all
  sheets reconcile to the same $650.04bn, but it is too sparse to support
  year-on-year inference.

## Key Findings

- **Growth depends on the unit.** Deal count grew from 10 in 2018 to 238 in 2023
  (+2,280%); USD volume over the same period grew from $17.6bn to $184.5bn
  (+950%). Deal count overstates growth because average deal size fell as the
  market broadened. The +2,280% figure is a count, not a volume.
- **Green bonds are 67% of deals but 81% of volume** — the average green deal is
  materially larger than the average labelled bond.
- **SLBs are the fastest-growing theme but remain small in dollars**: ~15% of
  deals, ~3% of volume, reaching 11.8% of annual volume in 2024 from nil before
  2021.
- **Sovereign issuers are 82% of volume** across 448 deals. Government
  programmes, not corporate issuance, are what scaled this market.
- **Deal count and volume rank countries differently.** China leads on deal count
  (68) but is sixth by volume, because Chinese issuance here is many small bank
  deals while European volume sits in large sovereign programmes. Germany,
  France and the UK are the top three by volume (36% combined).
- **Greenium: −1.50bps**, measured on Germany's green twin Bunds across 8,094
  paired daily observations (HAC SE 0.052, t = −28.7), and **compressed ~80% since
  2021**. That sits close to Zerbib's −2bps and well below the primary-market
  studies' −20bps, which is expected: those measure the issuance concession, this
  measures secondary trading. German sovereign only — see the limitations below.

## Methodology

Data is cleaned and aggregated in Python (pandas), then written to a nine-sheet
Excel model with openpyxl. Every figure in the workbook is computed at build time
— nothing is hardcoded — so the model regenerates cleanly when the dataset is
extended.

### Data cleaning

The source extract is a public dataset rather than a curated product, and it is
dirty in ways that silently distort the analysis if left alone. All of this is
applied in code and documented on sheet 1 of the workbook:

| Issue | Records | Why it matters |
|---|---|---|
| `Sector` uses the string `"0"` for "not disclosed" | 64 | Appears as a sector named "0" in the breakdown |
| `Sector` missing entirely | 1 | Grouped with the above as "Unclassified" |
| `Sector` taxonomy fragmented — 34 labels for 11 real groups | 140 | "Financials"/"Financial"/"Finance"/"Banks"/"Commercial Bank"/"Diversified Banks"/"Financial Institution" are one sector; split across seven rows none of them ranks |
| `Country` duplicate labels — USA/United States, UK/United Kingdom, China_HK, Supernational/Supranational | 42 | Splits one country's volume across rows and inflates the country count |
| `Country` trailing whitespace — `"Netherlands "` | 1 | Aggregated separately from `"Netherlands"` |
| `Issuer Name` case variants — GoodLeap/Goodleap | 1 | One issuer counted twice |

Folding the sector labels is what moves Financials into second place by volume.
Folding the country labels raises the UK from $59.34bn to $59.79bn and the
Netherlands from $28.81bn to $29.58bn, and corrects the country count from an
apparent 69 to an actual 64.

Two source records look wrong but are **left as published** rather than silently
overwritten, and are flagged on sheet 1: Schneider Electric SE (a French issuer)
is tagged to the United States, and its 2015 transaction is labelled SLB years
before that market existed — which is why 2015 shows a 100% SLB share.

## Running it

```bash
pip install -r ../requirements.txt
python scripts/process_data.py
```

Rebuilds `Green_Bond_Market_Analysis.xlsx` from `data/cbi_newsmakers.csv`.
Options: `--input`, `--output`, `--min-year`.

```bash
python scripts/build_brief.py   # regenerate the investment brief PDF
pytest ../tests/                # 262 tests: cleaning, aggregation, model, brief, greenium
```

### The investment brief

[`brief/Green_Bond_Market_Brief.pdf`](./brief/Green_Bond_Market_Brief.pdf) argues
that the labelled bond market's $650bn headline conceals a European sovereign
funding programme with a small private tail: 82.5% of volume is sovereign, 64.4%
is European, and the instrument with the strongest theoretical claim — the
performance-linked SLB — is 14.8% of deals but 3.4% of volume.

The markdown is the source of truth and the PDF is generated from it. Every
headline figure in the brief is re-derived from the committed dataset and asserted
in `tests/test_brief.py`, so the document cannot drift from the data.

## Files

| File | Description |
|------|-------------|
| `data/cbi_newsmakers.csv` | Source extract — 732 records, the input to everything |
| `scripts/clean.py` | Loading, normalisation and aggregation (pure pandas, unit-tested) |
| `scripts/greenium.py` | Greenium estimator — twin-bond spreads with HAC-corrected inference |
| `scripts/fetch_bund_yields.py` | Downloads the twin pairs and daily yields from the Finanzagentur |
| `data/green_twin_pairs.csv` | The nine twin pairs, coupon- and maturity-matched |
| `data/bund_yields.csv` | 17,656 daily per-ISIN yields across 18 securities |
| `data/green_twin_pairs.example.csv` | Pair-registry template, for other issuers |
| `scripts/process_data.py` | Builds the Excel model from the cleaned data |
| `Green_Bond_Market_Analysis.xlsx` | Nine-sheet model (generated — do not edit by hand) |
| `brief/Green_Bond_Market_Brief.md` | Investment brief — the editable source |
| `brief/Green_Bond_Market_Brief.pdf` | The brief as a PDF (generated from the markdown) |
| `scripts/build_brief.py` | Renders the brief to PDF |

### Workbook contents

| Sheet | Contents |
|---|---|
| 0. Summary Dashboard | Headline KPIs, key findings, scope reconciliation |
| 1. Data Quality | Every cleaning rule, with records affected and rationale |
| 2. Annual Issuance | Deals, volume, both YoY series; two charts |
| 3. Geography | Top 15 countries by volume, with share |
| 4. Sector Breakdown | Normalised sector taxonomy, with share |
| 5. Theme Evolution | Theme totals plus Year × Theme on deals *and* volume |
| 6. SLB Analysis | SLB vs green, two penetration measures, largest SLB issuers |
| 7. Greenium Framework | Published evidence, sign convention, open-data method |
| 8. Cleaned Data | The post-normalisation dataset the model is built from |

## Greenium: sign convention

Reported throughout as **(green yield − conventional yield) in bps**, so a
**negative** number means the green bond yields less and the greenium exists.
The opposite convention is also common in practice, so it is stated explicitly
to avoid ambiguity.

The measurement uses sovereign **green "twin" bonds**: Germany issues each green
Bund alongside a conventional Bund with the *same coupon and same maturity from
the same issuer*, so the yield difference is the greenium almost by construction,
with no matching model required. That is a cleaner identification strategy than
the matched-pair regressions the literature relies on, not merely a free
substitute for them. France (OAT verte) and the UK (green gilts) publish
comparable series without the exact-twin structure.

### Running the estimator

`scripts/greenium.py` implements it:

```bash
python scripts/greenium.py --pairs data/green_twin_pairs.csv \
                          --yields data/bund_yields.csv --strict
```

- **`--pairs`** is a registry of green/conventional pairs. The committed file is
  a *template* (`green_twin_pairs.example.csv`) and the script refuses to run
  while it still contains `FILL_ME` — populate it from the issuer's published
  list so every ISIN traces to a primary source.
- **`--yields`** is a tidy `date,isin,yield_pct` CSV of daily yields, downloaded
  free from the relevant debt management office.
- **`--strict`** refuses any pair that is not an exact twin. Without it,
  non-twin pairs are usable but flagged, and the output reports each pair's
  `maturity_gap_days` so a mismatched comparison can't be mistaken for a clean one.

Inference is **Newey-West HAC corrected**. A daily yield spread is strongly
autocorrelated, so the ordinary standard error of its mean is badly understated
and an uncorrected t-test will find significance that is not there. The estimator
reports the HAC standard error, the resulting t-statistic, the full distribution
across pairs, and the share of days on which the spread was actually negative —
because the published range (−2 to −20bps) is mostly heterogeneity across issuers
and periods rather than disagreement about method.

### The result

Measured across all nine outstanding German green Federal securities and their
exact twins — **8,094 paired daily observations, September 2020 to October 2026**:

| | |
|---|---|
| Pooled greenium | **−1.50bps** (HAC SE 0.052, t = −28.7) |
| Days with a negative spread | 99.8% |
| Per-pair means | −0.65bps to −2.40bps, all negative |
| 2021 → 2025 | −4.71bps → −0.76bps (~80% compression) |

The HAC correction is not cosmetic: on this data it triples the standard error,
taking the t-statistic from −94 to −28.7. There is no maturity pattern
(correlation 0.11), so this is a label effect, not a term-structure artefact.

Reproduce it with:

```bash
python scripts/fetch_bund_yields.py        # downloads pairs + yields from the issuer
python scripts/greenium.py --pairs data/green_twin_pairs.csv \
                           --yields data/bund_yields.csv --strict
```

The estimate is pinned in `tests/test_greenium_result.py` so the figures quoted
here and in the brief cannot drift from the committed data.

## Skills Demonstrated

- Sustainable finance market analysis and investment research
- Data cleaning and transformation, including diagnosing silent data-quality defects
- Financial modelling and charting in Excel (openpyxl), fully reproducible from source
- Reproducible analysis: tested, CI-checked, regenerable with one command
- Research design — specifying an identification strategy against open data

## Status

- [x] Data acquisition, cleaning and documented normalisation
- [x] Annual issuance analysis (2015–2024, deals and volume)
- [x] Geographic and sector breakdown
- [x] SLB vs green bond comparison
- [x] Greenium literature review and matched-pair framework
- [x] Greenium estimator implemented and unit-tested
- [x] Greenium empirical estimate — −1.50bps across 8,094 paired observations
- [x] Reproducible build from committed source data
- [x] Unit tests and CI
- [x] Investment brief — market structure, the SLB puzzle, and the measured greenium

## Data Sources

All data used here is freely and publicly available:

- **Climate Bonds Initiative** — public market reports and News Makers dataset
- **Academic papers** — cited below (open access or author preprints)
- **Sovereign debt management offices** — Finanzagentur (DE), AFT (FR), DMO (UK),
  for the greenium framework
- **No proprietary data** (Bloomberg, Refinitiv, or similar) is used anywhere,
  and CI fails the build if a reference to one reappears — including inside the
  `.xlsx` files, where a plain text search would not find it

## References

Zerbib, O.D. (2019). *The effect of pro-environmental preferences on bond prices:
Evidence from green bonds.* Journal of Banking & Finance, 98, 39–60.

Löffler, K.U., Petreski, A. & Stephan, A. (2021). *Drivers of green bond issuance
and new evidence on the "greenium".* Eurasian Economic Review, 11, 1–24.

Caramichael, J. & Rapp, A.C. (2022). *The Green Corporate Bond Issuance Premium.*
Federal Reserve International Finance Discussion Paper 1346.

Panizza, U. et al. (2025). *Sovereign Green Bonds.* CEPR Discussion Paper No. 20817.

Banque de France (2025). *The Green Bond Premium.* Working Paper No. 1010.

---
*Last updated: 2026-10-02*

*Part of the [Sustainable Finance Portfolio](../README.md)*
