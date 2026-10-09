"""
Greenium estimation from sovereign green "twin" bonds
====================================================
Estimates the green bond premium as the yield difference between a sovereign
green bond and its conventional twin.

Why twins
---------
The identification problem in greenium research is that no two bonds are truly
comparable: maturity, coupon, liquidity and seniority all differ, so the matching
model does most of the work and the estimate inherits its assumptions. Zerbib
(2019) handles this with a two-step matched-pair regression; Löffler et al.
(2021) with coarsened exact matching.

Germany sidesteps it. Each green Federal security is issued as a *twin* of a
conventional one with the **same coupon, same maturity date and same issuer** —
the two differ only in the green label and in outstanding size. The yield
difference is therefore the greenium almost by construction, with no matching
model required. France (OAT verte) and the UK (green gilts) publish comparable
series without the exact-twin structure.

Sign convention
---------------
The greenium is reported throughout as **(green yield − conventional yield) in
basis points**. A **negative** number means the green bond yields *less*, i.e.
investors accept a lower return to hold it, i.e. the greenium exists. This
matches the literature. The opposite convention is also common in practice, so
it is stated explicitly rather than left to the reader.

Inference
---------
A daily yield-spread series is strongly autocorrelated, so the ordinary standard
error of its mean is badly understated and an ordinary t-test will find
significance that is not there. Two corrections are needed, not one:

* **Persistence.** On the twin-Bund data the cross-pair daily spread is still
  correlated 0.66 with itself 120 trading days later. The Newey-West rule-of-thumb
  bandwidth (10 lags at this sample size) truncates almost all of that, so the
  long-run variance uses :data:`LONG_RUN_LAGS` — one trading year — instead.
* **Pairs quoted on the same date.** The pooled sample stacks nine bonds' daily
  histories. :func:`driscoll_kraay_se` sums residuals across pairs within each
  date before applying the HAC weights, so same-date co-movement between pairs is
  counted rather than treated as independent evidence.

An earlier version applied a 10-lag correction to the stacked histories and
reported t = -28.7; this module now gives t = -4.5 for the same mean. The sign
survives every specification in ``greenium_diagnostics.json``; the precision of
the old figure did not.

The estimator is verified against synthetic series with a known true greenium.
Applied to the German twin-Bund data it gives **-1.50bps** pooled (robust SE
0.330, t = -4.5, n = 8,094); ``fetch_bund_yields.py`` reproduces the download and
``--help`` documents the inputs.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

# Marker used in the committed pair template. Rows carrying it are placeholders,
# not real securities, and are rejected rather than silently estimated from.
PLACEHOLDER = "FILL_ME"

PAIR_COLUMNS = ["pair_id", "green_isin", "conventional_isin",
                "green_coupon_pct", "green_maturity",
                "conventional_coupon_pct", "conventional_maturity", "issuer"]
YIELD_COLUMNS = ["date", "isin", "yield_pct"]

# Coupons are quoted to at most 3dp, so anything closer than this is the same coupon.
COUPON_TOLERANCE = 1e-6


# ── pair registry ────────────────────────────────────────────────────────────

def load_pairs(path: str, strict: bool = False) -> pd.DataFrame:
    """
    Load the green/conventional pair registry and classify each pair.

    The registry is data, not code: it is populated from the issuer's own
    published list (see the template in ``data/``), because hardcoding ISINs
    from memory into a repository about data integrity would be exactly the
    wrong thing to do.

    Two derived columns are added, because the strength of the estimate depends
    on them:

    ``twin_exact``
        True when the two legs share coupon and maturity. Only then is the yield
        difference the greenium *by construction*, with no matching assumptions.
    ``maturity_gap_days``
        Absolute difference in maturity. Non-zero means the pair carries a
        residual term-structure mismatch that the raw spread does not control
        for — fine for France/UK, but it must be reported, not hidden.

    With ``strict=True``, raises unless every pair is an exact twin. Raises
    regardless if columns are missing, a row still carries the placeholder
    marker, a green ISIN is duplicated, or a pair lists the same ISIN twice.
    """
    df = pd.read_csv(path, comment="#")
    df.columns = df.columns.str.strip()

    missing = [c for c in PAIR_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"pair registry missing columns: {', '.join(missing)}")

    df = df[PAIR_COLUMNS].copy()
    for col in ("pair_id", "green_isin", "conventional_isin", "issuer"):
        df[col] = df[col].astype("string").str.strip()

    placeholders = df.apply(
        lambda r: r.astype("string").str.contains(PLACEHOLDER, na=False).any(), axis=1)
    if placeholders.any():
        raise ValueError(
            f"{int(placeholders.sum())} row(s) in {path} still contain "
            f"'{PLACEHOLDER}'. Populate the registry from the issuer's published "
            f"list of green securities and their twins before estimating."
        )
    if df["green_isin"].duplicated().any():
        raise ValueError("duplicate green_isin in pair registry")
    if (df["green_isin"] == df["conventional_isin"]).any():
        raise ValueError("a pair lists the same ISIN as both green and conventional")

    for col in ("green_coupon_pct", "conventional_coupon_pct"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("green_maturity", "conventional_maturity"):
        df[col] = pd.to_datetime(df[col], errors="coerce")

    unparseable = df[["green_coupon_pct", "conventional_coupon_pct",
                      "green_maturity", "conventional_maturity"]].isna().any(axis=1)
    if unparseable.any():
        bad = df.loc[unparseable, "pair_id"].tolist()
        raise ValueError(f"unparseable coupon or maturity for pair(s): {bad}")

    same_coupon = (df["green_coupon_pct"] - df["conventional_coupon_pct"]).abs() <= COUPON_TOLERANCE
    df["maturity_gap_days"] = (
        df["green_maturity"] - df["conventional_maturity"]).dt.days.abs()
    df["twin_exact"] = same_coupon & (df["maturity_gap_days"] == 0)

    if strict and not bool(df["twin_exact"].all()):
        bad = df.loc[~df["twin_exact"], "pair_id"].tolist()
        raise ValueError(
            f"strict=True but these pairs are not exact twins (coupon and "
            f"maturity must both match): {bad}")
    return df.reset_index(drop=True)


def load_yields(path: str) -> pd.DataFrame:
    """
    Load a tidy daily yield file: ``date, isin, yield_pct``.

    Long format rather than wide so the same file serves any number of
    securities. Rows with an unparseable date or a missing yield are dropped.
    """
    df = pd.read_csv(path, comment="#")
    df.columns = df.columns.str.strip()

    missing = [c for c in YIELD_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"yield file missing columns: {', '.join(missing)}")

    df = df[YIELD_COLUMNS].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["isin"] = df["isin"].astype("string").str.strip()
    df["yield_pct"] = pd.to_numeric(df["yield_pct"], errors="coerce")
    return df.dropna(subset=["date", "isin", "yield_pct"]).reset_index(drop=True)


# ── spread construction ──────────────────────────────────────────────────────

def build_spreads(pairs: pd.DataFrame, yields: pd.DataFrame) -> pd.DataFrame:
    """
    Join yields onto pairs and compute the daily greenium in basis points.

    Returns one row per (pair_id, date) on which **both** legs traded; a day
    where only one leg has a yield is dropped rather than carried forward,
    because a stale leg manufactures a spread that was never observable.

    Columns: pair_id, date, green_yield_pct, conventional_yield_pct,
    greenium_bps.
    """
    wide = yields.pivot_table(index="date", columns="isin", values="yield_pct",
                              aggfunc="last")
    rows = []
    for pair in pairs.itertuples(index=False):
        g, c = pair.green_isin, pair.conventional_isin
        if g not in wide.columns or c not in wide.columns:
            continue
        both = wide[[g, c]].dropna()
        if both.empty:
            continue
        rows.append(pd.DataFrame({
            "pair_id": pair.pair_id,
            "date": both.index,
            "green_yield_pct": both[g].to_numpy(),
            "conventional_yield_pct": both[c].to_numpy(),
            "twin_exact": bool(getattr(pair, "twin_exact", True)),
            "maturity_gap_days": int(getattr(pair, "maturity_gap_days", 0) or 0),
        }))
    if not rows:
        return pd.DataFrame(columns=["pair_id", "date", "green_yield_pct",
                                     "conventional_yield_pct", "twin_exact",
                                     "maturity_gap_days", "greenium_bps"])

    out = pd.concat(rows, ignore_index=True)
    # Negative = green yields less = greenium exists.
    out["greenium_bps"] = (
        out["green_yield_pct"] - out["conventional_yield_pct"]) * 100.0
    return out.sort_values(["pair_id", "date"]).reset_index(drop=True)


# ── inference ────────────────────────────────────────────────────────────────

# Bandwidth for the long-run variance, in trading days: about one trading year.
# The rule-of-thumb bandwidth suits weakly dependent data; a daily yield spread is
# not that (autocorrelation 0.86 at 60 days, 0.66 at 120 on the twin-Bund data),
# and a short window reports most of that dependence as independent evidence.
LONG_RUN_LAGS = 250


def long_run_lags(n: int) -> int:
    """
    Bandwidth for a series of ``n`` observations: :data:`LONG_RUN_LAGS`, capped
    at a quarter of the sample so a short series is not handed more lags than it
    can estimate.
    """
    return int(min(LONG_RUN_LAGS, max(n // 4, 0)))


def _bartlett_long_run(h, lags: int) -> float:
    """``sum_t h_t^2 + 2 * sum_l w_l * sum_t h_t h_{t-l}`` with Bartlett weights."""
    h = np.asarray(h, dtype="float64")
    lags = max(0, min(lags, h.size - 1))
    omega = float(h @ h)
    for lag in range(1, lags + 1):
        omega += 2.0 * (1.0 - lag / (lags + 1.0)) * float(h[lag:] @ h[:-lag])
    return omega

def newey_west_lags(n: int) -> int:
    """
    Automatic Bartlett bandwidth, ``floor(4 * (n/100) ** (2/9))``.

    The conventional Newey-West rule of thumb. Returns 0 for n < 2, where no
    autocovariance is estimable.
    """
    if n < 2:
        return 0
    return int(math.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))


def hac_standard_error(series: pd.Series | list[float], lags: int | None = None) -> float:
    """
    Newey-West HAC standard error of the sample mean.

    The long-run variance is ``g0 + 2 * sum_l w_l * g_l`` with Bartlett weights
    ``w_l = 1 - l/(lags+1)``, and ``SE = sqrt(omega / n)``.

    A daily yield spread is highly persistent, so the iid standard error
    understates uncertainty — often by a large factor — and an uncorrected
    t-statistic will manufacture significance. ``lags`` defaults to
    :func:`newey_west_lags`. Falls back to the iid standard error if the HAC
    estimate of the long-run variance is non-positive, which can happen in small
    samples.
    """
    x = pd.Series(list(series), dtype="float64").dropna().to_numpy()
    n = x.size
    if n < 2:
        return float("nan")
    if lags is None:
        lags = newey_west_lags(n)
    lags = max(0, min(lags, n - 1))

    demeaned = x - x.mean()
    gamma0 = float((demeaned @ demeaned) / n)
    if gamma0 == 0.0:
        return 0.0

    omega = gamma0
    for lag in range(1, lags + 1):
        gamma = float((demeaned[lag:] @ demeaned[:-lag]) / n)
        weight = 1.0 - lag / (lags + 1.0)
        omega += 2.0 * weight * gamma

    if omega <= 0.0:                      # small-sample pathology
        omega = gamma0
    return math.sqrt(omega / n)


@dataclass(frozen=True)
class GreeniumEstimate:
    """A greenium estimate for one pair, or pooled across pairs."""
    label: str
    n_obs: int
    mean_bps: float
    median_bps: float
    std_bps: float
    min_bps: float
    max_bps: float
    hac_se_bps: float
    t_stat: float
    share_negative: float

    @property
    def significant_5pct(self) -> bool:
        """Whether the mean differs from zero at roughly 5% on a two-sided test."""
        return abs(self.t_stat) > 1.96

    @property
    def greenium_exists(self) -> bool:
        """A greenium requires a mean that is both negative and distinguishable from zero."""
        return self.mean_bps < 0 and self.significant_5pct


def driscoll_kraay_se(spreads: pd.DataFrame, lags: int | None = None) -> float:
    """
    Standard error of the pooled mean over a panel of pairs (Driscoll-Kraay).

    Residuals are summed across pairs within each date, then the Bartlett long-run
    variance is taken over dates. That handles both autocorrelation within a pair
    and correlation between pairs quoted on the same day — the second of which a
    HAC correction applied to the stacked series cannot see, because same-date
    observations of different pairs sit thousands of rows apart. ``lags`` defaults
    to :func:`long_run_lags` of the number of dates.
    """
    x = spreads["greenium_bps"].astype("float64")
    n = int(x.size)
    if n < 2:
        return float("nan")
    resid = x - x.mean()
    by_date = resid.groupby(spreads["date"]).sum().sort_index().to_numpy()
    if lags is None:
        lags = long_run_lags(by_date.size)
    gamma0 = float(by_date @ by_date)
    if gamma0 == 0.0:
        return 0.0
    omega = _bartlett_long_run(by_date, lags)
    if omega <= 0.0:                      # small-sample pathology
        omega = gamma0
    return math.sqrt(omega) / n


def estimate(spreads: pd.Series | list[float], label: str = "pooled",
             lags: int | None = None) -> GreeniumEstimate:
    """
    Summarise a single pair's spread series with HAC-corrected inference.

    ``t_stat`` uses the Newey-West standard error, not the iid one. For a series
    stacked across several pairs use :func:`estimate_pooled` instead.
    """
    x = pd.Series(list(spreads), dtype="float64").dropna()
    if x.empty:
        raise ValueError("no observations to estimate from")
    return _summarise(x, label, hac_standard_error(x, lags=lags))


def estimate_pooled(spreads: pd.DataFrame, label: str = "POOLED",
                    lags: int | None = None) -> GreeniumEstimate:
    """
    Pooled estimate across pairs, with the Driscoll-Kraay standard error.

    The mean weights every paired observation equally, so pairs with longer
    histories count for more; the equal-weight alternatives are reported in
    :func:`diagnostics`.
    """
    x = spreads["greenium_bps"].astype("float64").dropna()
    if x.empty:
        raise ValueError("no observations to estimate from")
    return _summarise(x, label, driscoll_kraay_se(spreads.loc[x.index], lags))


def _summarise(x: pd.Series, label: str, se: float) -> GreeniumEstimate:
    """Assemble a :class:`GreeniumEstimate` from a series and its standard error."""
    n = int(x.size)
    mean = float(x.mean())
    return GreeniumEstimate(
        label=label,
        n_obs=n,
        mean_bps=mean,
        median_bps=float(x.median()),
        std_bps=float(x.std(ddof=1)) if n > 1 else 0.0,
        min_bps=float(x.min()),
        max_bps=float(x.max()),
        hac_se_bps=se,
        t_stat=(mean / se) if se and se > 0 else float("nan"),
        share_negative=float((x < 0).mean()),
    )


def estimate_by_pair(spreads: pd.DataFrame) -> pd.DataFrame:
    """
    Per-pair estimates plus a pooled row.

    Reporting the distribution across pairs matters: the published range
    (−2 to −20bps) is mostly heterogeneity across issuers and periods rather
    than disagreement about method, so a single pooled mean hides the finding.
    """
    if spreads.empty:
        return pd.DataFrame()

    results, flags = [], {}
    for pair, g in spreads.groupby("pair_id", sort=True):
        results.append(estimate(g["greenium_bps"], label=str(pair),
                                lags=long_run_lags(len(g))))
        exact = bool(g["twin_exact"].all()) if "twin_exact" in g else True
        gap = int(g["maturity_gap_days"].max()) if "maturity_gap_days" in g else 0
        flags[str(pair)] = "exact twin" if exact else f"+/-{gap}d maturity"
    results.append(estimate_pooled(spreads, label="POOLED"))
    all_exact = (bool(spreads["twin_exact"].all())
                 if "twin_exact" in spreads else True)
    flags["POOLED"] = "all exact twins" if all_exact else "mixed"

    return pd.DataFrame([{
        "Pair": r.label,
        "Basis": flags.get(r.label, ""),
        "Obs": r.n_obs,
        "Mean (bps)": round(r.mean_bps, 2),
        "Median (bps)": round(r.median_bps, 2),
        "Std (bps)": round(r.std_bps, 2),
        "Min (bps)": round(r.min_bps, 2),
        "Max (bps)": round(r.max_bps, 2),
        "HAC SE": round(r.hac_se_bps, 3),
        "t-stat": round(r.t_stat, 2) if not math.isnan(r.t_stat) else None,
        "% observations negative": round(r.share_negative * 100, 1),
        "Greenium at 5%": "yes" if r.greenium_exists else "no",
    } for r in results])


def estimate_by_year(spreads: pd.DataFrame) -> pd.DataFrame:
    """
    Pooled estimate per calendar year.

    The trend is the more interesting result than the level: a mean taken over
    the whole sample hides the compression from the 2021 peak, which is the part
    that bears on whether the label carries a funding benefit today.

    Descriptive only: no standard error is reported. Within a single year the
    spread's dependence runs for months, so a long-run variance cannot be
    estimated reliably and a per-year t-statistic would overstate precision.
    """
    if spreads.empty:
        return pd.DataFrame()

    rows = []
    for year, g in spreads.groupby(spreads["date"].dt.year, sort=True):
        x = g["greenium_bps"].astype("float64")
        rows.append({
            "Year": int(year),
            "Obs": int(x.size),
            "Mean (bps)": round(float(x.mean()), 2),
            "Median (bps)": round(float(x.median()), 2),
            "Std (bps)": round(float(x.std(ddof=1)), 2) if x.size > 1 else 0.0,
            "Pairs": int(g["pair_id"].nunique()),
        })
    return pd.DataFrame(rows)


def diagnostics(spreads: pd.DataFrame, pairs: pd.DataFrame) -> dict:
    """
    The numbers that qualify the headline estimate rather than state it.

    * **Inference sensitivity.** The pooled t-statistic at several bandwidths,
      the superseded stacked 10-lag figure, and a t-test across the nine pair
      means, which needs no bandwidth. The last is a cross-check, not independent
      confirmation: the pairs trade in the same market and share common shocks.
    * **Weighting.** The pooled mean weights observations, so long-lived pairs
      count for more. Equal weight per pair and per date are reported alongside.
    * **Dependence.** Autocorrelation of the cross-pair daily average, which is
      why the bandwidth is long, and the cross-pair correlation of daily changes.
    * **Maturity.** Correlation of pair means with years to maturity. Nine points
      cannot separate a label effect from liquidity or repo effects; it only rules
      out a strong tenor pattern.
    """
    series = spreads["greenium_bps"].astype("float64")
    n = int(series.size)
    pooled = estimate_pooled(spreads, "POOLED")
    ordinary_se = float(series.std(ddof=1) / math.sqrt(n))
    stacked_se = hac_standard_error(series)            # the superseded method

    per_pair = spreads.groupby("pair_id")["greenium_bps"].mean()
    pair_t = float(per_pair.mean() / (per_pair.std(ddof=1) / math.sqrt(len(per_pair))))
    daily = spreads.groupby("date")["greenium_bps"].mean().sort_index()
    wide = spreads.pivot_table(index="date", columns="pair_id", values="greenium_bps")
    change_corr = wide.diff().corr().to_numpy()
    upper = change_corr[np.triu_indices_from(change_corr, 1)]

    tenor = pairs.set_index("pair_id")["green_maturity"]
    years_out = (tenor - spreads["date"].max()).dt.days / 365.25
    common = per_pair.index.intersection(years_out.index)
    maturity_corr = (float(per_pair.loc[common].corr(years_out.loc[common]))
                     if len(common) > 2 else float("nan"))

    sensitivity = {f"lags_{lags}": round(pooled.mean_bps / driscoll_kraay_se(spreads, lags), 1)
                   for lags in (60, 120, LONG_RUN_LAGS)}

    return {
        "pooled_mean_bps": round(pooled.mean_bps, 2),
        "pooled_obs": pooled.n_obs,
        "pooled_se_bps": round(pooled.hac_se_bps, 3),
        "pooled_t": round(pooled.t_stat, 1),
        "se_method": "Driscoll-Kraay (residuals summed across pairs by date, Bartlett weights)",
        "bandwidth_lags": LONG_RUN_LAGS,
        "pooled_t_by_bandwidth": sensitivity,
        "pair_means_t": round(pair_t, 1),
        "pair_means_df": int(len(per_pair) - 1),
        "equal_weight_per_pair_mean_bps": round(float(per_pair.mean()), 2),
        "equal_weight_per_date_mean_bps": round(float(daily.mean()), 2),
        "superseded_stacked_nw_t": round(pooled.mean_bps / stacked_se, 1),
        "superseded_stacked_nw_lags": newey_west_lags(n),
        "pooled_ordinary_se_bps": round(ordinary_se, 4),
        "pooled_ordinary_t": round(pooled.mean_bps / ordinary_se, 1),
        "se_inflation_vs_ordinary": round(pooled.hac_se_bps / ordinary_se, 1),
        "daily_average_autocorr": {f"lag_{k}": round(float(daily.autocorr(k)), 2)
                                   for k in (1, 20, 60, 120)},
        "median_cross_pair_corr_of_daily_changes": round(float(np.nanmedian(upper)), 2),
        "share_observations_negative_pct": round(pooled.share_negative * 100, 1),
        "n_dates": int(daily.size),
        "share_dates_daily_average_negative_pct": round(float((daily < 0).mean()) * 100, 1),
        "daily_average_max_bps": round(float(daily.max()), 2),
        "maturity_vs_greenium_corr": round(maturity_corr, 2),
        "n_pairs": int(spreads["pair_id"].nunique()),
        "date_min": f"{spreads['date'].min():%Y-%m-%d}",
        "date_max": f"{spreads['date'].max():%Y-%m-%d}",
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """Estimate the greenium from a pair registry and a yield file."""
    parser = argparse.ArgumentParser(
        description="Estimate the greenium from sovereign green twin bonds.",
        epilog=(
            "Yield data is not committed to this repository. Download the daily "
            "yields for each security in the pair registry from the issuer's "
            "debt management office (Germany: Deutsche Finanzagentur; France: "
            "Agence France Tresor; UK: UK DMO) and save them as a tidy CSV with "
            "columns date,isin,yield_pct. All of these publishers provide the "
            "data free of charge."
        ))
    parser.add_argument("--pairs", required=True,
                        help="CSV of green/conventional twin pairs")
    parser.add_argument("--yields", required=True,
                        help="Tidy CSV of daily yields: date,isin,yield_pct")
    parser.add_argument("--out", help="Optional path to write the per-pair summary CSV")
    parser.add_argument("--out-by-year", help="Optional path to write the yearly CSV")
    parser.add_argument("--out-diagnostics",
                        help="Optional path to write the diagnostics JSON")
    parser.add_argument("--strict", action="store_true",
                        help="Refuse any pair that is not an exact twin "
                             "(coupon and maturity must match on both legs)")
    args = parser.parse_args()

    pairs = load_pairs(args.pairs, strict=args.strict)
    yields = load_yields(args.yields)
    spreads = build_spreads(pairs, yields)

    if spreads.empty:
        raise SystemExit(
            "No pair had both legs quoted on any date. Check that the ISINs in "
            "the pair registry match those in the yield file.")

    summary = estimate_by_pair(spreads)
    print(f"\nPairs: {pairs.shape[0]}  ·  paired observations: {len(spreads)}  ·  "
          f"{spreads['date'].min():%Y-%m-%d} to {spreads['date'].max():%Y-%m-%d}")
    print("\nGreenium = green yield - conventional yield, in bps. "
          "Negative means a greenium.\n")
    print(summary.to_string(index=False))

    n_exact = int(pairs["twin_exact"].sum())
    if n_exact < len(pairs):
        print(f"Note: {len(pairs) - n_exact} of {len(pairs)} pairs are not exact "
              f"twins; their spreads carry a maturity mismatch this estimator "
              f"does not control for.\n")

    pooled = estimate_pooled(spreads, "POOLED")
    print(f"\nPooled: {pooled.mean_bps:.2f}bps "
          f"(Driscoll-Kraay SE {pooled.hac_se_bps:.3f}, t = {pooled.t_stat:.2f}, "
          f"n = {pooled.n_obs})")
    print("Greenium at 5%:", "yes" if pooled.greenium_exists else "no")

    if args.out:
        summary.to_csv(args.out, index=False)
        print(f"\nSummary written to {args.out}")

    if args.out_by_year:
        by_year = estimate_by_year(spreads)
        by_year.to_csv(args.out_by_year, index=False)
        print(f"Yearly series written to {args.out_by_year}")

    if args.out_diagnostics:
        with open(args.out_diagnostics, "w", encoding="utf-8") as fh:
            json.dump(diagnostics(spreads, pairs), fh, indent=2, sort_keys=True)
        print(f"Diagnostics written to {args.out_diagnostics}")


if __name__ == "__main__":
    main()
