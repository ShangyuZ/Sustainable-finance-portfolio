# Sustainable Finance Portfolio
### ShangyuZ · BSc Statistics, Economics & Finance · UCL

I'm building this portfolio to work with the actual instruments and data of
sustainable finance — green bonds, sustainability-linked loans, climate datasets
— rather than just reading about them. Everything uses open, freely licensed
sources.

## The argument

Labelled debt splits into two families. **Use-of-proceeds** instruments (green
bonds) promise what the money is spent on. **Performance-linked** instruments
(SLBs, SLLs) promise an *outcome*, and the borrower's cost of capital moves with
whether they hit it. The second family is the more intellectually satisfying one,
which is why it gets the attention.

Working through both, I think the performance-linked family has a pricing
problem:

- The incentive is small — a ±7.5bps ratchet sits inside the ordinary spread
  volatility of a BBB– borrower.
- It scales with drawdown, so it is weakest exactly where revolving facilities
  actually sit: undrawn, as liquidity backstops.
- It is gated by a fixed cost. Below **20.5% utilisation**, the best possible ESG
  outcome does not pay for the verification needed to prove it.

Meanwhile the use-of-proceeds market did scale — $650bn across 732 deals — but
**82% of that volume is sovereign**. It scaled because governments issued, not
because the private incentive worked.

So neither family looks primarily priced into existence. The case for
sustainability-linked structures is signalling, governance and internal
accountability — a real case, but not the cost-of-capital case the marketing
makes. Project 2 is the evidence for the first half, Project 1 for the second,
and Project 3 is the underlying climate data.

## What I got wrong

In October 2026 I audited this portfolio instead of adding to it, and found five
things wrong — two of which meant dashboard sections that had never worked, and
one of which meant this README's own headline claim was false (four Bloomberg
references were sitting inside an `.xlsx`, where no text search could find them).

**→ [FINDINGS.md](./FINDINGS.md)** documents all of them, with mechanisms and
quantified consequences. It is probably the most useful thing in this repository.

## How this was built, and what the data is

**AI assistance.** This portfolio was built with substantial help from Claude
(via Claude Code), and the commit history records it — the content commits are
authored by `Claude <noreply@anthropic.com>`. I set the direction, decided what to
investigate, made the calls on what to correct versus flag and leave, and verified
the results. The analysis and its conclusions are mine to defend.

**Data provenance.** This README used to claim that all data here is "openly
licensed" and that "no proprietary or restricted data is used anywhere". That was
an absolute statement about third-party rights which I had not verified. When I
went and read the terms, two of them said no: Climate Bonds Initiative prohibits
reproducing their content without written permission, and Deutsche Finanzagentur
reserves all rights in theirs. I had been redistributing both.

Both are now out of the repository. What stands in their place is my own derived
output — the aggregate tables for Project 1 and the greenium estimator results —
so every figure quoted anywhere here is still checkable against a committed file,
while the records themselves stay with their publishers. The cost is real and
worth naming: rebuilding Project 1 *from source records* now needs your own
licensed copy of the extract. **[DATA.md](./DATA.md)** has the terms, what was
removed, and what it cost.

Two things are enforced rather than claimed: no paid-terminal data is used
anywhere in the analysis, and CI fails the build if a vendor reference reappears
or if anything record-shaped is committed again — the latter checked by file and
sheet size rather than by filename, because the first time round the records were
hiding inside an `.xlsx` where no text search of the repository would have found
them.

[![CI](https://github.com/ShangyuZ/Sustainable-finance-portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/ShangyuZ/Sustainable-finance-portfolio/actions/workflows/ci.yml)

**▶ Live dashboard: [shangyuz-sustainable-finance.streamlit.app](https://shangyuz-sustainable-finance.streamlit.app)** · **📄 [Investment brief (PDF)](./project1-green-bond-analysis/brief/Green_Bond_Market_Brief.pdf)** · **📄 [SLL structuring memo (PDF)](./project2-sll-structuring/memo/SLL_Structuring_Memo.pdf)**

---

## Projects

### 01 · Green Bond Market Analysis
`Python` `pandas` `openpyxl` `Climate Bonds Initiative` · **Status: Complete** *(brief outstanding)*

Analysis of 732 labelled sustainable bond issuances (2015–2024, $650bn) using
public Climate Bonds Initiative data. Covers market growth measured in both deals
and dollars, geographic and sector breakdown, the rise of sustainability-linked
bonds, and a **measured greenium of −1.50bps** from Germany's green "twin" Bunds
across 8,094 paired daily observations.

Rebuilds end to end with one command from the committed aggregates. The
underlying records are not redistributable, so what ships is the derived
statistics — and the tests check every published figure against them.

→ [View project](./project1-green-bond-analysis/)

---

### 02 · SLL Structuring — Hypothetical Framework
`Excel` `LMA/ICMA Principles` · **Status: In Progress**

A framework exercise in structuring a sustainability-linked loan from first
principles, with a hypothetical borrower and publicly available LMA/ICMA guidance.
Covers KPI selection, SPT calibration and margin ratchet design in a formula-driven
Excel model, with a credit-committee-style structuring memo.

The useful finding is that the headline ratchet saving overstates the benefit: the
ratchet applies only to the drawn margin of a revolving facility, the undrawn
balance carries a commitment fee, and the verification cost is fixed — so the
structure only pays for itself above **20.5% utilisation**.

→ [View project](./project2-sll-structuring/)

---

### 03 · Climate & Energy Transition Dashboard
`Python` `Streamlit` `Plotly` `Our World in Data` · **Status: Deployed**

**▶ Live: [shangyuz-sustainable-finance.streamlit.app](https://shangyuz-sustainable-finance.streamlit.app)**

A live dashboard on Our World in Data's CC BY 4.0 energy and CO₂ datasets,
fetched at runtime: energy transition trends by country, a country climate
scorecard, and a portfolio carbon intensity (WACI) calculator — plus EU carbon
price history from a bundled series that is indicative rather than a reference
(see [DATA.md](./DATA.md)).

→ [View project](./project3-climate-dashboard/)

---

## Running it

```bash
pip install -r requirements.txt
pytest tests/                                            # 334 tests

python project1-green-bond-analysis/scripts/process_data.py    # rebuild model 1
python project2-sll-structuring/scripts/build_model.py         # rebuild model 2

cd project3-climate-dashboard && streamlit run app.py          # launch the dashboard
```

## Repository layout

```
project1-green-bond-analysis/
  data/aggregates/             derived tables — the source records are not
                               redistributable, so these ship instead (DATA.md)
  data/greenium_*.csv|json     greenium output: per-pair, by year, diagnostics
  scripts/clean.py             loading, normalisation, aggregation — pure, tested
  scripts/aggregates.py        one table set, built from records or from the CSVs
  scripts/export_aggregates.py regenerates the tables from a licensed extract
  scripts/process_data.py      builds the eight-sheet Excel model
project2-sll-structuring/
  scripts/sll.py               facility economics — ratchet, utilisation, break-even
  scripts/build_model.py       builds the six-sheet formula-driven Excel model
  memo/                        structuring memo (markdown source + generated PDF)
project3-climate-dashboard/
  app.py                       Streamlit UI and data loading
  transforms.py                pure calculations — no Streamlit, unit-tested
tests/                         334 tests across all three projects
FINDINGS.md                    what the audit found, and what I changed
DATA.md                        per-source provenance, terms, and what was removed
LICENSE                        MIT, covering the code, analysis and derived stats
.github/workflows/ci.yml       lint, tests, model rebuilds, data-licensing guards
```

The split between the calculation modules (`clean.py`, `sll.py`, `transforms.py`)
and the presentation layers is deliberate: the arithmetic that is easy to get
silently wrong lives in plain functions that can be tested without a network
connection, a running app, or Excel. Both workbooks are generated by script rather
than hand-maintained, and the tests check that the Excel formulas evaluate to the
same numbers as the Python — so the figures in the READMEs, the code and the
spreadsheets cannot drift apart.

---

## Data Sources

Per-source terms, and what of each is actually in this repository — full detail
in [DATA.md](./DATA.md):

| Dataset | In this repository | Terms |
|---------|--------------------|-------|
| Green bond issuance | **Derived aggregates only** | Climate Bonds Initiative — all rights reserved; records not redistributed |
| Sovereign green bond yields | **Estimator output only** | Deutsche Finanzagentur — all rights reserved; observations not redistributed |
| Energy & electricity mix by country | Fetched at runtime | Our World in Data — [energy dataset](https://github.com/owid/energy-data), CC BY 4.0 |
| CO₂ emissions by country | Fetched at runtime | Our World in Data — [CO2 dataset](https://github.com/owid/co2-data), CC BY 4.0 |
| EU ETS carbon prices | Bundled CSV | Uncited; **indicative only**, not a reference series |
| Academic greenium evidence | Cited inline | Published papers — cited, not reproduced |

Every conclusion here is reproducible from what is committed. Reproducing the two
reserved datasets' *pipelines from source* takes one command each, against your
own copy. That trade was deliberate: the arrangement it replaced was reproducible
only because it redistributed data it had no right to.

---

## Why I'm Doing This

I study statistics, economics and finance at UCL. The quant side of sustainable
finance — modelling, data, statistical thinking — is under-represented relative
to the policy and qualitative work. I want to show I can work with both: the
finance instruments and the underlying data, using reproducible, open methods.

In practice the most useful thing I've learned is how much of the work is data
quality rather than modelling. The green bond dataset encodes missing sectors as
the string `"0"`, splits one country's volume across two spellings, and lists
seven different labels for the financial sector. None of that throws an error —
it just quietly produces the wrong league table. Sheet 1 of the Project 1 model
documents every correction, because being able to show what you changed and why
matters more than a clean-looking chart.

The second most useful thing is that my own mistakes turned out to be more
interesting than my results. Auditing this portfolio taught me more than building
it did, which is why [FINDINGS.md](./FINDINGS.md) is written up as carefully as
the analysis.

---

*Last updated: 2026-10-02*
