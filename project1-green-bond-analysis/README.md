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
- **Greenium:** the literature consistently finds a small negative premium —
  green bonds yield a few bps *less* than comparable conventional bonds (−2bps in
  Zerbib 2019, up to −20bps in primary-market studies). No empirical estimate is
  claimed here; sheet 7 specifies a framework that can be run on free data.

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
pytest ../tests/            # 125 tests covering cleaning, aggregation and the model
```

## Files

| File | Description |
|------|-------------|
| `data/cbi_newsmakers.csv` | Source extract — 732 records, the input to everything |
| `scripts/clean.py` | Loading, normalisation and aggregation (pure pandas, unit-tested) |
| `scripts/process_data.py` | Builds the Excel model from the cleaned data |
| `Green_Bond_Market_Analysis.xlsx` | Nine-sheet model (generated — do not edit by hand) |

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

The measurement framework uses sovereign **green "twin" bonds**: Germany issues
each green Bund alongside a conventional Bund with the *same coupon and same
maturity from the same issuer*, so the yield difference is the greenium almost by
construction, with no matching model required. France (OAT verte) and the UK
(green gilts) publish comparable series. All of these yields are published free
by the respective debt management offices — which is why this framework needs no
paid data subscription.

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
- [x] Reproducible build from committed source data
- [x] Unit tests and CI
- [ ] 3-page investment brief *(not started — no PDF in this repo yet)*

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
