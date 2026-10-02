# What I Got Wrong

I built the first version of this portfolio over a few months, then stepped away
from it for the summer. When I came back in October 2026 I decided not to add
features but to audit what I already had — reading my own code and workbooks as
if someone else had written them and I had to sign off on the numbers.

I found five things wrong. Two of them meant features that had never worked at
all. One of them meant the portfolio's own headline claim was false. This file
documents all of them, with the mechanism and the consequence, because a
portfolio that only shows the finished surface tells you nothing about whether
the person can be trusted with the parts you can't see.

Every figure below is computed from committed data and asserted in the test
suite (`pytest tests/` — 252 tests). The fixes are in
[PR #1](https://github.com/ShangyuZ/Sustainable-finance-portfolio/pull/1).

---

## The argument these projects add up to

Labelled debt splits into two families:

- **Use-of-proceeds** instruments (green bonds): you promise what the money is
  spent on.
- **Performance-linked** instruments (SLBs, SLLs): you promise an outcome, and
  your cost of capital moves with whether you hit it.

The second family is the more intellectually satisfying one. It targets
outcomes rather than inputs, and it doesn't care whether you can ring-fence a
project. That is why it gets the attention.

**My work suggests the performance-linked family has a pricing problem.** From
the SLL model in Project 2:

- The incentive is small. A ±7.5bps ratchet is inside the ordinary
  spread volatility of a BBB– borrower, so it is unlikely to be the binding
  factor in anyone's cost of capital.
- It scales with drawdown, and it is therefore weakest exactly where revolving
  facilities actually sit — undrawn, as liquidity backstops.
- It is gated by a fixed cost. Verification does not get cheaper when you draw
  less, so below **20.5% utilisation** the best possible ESG outcome does not
  pay for proving you achieved it.

And from the green bond data in Project 1: the use-of-proceeds market did scale
— $650bn across 732 deals — but **82% of that volume is sovereign**. It scaled
because governments issued, not because the private incentive worked.

So the honest read is that neither family is primarily priced into existence.
The case for sustainability-linked structures is signalling, governance and
internal accountability. That is a real case. It is just not the cost-of-capital
case the marketing makes.

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
| Pooled greenium | **−1.50bps** |
| HAC standard error | 0.052 |
| t-statistic | −28.7 |
| Days with a negative spread | 99.8% |
| Per-pair means | −0.65bps to −2.40bps, all negative |

Two things I would not have predicted.

**The inference correction mattered more than I expected.** A daily yield spread
is strongly autocorrelated, so I used Newey-West HAC standard errors. On this
data the HAC standard error is **3.3× the ordinary one**: the naive t-statistic
is −94, the honest one is −28.7. The conclusion survives either way because the
sample is large, but on a shorter sample that factor of three is the difference
between a finding and an artefact. I would not have known that without computing
both.

**The greenium has compressed by about 80% since 2021** — from −4.71bps to
−0.76bps in 2025. That is a more interesting result than the level. At −4.7bps
there was arguably a funding incentive to issue green; at under 1bp the advantage
is inside the bid-offer spread on most days. It fits the thesis above rather than
contradicting it: this market's growth is driven by sovereign funding strategy,
not by price.

It also shows no maturity pattern (correlation 0.11 between years-to-maturity and
mean greenium), so it is a label effect rather than a term-structure artefact.

The estimate is pinned by tests (`tests/test_greenium_result.py`) so the figures
in the brief and in this file cannot drift from the data, and
`scripts/fetch_bund_yields.py` reproduces the whole download.

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

- Streamlit Cloud deployment.

---

*Part of the [Sustainable Finance Portfolio](./README.md). Fixes in
[PR #1](https://github.com/ShangyuZ/Sustainable-finance-portfolio/pull/1).*
