# SLL Structuring Memo

## Albion Industrials plc — £650m sustainability-linked revolving credit facility

**ShangyuZ** · BSc Statistics, Economics & Finance, UCL · October 2026

*Albion Industrials plc is a fictional borrower. All financial data, targets, rates and costs are illustrative. This memo is a structuring exercise against the LMA/APLMA/LSTA Sustainability-Linked Loan Principles (2023), not advice on any real transaction. Figures are computed by `scripts/sll.py` and asserted in the test suite.*

---

## Recommendation

**Structure the facility as sustainability-linked, but do not present the margin ratchet as the commercial rationale.**

The KPI set is material and the targets are benchmarked to a recognised pathway, so the structure satisfies SLLP guidance. The pricing mechanism, however, does not do the work it is usually claimed to do:

- At full drawdown the ratchet is worth **£487.5k a year** at best. At a realistic 60% utilisation it is **£292.5k**.
- The undrawn balance carries a commitment fee of **£1.09m a year** at that utilisation — several times the entire ratchet.
- Because the ratchet scales with drawdown while verification cost does not, the structure only covers its own costs above **20.5% utilisation**.

A revolver is normally held as a liquidity backstop, well below that threshold. So for this borrower the honest case for the SLL is governance and signalling — board-level accountability for targets, and access to sustainability-mandated lenders — not cost of capital. Recommending it on price would not survive scrutiny.

**Conditions I would require** are set out in §6.

---

## 1. Borrower and facility

| | |
|---|---|
| Borrower | Albion Industrials plc *(fictional)* |
| Sector | UK heavy industrials — steel and construction materials |
| Revenue / EBITDA margin | £2.8bn / 11% |
| Credit rating | BBB– (investment grade) |
| Facility | £650m revolving credit facility |
| Reference rate / base margin | SONIA / 120bps |
| Commitment fee | 42bps (35% of margin — market convention for IG) |
| Ratchet | ±7.5bps two-way, tested annually |

Heavy industry is the right place to test a sustainability-linked structure: emissions are material to operations rather than incidental, so KPIs can be tied to the core business instead of to peripheral reporting.

## 2. KPI selection

SLLP guidance requires KPIs that are material to the core business, measurable, externally verifiable, and aligned to the borrower's stated strategy.

| # | KPI | Metric | Why it is material |
|---|---|---|---|
| 1 | Carbon intensity | tCO₂e per £m revenue (Scope 1+2) | The principal emissions driver for steel and cement; directly exposed to UK ETS cost |
| 2 | Renewable electricity share | % of electricity from renewables | An operational lever management actually controls, verifiable through REGO certificates |
| 3 | Supply-chain audit coverage | % tier-1 suppliers audited to ESG standards | Governance quality, and the route by which Scope 3 exposure becomes manageable |

**Assessment: adequate.** All three are core-business metrics with external verification routes. KPI 1 carries the most weight and is the hardest to game, because revenue-normalised intensity cannot be improved by divesting output alone without also shedding revenue.

**The weakness** is KPI 3. Audit *coverage* measures process, not outcome: a borrower can audit 80% of suppliers and act on none of the findings. If the lender group wants Scope 3 traction, coverage should eventually give way to a measured supplier-emissions metric. I would accept coverage for the first facility term as a stepping stone, and say so explicitly rather than pretend it is an outcome measure.

## 3. SPT calibration

| KPI | Baseline (2024) | Target | SPT | Benchmark |
|---|---|---|---|---|
| Carbon intensity | 310 tCO₂e/£m | 2028 | ≤217 (−30%) | SBTi 1.5°C near-term, Industrials |
| Renewable share | 18% | 2028 | ≥60% | UK CCC 6th Carbon Budget |
| Supply-chain audit | 35% | 2027 | ≥80% | LMA SLLP best practice |

A 30% intensity reduction over four years is ~7% a year, consistent with the SBTi near-term pathway. The model derives the interim glide path linearly from the two endpoints — 310 → 286.75 → 263.50 → 240.25 → 217 — which matters because the ratchet is tested **annually**, not once at maturity. Without interim targets a borrower can miss for three years and still collect a step-down by hitting the final number.

**Assessment: the carbon SPT is defensible; the renewable SPT is the one to interrogate.** Moving from 18% to 60% of electricity in four years is a large step, and the cheapest route to it is a corporate PPA or REGO purchase rather than any change in physical generation. That is not illegitimate — it is how most corporates decarbonise electricity — but it means KPI 2 can be satisfied substantially through procurement. It should not be weighted as though it evidenced operational transformation.

## 4. Pricing — the analysis that changes the recommendation

The scenario table at **full drawdown**:

| SPTs met | Margin | All-in rate | Annual cost | Δ vs base |
|---|---|---|---|---|
| 3 of 3 | SONIA + 112.5bps | 5.375% | £34.94m | −£487.5k |
| 2 of 3 | SONIA + 117.5bps | 5.425% | £35.26m | −£162.5k |
| 1 of 3 | SONIA + 120bps | 5.450% | £35.43m | — |
| 0 of 3 | SONIA + 127.5bps | 5.525% | £35.91m | +£487.5k |

**Full drawdown is the wrong assumption.** A revolving facility is a liquidity backstop; assuming it fully drawn flatters the structure twice over:

1. **The ratchet applies only to the drawn margin.** At 60% utilisation the −7.5bps step applies to £390m, not £650m, so the best case falls from £487.5k to **£292.5k**.
2. **The undrawn balance is not free.** At 42bps on £260m it costs **£1.09m a year** — a cost the headline table omits entirely, and several times larger than the entire ratchet benefit.

At 60% utilisation the facility costs £21.26m of drawn interest plus £1.09m of commitment fee = **£22.35m**, against the £35.43m implied by the full-drawdown table.

**The break-even.** The ratchet benefit scales with drawdown. The third-party verification that earns it (ISAE 3000 assurance, ~£100k a year) does not. So:

| Utilisation | Drawn | Best-case saving | Verification | Net |
|---|---|---|---|---|
| 0% | £0m | £0k | £100k | **−£100k** |
| 20% | £130m | £97.5k | £100k | **−£2.5k** |
| 40% | £260m | £195k | £100k | +£95k |
| 60% | £390m | £292.5k | £100k | +£192.5k |
| 80% | £520m | £390k | £100k | +£290k |
| 100% | £650m | £487.5k | £100k | +£387.5k |

**Break-even utilisation: 20.5%.** Below that, the best possible sustainability outcome does not cover the cost of proving it was achieved.

Two further points of perspective. First, ±7.5bps is well inside the ordinary spread volatility of a BBB– credit, so even at full drawdown the ratchet is unlikely to be the binding factor in this borrower's cost of capital. Second, the step is symmetric, so the expected value to the borrower of a structure they are confident of hitting is positive but small — and the *variance* they take on from the step-up is of the same order.

This is why the recommendation does not rest on pricing.

## 5. Integrity risks

Ranked by how much they would worry me:

1. **A step-down-only ratchet.** A one-way structure hands the borrower a free option: upside for hitting targets, no consequence for missing. This is the central greenwashing channel the SLLP guidance targets, and it is why §1 specifies a **two-way** ratchet with the step-up genuinely enforced. If the borrower negotiates the step-up away, the structure loses most of its integrity and should arguably drop the label.
2. **Unambitious SPTs priced identically to demanding ones.** Nothing in the pricing mechanism distinguishes a stretch target from business-as-usual. A model like this one will produce the same £292.5k for either. **KPI and SPT selection, not pricing design, is where the real integrity work happens** — which is an argument for lender scrutiny at origination rather than for more elaborate ratchets.
3. **Baseline restatement.** A borrower that restates its 2024 baseline upward makes a −30% target easier. The facility agreement should fix the baseline and require that any restatement be externally verified and re-benchmarked.
4. **Verification scope creep downward.** Assurance can be narrowed year on year to reduce cost and risk. Scope should be specified at signing, not left to the borrower's auditor-selection.
5. **Procurement-only improvement on KPI 2** (§3), which is acceptable but should not be presented as operational change.

## 6. Conditions I would require

1. **Two-way ratchet, step-up non-negotiable.** Without it, drop the sustainability-linked label.
2. **Fixed baseline**, with any restatement externally verified and the SPT re-benchmarked.
3. **Annual interim SPTs** per the glide path in §3, not a single 2028 test.
4. **Assurance scope fixed at signing** to ISAE 3000, with the verifier's report delivered to lenders, not only summarised in the sustainability report.
5. **Declassification clause.** If a KPI becomes unmeasurable or an SPT is rendered meaningless by a disposal or restatement, the margin reverts to the unadjusted base rather than defaulting to the step-down.
6. **A Scope 3 pathway**: KPI 3 moves from audit coverage to a measured supplier-emissions metric at first refinancing.

## 7. What this analysis does not claim

- **Single-year, undiscounted figures.** Over a five-year facility the saving is roughly five times the annual number less annual verification cost; it is not NPV'd.
- **The ratchet is priced on the drawn margin only.** Some SLLs also ratchet the commitment fee pro rata, which would widen the scenario spread by roughly the commitment-fee percentage. I have modelled the more common structure.
- **Verification cost is one illustrative input.** Real assurance cost varies with scope, and the first year is usually dearer.
- **Utilisation is assumed, not forecast.** The break-even is robust; where this borrower actually sits on it is a credit question I have not modelled.
- **No credit analysis.** This memo prices a sustainability feature. It does not assess whether £650m is the right facility size or BBB– the right rating.

---

## Method and reproducibility

The economics live in `scripts/sll.py` as plain functions, and `scripts/build_model.py` generates `SLL_Structuring_Model.xlsx` from them, so the workbook cannot drift from the code. Yellow cells in the workbook are inputs; every result is a live formula, and the test suite evaluates those Excel formulas and compares them to the Python model cell by cell — a formula-driven spreadsheet that silently disagrees with its own code is worse than no spreadsheet.

All sources are public: LMA/APLMA/LSTA Sustainability-Linked Loan Principles (2023), SBTi sector guidance, the UK Climate Change Committee's 6th Carbon Budget, and — for the verification route — SECR disclosures and the REGO certificate registry. No proprietary terminal data is used or required.

**Repository:** github.com/ShangyuZ/Sustainable-finance-portfolio

## References

LMA/APLMA/LSTA (2023). *Sustainability-Linked Loan Principles.*

ICMA (2023). *Sustainability-Linked Bond Principles.*

SBTi (2023). *Corporate Net-Zero Standard — Industrials Sector Guidance.*

UK Climate Change Committee (2023). *6th Carbon Budget: Sector Pathways.*

CDP (2024). *CDP Climate Questionnaire — Technical Note on Scope 1+2 reporting.*
