# SLL Structuring Memo

## Albion Industrials plc — £650m sustainability-linked revolving credit facility (hypothetical)

**ShangyuZ** · BSc Statistics, Economics & Finance, UCL · October 2026

*Albion Industrials plc is a fictional borrower. All financial data, targets, rates and costs are illustrative. This memo is a structuring exercise against the LMA/APLMA/LSTA Sustainability-Linked Loan Principles (2023 edition; the principles were revised in March 2025 — see §7), not advice on any real transaction. Figures are computed by `scripts/sll.py`, and tests check them against the Excel model.*

---

## Recommendation

**Structure the facility as sustainability-linked, and present its pricing benefit as conditional on utilisation.**

Under the model's assumptions, the pricing case is positive in the base case and disappears when the facility is lightly drawn:

- At **60% utilisation** — the scenario assumed here, not a forecast — the best-case margin saving is **£292.5k a year**, and **£192.5k a year net** of an assumed £100k of incremental assurance cost.
- The saving applies only to the drawn balance, while the assurance cost is fixed. Below about **20.5% utilisation**, the best-case annual saving no longer covers that cost.
- The commitment fee is charged whether or not the facility is sustainability-linked, so it does not enter the comparison with an equivalent conventional revolver (§4).

The model does not establish where this borrower would actually operate on that range. That depends on its liquidity needs and is a credit question outside this memo. A modest saving relative to total interest expense is not by itself commercially irrelevant. The non-price reasons — board-level accountability for targets, and access to lenders with sustainability mandates — apply at any utilisation.

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
| Commitment fee | 42bps (35% of margin — a common convention for investment grade) |
| Ratchet | ±7.5bps two-way, tested annually |

Heavy industry is a useful place to test a sustainability-linked structure: emissions are material to operations rather than incidental, so KPIs can be tied to the core business instead of to peripheral reporting.

## 2. KPI selection

SLLP guidance requires KPIs that are material to the core business, measurable, externally verifiable, and consistent with the borrower's stated strategy.

| # | KPI | Metric | Why it is material |
|---|---|---|---|
| 1 | Carbon intensity | tCO₂e per £m revenue (Scope 1+2) | The principal emissions driver for steel and cement; directly exposed to UK ETS cost |
| 2 | Renewable electricity share | % of electricity from renewables | An operational lever management controls, verifiable through REGO certificates |
| 3 | Supply-chain audit coverage | % tier-1 suppliers audited to ESG standards | Governance quality, and a route towards managing Scope 3 exposure |

**The pricing grid is unweighted.** The ratchet is priced on the *number* of targets met — three, two, one or none — not on which ones. A borrower can miss the carbon target, meet the other two, and still receive the 2.5bps partial step-down. Carbon intensity is the most material KPI for this borrower, but the model does not give it more weight. §6 proposes a carbon condition; it is not implemented in the model.

**Revenue-normalised intensity can improve without any emissions reduction.** If emissions are unchanged and revenue rises 20% through prices or product mix, intensity falls from 310 to about 258 tCO₂e/£m — an apparent 16.7% improvement. That is a limitation of KPI 1 as specified. An absolute-emissions condition, or a physical-output denominator, would address it.

**KPI 3 measures process, not outcome.** A borrower can audit 80% of suppliers and act on none of the findings. I would accept coverage for the first facility term as a stepping stone towards a measured supplier-emissions metric, and say so explicitly.

## 3. SPT calibration

| KPI | Baseline (2024) | Target year | SPT | Informed by |
|---|---|---|---|---|
| Carbon intensity | 310 tCO₂e/£m | 2028 | ≤217 (−30%) | SBTi near-term criteria |
| Renewable share | 18% | 2028 | ≥60% | UK CCC Sixth Carbon Budget |
| Supply-chain audit | 35% | 2027 | ≥80% | LMA SLLP guidance on ambition |

**These are illustrative targets informed by those frameworks, and their alignment with them has not been independently established.** SBTi's criteria, for example, accept Scope 1+2 intensity targets only when they are modelled on an approved 1.5°C sector pathway applicable to the company's activities, and steel has its own sector guidance and boundaries. A chosen percentage reduction is not evidence of alignment. For a real facility, each SPT would need its derivation from the relevant pathway documented.

The model sets the interim path linearly for all three KPIs, because the ratchet is tested **annually**, not once at maturity. Without interim targets a borrower could miss for three years and still collect a step-down by hitting the final number.

| KPI | 2024 | 2025 | 2026 | 2027 | 2028 |
|---|---|---|---|---|---|
| Carbon intensity (tCO₂e/£m) | 310 | 286.75 | 263.50 | 240.25 | 217 |
| Renewable share (%) | 18 | 28.5 | 39 | 49.5 | 60 |
| Supply-chain audit (%) | 35 | 50 | 65 | 80 | — |

On the linear carbon path, intensity falls by **7.5% of the 2024 baseline each year**. The equivalent constant annual rate would be about **8.5% a year**, compounded.

**The renewable SPT is the one to interrogate.** Moving from 18% to 60% of electricity in four years is a large step, and the cheapest route to it is a corporate PPA or REGO purchase rather than any change in physical generation. That is a legitimate route, but KPI 2 can be met substantially through procurement, and it should not be read as evidence of operational transformation.

## 4. Pricing

### Total facility cost

This is what the borrower pays for the revolver. At **full drawdown** there is no undrawn balance, so no commitment fee is payable:

| SPTs met | Margin | All-in rate | Annual cost | Δ vs no adjustment |
|---|---|---|---|---|
| 3 of 3 | SONIA + 112.5bps | 5.375% | £34.94m | −£487.5k |
| 2 of 3 | SONIA + 117.5bps | 5.425% | £35.26m | −£162.5k |
| 1 of 3 | SONIA + 120bps | 5.450% | £35.43m | — |
| 0 of 3 | SONIA + 127.5bps | 5.525% | £35.91m | +£487.5k |

At **60% utilisation**, with no margin adjustment, the facility costs £21.26m of drawn interest plus £1.09m of commitment fee on the undrawn £260m — **£22.35m** in total.

### Incremental economics of the sustainability feature

Whether the label pays depends on a different comparison: **this facility minus an otherwise identical conventional revolver.** The commitment fee is charged on both, so it cancels. What remains is the drawn-margin adjustment and the incremental assurance cost:

| Utilisation | Drawn | Best-case margin saving | Incremental assurance | Net, vs conventional |
|---|---|---|---|---|
| 0% | £0m | £0k | £100k | **−£100k** |
| 20% | £130m | £97.5k | £100k | **−£2.5k** |
| 40% | £260m | £195k | £100k | +£95k |
| 60% | £390m | £292.5k | £100k | **+£192.5k** |
| 80% | £520m | £390k | £100k | +£290k |
| 100% | £650m | £487.5k | £100k | +£387.5k |

**Best-case annual pricing break-even under the model assumptions: 20.5% utilisation.** The figure assumes that:

- every SPT is met;
- the whole £100k of assurance is incremental. Under the SLLP, information already verified in the borrower's annual reporting need not be verified again, which would lower this cost and the break-even;
- only the drawn margin changes;
- there are no other incremental costs, such as legal, structuring or internal reporting.

The grid is symmetric, so missing every target costs the borrower as much as meeting every target saves. The expected benefit therefore depends on how confident the borrower is of meeting its SPTs, which this model does not estimate.

## 5. Integrity risks

Ranked by how much they would worry me:

1. **A step-down-only ratchet.** A one-way structure hands the borrower a free option: upside for hitting targets, no consequence for missing. This is a central greenwashing concern in SLL practice, and it is why §1 specifies a **two-way** ratchet with the step-up enforced.
2. **Unambitious SPTs priced identically to demanding ones.** Nothing in the pricing mechanism distinguishes a stretch target from business-as-usual. **KPI and SPT selection, not pricing design, is where most of the integrity work happens.**
3. **An unweighted grid** (§2). The most material KPI can be missed while a step-down is still earned.
4. **Intensity gains from revenue rather than emissions** (§2).
5. **Baseline restatement.** A borrower that restates its 2024 baseline upward makes a −30% target easier. The facility agreement should fix the baseline and require any restatement to be externally verified and re-benchmarked.
6. **Verification scope narrowing.** Assurance can be narrowed year on year to reduce cost and risk. Scope should be specified at signing.
7. **Procurement-only improvement on KPI 2** (§3), which is acceptable but should not be presented as operational change.

## 6. Conditions I would require

These are recommendations for the term sheet. Only the two-way ratchet and the annual interim paths are reflected in the model.

1. **Two-way ratchet, step-up non-negotiable.** Without it, drop the sustainability-linked label.
2. **A carbon condition on any step-down:** no margin reduction unless the carbon intensity SPT is met, plus an absolute-emissions backstop so that intensity cannot improve through revenue growth alone. *Not modelled.*
3. **Fixed baseline**, with any restatement externally verified and the SPT re-benchmarked.
4. **Annual interim SPTs** per the paths in §3, not a single 2028 test.
5. **Assurance scope fixed at signing**, to ISAE 3000 or an equivalent standard, with the verifier's report delivered to lenders.
6. **Documented SPT derivation**: each target traced to the specific sector pathway or benchmark it relies on, before signing.
7. **Declassification clause.** If a KPI becomes unmeasurable or an SPT is rendered meaningless by a disposal or restatement, the margin reverts to the unadjusted base rather than defaulting to the step-down.
8. **A Scope 3 pathway**: KPI 3 moves from audit coverage to a measured supplier-emissions metric at first refinancing.

## 7. What this analysis does not claim

- **Single-year, undiscounted figures.** Over a five-year facility the saving is roughly five times the annual number less annual assurance cost; it is not discounted.
- **Only the drawn margin is ratcheted.** Some SLLs also link the commitment fee. The effect of that depends on utilisation, because the fee falls on the undrawn balance: at 0% utilisation, a fee set at 35% of the margin would move by 2.625bps on the full £650m, worth **£170,625 a year** when all SPTs are met, while the drawn-only ratchet is worth nothing.
- **Assurance cost is one illustrative input.** Real cost varies with scope, the first year is usually dearer, and existing verification may cover part of it.
- **Utilisation is a scenario, not a forecast.** Where this borrower would sit is a credit and liquidity question this memo does not model.
- **No credit analysis.** This memo prices a sustainability feature. It does not assess whether £650m is the right facility size or BBB– the right rating.
- **Framework edition.** The exercise uses the 2023 SLLP. The March 2025 revision would need to be checked before applying this structure to a current transaction.

---

## Method and reproducibility

The economics live in `scripts/sll.py` as plain functions, and `scripts/build_model.py` generates `SLL_Structuring_Model.xlsx` from them. Yellow cells in the workbook are inputs and every result is a live formula; the test suite evaluates the Excel formulas and compares them with the Python model. The number of SPTs met is a separate scenario input on the pricing sheet — the KPI Tracker shows progress but does not drive pricing.

All sources are public: the LMA/APLMA/LSTA Sustainability-Linked Loan Principles, SBTi criteria and sector guidance, the UK Climate Change Committee's Sixth Carbon Budget, and — for the verification route — SECR disclosures and the REGO certificate registry. No paid terminal data is used.

This memo was drafted with AI assistance (Claude Code); the structuring choices and conclusions are mine.

**Repository:** github.com/ShangyuZ/Sustainable-finance-portfolio

## References

LMA/APLMA/LSTA (2023). *Sustainability-Linked Loan Principles.*

LMA/APLMA/LSTA (2025). *Sustainability-Linked Loan Principles*, revised 26 March 2025.

Science Based Targets initiative. *SBTi Corporate Near-Term Criteria*, version 5.3.1 — criterion C17 on intensity targets.

Science Based Targets initiative. *Steel sector guidance.*

UK Climate Change Committee (December 2020). *The Sixth Carbon Budget.*
