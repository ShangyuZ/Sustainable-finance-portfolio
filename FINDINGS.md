# What I Got Wrong

I built the first version of this portfolio over a few months, then stepped away
from it for the summer. When I came back in October 2026 I decided not to add
features but to audit what I already had, working with an AI assistant (Claude)
to read the code and workbooks as if someone else had written them and I had to
sign off on the numbers. That collaboration is visible in the commit history, and
how it was used is described in the [README](./README.md).

The audit surfaced five defects. Two of them meant features that had never worked
at all. One meant the portfolio's own headline claim was false. This file
documents all of them, with the mechanism and the consequence, because a portfolio
that only shows the finished surface tells you nothing about whether the person
can be trusted with the parts you can't see.

Every figure below is computed from committed data and asserted in the test
suite (`pytest tests/` — 341 tests). The fixes are in
[PR #1](https://github.com/ShangyuZ/Sustainable-finance-portfolio/pull/1).

---

## What the projects show — and what they do not

Labelled debt splits into two families:

- **Use-of-proceeds** instruments (green bonds): you promise what the money is
  spent on.
- **Performance-linked** instruments (SLBs, SLLs): you promise an outcome, and
  your cost of capital moves with whether you hit it.

I looked at one concrete pricing question in each. On Germany's green twin Bunds
the greenium is small (−1.50bps) and has narrowed since 2021 (§7). In a
hypothetical sustainability-linked revolver, the ratchet only pays for its own
verification above 20.5% utilisation (§6). In both cases the direct pricing
incentive is small, which is consistent with the case for these structures
resting largely on signalling, investor access and internal accountability.

This section used to say more than that. It claimed that the use-of-proceeds
market "scaled because governments issued", on the strength of an 82% sovereign
share, and that the loan model showed the performance-linked incentive was too
weak to scale. Both overreached, and §8 explains why.

---

## 1. My portfolio claimed something that was not true

The root README said, and had said for months:

> No proprietary or restricted data (Bloomberg, Refinitiv, etc.) is used anywhere.

The CHANGELOG went further and claimed those references had been *"removed
throughout"* in v0.2.0.

Both were false. `Green_Bond_Market_Analysis.xlsx` still contained four live
references:

- *"This sheet is designed to be populated using Bloomberg/Refinitiv data available via UCL library access"*
- *"Enter data from Bloomberg terminal (blue cells)"*
- *"Visit a UCL Bloomberg terminal — search for your chosen issuer"*
- *"Greenium analysis pending Bloomberg data collection"*

**Why I missed it.** An `.xlsx` is a zip archive of XML. A text search of the
repository — which is how I had "checked" — cannot see inside it. The
references were in cells, invisible to `grep`, and visible to anyone who opened
the file. Which, for a portfolio, is everyone.

**What I changed.** The greenium sheet is rebuilt on sovereign green *twin*
bonds (see §6). And CI now opens every workbook in the repo and scans every
cell, so the claim is enforced rather than asserted:

```
- name: No proprietary data references anywhere
  # Text search alone misses references inside .xlsx files, so check cells too.
```

**What I take from it.** A claim you have no test for is a claim you should not
make. I had written the sentence once and then trusted it for months. The
version of me that wrote "removed throughout" in the changelog genuinely
believed it.

**And it happened again, in the same README — and this time it cost me
something.** The sentence immediately after the Bloomberg claim made a second
absolute assertion, this time about *third-party* rights rather than my own
sourcing:

> All data is publicly available and openly licensed. No proprietary or
> restricted data is used anywhere.

Nobody had verified it either. So I went and read the terms, which is what I
should have done before writing the sentence. Two of them said no:

- **Climate Bonds Initiative:** *"Reproduction, use, storage, or transmission of
  any content and / or materials available on this website, in any form, is
  prohibited other than with the prior written permission of Climate Bonds
  Initiative."*
- **Deutsche Finanzagentur:** *"Copyright: Bundesrepublik Deutschland –
  Finanzagentur GmbH, Frankfurt/Main, Germany. All rights reserved."*

I had been redistributing 732 records from the first and 17,656 yield
observations from the second. Not maliciously — I had assumed that public access
meant permission to republish, which is simply not what it means.

**What I changed, and what it cost.** Both datasets are out. In their place the
repository commits my own derived output: the aggregate tables for Project 1, and
the greenium estimator's per-pair, yearly and diagnostic results. Every figure I
publish anywhere is still checkable against a committed file, and
`tests/test_aggregates.py` checks each one. What I gave up is the line I had been
proudest of — "rebuilds end to end from the committed CSV" — because rebuilding
*from records* now needs your own licensed copy of the extract. That was the right
trade, and it is worth being precise about why: the old reproducibility was only
possible because it redistributed data I had no right to. It was never mine to
offer.

**The part I nearly got wrong twice.** My first instinct was to delete the CSV.
That would have achieved nothing. The same 732 records also sat inside
`Green_Bond_Market_Analysis.xlsx`, on a sheet called "8. Cleaned Data" — and that
is in fact how they first entered the repository, in the original March 2026
commit, *inside the workbook*. Deleting the CSV would have left the repository
still shipping the data, in the one place a text search cannot see. Exactly the §1
blind spot, a second time, on a second subject.

So the guard is structural rather than name-based.
`tests/test_data_licensing.py` fails the build if any committed CSV is large
enough to be a record-level dataset, or if any workbook sheet is — by size, under
any name, with an allowlist that has to state its reasons. A guard that checked
filenames would have passed the repository that still shipped the data.

**What I take from it.** Three versions of the same lesson, which is presumably
why it took three goes:

1. A claim you have no test for is a claim you should not make *(my own sources)*.
2. The same, for claims about other people's rights — and that one you cannot
   test by inspecting your own repository. You have to go and read what the
   publisher actually says.
3. When the answer is no, the data comes out, even when it costs you the thing
   you were proudest of. The alternative is a portfolio whose central argument is
   that claims you cannot defend should not be made, built on one I could not
   defend.

---

## 2. Two of my four dashboard sections had never worked

The dashboard advertises four sections. Two of them — the CO₂ Emissions tab and
the entire Country Climate Scorecard — had never rendered anything. The
Scorecard was the headline feature of release v0.3.0.

**Why.** Our World in Data publishes energy and emissions as two *separate*
datasets. `renewables_share_elec` is in the energy dataset;
`co2` and `co2_per_capita` exist only in the CO2 dataset. I was reading
emissions columns off the energy dataset, where they simply do not exist.

**Why nothing broke loudly.** I had written defensive guards:

```python
if not all(c in df.columns for c in needed):
    st.warning("Required columns not found in dataset version.")
    st.stop()
```

So the section checked for the columns, didn't find them, and stopped cleanly —
every single time. My error handling was hiding the error. A crash would have
told me in a minute; a graceful degradation hid it for months.

**What I changed.** Both datasets are loaded and merged on `(country, year)`.
And CI now runs a smoke job that renders all four sections against live OWID
data on every build, so a silent section fails the build:

```
ok    🏭 EU Carbon Price
ok    ⚡ Energy Transition
ok    🏆 Country Climate Scorecard
ok    🌍 Portfolio Carbon Calculator
```

**What I take from it.** Defensive code that degrades silently is worse than no
defensive code, because it converts a loud failure into an invisible one. If a
guard fires in normal operation, it is not a guard — it is a bug report nobody
receives.

---

## 3. The cleaning was the analysis, and I had skipped it

My sector league table showed financials as a rounding error. Financials are in
fact the **second largest sector by volume** at 7.1%.

The Climate Bonds extract is a public dataset, not a curated product, and it is
dirty in four specific ways:

| Defect | Records | What it did |
|---|---|---|
| `Sector` encodes "not disclosed" as the string `"0"` | 64 | Rendered as a sector literally named **"0"** in my output |
| `Sector` missing entirely | 1 | Silently dropped from shares |
| 34 sector labels for 11 real groups | 140 | `Financials` / `Financial` / `Finance` / `Banks` / `Commercial Bank` / `Diversified Banks` / `Financial Institution` each ranked **separately**, so none of them ranked |
| `Country` duplicate labels | 42 | `USA`/`United States`, `UK`/`United Kingdom`, `China_HK`, and the misspelt `Supernational`/`Supranational` each split one country's volume across rows |
| `Country` trailing whitespace | 1 | `'Netherlands '` aggregated as a **different country** from `'Netherlands'` |
| `Issuer Name` case variants | 1 | `GoodLeap LLC` and `Goodleap LLC` counted as two issuers |

**Consequences, quantified.** Folding these raised the UK from $59.34bn to
**$59.79bn** and the Netherlands from $28.81bn to **$29.58bn**, and corrected
the country count from an apparent **69 to an actual 64**. My dashboard had also
labelled that 69 as "unique issuers" — the real issuer count is **180**.

**What I changed.** All of it happens in `clean.py` with explicit, auditable
maps rather than fuzzy matching, and the workbook now ships a **Data Quality
sheet** listing every rule, the records it touched, and why it matters.

I also left two things **deliberately uncorrected** and flagged them instead:
Schneider Electric SE (a French issuer) is tagged to the United States, and its
2015 transaction is labelled SLB years before that market existed — which is why
2015 shows a 100% SLB share. Silently overwriting source records is a habit I
would rather not form; the point of the Data Quality sheet is that a reader can
disagree with my choices, which requires knowing what they were.

**What I take from it.** On a real dataset the normalisation decisions *are* the
analysis, and they are invisible in the output. Publishing them is the only way
the numbers can be argued with.

---

## 4. A chart that summed to 198%

My electricity-mix pie chart put renewables, fossil, nuclear, hydro, solar and
wind in one pie. For Norway it summed to **198%**. Brazil 181%. The UK 135%.

`renewables_share_elec` already *contains* hydro, wind and solar. They are
nested inside it, not alongside it. I had treated a hierarchy as a partition.

**What I changed.** Fossil / renewables / nuclear is the top-level split — it
sums to exactly 100.0% — and renewables gets its own breakdown underneath. The
test suite asserts the two column sets are disjoint, so the categories cannot be
mixed again:

```python
def test_top_level_mix_and_renewable_parts_do_not_overlap():
    assert set(T.TOP_LEVEL_MIX) & set(T.RENEWABLE_PARTS) == set()
```

**What I take from it.** Before charting proportions, check whether the
categories partition the whole or nest inside each other. Nobody reported this;
I found it by adding up the slices.

---

## 5. My headline growth number measured the wrong thing

The README said:

> Deal **volume** grew from 10 transactions in 2018 to 238 in 2023 — a 2,280% increase

That is deal **count**, not volume, and the two diverge sharply. USD volume over
the same period grew from $17.6bn to $184.5bn — **+950%**. Deal count overstates
growth by a factor of more than two, because average deal size fell as the
market broadened.

This matters beyond pedantry: count and volume rank the market differently.
China leads on deal count (68) but is **sixth** by volume, because Chinese
issuance here is many small bank deals while European volume sits in large
sovereign programmes. If you only look at counts you conclude the wrong thing
about where this market actually is.

I also found the workbook internally inconsistent: it headlined "2018–2024 /
7-year time series" while its annual table summed to $638.15bn and its total
said $650.0bn — an unexplained **$11.90bn** gap, which turned out to be
2015–2017 included in one place and not the other. Every sheet now covers
2015–2024 and reconciles to $650.04bn, and the aggregation tests assert that
reconciliation so it cannot drift again.

---

## 6. The model priced a revolver as if it were a term loan

This is the finding I'd most want to be asked about.

My SLL model said the margin ratchet saves the borrower **£490k a year** if it
hits all three sustainability targets. That number assumed the £650m revolving
credit facility was **fully drawn**, with no commitment fee.

Both assumptions flatter the structure, and a revolver is precisely the
instrument where they are least defensible:

1. **A revolver is normally a liquidity backstop**, held largely undrawn. And
   the ratchet only applies to the *drawn* margin. At 60% utilisation the
   −7.5bps step applies to £390m, not £650m, so the best-case saving falls from
   £487.5k to **£292.5k**.
2. **The undrawn balance is not free.** It carries a commitment fee —
   conventionally ~35% of the margin, so 42bps here — which my model ignored
   entirely. At 60% utilisation that is **£1.09m a year**, several times the
   whole ratchet saving.

So the facility actually costs £21.26m of drawn interest plus £1.09m of
commitment fee = **£22.35m**, against the £35.43m the full-drawdown table
implied.

**Then the part I didn't expect.** The ratchet saving scales with drawdown, but
the third-party verification cost that earns it (ISAE 3000 assurance, ~£100k) is
fixed. So there is a break-even:

| Utilisation | Drawn | Best-case saving | Verification | Net |
|---|---|---|---|---|
| 0% | £0m | £0k | £100k | **−£100k** |
| 20% | £130m | £97.5k | £100k | **−£2.5k** |
| 40% | £260m | £195k | £100k | +£95k |
| 60% | £390m | £292.5k | £100k | +£192.5k |
| 100% | £650m | £487.5k | £100k | +£387.5k |

**Break-even utilisation is 20.5%.** Below that, the best possible
sustainability outcome does not cover the cost of proving you achieved it.

For a facility held as a backstop — the normal case — sustainability-linked
pricing is close to economically irrelevant, and the real reasons to do it are
signalling, investor relations and internal accountability. That is a recognised
criticism of the instrument, and quoting the full-drawdown number obscures it.

It is also worth keeping ±7.5bps in perspective against the spread volatility of
a BBB– credit. The ratchet is unlikely to be what moves this borrower's cost of
capital either way.

**What I changed.** Utilisation and commitment fee are now inputs, there are two
new sheets (Utilisation Sensitivity, Economics & Caveats), and the economics live
in `sll.py` as tested functions. The workbook's Excel formulas are evaluated in
the test suite and compared to the Python model cell by cell — a formula-driven
spreadsheet that silently disagrees with its own code is worse than no
spreadsheet, because a reader has no reason to doubt it.

---

## 7. What the audit led to: I measured the greenium

Rebuilding the greenium sheet on open data (§1) left me with a framework and no
result, which is an unsatisfying place to stop. So I ran it.

Germany issues each green Federal security as a **twin** of a conventional one
with the same coupon, the same maturity and the same issuer. I matched all nine
outstanding green securities to their exact twins — deriving the pairing by
matching coupon and maturity rather than asserting it — and took the daily yield
series the issuer publishes for each. That gives **8,094 paired daily
observations, September 2020 to October 2026**.

| | |
|---|---|
| Pooled greenium (per observation) | **−1.50bps** |
| Panel HAC standard error (Driscoll-Kraay, 250-day bandwidth) | 0.330 |
| t-statistic | −4.5 |
| Days with a negative spread | 99.8% |
| Per-pair means | −0.65bps to −2.40bps, all negative |

The greenium narrowed from −4.71bps in 2021 to −0.76bps in 2025. The yearly
means are descriptive: the number of pairs rises from one to nine over the
period, so composition contributes to that trend.

The first version of this section reported t = −28.7 and presented the inference
correction as its most instructive lesson. §8 explains why that figure was wrong.
The estimate is pinned by tests (`tests/test_greenium_result.py`) so the figures
in the brief and in this file cannot drift from the data, and
`scripts/fetch_bund_yields.py` reproduces the whole download.

## 8. What an outside review found in my corrected version

A week after the audit, someone read the repository and the brief properly and
sent a review. Every point in it held up when I checked it, and checking it
turned up two more. The pattern is the uncomfortable part: several of these were
in the sections I had written *about* being careful.

**The precision of my greenium was wrong, in the section about getting precision
right.** §7 originally reported t = −28.7 and said the Newey-West correction had
"tripled" the standard error. Two things were wrong with it. The rule-of-thumb
bandwidth gave 10 lags, but the spread is still correlated 0.86 with itself 60
trading days later and 0.66 after 120 — ten lags discard most of that. And I had
applied a single-series correction to nine bonds' histories stacked end to end,
so pairs quoted on the same date counted as independent evidence. A panel HAC
(Driscoll-Kraay) standard error handles both:

| Specification | t-statistic |
|---|---|
| Ordinary standard error | −94.2 |
| Stacked series, 10 lags (what I published) | −28.7 |
| Driscoll-Kraay, 60 / 120 / 250 lags | −8.2 / −6.0 / −4.5 |
| t-test across the nine pair means | −5.7 |

The greenium survives every row; my claimed precision did not. The real
correction from the ordinary standard error is about 21×, not 3.3×. I had also
written that a 0.11 correlation with maturity made it "a label effect rather
than a term-structure artefact". Nine pairs cannot show that — the green twins
are smaller and less liquid, and the conventional twins can trade special in repo.
`tests/test_greenium.py` now includes a case my old estimator fails: two
identical pairs must carry no more information than one.

**My headline market claim was a property of my sample.** I wrote that 82% of
labelled-bond volume is sovereign and that governments built the market. The
dataset is CBI's News Makers extract, which tracks notable deals — and I had said
so in the brief's limitations, then drawn the market-wide conclusion anyway. CBI's
own Q3 2024 summary records $5.4tn of aligned sustainable debt, of which $630.5bn,
about 11.6%, is sovereign. My extract holds roughly 85% of that sovereign volume
and about 2% of everything else. Every composition figure is now stated as a
property of the sample, and the supply-forecasting recommendation built on it is
gone.

**I used a loan to explain a bond market.** The 20.5% break-even in §6 is correct
for a revolving loan. I then used it to explain why sustainability-linked *bonds*
stayed small. A bond is fully funded at issue and adjusts its coupon differently,
so the drawdown mechanism does not exist there. It is now presented as a loan
scenario only.

**Four of the five studies in my literature table were wrong in some respect.** Panizza et
al. had the wrong title and figure (their paper reports about −2bps for advanced
and −13bps for emerging-market sovereigns, not −5 to −8bps, and uses matched
pairs, not synthetic control). The Banque de France paper (Pietsch & Salakhova)
had the wrong title, authors, method and range. Caramichael & Rapp study a global
panel, not US corporates, and use fixed-effects regression — they explicitly
reject matching. Löffler et al. cover secondary as well as primary markets and
use propensity-score as well as coarsened exact matching. I had summarised papers
from memory and secondary sources rather than reading them.

**Smaller things.** "A fifth" of sustainability-bond volume was 31%; "nil before
2021" contradicted a 2015 record I had deliberately kept and flagged; the README's
first paragraph still said "freely licensed" two sections above the explanation
of why that was false; the PDF renderer flattened numbered lists and leaked a
backslash; and six tests failed under pandas 2.2, which `requirements.txt` claims
to support, because `~` on a `None` from `.str.startswith` raises there.

**What I take from it.** The audit fixed the errors I could see by reading my own
work, and its write-up then repeated a lesson — "a claim you have no test for is a
claim you should not make" — while making untested claims about inference, about
the market and about other people's papers. Tests pin numbers to data. They do not
check that the method behind the number is right, that the sample can carry the
conclusion, or that a citation says what I said it does. Those need someone else
to read the work.

## How I check things now

The audit changed my process more than it changed the output:

- **Calculations are separated from presentation.** `clean.py`, `sll.py` and
  `transforms.py` are plain functions over plain data, testable without a
  network connection, a running app, or Excel. The arithmetic that is easy to
  get silently wrong is the arithmetic that is now easiest to test.
- **Both workbooks are generated, never hand-edited.** CI rebuilds them from
  committed sources, so the figures in the READMEs, the code and the
  spreadsheets cannot drift apart.
- **The claims are tested, not asserted.** The proprietary-data guard, the
  reconciliation invariants and the category-disjointness check are all
  regression tests for specific mistakes I actually made.
- **I mutation-tested the suite.** Reintroducing each original bug — the pie
  double-count, the naive weights, the coverage-blind year selection, the `"0"`
  sentinel, the country folding, a Bloomberg reference — makes the tests fail.
  A suite that cannot fail is not evidence of anything.

## What is still not done

Listed honestly rather than quietly dropped:

- Reconciling Project 1's sample against a full issuance database, which is what
  any market-wide statement would need.
- The Zerbib (2019) row of the literature table is the one citation I have not
  been able to re-check against the paper itself.

---

*Part of the [Sustainable Finance Portfolio](./README.md). Fixes in
[PR #1](https://github.com/ShangyuZ/Sustainable-finance-portfolio/pull/1).*
