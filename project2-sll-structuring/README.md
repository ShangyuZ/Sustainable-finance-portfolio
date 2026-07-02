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
with the SBTi near-term pathway for the Industrials sector.

### 3. Margin Ratchet Design

A two-way ratchet (step-up AND step-down) is considered best practice to avoid
moral hazard:

```
All 3 SPTs met      → −7.5 bps on margin
2 of 3 SPTs met     → −2.5 bps on margin
1 of 3 SPTs met     → no adjustment
0 SPTs met          → +7.5 bps on margin
```

Ratchet applied annually on the interest payment date following third-party
verification. Market practice typically ranges from 2.5–15 bps per year.

### 4. Financial Impact (Illustrative)

Assuming £650m facility at SONIA + 120 bps:

| Scenario | Margin | Annual interest cost | Δ vs base |
|----------|--------|---------------------|-----------|
| All SPTs met | SONIA + 112.5 bps | ~£8.7m* | −£490k |
| No adjustment | SONIA + 120 bps | ~£9.2m* | — |
| No SPTs met | SONIA + 127.5 bps | ~£9.7m* | +£490k |

*Illustrative only. Assumes SONIA = 4.25%, full facility drawn.*

### 5. Verification & Reporting

- External verifier: Big 4 assurance or specialist ESG verifier (e.g. Bureau Veritas, DNV)
- Reporting cadence: Annual sustainability report + loan anniversary letter
- Assurance standard: ISAE 3000 / AA1000AS
- KPI data: Verified via Streamlined Energy and Carbon Reporting (SECR) disclosures
  and REGO certificate registry (for renewable share)

## Files

| File | Description |
|------|-------------|
| `SLL_Structuring_Model.xlsx` | KPI tracker, SPT calibration, margin ratchet calculator *(in progress)* |

## Status

- [x] Framework document and structuring approach
- [x] Hypothetical borrower profile
- [x] KPI selection with rationale
- [x] SPT calibration with benchmark sources
- [x] Margin ratchet design with financial impact table
- [x] Verification & reporting framework
- [ ] Excel model (KPI tracker + ratchet calculator)
- [ ] Structuring memo / brief

## References

LMA/APLMA/LSTA (2023). *Sustainability-Linked Loan Principles.*

ICMA (2023). *Sustainability-Linked Bond Principles.*

SBTi (2023). *Corporate Net-Zero Standard — Industrials Sector Guidance.*

UK Climate Change Committee (2023). *6th Carbon Budget: Sector Pathways.*

CDP (2024). *CDP Climate Questionnaire — Technical Note on Scope 1+2 reporting.*

---
*Last updated: 2026-07-02*

*Part of the [Sustainable Finance Portfolio](../README.md)*
