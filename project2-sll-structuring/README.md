# Project 2 — SLL Structuring Case Study

## Overview

Sustainability-linked loans (SLLs) differ from green bonds in one critical respect:
the cost of capital is contingent on the borrower hitting ESG performance targets,
not on how proceeds are used. This makes KPI selection and target calibration the
core intellectual challenge — and the area most prone to greenwashing.

This project structures a hypothetical SLL from first principles for a fictional
UK industrial company, benchmarked against the LMA/APLMA/LSTA Sustainability-Linked
Loan Principles (2023 edition). All data and targets are illustrative only —
no real company financial data is used.

**The main finding is that the headline ratchet saving is not the real one.** A
revolving facility is rarely fully drawn, the ratchet applies only to the drawn
margin, and the verification cost that earns the saving is fixed. Taken together
these decide whether the structure pays for itself at all — see
[Financial Impact](#4-financial-impact) below.

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

SPTs must represent a material improvement vs baseline, consistent with recognised
science-based pathways (e.g. SBTi) or sector benchmarks.

| KPI | Baseline (2024) | Target Year | SPT | Benchmark Source |
|-----|----------------|-------------|-----|-----------------|
| Carbon intensity | 310 tCO₂e/£m rev | 2028 | ≤217 tCO₂e/£m rev (−30%) | SBTi 1.5°C near-term pathway (Industrials) |
| Renewable share | 18% | 2028 | ≥60% | UK Climate Change Committee 6th Carbon Budget |
| Supply chain audit | 35% | 2027 | ≥80% | LMA SLLP best practice |

A 30% carbon intensity reduction over four years (~7% per year) is consistent
with the SBTi near-term pathway for the Industrials sector. The model derives the
interim glide path (310 → 286.75 → 263.5 → 240.25 → 217) from the two endpoints,
so changing either moves every interim target — which matters because the ratchet
is tested annually, not once at maturity.

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

#### Why that overstates the benefit

A revolving credit facility is normally a **liquidity backstop**, held largely
undrawn. Two things follow, and the earlier version of this model missed both:

1. **The ratchet only touches the drawn margin.** At 60% utilisation the −7.5bps
   step applies to £390m, not £650m, so the best-case saving falls from £487.5k to
   **£292.5k**.
2. **The undrawn balance is not free.** It carries a commitment fee —
   conventionally ~35% of the margin, so 42bps here — which the original model
   ignored entirely. At 60% utilisation that is £1.09m a year on the undrawn
   £260m, several times larger than the entire ratchet saving.

At 60% utilisation the facility therefore costs £21.26m drawn interest + £1.09m
commitment fee = **£22.35m**, against the £35.43m the full-drawdown table implies.

#### Does the structure pay for itself?

The ratchet saving scales with drawdown; the annual third-party verification cost
(ISAE 3000 assurance, taken here as £100k) does not. So there is a break-even:

| Utilisation | Drawn | Best-case saving | Verification | Net |
|---|---|---|---|---|
| 0% | £0m | £0k | £100k | **−£100k** |
| 20% | £130m | £97.5k | £100k | **−£2.5k** |
| 40% | £260m | £195k | £100k | +£95k |
| 60% | £390m | £292.5k | £100k | +£192.5k |
| 80% | £520m | £390k | £100k | +£290k |
| 100% | £650m | £487.5k | £100k | +£387.5k |

**Break-even utilisation is 20.5%.** Below that, the best possible ratchet outcome
does not cover the cost of proving you achieved it.

This is the substantive point of the exercise. A borrower using the facility as an
undrawn backstop gets little or no pricing benefit, and the case for the SLL has to
rest on signalling, investor relations or internal accountability rather than on
cost of capital. That is a recognised criticism of the instrument, and quoting only
the full-drawdown figure obscures it.

It is also worth keeping the magnitude in perspective: ±7.5bps is small relative to
ordinary credit-spread volatility for a BBB– borrower, so the SLL label is unlikely
to be the binding factor in the cost of capital either way.

### 5. Verification & Reporting

- External verifier: Big 4 assurance or specialist ESG verifier (e.g. Bureau Veritas, DNV)
- Reporting cadence: Annual sustainability report + loan anniversary letter
- Assurance standard: ISAE 3000 / AA1000AS
- KPI data: Verified via Streamlined Energy and Carbon Reporting (SECR) disclosures
  and the REGO certificate registry (for renewable share) — both UK statutory or
  registry-based, so no paid data subscription is required

## What this model deliberately does not claim

- The ratchet is priced on the drawn margin only. Structures that also ratchet the
  commitment fee pro rata would show a wider spread between scenarios.
- No discounting — these are single-year figures.
- Verification cost is one illustrative input; real assurance costs vary with
  scope, and the first year is usually dearer.
- **KPI selection, not pricing, is where the integrity risk sits.** A material KPI
  with an unambitious SPT prices identically to a demanding one in this model. No
  amount of ratchet engineering fixes a weak target.

## The memo

[`memo/SLL_Structuring_Memo.pdf`](./memo/SLL_Structuring_Memo.pdf) is the
credit-committee-style document the model supports. It recommends structuring the
facility as sustainability-linked **but not presenting the margin ratchet as the
commercial rationale**, on the basis that the ratchet is worth £292.5k at
realistic utilisation against a £1.09m commitment fee the original model ignored,
and only covers its own verification cost above 20.5% drawdown.

It also takes a view on the KPI set rather than just describing it: KPI 3
(supply-chain audit *coverage*) measures process rather than outcome, and the
renewable-share SPT can be met substantially through procurement rather than
operational change. Both are accepted, with conditions, and said plainly.

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

The workbook is generated, not hand-maintained, and the tests assert that its
Excel formulas evaluate to the same numbers as the Python model — so the figures
in this README, the code, and the spreadsheet cannot drift apart.

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
| 1. KPI Tracker | Baseline vs current vs target, live progress % |
| 2. SPT Calibration | SPTs with benchmark sources; formula-driven glide path |
| 3. Margin Ratchet | Pricing with utilisation and commitment fee; scenario table |
| 4. Utilisation Sensitivity | Ratchet benefit by drawdown, with break-even |
| 5. Economics & Caveats | Does it pay for itself, and what the model does not claim |

Yellow cells are inputs; everything else is a live formula.

## Status

- [x] Framework document and structuring approach
- [x] Hypothetical borrower profile
- [x] KPI selection with rationale
- [x] SPT calibration with benchmark sources and formula-driven glide path
- [x] Margin ratchet design with financial impact
- [x] Realistic RCF economics — utilisation, commitment fee, break-even analysis
- [x] Verification & reporting framework
- [x] Reproducible build from script, with unit tests
- [x] Structuring memo with a recommendation and conditions precedent

## References

LMA/APLMA/LSTA (2023). *Sustainability-Linked Loan Principles.*

ICMA (2023). *Sustainability-Linked Bond Principles.*

SBTi (2023). *Corporate Net-Zero Standard — Industrials Sector Guidance.*

UK Climate Change Committee (2023). *6th Carbon Budget: Sector Pathways.*

CDP (2024). *CDP Climate Questionnaire — Technical Note on Scope 1+2 reporting.*

---
*Last updated: 2026-10-02*

*Part of the [Sustainable Finance Portfolio](../README.md)*
