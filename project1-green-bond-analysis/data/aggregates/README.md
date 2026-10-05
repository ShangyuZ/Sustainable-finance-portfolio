# Derived aggregates

Summary statistics computed from the Climate Bonds Initiative "News Makers"
extract. **The record-level source data is not redistributed here** — CBI's terms
of use prohibit reproducing or storing their content without prior written
permission (see ../../../DATA.md).

These files are the derived output of that analysis, not the dataset. Every
figure quoted in the project README, the Excel model and the investment brief is
computed from the same pipeline and is checked against these files by
`tests/test_aggregates.py`, so the published numbers still cannot drift
unnoticed.

Regenerate with `scripts/export_aggregates.py --input <your copy of the extract>`.

| File | Contents |

|---|---|
| `annual_issuance.csv` | Deals, USD volume and both YoY series by year |
| `by_country.csv` | Top 25 countries by USD volume |
| `by_sector.csv` | Volume and deal count by normalised sector |
| `by_theme.csv` | Volume and deal count by bond theme |
| `slb_vs_green.csv` | SLB vs green issuance and two penetration measures |
| `theme_by_year_deals.csv` | Year x theme, deal count |
| `theme_by_year_volume.csv` | Year x theme, USD volume |
| `top_issuers_slb.csv` | Largest SLB issuers by volume |
| `annual_precise.csv` | Unrounded deal count and volume by Year |
| `sector_precise.csv` | Unrounded deal count and volume by Sector |
| `theme_precise.csv` | Unrounded deal count and volume by Theme |
| `data_quality.csv` | Cleaning rules applied, with records affected |
| `headline_metrics.json` | Totals, coverage, counts and shares |
