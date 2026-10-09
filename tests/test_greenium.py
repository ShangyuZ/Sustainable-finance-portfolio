"""
Tests for the greenium estimator.

No real yield data is committed to this repository, so these tests build
synthetic series with a *known* true greenium and check the estimator recovers
it. All fixtures here are synthetic by construction and are never written to the
repository as data.

The substantive test is :func:`test_hac_se_exceeds_iid_se_under_persistence`.
A daily yield spread is strongly autocorrelated; the iid standard error of its
mean is therefore too small, and an uncorrected t-test manufactures
significance. If the HAC correction stopped working, every estimate would look
more certain than it is — which is the failure mode that matters here.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

import greenium as G


# ── fixtures ─────────────────────────────────────────────────────────────────

def ar1(n: int, mean: float, rho: float = 0.95, sigma: float = 0.4,
        seed: int = 7) -> np.ndarray:
    """
    A persistent AR(1) series around ``mean`` — the shape a real yield spread has.

    Synthetic: used only to check the estimator's arithmetic and inference.
    """
    rng = np.random.default_rng(seed)
    out = np.empty(n)
    x = 0.0
    for i in range(n):
        x = rho * x + rng.normal(0.0, sigma)
        out[i] = mean + x
    return out


def pairs_csv(tmp_path, rows: list[dict]) -> str:
    """Write a pair registry with the real schema."""
    path = tmp_path / "pairs.csv"
    pd.DataFrame(rows)[G.PAIR_COLUMNS].to_csv(path, index=False)
    return str(path)


def exact_pair(pair_id="DE_twin_2030", green="GREEN1", conv="CONV1",
               coupon=0.0, maturity="2030-08-15") -> dict:
    """One exact twin: same coupon, same maturity on both legs."""
    return {"pair_id": pair_id, "green_isin": green, "conventional_isin": conv,
            "green_coupon_pct": coupon, "green_maturity": maturity,
            "conventional_coupon_pct": coupon, "conventional_maturity": maturity,
            "issuer": "Synthetic Sovereign"}


def yields_csv(tmp_path, frames: dict[str, np.ndarray], start="2024-01-01") -> str:
    """Write a tidy yield file from {isin: array}."""
    n = len(next(iter(frames.values())))
    dates = pd.bdate_range(start, periods=n)
    rows = []
    for isin, vals in frames.items():
        rows.append(pd.DataFrame({"date": dates, "isin": isin, "yield_pct": vals}))
    path = tmp_path / "yields.csv"
    pd.concat(rows, ignore_index=True).to_csv(path, index=False)
    return str(path)


# ── pair registry ────────────────────────────────────────────────────────────

def test_committed_template_is_rejected():
    """
    The shipped template must never estimate.

    It exists to be filled in from a primary source; if it silently produced
    numbers, the repository would be publishing results for securities that do
    not exist.
    """
    from pathlib import Path
    template = (Path(__file__).resolve().parent.parent
                / "project1-green-bond-analysis" / "data"
                / "green_twin_pairs.example.csv")
    if not template.exists():
        pytest.skip("template not present")
    with pytest.raises(ValueError, match=G.PLACEHOLDER):
        G.load_pairs(str(template))


def test_load_pairs_accepts_a_populated_registry(tmp_path):
    pairs = G.load_pairs(pairs_csv(tmp_path, [exact_pair()]))
    assert len(pairs) == 1
    assert bool(pairs["twin_exact"].iat[0]) is True
    assert int(pairs["maturity_gap_days"].iat[0]) == 0


def test_load_pairs_rejects_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([{"pair_id": "x", "green_isin": "A"}]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="missing columns"):
        G.load_pairs(str(path))


def test_load_pairs_rejects_duplicate_green_isin(tmp_path):
    rows = [exact_pair(pair_id="a"), exact_pair(pair_id="b", conv="CONV2")]
    with pytest.raises(ValueError, match="duplicate"):
        G.load_pairs(pairs_csv(tmp_path, rows))


def test_load_pairs_rejects_self_pair(tmp_path):
    with pytest.raises(ValueError, match="same ISIN"):
        G.load_pairs(pairs_csv(tmp_path, [exact_pair(green="X", conv="X")]))


def test_load_pairs_rejects_unparseable_maturity(tmp_path):
    bad = exact_pair()
    bad["conventional_maturity"] = "not-a-date"
    with pytest.raises(ValueError, match="unparseable"):
        G.load_pairs(pairs_csv(tmp_path, [bad]))


def test_mismatched_maturity_is_flagged_not_silently_accepted(tmp_path):
    """A non-twin pair must be usable but marked, never passed off as a twin."""
    row = exact_pair()
    row["conventional_maturity"] = "2031-08-15"   # one year later
    pairs = G.load_pairs(pairs_csv(tmp_path, [row]))
    assert bool(pairs["twin_exact"].iat[0]) is False
    assert int(pairs["maturity_gap_days"].iat[0]) == 365


def test_mismatched_coupon_is_flagged(tmp_path):
    row = exact_pair()
    row["conventional_coupon_pct"] = 1.25
    pairs = G.load_pairs(pairs_csv(tmp_path, [row]))
    assert bool(pairs["twin_exact"].iat[0]) is False


def test_strict_mode_refuses_a_non_twin(tmp_path):
    row = exact_pair()
    row["conventional_maturity"] = "2031-08-15"
    with pytest.raises(ValueError, match="not exact twins"):
        G.load_pairs(pairs_csv(tmp_path, [row]), strict=True)


def test_strict_mode_accepts_an_exact_twin(tmp_path):
    pairs = G.load_pairs(pairs_csv(tmp_path, [exact_pair()]), strict=True)
    assert bool(pairs["twin_exact"].all())


# ── spread construction ──────────────────────────────────────────────────────

def test_sign_convention_negative_means_greenium(tmp_path):
    """
    Green yielding LESS must give a NEGATIVE greenium.

    The two artifacts in this repo previously used opposite conventions, so this
    is pinned down by a test rather than by prose.
    """
    pairs = G.load_pairs(pairs_csv(tmp_path, [exact_pair()]))
    yields = G.load_yields(yields_csv(tmp_path, {
        "GREEN1": np.full(30, 2.40),      # green yields less
        "CONV1": np.full(30, 2.45),
    }))
    spreads = G.build_spreads(pairs, yields)
    assert (spreads["greenium_bps"] < 0).all()
    assert spreads["greenium_bps"].iat[0] == pytest.approx(-5.0, abs=1e-9)


def test_spread_is_in_basis_points(tmp_path):
    """A 0.01 percentage-point difference is 1bp."""
    pairs = G.load_pairs(pairs_csv(tmp_path, [exact_pair()]))
    yields = G.load_yields(yields_csv(tmp_path, {
        "GREEN1": np.full(10, 2.00), "CONV1": np.full(10, 2.01)}))
    assert G.build_spreads(pairs, yields)["greenium_bps"].iat[0] == pytest.approx(-1.0)


def test_days_with_only_one_leg_are_dropped(tmp_path):
    """
    A stale leg manufactures a spread that was never observable.

    The green leg is missing for the last 5 days; those days must not appear.
    """
    pairs = G.load_pairs(pairs_csv(tmp_path, [exact_pair()]))
    green = np.full(20, 2.40)
    green[-5:] = np.nan
    yields = G.load_yields(yields_csv(tmp_path, {
        "GREEN1": green, "CONV1": np.full(20, 2.45)}))
    assert len(G.build_spreads(pairs, yields)) == 15


def test_pair_with_no_quotes_is_skipped(tmp_path):
    pairs = G.load_pairs(pairs_csv(tmp_path, [exact_pair(green="ABSENT")]))
    yields = G.load_yields(yields_csv(tmp_path, {"CONV1": np.full(10, 2.45)}))
    assert G.build_spreads(pairs, yields).empty


def test_empty_spreads_keeps_the_schema(tmp_path):
    pairs = G.load_pairs(pairs_csv(tmp_path, [exact_pair(green="ABSENT")]))
    yields = G.load_yields(yields_csv(tmp_path, {"CONV1": np.full(5, 2.0)}))
    out = G.build_spreads(pairs, yields)
    assert out.empty
    assert "greenium_bps" in out.columns


# ── HAC inference: the part that matters ─────────────────────────────────────

def test_hac_se_exceeds_iid_se_under_persistence():
    """
    With positive autocorrelation the HAC standard error must be LARGER.

    If this inverts, every greenium estimate looks more statistically certain
    than the data supports — the one failure mode of this module that would
    produce a confident wrong answer rather than an obvious error.
    """
    x = ar1(600, mean=-3.0, rho=0.95)
    iid_se = float(pd.Series(x).std(ddof=1) / math.sqrt(len(x)))
    hac_se = G.hac_standard_error(x)
    assert hac_se > iid_se * 1.5


def test_hac_se_matches_iid_se_for_white_noise():
    """With no autocorrelation the correction should be roughly a no-op."""
    rng = np.random.default_rng(3)
    x = rng.normal(-2.0, 1.0, 4000)
    iid_se = float(pd.Series(x).std(ddof=1) / math.sqrt(len(x)))
    assert G.hac_standard_error(x) == pytest.approx(iid_se, rel=0.25)


def test_hac_se_of_a_constant_series_is_zero():
    assert G.hac_standard_error([2.0] * 50) == 0.0


def test_hac_se_is_nan_for_a_single_observation():
    assert math.isnan(G.hac_standard_error([1.0]))


def test_hac_se_is_positive_and_finite():
    se = G.hac_standard_error(ar1(300, mean=-4.0))
    assert se > 0 and math.isfinite(se)


def test_hac_lag_respects_the_sample_size():
    assert G.newey_west_lags(1) == 0
    assert G.newey_west_lags(100) == 4
    assert G.newey_west_lags(1000) >= G.newey_west_lags(100)


def test_hac_lags_cannot_exceed_available_lags():
    """An over-long bandwidth must be clamped, not raise."""
    assert G.hac_standard_error([1.0, 2.0, 3.0], lags=99) >= 0.0


# ── estimates ────────────────────────────────────────────────────────────────

def test_estimate_recovers_a_known_greenium():
    """A series centred on -4bps must estimate close to -4bps."""
    est = G.estimate(ar1(2000, mean=-4.0, rho=0.9), "synthetic")
    assert est.mean_bps == pytest.approx(-4.0, abs=0.5)
    assert est.n_obs == 2000


def test_estimate_reports_the_distribution_not_just_the_mean():
    est = G.estimate(ar1(400, mean=-5.0), "synthetic")
    assert est.min_bps < est.mean_bps < est.max_bps
    assert est.std_bps > 0
    assert 0.0 <= est.share_negative <= 1.0


def test_greenium_requires_negative_and_significant():
    """A clearly negative, well-sampled mean counts as a greenium."""
    est = G.estimate(ar1(2000, mean=-8.0, rho=0.5), "synthetic")
    assert est.mean_bps < 0
    assert est.significant_5pct
    assert est.greenium_exists


def test_a_positive_mean_is_not_a_greenium():
    """Green yielding MORE is not a greenium, however significant."""
    est = G.estimate(ar1(2000, mean=+8.0, rho=0.5), "synthetic")
    assert est.mean_bps > 0
    assert not est.greenium_exists


def test_a_noisy_zero_mean_is_not_a_greenium():
    """No effect must not be reported as one."""
    rng = np.random.default_rng(11)
    est = G.estimate(rng.normal(0.0, 5.0, 500), "synthetic")
    assert not est.greenium_exists


def test_estimate_rejects_an_empty_series():
    with pytest.raises(ValueError, match="no observations"):
        G.estimate([])


def test_estimate_t_stat_uses_the_hac_se():
    est = G.estimate(ar1(800, mean=-6.0, rho=0.95), "synthetic")
    assert est.t_stat == pytest.approx(est.mean_bps / est.hac_se_bps, rel=1e-9)


# ── summary table ────────────────────────────────────────────────────────────

def test_estimate_by_pair_reports_each_pair_and_a_pooled_row(tmp_path):
    rows = [exact_pair(pair_id="p1", green="G1", conv="C1"),
            exact_pair(pair_id="p2", green="G2", conv="C2", maturity="2032-05-15")]
    pairs = G.load_pairs(pairs_csv(tmp_path, rows))
    yields = G.load_yields(yields_csv(tmp_path, {
        "G1": np.full(40, 2.40), "C1": np.full(40, 2.45),
        "G2": np.full(40, 3.00), "C2": np.full(40, 3.02),
    }))
    summary = G.estimate_by_pair(G.build_spreads(pairs, yields))
    assert list(summary["Pair"]) == ["p1", "p2", "POOLED"]
    assert summary.loc[summary["Pair"] == "p1", "Mean (bps)"].iat[0] == pytest.approx(-5.0)
    assert summary.loc[summary["Pair"] == "p2", "Mean (bps)"].iat[0] == pytest.approx(-2.0)


def test_summary_marks_whether_the_basis_is_an_exact_twin(tmp_path):
    """
    An estimate from a non-twin pair must not read like one from a twin.

    The whole methodological claim is that twins need no matching assumptions,
    so the output has to say which pairs actually are twins.
    """
    row = exact_pair(pair_id="loose")
    row["conventional_maturity"] = "2031-08-15"
    pairs = G.load_pairs(pairs_csv(tmp_path, [row]))
    yields = G.load_yields(yields_csv(tmp_path, {
        "GREEN1": np.full(30, 2.40), "CONV1": np.full(30, 2.45)}))
    summary = G.estimate_by_pair(G.build_spreads(pairs, yields))
    basis = summary.loc[summary["Pair"] == "loose", "Basis"].iat[0]
    assert "maturity" in basis
    assert "exact twin" != basis


def test_summary_is_empty_for_no_spreads():
    assert G.estimate_by_pair(pd.DataFrame()).empty


# ── yield loading ────────────────────────────────────────────────────────────

def test_load_yields_drops_unparseable_rows(tmp_path):
    path = tmp_path / "y.csv"
    pd.DataFrame({
        "date": ["2024-01-01", "not-a-date", "2024-01-03"],
        "isin": ["A", "A", "A"],
        "yield_pct": [2.0, 2.1, "oops"],
    }).to_csv(path, index=False)
    out = G.load_yields(str(path))
    assert len(out) == 1
    assert out["yield_pct"].iat[0] == pytest.approx(2.0)


def test_load_yields_rejects_missing_columns(tmp_path):
    path = tmp_path / "y.csv"
    pd.DataFrame({"date": ["2024-01-01"], "isin": ["A"]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="missing columns"):
        G.load_yields(str(path))


# ── panel inference ──────────────────────────────────────────────────────────

def _panel(series_by_pair: dict[str, list[float]]) -> pd.DataFrame:
    """Stack equal-length series into the spread-panel shape, one row per pair-date."""
    frames = []
    for pair, values in series_by_pair.items():
        dates = pd.bdate_range("2022-01-03", periods=len(values))
        frames.append(pd.DataFrame({"pair_id": pair, "date": dates,
                                    "greenium_bps": values}))
    return pd.concat(frames, ignore_index=True)


def test_driscoll_kraay_matches_newey_west_for_one_pair():
    """With a single pair there is no cross-section, so the two must agree."""
    x = list(ar1(600, mean=-3.0, rho=0.9))
    assert G.driscoll_kraay_se(_panel({"a": x}), lags=20) == pytest.approx(
        G.hac_standard_error(x, lags=20), rel=1e-9)


def test_duplicated_pairs_add_no_information():
    """
    Two pairs that move identically are one pair's worth of evidence.

    A HAC correction on the stacked series cannot see that — the duplicates sit
    hundreds of rows apart — and shrinks the standard error as if the sample had
    doubled. That is the failure the panel estimator exists to prevent.
    """
    x = list(ar1(600, mean=-3.0, rho=0.9))
    one = G.driscoll_kraay_se(_panel({"a": x}), lags=20)
    two = G.driscoll_kraay_se(_panel({"a": x, "b": x}), lags=20)
    assert two == pytest.approx(one, rel=1e-9)
    stacked = G.hac_standard_error(x + x, lags=20)
    assert stacked < one


def test_long_run_lags_cap_at_a_quarter_of_the_sample():
    assert G.long_run_lags(100) == 25
    assert G.long_run_lags(10_000) == G.LONG_RUN_LAGS


def test_pooled_estimate_uses_the_panel_standard_error():
    panel = _panel({"a": list(ar1(400, mean=-2.0, rho=0.8)),
                    "b": list(ar1(400, mean=-1.0, rho=0.8, seed=11))})
    est = G.estimate_pooled(panel)
    assert est.hac_se_bps == pytest.approx(G.driscoll_kraay_se(panel), rel=1e-12)
    assert est.n_obs == 800

