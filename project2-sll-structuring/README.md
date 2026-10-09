# Project 2 — SLL Structuring Case Study

## Overview

Sustainability-linked loans (SLLs) differ from green bonds in one critical respect:
the cost of capital is contingent on the borrower hitting ESG performance targets,
not on how proceeds are used. This makes KPI selection and target calibration the
core intellectual challenge — and the area most prone to greenwashing.

This project structures a hypothetical SLL from first principles for a fictional
UK industrial company, benchmarked against the LMA/APLMA/LSTA Sustainability-Linked
Loan Principles (2023 edition; revised March 2025). All data and targets are
illustrative only — no real company financial data is used.

**The main finding is that the pricing benefit depends on utilisation.** The
ratchet applies only to the drawn margin, while the assurance cost that earns it
is fixed. Under the model's assumptions the best-case benefit, net of assurance,
is **£192.5k a year at 60% utilisation** and disappears below about **20.5%** —
see [Financial Impact](#4-financial-impact) below.

## Hypothetical Borrower

**Albion Industrials plc** *(fictional entity — for illustrative purposes only)*

| Attribute | Details |
|-----------|---------|
| Sector | UK Heavy Industrials (Steel & Construction Materials) |
| Revenue (hypothetical) | £2.8bn |
| EBITDA margin (hypothetical) | 11% |
| Existing debt (hypothetical) | £650m revolving credit facility |
| Credit rating (hypothetical) | BBB– (investment grade) |
| Scope 1+2 intensity (baseline, hypothetical) | 310 tCO₂e per £m revenue |
| Renewable energy share (baseline, hypothetical) | 18% |

*For a real case study, equivalent data would be sourced from: company annual
reports and sustainability reports (available free on company IR websites),
Companies House filings, public bond prospectuses (London Stock Exchange),
and CDP Climate Disclosure responses (free at cdp.net).*

## Structuring Framework

### 1. KPI Selection

Per SLLP guidance, KPIs must be:
- Material to the borrower's core business
- Measurable and independently verifiable
- Aligned with the borrower's stated sustainability strategy

| # | KPI Candidate | Metric | Rationale |
|---|---------------|--------|-----------|
| 1 | Carbon intensity | tCO₂e per £m revenue (Scope 1+2) | Core emission driver for heavy industry |
| 2 | Renewable energy share | % of electricity from renewables | Operational lever, verifiable via REGO certificates |
| 3 | Supply chain audit coverage | % tier-1 suppliers audited to ESG standards | Governance, material for materials sector |

### 2. Sustainability Performance Targets (SPTs)

SPTs must represent a material improvement vs baseline. The targets below are
**illustrative, informed by the frameworks named; their alignment with those
frameworks has not been independently established.** SBTi, for example, accepts
Scope 1+2 intensity targets only when modelled on an approved 1.5°C sector pathway
applicable to the company — a chosen percentage is not evidence of alignment.

| KPI | Baseline (2024) | Target Year | SPT | Informed by |
|-----|----------------|-------------|-----|-----------------|
| Carbon intensity | 310 tCO₂e/£m rev | 2028 | ≤217 tCO₂e/£m rev (−30%) | SBTi near-term criteria |
| Renewable share | 18% | 2028 | ≥60% | UK CCC Sixth Carbon Budget |
| Supply chain audit | 35% | 2027 | ≥80% | LMA SLLP guidance on ambition |

The model derives a linear interim path for every KPI from its two endpoints —
carbon 310 → 286.75 → 263.5 → 240.25 → 217, renewables 18 → 28.5 → 39 → 49.5 → 60,
audit coverage 35 → 50 → 65 → 80 by 2027 — because the ratchet is tested
annually, not once at maturity. On the linear carbon path intensity falls by 7.5%
of the baseline each year; the equivalent constant annual rate is about 8.5%.

Two limitations of the KPI design:

- **The grid is unweighted.** Pricing depends on how many SPTs are met, not which:
  missing carbon but meeting the other two still earns the 2.5bps partial
  step-down.
- **Revenue-normalised intensity can improve without emissions falling.** Flat
  emissions with 20% revenue growth take intensity from 310 to about 258 — an
  apparent 16.7% improvement.

### 3. Margin Ratchet Design

A two-way ratchet (step-up **and** step-down) is best practice. A step-down-only
structure hands the borrower a free option, which is the main greenwashing channel
the SLLP guidance targets.

```
All 3 SPTs met      → −7.5 bps on margin
2 of 3 SPTs met     → −2.5 bps on margin
1 of 3 SPTs met     → no adjustment
0 SPTs met          → +7.5 bps on margin
```

Ratchet applied annually on the interest payment date following third-party
verification. Market practice typically ranges from 2.5–15 bps per year.

### 4. Financial Impact

£650m facility at SONIA + 120 bps, SONIA = 4.25%. All figures recalculate live in
`SLL_Structuring_Model.xlsx` and are unit-tested in `../tests/test_sll.py`.

#### At 100% drawdown

| Scenario | Margin | All-in rate | Annual cost | Δ vs base |
|----------|--------|-------------|-------------|-----------|
| All 3 SPTs met | SONIA + 112.5 bps | 5.375% | £34.94m | −£487.5k |
| 2 of 3 met | SONIA + 117.5 bps | 5.425% | £35.26m | −£162.5k |
| No adjustment | SONIA + 120 bps | 5.450% | £35.43m | — |
| No SPTs met | SONIA + 127.5 bps | 5.525% | £35.91m | +£487.5k |

At full drawdown there is no undrawn balance, so no commitment fee is payable.

#### Total cost at lower utilisation

The ratchet touches only the drawn margin. At 60% utilisation the −7.5bps step
applies to £390m, so the best-case saving is **£292.5k** rather than £487.5k. The
undrawn £260m carries a commitment fee — 35% of the margin, so 42bps — of £1.09m a
year. Total facility cost at 60% with no adjustment is £21.26m drawn interest +
£1.09m commitment fee = **£22.35m**.

#### Incremental economics: versus an equivalent conventional revolver

Whether the sustainability feature pays is a different question from what the
facility costs. Against an otherwise identical conventional revolver, the
commitment fee is charged on both and **cancels**. What remains is the
drawn-margin adjustment and the incremental assurance cost (taken here as £100k a
year, fixed):

| Utilisation | Drawn | Best-case margin saving | Incremental assurance | Net vs conventional |
|---|---|---|---|---|
| 0% | £0m | £0k | £100k | **−£100k** |
| 20% | £130m | £97.5k | £100k | **−£2.5k** |
| 40% | £260m | £195k | £100k | +£95k |
| 60% | £390m | £292.5k | £100k | +£192.5k |
| 80% | £520m | £390k | £100k | +£290k |
| 100% | £650m | £487.5k | £100k | +£387.5k |

**Best-case annual pricing break-even under the model assumptions: 20.5%
utilisation.** It assumes every SPT is met, the whole £100k of assurance is
incremental (under the SLLP, information already verified in annual reporting
need not be verified again, which would lower it), only the drawn margin changes,
and there are no other incremental costs.

So the pricing case is conditional: positive at the assumed 60% utilisation,
absent below about 20.5%. The model does not say where a real borrower would
operate — that is a liquidity and credit question.

### 5. Verification & Reporting

- External verifier: Big 4 assurance or specialist ESG verifier (e.g. Bureau Veritas, DNV)
- Reporting cadence: Annual sustainability report + loan anniversary letter
- Assurance standard: ISAE 3000 / AA1000AS
- KPI data: Verified via Streamlined Energy and Carbon Reporting (SECR) disclosures
  and the REGO certificate registry (for renewable share) — both UK statutory or
  registry-based, so no paid data subscription is required

## What this model deliberately does not claim

- The ratchet is priced on the drawn margin only. If the commitment fee were also
  linked, the effect would depend on utilisation: at 0% drawn, a fee at 35% of
  the margin would save £170,625 a year with all SPTs met, while the drawn-only
  ratchet saves nothing.
- The number of SPTs met is a scenario input; the KPI Tracker shows progress but
  does not drive pricing.
- The SPTs are illustrative; their alignment with SBTi, CCC or SLLP benchmarks
  has not been independently established.
- No discounting — these are single-year figures.
- Verification cost is one illustrative input; real assurance costs vary with
  scope, and the first year is usually dearer.
- **KPI selection, not pricing, is where the integrity risk sits.** A material KPI
  with an unambitious SPT prices identically to a demanding one in this model. No
  amount of ratchet engineering fixes a weak target.

## The memo

[`memo/SLL_Structuring_Memo.pdf`](./memo/SLL_Structuring_Memo.pdf) is the
credit-committee-style document the model supports. It recommends structuring the
facility as sustainability-linked and **presenting the pricing benefit as
conditional on utilisation**: £192.5k a year net at the assumed 60%, nothing below
about 20.5%.

It also takes a view on the KPI set: the grid is unweighted, revenue-normalised
intensity can improve without emissions falling, KPI 3 measures process rather
than outcome, and the renewable SPT can be met largely through procurement. It
proposes a carbon condition on any step-down — a term-sheet recommendation that
is stated as not modelled.

## Running it

```bash
pip install -r ../requirements.txt
python scripts/build_model.py                                      # rebuild the Excel model
python ../project1-green-bond-analysis/scripts/build_brief.py \
    --input memo/SLL_Structuring_Memo.md \
    --output memo/SLL_Structuring_Memo.pdf                         # rebuild the memo PDF
```

Rebuilds `SLL_Structuring_Model.xlsx`. Options: `--output`, `--utilisation`.

```bash
pytest ../tests/test_sll.py ../tests/test_sll_workbook.py
```

The workbook is generated, not hand-maintained, and the tests check that its
Excel formulas evaluate to the same numbers as the Python model. The prose in
this README and the memo is written by hand.

## Files

| File | Description |
|------|-------------|
| `scripts/sll.py` | Facility economics — ratchet, utilisation, commitment fee, break-even (pure, unit-tested) |
| `scripts/build_model.py` | Builds the Excel model from `sll.py` |
| `SLL_Structuring_Model.xlsx` | Six-sheet formula-driven model (generated — do not edit by hand) |
| `memo/SLL_Structuring_Memo.md` | Structuring memo — the editable source |
| `memo/SLL_Structuring_Memo.pdf` | The memo as a PDF (generated from the markdown) |

### Workbook contents

| Sheet | Contents |
|---|---|
| 0. Borrower Profile | Hypothetical borrower, usage guide |
| 1. KPI Tracker | Baseline vs current vs target, with target years; live progress % |
| 2. SPT Calibration | Illustrative SPTs; formula-driven glide paths for all three KPIs |
| 3. Margin Ratchet | Pricing with utilisation and commitment fee; scenario table |
| 4. Utilisation Sensitivity | Ratchet benefit by drawdown, with break-even |
| 5. Economics & Caveats | Incremental economics vs a conventional facility, and what the model does not claim |

Yellow cells are inputs; everything else is a live formula.

## Status

- [x] Framework document and structuring approach
- [x] Hypothetical borrower profile
- [x] KPI selection with rationale
- [x] Illustrative SPT calibration with formula-driven glide paths
- [x] Margin ratchet design with financial impact
- [x] RCF economics — utilisation, total cost, incremental cost vs conventional, break-even
- [x] Verification & reporting framework
- [x] Reproducible build from script, with unit tests
- [x] Structuring memo with a recommendation and conditions precedent

## References

LMA/APLMA/LSTA (2023). *Sustainability-Linked Loan Principles.*

LMA/APLMA/LSTA (2025). *Sustainability-Linked Loan Principles*, revised 26 March 2025.

Science Based Targets initiative. *SBTi Corporate Near-Term Criteria*, version 5.3.1.

Science Based Targets initiative. *Steel sector guidance.*

UK Climate Change Committee (December 2020). *The Sixth Carbon Budget.*

---
*Last updated: 2026-10-09*

*Part of the [Sustainable Finance Portfolio](../README.md)*
