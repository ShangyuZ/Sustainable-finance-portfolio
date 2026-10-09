# Green Bond Market Brief

## What a sample of 732 labelled bonds shows — and what it cannot

**ShangyuZ** · BSc Statistics, Economics & Finance, UCL · October 2026

*Data: Climate Bonds Initiative News Makers extract — 732 labelled issuances, 2015–2024, $650.04bn. Every figure here is computed from the aggregate tables published alongside this brief, not quoted by hand; see Methodology.*

---

## Summary view

This is an exploratory analysis of a curated sample: the Climate Bonds Initiative News Makers extract, which tracks notable transactions rather than the whole market. It is useful for practising cleaning, aggregation and description on real issuance records. It is not a basis for statements about the size or make-up of the labelled-debt market, and the findings below are about the sample.

- **In this sample, 82% of volume is sovereign.** That is a property of how the sample was selected, not of the market. CBI's own market summary records $5.4tn of cumulative aligned sustainable debt to Q3 2024, of which $630.5bn — about 11.6% — is sovereign. The two sources have different coverage, so the comparison shows that the sample is not representative, not by how much (§2).
- **64% of sample volume is European.** Germany, France and the UK alone are 36.5%.
- **Sustainability-linked bonds are 15% of the sample's deals but 3.4% of its volume**, averaging $206m against green bonds' $1,077m.
- **Average deal size in the sample fell 66%** from 2018 to the partial year 2024, from $1,757m to $590m.
- **Germany's green twin Bunds trade at a small, persistent greenium.** Over 8,094 paired daily observations the mean is **−1.50bps**, down from −4.71bps in 2021 to under 1bp in 2025. The sign is robust to every inference choice tested; the precision is modest (t = −4.5 once persistence and same-day co-movement are accounted for, §4).

---

## 1. Growth depends on what you count

The most-quoted growth figure for this market measures the wrong thing.

| Measure | 2018 | 2023 | Growth |
|---|---|---|---|
| Deal count | 10 | 238 | **+2,280%** |
| USD volume | $17.6bn | $184.5bn | **+950%** |
| Average deal size | $1,757m | $775m | **−56%** |

Deal count overstates growth by more than a factor of two, because average deal size fell as the market broadened. Both numbers are true; only the second describes how much capital moved.

This is not pedantry — count and volume rank the market differently. **China leads on deal count (68 transactions) but ranks sixth by volume**, because Chinese issuance in this dataset is many small bank deals while European volume sits in a handful of large sovereign programmes. An analysis built on counts would conclude the wrong thing about where this market is.

Annual volume, with 2024 as a partial year in this extract:

| Year | Deals | Volume ($bn) | Avg deal ($m) |
|---|---|---|---|
| 2018 | 10 | 17.6 | 1,757 |
| 2019 | 20 | 25.2 | 1,258 |
| 2020 | 36 | 44.9 | 1,247 |
| 2021 | 85 | 128.4 | 1,510 |
| 2022 | 169 | 140.3 | 830 |
| 2023 | 238 | 184.5 | 775 |
| 2024* | 165 | 97.3 | 590 |

*\*2024 is incomplete in this extract. Its −47% volume change is a data cut-off, not a market contraction.*

---

## 2. The sample is mostly sovereign — the market is not

| Sector | Deals | Volume ($bn) | % of volume | Avg deal ($m) |
|---|---|---|---|---|
| Sovereign | 448 | 536.2 | **82.5%** | 1,197 |
| Financials | 95 | 46.2 | 7.1% | 486 |
| Unclassified | 65 | 23.8 | 3.7% | 366 |
| Industrials | 53 | 18.1 | 2.8% | 341 |
| All others | 71 | 25.7 | 4.0% | 362 |

Within the sample, sovereign deals are **three times larger** on average than everything else ($1,197m vs $401m).

**Why this cannot be read as a market share.** CBI's *Sustainable Debt Market Summary Q3 2024* records $5.4tn of cumulative aligned green, social, sustainability and sustainability-linked debt, of which $630.5bn is sovereign — about 11.6%. The two sources have different coverage — dates, alignment screens and instrument scope all differ — so the figures cannot be divided into each other to say how much of the market this extract captures. What the gap between 82.5% and about 11.6% does show is that the sample's composition cannot stand in for the market's. A newsflow series that tracks notable transactions is likely to over-represent large sovereign deals.

Geographic concentration in the sample follows from the same selection. Europe is 64.4% of sample volume across 293 deals; the top three countries are 36.5%:

| Country | Deals | Volume ($bn) | % of volume |
|---|---|---|---|
| Germany | 58 | 95.2 | 14.6% |
| France | 42 | 82.2 | 12.6% |
| UK | 20 | 59.8 | 9.2% |
| Italy | 16 | 45.9 | 7.1% |
| Chile | 36 | 37.6 | 5.8% |
| China | 68 | 33.1 | 5.1% |

What the sample does show well is the sovereign segment itself: European programmes — the green Bund, the OAT verte, the green gilt — and a cluster of emerging-market sovereigns (Chile, Mexico, Indonesia, Hungary) that have used the format for budget funding.

---

## 3. Sustainability-linked bonds in the sample

Sustainability-linked bonds have the stronger theoretical claim. Green bonds restrict *use of proceeds*, which says nothing about whether the issuer's overall emissions fall and requires a ring-fenceable project. SLBs tie the coupon to an *outcome* — a measured KPI — so in principle they work for any issuer and reward actual performance.

In this sample they are small:

| Theme | Deals | % of deals | Volume ($bn) | % of volume | Avg deal ($m) |
|---|---|---|---|---|---|
| Green | 490 | 66.9% | 527.7 | 81.2% | 1,077 |
| Sustainability | 109 | 14.9% | 72.5 | 11.2% | 665 |
| SLB | 108 | 14.8% | 22.2 | **3.4%** | **206** |
| Social | 25 | 3.4% | 27.6 | 4.2% | 1,105 |

SLBs match sustainability bonds on deal count but carry under a third of their volume ($22.2bn against $72.5bn). The average SLB is **five times smaller** than the average green bond. SLB share of annual sample volume reached 11.8% in 2024, from almost nothing before 2021 — the only earlier record is a single 2015 deal that the Data Quality sheet flags as mislabelled — but from a very low base and in the partial year. Given the selection issue in §2, none of this says how large the SLB market is; CBI records $55.4bn of aligned SLB volume to Q3 2024.

**A related exercise, not an explanation.** My companion project structures a hypothetical sustainability-linked *loan* — a £650m revolving facility with a ±7.5bps margin ratchet and ~£100k of annual KPI assurance. Because the ratchet applies only to the drawn margin while assurance is a fixed cost, the best-case outcome only covers its own verification above **20.5% utilisation**. That result is specific to an undrawn revolver. An SLB is fully funded at issue and adjusts its coupon by a different mechanism, so the loan scenario does not explain the size of the SLB market, and this brief does not use it to.

---

## 4. Greenium: what can and cannot be claimed

The academic literature consistently finds a small negative premium — green bonds yielding *less* than comparable conventional bonds:

| Study | Market | Estimate (bps) | Method |
|---|---|---|---|
| Zerbib (2019) | Global, 110 bonds | −2 | Matched-pair + 2-step OLS |
| Löffler et al. (2021) | Global, primary and secondary | −15 to −20 | Propensity-score and coarsened exact matching |
| Caramichael & Rapp (2022) | Global corporates, at issuance | −8 | Fixed-effects panel regression |
| Panizza et al. (2025) | Sovereign and sovereign-backed, secondary | ≈ −2 advanced, ≈ −13 emerging | 332 matched pairs |
| Pietsch & Salakhova (2025) | Euro area, secondary | ≈ −3.7 average | k-prototypes matching |

*Convention: (green yield − conventional yield); negative means a greenium exists.*

These are not directly comparable — they differ in market, period, primary versus secondary pricing, and matching method. The spread of estimates is mostly heterogeneity, not disagreement about technique.

### My own estimate: −1.50bps, and narrowing

I measured it rather than citing it. The method avoids the literature's central weakness: instead of modelling comparability, it uses Germany's green **twin** Bunds, where each green security has a conventional counterpart with the *same coupon, same maturity and same issuer*. The yield difference is then the greenium almost by construction, with no matching model doing the work.

All nine green Federal securities outstanding were matched to their exact twins — coupon and maturity identical on both legs — giving **8,094 paired daily observations from September 2020 to October 2026**, all from the issuer's own published data.

| | |
|---|---|
| Pooled greenium (each paired observation weighted equally) | **−1.50bps** |
| Panel HAC standard error (Driscoll-Kraay, 250-day bandwidth) | 0.330 |
| t-statistic | −4.5 |
| Paired observations | 8,094 across 9 twin pairs |
| Days with a negative spread | 99.8% |
| Range of per-pair means | −0.65bps to −2.40bps |

The greenium is small and persistent, and its sign is robust: all nine pairs have a negative mean, and the result holds under every inference choice tested. The *size* of the headline depends on weighting — −1.50bps per observation, −1.29bps with each pair weighted equally, −2.04bps with each date weighted equally (early dates have fewer pairs and the wide 2021 spreads) — so it is quoted with its weighting stated.

**Inference: how the published precision was corrected.** The daily spread is strongly autocorrelated and stays so for months — 0.86 at 60 trading days and 0.66 at 120. An earlier version of this brief applied a Newey-West correction with the rule-of-thumb 10 lags to the nine pairs' histories stacked end to end, and reported t = −28.7. That understated the uncertainty twice over: 10 lags cut off most of the persistence, and stacking treated pairs quoted on the same date as independent evidence. Re-estimated with a panel HAC (Driscoll-Kraay) standard error, which sums residuals across pairs by date before applying the Newey-West weights:

| Specification | t-statistic |
|---|---|
| Ordinary standard error (no correction) | −94.2 |
| Stacked series, Newey-West, 10 lags (previously published) | −28.7 |
| Driscoll-Kraay, 60 / 120 / 250 lags | −8.2 / −6.0 / −4.5 |
| t-test across the nine pair means (8 df, no bandwidth needed) | −5.7 |

The 250-day figure is the one quoted. The conclusion that a greenium exists survives every row; the precision of the earlier figure did not.

**What the twin design does and does not identify.** Same issuer, coupon and maturity remove the matching problem, but not every difference: the green twin is smaller and less liquid, and the conventional twin can trade special in repo. The correlation between years-to-maturity and pair means is 0.11, but across nine pairs that only rules out a strong tenor pattern — it cannot establish that the spread is a pure label effect.

**The more interesting result is the trend.** The greenium has compressed by roughly 80% from its 2021 peak:

| Year | Mean greenium | Obs |
|---|---|---|
| 2020 | −2.35bps | 80 |
| 2021 | −4.71bps | 495 |
| 2022 | −1.94bps | 855 |
| 2023 | −2.27bps | 1,331 |
| 2024 | −1.07bps | 1,695 |
| 2025 | −0.76bps | 1,955 |
| 2026 | −0.95bps | 1,683 |

The yearly means are descriptive; no per-year standard errors are reported, because within one year the dependence runs too long to estimate reliably. The pattern is consistent with a maturing market in which the novelty premium faded as green supply grew, though the number of pairs also rises from one to nine over the period, so composition contributes to the trend. The average yield difference is below 1bp in 2025.

My estimate sits close to Zerbib's −2bps and to Panizza et al.'s ≈ −2bps for advanced-economy sovereigns, and well below Löffler et al.'s −15 to −20bps. That gap is plausible rather than contradictory: their matched universe spans corporate and lower-rated issuers, where comparability is hardest to achieve, while this measures exact twins on the most liquid sovereign curve in Europe, where any mispricing is arbitraged hardest.

---

## 5. What would change my view

The honest limitations of this analysis:

- **The dataset is a curated newsflow extract**, not an exhaustive market census. The Climate Bonds Initiative News Makers series tracks notable transactions, and large sovereign deals are more likely to be *notable* — a selection effect large enough that the sample's 82% sovereign share sits beside about 11.6% in CBI's own market summary (§2). Every composition figure here is therefore a statement about the sample. Reconciling against a full issuance database is the first thing I would do next.
- **2024 is partial**, so the recent trend and the 11.8% SLB share are provisional.
- **Sector is undisclosed for 65 deals** ($23.8bn, 3.7% of volume), shown as Unclassified rather than dropped or allocated.
- **Two source records are known to be wrong** and are flagged rather than silently corrected: one issuer is tagged to the wrong country, and one 2015 transaction is labelled SLB years before that market existed.
- **The greenium estimate is German sovereign only.** The twin structure removes the matching problem rather than modelling around it, but it does not generalise to corporate issuers, to other sovereigns, or to primary-market pricing, where the published estimates are several times larger. Its precision depends on the bandwidth chosen (§4); its sign does not.

What would change the greenium finding: a bandwidth or resampling scheme under which the sign stops being robust, or evidence that liquidity or repo effects account for the spread.

---

## Methodology

Data was cleaned and aggregated in Python (pandas) and the model built with openpyxl; every figure in this brief regenerates from the published aggregate tables with one command, and tests check key calculations and the consistency of the quoted figures with those tables. They do not validate every interpretation or citation.

The source extract required substantive normalisation before it could be aggregated, all documented on the model's Data Quality sheet: sector "not disclosed" was encoded as the string `"0"` (64 records); 34 sector labels denoted 11 real groups (seven spellings of the financial sector each ranked separately); and four country labels were duplicated — `USA`/`United States`, `UK`/`United Kingdom`, `China_HK`, and a misspelt `Supranational`, plus one trailing-space variant of `Netherlands`. Left uncorrected these understated the UK by $0.45bn and inflated the country count from 64 to an apparent 69.

The greenium estimate uses the Deutsche Finanzagentur's published daily price and yield series for each green Federal security and its conventional twin; the twin pairing is derived by matching coupon and maturity exactly, not asserted. Standard errors are Driscoll-Kraay with a 250-trading-day Bartlett bandwidth; the sensitivity table in §4 is regenerated with the estimate. `scripts/fetch_bund_yields.py` reproduces the download and `scripts/greenium.py` the estimate.

Sources are public throughout: Climate Bonds Initiative for issuance and for the market-wide comparison in §2, published academic papers for the comparative greenium evidence, and the Deutsche Finanzagentur for bond yields. No proprietary terminal data is used, and the repository's CI fails the build if a reference to one appears — including inside the Excel files.

Public access is not the same as permission to republish, and two of these sources reserve their rights: CBI prohibits reproducing their content without written permission, and Finanzagentur marks its published data all rights reserved. Neither dataset is redistributed in the repository. What is published instead is this project's own derived output — the aggregate tables and the greenium estimator results — which is what every figure above is computed from and checked against. Both are regenerable from their publishers in one command by anyone with access. The repository's DATA.md records the terms and the trade-off.

**Repository:** github.com/ShangyuZ/Sustainable-finance-portfolio

---

## References

Zerbib, O.D. (2019). *The effect of pro-environmental preferences on bond prices: Evidence from green bonds.* Journal of Banking & Finance, 98, 39–60.

Löffler, K.U., Petreski, A. & Stephan, A. (2021). *Drivers of green bond issuance and new evidence on the "greenium".* Eurasian Economic Review, 11, 1–24.

Caramichael, J. & Rapp, A.C. (2022). *The Green Corporate Bond Issuance Premium.* Federal Reserve International Finance Discussion Paper 1346.

Climate Bonds Initiative (2024). *Sustainable Debt Market Summary Q3 2024.*

Driscoll, J.C. & Kraay, A.C. (1998). *Consistent covariance matrix estimation with spatially dependent panel data.* Review of Economics and Statistics, 80(4), 549–560.

Panizza, U., Shi, S., Weder di Mauro, B. & Gulati, M. (2025). *The Sovereign Greenium: Big Promise but Small Price Effect.* CEPR Discussion Paper No. 20817.

Pietsch, A. & Salakhova, D. (2025). *Pricing of Green Bonds: Greenium Dynamics and the Role of Retail Investors.* Banque de France Working Paper No. 1010.

LMA/APLMA/LSTA (2023). *Sustainability-Linked Loan Principles.*
