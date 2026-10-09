# Data provenance

Per-source, rather than one blanket claim. The root README previously said *"All
data is publicly available and openly licensed. No proprietary or restricted data
is used anywhere."* That was an absolute statement about third-party rights that
nobody had verified — the same failure mode [FINDINGS.md](./FINDINGS.md) §1
describes, so it has been replaced with the table below.

Two of those sources turned out to prohibit redistribution. Their data has been
removed from this repository; what remains in its place is this project's own
derived output. The reasoning is in §1 and §2.

| Dataset | What is in this repository | Source | Licence / terms | Verified? |
|---|---|---|---|---|
| Energy & electricity mix | fetched at runtime | [OWID energy-data](https://github.com/owid/energy-data) | **CC BY 4.0** | ✅ stated by publisher |
| CO₂ emissions | fetched at runtime | [OWID co2-data](https://github.com/owid/co2-data) | **CC BY 4.0** | ✅ stated by publisher |
| Green bond issuance | **aggregates only** — `data/aggregates/` | Climate Bonds Initiative, "News Makers" | **All rights reserved**; reproduction prohibited without written permission | ✅ verified — records removed, see §1 |
| German Federal securities, daily yields | **estimator output only** — `data/greenium_*.csv` | [Deutsche Finanzagentur](https://www.deutsche-finanzagentur.de) | **All rights reserved** | ✅ verified — observations removed, see §2 |
| EU ETS allowance prices | `project3-.../data/eua_prices.csv` | "Compiled from public sources" | Unknown | ❌ **uncited and not verified** — see §3 |
| Greenium literature | cited inline | Published papers | Academic, cited not reproduced | ✅ |
| Sector carbon intensities | hardcoded in `app.py` | **None** — assumed illustrative inputs | n/a | ⚠️ not sourced; the calculator is labelled illustrative |

## 1. Climate Bonds Initiative issuance data — removed

**The terms, now checked.** Climate Bonds Initiative's website terms state that
*"reproduction, use, storage, or transmission of any content and / or materials
available on this website, in any form, is prohibited other than with the prior
written permission of Climate Bonds Initiative"*. I do not have that permission.
Redistributing their records here was not mine to do, whatever the attribution.

**What was removed.** 732 records, which sat in two places: `cbi_newsmakers.csv`
and sheet "8. Cleaned Data" of `Green_Bond_Market_Analysis.xlsx`. Both are gone.
The workbook sheet mattered as much as the file — the data entered this repository
in the original March 2026 commit *inside that workbook*, so deleting the CSV
alone would have changed nothing while the records still shipped in the `.xlsx`,
where no text search of the repository would have found them.

**What is published instead.** The derived aggregates in
`project1-green-bond-analysis/data/aggregates/`: annual issuance, the country,
sector and theme breakdowns, the year-by-theme matrices, SLB penetration, the
largest SLB issuers, the cleaning report and the headline metrics. These are
summary statistics I computed, not CBI's dataset.

**What that costs, stated plainly.** Project 1 no longer rebuilds from records
inside this repository. Every published figure is still verifiable — the workbook
builds from the committed aggregates with one command, and `tests/test_aggregates.py`
checks each one — but reproducing the pipeline *from source* now requires your own
licensed copy of the extract. `scripts/export_aggregates.py --input <your copy>`
regenerates every aggregate, and `tests/test_aggregates.py` then asserts the
result matches the committed files exactly, so the substitution is checkable
rather than asserted.

That is a real loss of reproducibility, and it is the right trade: the previous
position was reproducible because it redistributed data it had no right to.

## 2. Deutsche Finanzagentur yields — removed

**The terms, now checked.** The factsheet pages carry *"Copyright:
Bundesrepublik Deutschland – Finanzagentur GmbH, Frankfurt/Main, Germany. All
rights reserved."* German public-sector information is often reusable and this is
an issuer publishing data about its own securities, so the position is weaker than
CBI's — but "all rights reserved" is an explicit reservation, and I am not going
to read a permission into it that it does not grant.

**What was removed.** 17,656 daily yield observations (`bund_yields.csv`) and the
pair registry derived from the same factsheets (`green_twin_pairs.csv`).

**What is published instead.** This project's own estimator output:
`greenium_summary.csv` (per-pair and pooled estimates), `greenium_by_year.csv`
(the compression series) and `greenium_diagnostics.json` (the HAC correction, the
maturity correlation, the sample bounds). Every greenium figure quoted in the
brief is checked against these by `tests/test_greenium_result.py`.

**What that costs — almost nothing.** `scripts/fetch_bund_yields.py` restores both
files from the issuer in one command. Once they are present, the suite's
reproducibility tests run as well and assert that re-estimating reproduces the
committed output exactly. The pair registry template
(`green_twin_pairs.example.csv`) stays, because it documents the method rather
than the data.

## 3. EU ETS allowance prices — uncited, and demonstrably approximate

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

**Why it was not removed with the other two.** No rightsholder is identified and
no terms are asserted over it, so unlike §1 and §2 there is nothing here saying it
may not be redistributed. Removing it would therefore be a guess rather than a
response to stated terms. What it needs is a citation, not deletion — and until it
has one, the honest label is the one above. If a source is identified that does
prohibit redistribution, it goes the same way as the other two.

## Git history

Removing the files from the current tree was not sufficient on its own, for the
same reason that deleting the CSV without the workbook sheet was not: the data
remained in git history, and a plain `git clone` of this public repository handed
over all 18,389 rows to anyone who ran `git show` against an old commit.

History has therefore been rewritten (`git filter-repo`, stripping the three
record blobs and the three record-bearing workbook versions). All 32 commits and
their messages are preserved — the audit trail this repository is largely about
is intact — and the working tree is byte-identical to before the rewrite. A fresh
clone now contains no record-level data at any commit; the largest blob in the
whole history is this repository's own CHANGELOG.

**One residual exposure, stated rather than glossed — and corrected.** The first
version of this note said the old objects were unreachable and awaiting garbage
collection. That was wrong, and the error mattered: it implied the problem would
expire on its own. It will not.

The pre-rewrite commits are still *reachable*, pinned by nine permanent
`refs/pull/N/head` refs that GitHub creates for every pull request and keeps for
the life of the repository. Verified: fetching `refs/pull/7/head` and walking one
commit back yields both record files. So the data remains retrievable
indefinitely by anyone who fetches a PR ref or constructs a
`raw.githubusercontent.com` URL from a pre-rewrite SHA — and those SHAs are
listed on this repository's own pull-request pages, so they are discoverable
rather than secret.

A fresh clone gets nothing, and the web interface shows nothing. That is not the
same as gone, and no amount of waiting changes it. Only two things actually do:
GitHub Support dereferencing those PR refs, or deleting the repository, which
takes its PR refs with it. GitHub's documented purge workflow is written for
*sensitive* data such as leaked credentials, and states that non-sensitive data
will not be removed, so a request on licensing grounds may well be declined.
This note stays until the exposure is actually closed, and says so plainly
rather than implying a fix is pending.

## How this is kept true

`tests/test_data_licensing.py` enforces the position rather than trusting this
file. It checks that the removed files are absent *and* gitignored, that no
committed CSV is large enough to be a record-level dataset, and that no workbook
sheet is either — a structural check rather than a filename check, because the
first attempt at this would have passed a repository that still shipped the data
inside an `.xlsx`. Anything exempted from the row cap has to be listed with a
reason and named in this file.

## Principle

Where a licence is stated by the publisher, it is cited. Where it is not, this
file says so rather than assuming. An unverified claim about someone else's rights
is worse than an acknowledged gap, and the portfolio's own argument is that claims
you cannot test should not be made.

The corollary, learned the hard way: when you do check and the answer is no, the
data comes out — even when it costs you the reproducibility you were proud of.

And the corollary to *that*: "removed" means removed from everywhere it is
actually served, not from the place you happened to look. Three times now the
answer to "is it gone?" has been no in a place I had not checked — the workbook
sheet, then the reworded claim, then git history.
