"""
Pins the committed greenium estimate.

`test_greenium.py` checks the estimator's arithmetic against synthetic series.
This file checks the *published result* — the figures quoted in the investment
brief and in FINDINGS.md — against the committed data, so the documents and the
data cannot drift apart. If the yield file is refreshed and the estimate moves,
these tests fail and the write-ups get updated deliberately rather than silently.

Skips cleanly when the fetched data is absent, since it is reproducible with
`scripts/fetch_bund_yields.py` but not required to run the rest of the suite.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

import greenium as G

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "project1-green-bond-analysis" / "data"
PAIRS = DATA / "green_twin_pairs.csv"
YIELDS = DATA / "bund_yields.csv"
BRIEF = ROOT / "project1-green-bond-analysis" / "brief" / "Green_Bond_Market_Brief.md"

# The published estimate. Tolerances are wide enough to absorb a few extra days
# of data but tight enough that a methodology change fails the test.
PUBLISHED_POOLED_BPS = -1.50
PUBLISHED_N_PAIRS = 9


@pytest.fixture(scope="module")
def spreads() -> pd.DataFrame:
    if not (PAIRS.exists() and YIELDS.exists()):
        pytest.skip("fetched Bund data not present — run scripts/fetch_bund_yields.py")
    pairs = G.load_pairs(str(PAIRS), strict=True)
    return G.build_spreads(pairs, G.load_yields(str(YIELDS)))


@pytest.fixture(scope="module")
def pooled(spreads) -> G.GreeniumEstimate:
    return G.estimate(spreads["greenium_bps"], "POOLED")


# ── the pairs are genuine exact twins ────────────────────────────────────────

def test_every_pair_is_an_exact_twin():
    """
    The whole methodological claim rests on this.

    If a pair's coupon or maturity differs, the yield difference is no longer the
    greenium by construction and the estimate inherits a matching assumption.
    """
    if not PAIRS.exists():
        pytest.skip("pairs file not present")
    pairs = G.load_pairs(str(PAIRS), strict=True)   # strict=True raises on non-twins
    assert len(pairs) == PUBLISHED_N_PAIRS
    assert bool(pairs["twin_exact"].all())
    assert (pairs["maturity_gap_days"] == 0).all()


def test_pairs_have_distinct_legs():
    if not PAIRS.exists():
        pytest.skip("pairs file not present")
    pairs = G.load_pairs(str(PAIRS))
    assert (pairs["green_isin"] != pairs["conventional_isin"]).all()
    assert pairs["green_isin"].nunique() == len(pairs)
    assert pairs["conventional_isin"].nunique() == len(pairs)


def test_all_legs_are_german_federal_isins():
    if not PAIRS.exists():
        pytest.skip("pairs file not present")
    pairs = G.load_pairs(str(PAIRS))
    for col in ("green_isin", "conventional_isin"):
        assert pairs[col].str.match(r"^DE[0-9A-Z]{10}$").all()


# ── the published estimate ───────────────────────────────────────────────────

def test_pooled_estimate_matches_the_published_figure(pooled):
    assert pooled.mean_bps == pytest.approx(PUBLISHED_POOLED_BPS, abs=0.25)


def test_greenium_is_negative_and_significant(pooled):
    """Negative and distinguishable from zero — both are required."""
    assert pooled.mean_bps < 0
    assert pooled.significant_5pct
    assert pooled.greenium_exists


def test_sample_is_large_enough_to_report(pooled):
    assert pooled.n_obs > 5_000


def test_spread_is_negative_on_almost_every_day(pooled):
    """Persistence is the striking feature; a flaky sign would undercut the claim."""
    assert pooled.share_negative > 0.95


def test_hac_standard_error_exceeds_the_iid_one(spreads):
    """
    On this data the HAC correction roughly triples the standard error.

    Reported in the brief as 3.3x. If this inverted, every figure in the write-up
    would be overconfident.
    """
    x = spreads["greenium_bps"]
    iid = float(x.std(ddof=1) / math.sqrt(len(x)))
    assert G.hac_standard_error(x) > iid * 2.0


def test_every_pair_shows_a_negative_mean(spreads):
    """The brief states the per-pair range as -0.65 to -2.40bps, all negative."""
    per_pair = spreads.groupby("pair_id")["greenium_bps"].mean()
    assert (per_pair < 0).all()
    assert per_pair.min() > -5.0      # no pair is an outlier by an order of magnitude


def test_no_maturity_term_structure(spreads):
    """
    The brief claims the greenium is a label effect, not a maturity artefact,
    citing a correlation of 0.11 between years-to-maturity and mean greenium.
    """
    pairs = G.load_pairs(str(PAIRS))
    years = ((pd.to_datetime(pairs["green_maturity"]) - pd.Timestamp("2026-10-01"))
             .dt.days / 365.25)
    means = spreads.groupby("pair_id")["greenium_bps"].mean()
    merged = pd.DataFrame({"pair_id": pairs["pair_id"], "years": years}).merge(
        means.rename("mean_bps").reset_index(), on="pair_id")
    assert abs(merged["years"].corr(merged["mean_bps"])) < 0.5


# ── the compression finding ──────────────────────────────────────────────────

def test_greenium_has_compressed_since_2021(spreads):
    """
    The brief's headline trend: roughly an 80% compression from the 2021 peak.

    This is the finding most worth protecting, because it is the one a reader is
    most likely to quote.
    """
    by_year = spreads.assign(year=pd.to_datetime(spreads["date"]).dt.year) \
                     .groupby("year")["greenium_bps"].mean()
    assert 2021 in by_year.index and 2025 in by_year.index
    assert by_year.loc[2021] < -3.0      # clearly wide in 2021
    assert by_year.loc[2025] > -1.5      # clearly narrow by 2025
    assert by_year.loc[2025] > by_year.loc[2021]


# ── the brief must quote what the data says ──────────────────────────────────

def test_brief_quotes_the_computed_estimate(pooled):
    if not BRIEF.exists():
        pytest.skip("brief not present")
    # The brief uses a typographic minus (U+2212); normalise before comparing.
    text = BRIEF.read_text(encoding="utf-8").replace("\u2212", "-")
    assert f"{pooled.mean_bps:.2f}" in text, (
        f"brief does not quote the computed pooled estimate {pooled.mean_bps:.2f}bps")
    assert f"{pooled.n_obs:,}" in text, "brief does not quote the observation count"


def test_brief_no_longer_disclaims_an_estimate():
    """§4 used to say no empirical claim was made. It now makes one."""
    if not BRIEF.exists():
        pytest.skip("brief not present")
    assert "I make no empirical claim here" not in BRIEF.read_text(encoding="utf-8")
