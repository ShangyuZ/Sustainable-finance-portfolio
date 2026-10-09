# Project 1 — Green Bond Market Analysis

## Overview

This project is an exploratory analysis of a curated sample of labelled
sustainable bonds — the Climate Bonds Initiative's News Makers extract, which
tracks notable transactions rather than the whole market. I built it to understand
how sustainable debt markets have evolved — and specifically to examine how quickly
sustainability-linked bonds are emerging as a structurally different instrument
relative to traditional green bonds.

Two things surprised me. The first was how much the answer depends on whether you
measure in deal count or in dollars: SLBs are about 15% of transactions but only
3% of volume, so the "SLB boom" is many small deals rather than a shift in where
the money goes. The second was how much the sample's selection shapes its
composition: sovereign issuers are 82% of its volume, against about 11.6% in CBI's
own market-wide summary. A newsflow extract is a good place to practise cleaning
and description, and a poor basis for statements about the market's make-up.

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

### What is committed, and what is not

The record-level extract is **not** in this repository. Climate Bonds Initiative's
terms of use prohibit reproducing or storing their content without prior written
permission, which I do not have, so redistributing their records here was not mine
to do — see [DATA.md](../DATA.md) for the terms and the full reasoning.

What is committed instead is the derived output: the aggregate tables in
[`data/aggregates/`](./data/aggregates/). The whole model still rebuilds with one
command, every figure quoted below is computed from those tables, and
`tests/test_aggregates.py` checks each one — so nothing here is unverifiable. What
is lost is rebuilding from records inside this repository: that needs your own
licensed copy of the extract, and `scripts/export_aggregates.py --input <copy>`
regenerates every table from it. The tests then assert the regenerated tables match
the committed ones exactly, so the substitution is checked rather than asserted.

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
- **SLBs are the fastest-growing theme in the sample but small in dollars**: ~15%
  of deals, ~3% of volume, reaching 11.8% of annual volume in 2024 from almost
  nothing before 2021 (one 2015 record, flagged as mislabelled, aside).
- **Sovereign issuers are 82% of the sample's volume** across 448 deals. That is
  a selection effect, not a market share: CBI's *Sustainable Debt Market Summary
  Q3 2024* puts sovereigns at $630.5bn of $5.4tn cumulative aligned volume, about
  11.6%. The two sources have different coverage, so the comparison shows the
  sample is not representative of the market, not by how much.
- **Deal count and volume rank countries differently.** China leads on deal count
  (68) but is sixth by volume, because Chinese issuance here is many small bank
  deals while European volume sits in large sovereign programmes. Germany,
  France and the UK are the top three by volume (36% combined).
- **Greenium: −1.50bps**, measured on Germany's green twin Bunds across 8,094
  paired daily observations (panel HAC SE 0.330, t = −4.5), down from −4.71bps in
  2021 to −0.76bps in 2025. The sign is robust to every inference choice tested;
  the precision is modest. It sits close to Zerbib's −2bps and Panizza et al.'s
  ≈ −2bps for advanced-economy sovereigns. German sovereign only — see the
  limitations below.

## Methodology

Data is cleaned and aggregated in Python (pandas), then written to an eight-sheet
Excel model with openpyxl. Every figure in the workbook is computed at build time
— nothing is hardcoded — so the model regenerates cleanly when the dataset is
extended.

`clean.py` holds the record-level cleaning and aggregation; `aggregates.py` wraps
its output in one container that can be built either from records or from the
committed tables. The workbook reads only that container, so both paths produce an
identical file — which is what makes the committed tables usable in place of the
extract rather than merely convenient.

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

Rebuilds `Green_Bond_Market_Analysis.xlsx` from the committed aggregates in
`data/aggregates/`. With your own licensed copy of the extract, pass
`--input <path>` to recompute the tables from records first; both paths produce the
same workbook. Other options: `--output`, `--aggregates`, `--min-year`.

```bash
python scripts/export_aggregates.py --input <your copy of the extract>
                                # regenerate the aggregate tables from records
python scripts/build_brief.py   # regenerate the investment brief PDF
pytest ../tests/                # tests: cleaning, aggregation, model, brief, greenium
```

### The investment brief

[`brief/Green_Bond_Market_Brief.pdf`](./brief/Green_Bond_Market_Brief.pdf) argues
that the labelled bond market's $650bn headline conceals a European sovereign
funding programme with a small private tail: 82.5% of volume is sovereign, 64.4%
is European, and the instrument with the strongest theoretical claim — the
performance-linked SLB — is 14.8% of deals but 3.4% of volume.

The markdown is the source of truth and the PDF is generated from it. Every
headline figure in the brief is checked against the committed aggregates in
`tests/test_brief.py`, which checks key calculations and consistency with the
data; it does not validate interpretation or citations. Those checks
read the full-precision companion tables rather than the rounded presentation
ones: three figures in the brief's first draft were wrong because a value already
rounded to 2dp was then formatted to 1dp, which shifts it.

## Files

| File | Description |
|------|-------------|
| `data/aggregates/` | Derived tables — what ships in place of the records (see DATA.md) |
| `scripts/clean.py` | Loading, normalisation and aggregation (pure pandas, unit-tested) |
| `scripts/aggregates.py` | One table set, built from records or from the committed CSVs |
| `scripts/export_aggregates.py` | Regenerates the aggregate tables from a licensed extract |
| `scripts/greenium.py` | Greenium estimator — twin-bond spreads with HAC-corrected inference |
| `scripts/fetch_bund_yields.py` | Fetches the twin pairs and daily yields from the Finanzagentur |
| `data/greenium_summary.csv` | Per-pair and pooled estimates — the published result |
| `data/greenium_by_year.csv` | The yearly series behind the compression finding |
| `data/greenium_diagnostics.json` | HAC correction, maturity correlation, sample bounds |
| `data/green_twin_pairs.example.csv` | Pair-registry template, for other issuers |
| `scripts/process_data.py` | Builds the Excel model from the aggregates |
| `Green_Bond_Market_Analysis.xlsx` | Eight-sheet model (generated — do not edit by hand) |
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
| 7. Greenium Framework | Published evidence, sign convention, open-data method, result |

There is no longer a "Cleaned Data" sheet. It held all 732 source records, which
made the workbook a second copy of data that is not redistributable — and a copy
no text search of the repository would have found. `tests/test_data_licensing.py`
now fails the build on any sheet large enough to hold records, under any name.

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

`scripts/greenium.py` implements it. Neither input is committed — Finanzagentur
reserves all rights in their published data (see [DATA.md](../DATA.md)) — so fetch
them first:

```bash
python scripts/fetch_bund_yields.py        # writes both files, free, from the issuer
python scripts/greenium.py --pairs data/green_twin_pairs.csv \
                          --yields data/bund_yields.csv --strict
```

- **`--pairs`** is a registry of green/conventional pairs. The committed file is
  a *template* (`green_twin_pairs.example.csv`) and the script refuses to run
  while it still contains `FILL_ME` — populate it, or let the fetcher populate it,
  from the issuer's published list so every ISIN traces to a primary source.
- **`--yields`** is a tidy `date,isin,yield_pct` CSV of daily yields, downloaded
  free from the relevant debt management office.
- **`--strict`** refuses any pair that is not an exact twin. Without it,
  non-twin pairs are usable but flagged, and the output reports each pair's
  `maturity_gap_days` so a mismatched comparison can't be mistaken for a clean one.

Inference uses a **panel HAC (Driscoll-Kraay) standard error with a 250-day
Bartlett bandwidth**. A daily yield spread stays autocorrelated for months (0.66 at
120 trading days on this data), and the pooled sample stacks nine pairs quoted on
the same dates, so both the persistence and the same-day co-movement have to be
accounted for. The estimator reports that standard error, the resulting
t-statistic, a bandwidth sensitivity table, the full distribution across pairs, and
the share of days on which the spread was actually negative —
because the published range (−2 to −20bps) is mostly heterogeneity across issuers
and periods rather than disagreement about method.

### The result

Measured across all nine outstanding German green Federal securities and their
exact twins — **8,094 paired daily observations, September 2020 to October 2026**:

| | |
|---|---|
| Pooled greenium (per observation) | **−1.50bps** (panel HAC SE 0.330, t = −4.5) |
| Equal weight per pair / per date | −1.29bps / −2.04bps |
| t across bandwidths 60 / 120 / 250 days | −8.2 / −6.0 / −4.5 |
| t across the nine pair means (8 df; a cross-check — pairs share market shocks) | −5.7 |
| Pair-date observations with a negative spread | 99.8% |
| Dates on which the cross-pair average is negative | 1,544 of 1,544 |
| Per-pair means | −0.65bps to −2.40bps, all negative |
| 2021 → 2025 (descriptive) | −4.71bps → −0.76bps |

**A correction to the first version.** It applied a 10-lag Newey-West correction
to the nine pairs' histories stacked end to end and reported t = −28.7. Ten lags
cut off most of the persistence, and stacking treated pairs quoted on the same
date as independent evidence. The sign survives every specification above; the
precision of that figure did not. The maturity correlation of 0.11 across nine
pairs rules out a strong tenor pattern but cannot establish a pure label effect —
liquidity and repo differences between the twins remain possible contributors.

The estimator's output *is* committed, even though its input is not:
`data/greenium_summary.csv` (per-pair and pooled), `data/greenium_by_year.csv`
(the yearly means, descriptive only) and `data/greenium_diagnostics.json` (the
inference sensitivity table, alternative weightings, autocorrelation, the maturity
correlation, the sample bounds). Every figure in the table above is
checked against those files by `tests/test_greenium_result.py`, which keeps the
write-ups consistent with the computed result.

Reproduce the result from scratch with:

```bash
python scripts/fetch_bund_yields.py        # fetches pairs + yields from the issuer
python scripts/greenium.py --pairs data/green_twin_pairs.csv \
                           --yields data/bund_yields.csv --strict \
                           --out data/greenium_summary.csv \
                           --out-by-year data/greenium_by_year.csv \
                           --out-diagnostics data/greenium_diagnostics.json
```

With the fetched yields present, the test suite additionally asserts that
re-estimating reproduces the committed output exactly — so the published numbers
are verifiable from source, not just internally consistent.

## Skills Demonstrated

- Sustainable finance market analysis and investment research
- Data cleaning and transformation, including diagnosing silent data-quality defects
- Financial modelling and charting in Excel (openpyxl), generated by script rather
  than hand-maintained
- Reproducible analysis: tested, CI-checked, regenerable with one command from
  what is committed — and from the source records with a licensed copy of the
  extract, which the tests verify produces an identical result
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
- [x] Investment brief — sample composition, SLBs in the sample, and the measured greenium

## Data Sources

Every source here is publicly accessible without a paid subscription. Two of them
reserve their rights, which is a different thing, so neither is redistributed in
this repository — see [DATA.md](../DATA.md):

- **Climate Bonds Initiative** — public market reports and the News Makers
  dataset. Accessible free; reproduction prohibited without written permission,
  so the records are not here and the derived aggregates are.
- **Deutsche Finanzagentur** — daily yields for each green Federal security and
  its conventional twin. Published free; all rights reserved, so the
  observations are not here and the estimator output is. AFT (FR) and the UK DMO
  publish comparable series for the wider framework.
- **Academic papers** — cited below (open access or author preprints), cited
  rather than reproduced.
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

Climate Bonds Initiative (2024). *Sustainable Debt Market Summary Q3 2024.*

Driscoll, J.C. & Kraay, A.C. (1998). *Consistent covariance matrix estimation with
spatially dependent panel data.* Review of Economics and Statistics, 80(4), 549–560.

Panizza, U., Shi, S., Weder di Mauro, B. & Gulati, M. (2025). *The Sovereign
Greenium: Big Promise but Small Price Effect.* CEPR Discussion Paper No. 20817.

Pietsch, A. & Salakhova, D. (2025). *Pricing of Green Bonds: Greenium Dynamics and
the Role of Retail Investors.* Banque de France Working Paper No. 1010.

---
*Last updated: 2026-10-09*

*Part of the [Sustainable Finance Portfolio](../README.md)*
