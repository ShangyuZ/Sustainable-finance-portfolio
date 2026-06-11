# Project 2 — SLL Structuring Case Study

## Overview

Sustainability-linked loans (SLLs) differ from green bonds in one critical respect:
the cost of capital is contingent on the borrower hitting ESG performance targets,
not on how proceeds are used. This makes KPI selection and target calibration the
core intellectual challenge — and the area most prone to greenwashing.

This project picks one FTSE 100 company and structures a hypothetical SLL from
first principles, benchmarked against the LMA/APLMA/LSTA Sustainability-Linked
Loan Principles (2023 edition).

## Company Selected

**TBC — selection criteria:** FTSE 100, material ESG exposure, publicly disclosed
sustainability targets, existing debt profile visible in annual report or Bloomberg.

## Structuring Framework

### 1. KPI Selection

Per SLLP guidance, KPIs must be:
- Material to the borrower's core business
- Measurable and independently verifiable
- Aligned with the borrower's stated sustainability strategy

| # | KPI Candidate | Metric | Rationale |
|---|---------------|--------|-----------|
| 1 | Carbon intensity | tCO₂e per £m revenue | Scope 1+2, sector-relevant |
| 2 | Renewable energy share | % of electricity from renewables | Operational lever, verifiable |
| 3 | Supply chain audit coverage | % tier-1 suppliers audited | Governance, material for industrials |

### 2. Sustainability Performance Targets (SPTs)

SPTs must represent a material improvement vs baseline, consistent with recognised
science-based pathways (e.g. SBTi) or sector benchmarks.

| KPI | Baseline Year | Target Year | Target Level | Benchmark Source |
|-----|--------------|-------------|--------------|-----------------|
| Carbon intensity | 2023 | 2027 | -30% | SBTi sector pathway |
| Renewable share | 2023 | 2027 | ≥60% | UK grid decarbonisation trajectory |
| Supply chain audit | 2023 | 2026 | ≥80% | LMA best practice |

### 3. Margin Ratchet Design

A two-way ratchet (step-up AND step-down) is considered best practice to avoid
moral hazard:

```
All SPTs met     → −5 bps on margin
1–2 SPTs met     → no adjustment
0 SPTs met       → +5 bps on margin
```

Ratchet applied annually on interest payment date following third-party verification.

### 4. Verification & Reporting

- External verifier: Big 4 assurance or specialist ESG verifier
- Reporting cadence: Annual sustainability report + loan anniversary letter
- Assurance standard: ISAE 3000 / AA1000AS

## Files

| File | Description |
|------|-------------|
| `SLL_Structuring_Model.xlsx` | KPI tracker, SPT calibration, margin ratchet model *(in progress)* |
| `SLL_Brief.pdf` | 3-page structuring memo *(planned)* |

## Status

- [x] Framework document and structuring approach
- [x] KPI selection criteria
- [x] SPT calibration methodology
- [x] Margin ratchet design
- [ ] Company selection and data sourcing
- [ ] Excel model (KPI tracker + ratchet calculator)
- [ ] Structuring memo / brief

## References

LMA/APLMA/LSTA (2023). *Sustainability-Linked Loan Principles.*

ICMA (2023). *Sustainability-Linked Bond Principles.*

SBTi (2023). *Corporate Net-Zero Standard.*

---
*Part of the [Sustainable Finance Portfolio](../README.md)*
