# Data provenance

Per-source, rather than one blanket claim. The root README previously said *"All
data is publicly available and openly licensed. No proprietary or restricted data
is used anywhere."* That was an absolute statement about third-party rights that
nobody had verified — the same failure mode [FINDINGS.md](./FINDINGS.md) §1
describes, so it has been replaced with the table below.

| Dataset | File | Source | Licence / terms | Verified? |
|---|---|---|---|---|
| Energy & electricity mix | fetched at runtime | [OWID energy-data](https://github.com/owid/energy-data) | **CC BY 4.0** | ✅ stated by publisher |
| CO₂ emissions | fetched at runtime | [OWID co2-data](https://github.com/owid/co2-data) | **CC BY 4.0** | ✅ stated by publisher |
| German Federal securities, daily yields | `project1-.../data/bund_yields.csv` | [Deutsche Finanzagentur](https://www.deutsche-finanzagentur.de) | German public-sector information | ⚠️ **not verified** — see below |
| Green bond issuance | `project1-.../data/cbi_newsmakers.csv` and sheet 8 of the workbook | Climate Bonds Initiative, "News Makers" | Unknown | ❌ **not verified** — see below |
| EU ETS allowance prices | `project3-.../data/eua_prices.csv` | "Compiled from public sources" | Unknown | ❌ **uncited** — see below |
| Greenium literature | cited inline | Published papers | Academic, cited not reproduced | ✅ |
| Sector carbon intensities | hardcoded in `app.py` | MSCI / TCFD sector guidance, public | Public guidance | ⚠️ indicative benchmarks |

## The three that are not clean

### 1. Climate Bonds Initiative issuance data — redistribution terms unknown

732 records are redistributed here, in two places: `data/cbi_newsmakers.csv` and
sheet "8. Cleaned Data" of `Green_Bond_Market_Analysis.xlsx`. The data entered
this repository in the original March 2026 commit, inside that workbook; the CSV
is an extract of the same rows, so **removing the CSV alone would not change the
position**.

CBI publishes market commentary and reports publicly, but its underlying market
data is not released under an open licence as far as I can establish, and I have
not confirmed that redistributing a derived extract is permitted. Until that is
checked, this should be treated as **unresolved**, not as "public".

If the terms turn out to prohibit redistribution, the fix is to remove the rows
from both the CSV and the workbook sheet and ship the aggregates only — which
would make Project 1's figures non-reproducible from this repository, and that
trade-off should be made deliberately rather than by default.

### 2. Deutsche Finanzagentur yields — likely reusable, unverified

17,656 daily observations across 18 securities, extracted from the issuer's own
published factsheet pages. German public-sector information is generally reusable,
and this is the issuer publishing data about its own securities. But I have not
read their terms of use, so it is marked unverified rather than assumed.

Reproducible with `project1-green-bond-analysis/scripts/fetch_bund_yields.py`, so
it could be removed from the repository without losing reproducibility.

### 3. EU ETS allowance prices — uncited, and demonstrably approximate

`eua_prices.csv` (439 weekly observations, 2018–2026) is described only as
"compiled from public sources", with no citation. It predates the October 2026
audit, and its lineage includes a version that silently fell back to synthetic
data (see CHANGELOG v0.3.0).

Checked against known EUA history it is **broadly right but not exact**: realistic
volatility, and seven of eight historical checkpoints in range — but it misses the
March 2022 post-invasion crash entirely (it shows roughly €76–78 for early March
2022, when allowances actually fell to around €58), and its all-time high of
€97.88 understates the ~€100+ reached in February 2023.

It is therefore **indicative, not a reference series**, and is labelled as such in
the dashboard. Any analysis that turns on precise EUA levels or on the March 2022
episode should not use this file.

## Principle

Where a licence is stated by the publisher, it is cited. Where it is not, this
file says so rather than assuming. An unverified claim about someone else's rights
is worse than an acknowledged gap, and the portfolio's own argument is that claims
you cannot test should not be made.
