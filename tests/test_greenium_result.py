"""
Pins the committed greenium estimate.

`test_greenium.py` checks the estimator's arithmetic against synthetic series.
This file checks the *published result* — the figures quoted in the investment
brief and in FINDINGS.md — against the committed estimator output, so the
documents and the numbers cannot drift apart.

The daily Bund yields are not committed: Finanzagentur reserves all rights in
their published data (see DATA.md). What is committed is this project's own
derived output — the per-pair summary, the yearly series and the diagnostics —
and every figure in the brief is checked against those. Running
`scripts/fetch_bund_yields.py` restores the yields from the issuer in one
command, and the handful of tests that need record-level data then run too.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pytest

import greenium as G

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "project1-green-bond-analysis" / "data"
PAIRS = DATA / "green_twin_pairs.csv"
YIELDS = DATA / "bund_yields.csv"
SUMMARY = DATA / "greenium_summary.csv"
BY_YEAR = DATA / "greenium_by_year.csv"
DIAGNOSTICS = DATA / "greenium_diagnostics.json"
BRIEF = ROOT / "project1-green-bond-analysis" / "brief" / "Green_Bond_Market_Brief.md"

# The published estimate. Tolerances are wide enough to absorb a few extra days
# of data but tight enough that a methodology change fails the test.
PUBLISHED_POOLED_BPS = -1.50
PUBLISHED_N_PAIRS = 9


# ── the committed estimator output ───────────────────────────────────────────

@pytest.fixture(scope="module")
def summary() -> pd.DataFrame:
    """Per-pair and pooled estimates, as published."""
    assert SUMMARY.exists(), f"{SUMMARY} is a committed artifact and must be present"
    return pd.read_csv(SUMMARY)


@pytest.fixture(scope="module")
def pooled_row(summary) -> pd.Series:
    """The pooled row of the published summary."""
    hit = summary.loc[summary["Pair"] == "POOLED"]
    assert len(hit) == 1, "the summary must carry exactly one POOLED row"
    return hit.iloc[0]


@pytest.fixture(scope="module")
def by_year() -> pd.DataFrame:
    """The published yearly series."""
    assert BY_YEAR.exists(), f"{BY_YEAR} is a committed artifact and must be present"
    return pd.read_csv(BY_YEAR)


@pytest.fixture(scope="module")
def diagnostics() -> dict:
    """The published diagnostics that qualify the estimate."""
    assert DIAGNOSTICS.exists(), f"{DIAGNOSTICS} is a committed artifact and must be present"
    return json.loads(DIAGNOSTICS.read_text(encoding="utf-8"))


# ── record-level data, for whoever has a licensed copy ───────────────────────

@pytest.fixture(scope="module")
def spreads() -> pd.DataFrame | None:
    """
    The daily spread panel, if the fetched yields are present.

    ``None`` in CI: the yields are not redistributed. The published figures are
    checked against the committed estimator output regardless; these tests add
    the end-to-end recomputation on top, for anyone who has run the fetcher.
    """
    if not (PAIRS.exists() and YIELDS.exists()):
        return None
    pairs = G.load_pairs(str(PAIRS), strict=True)
    return G.build_spreads(pairs, G.load_yields(str(YIELDS)))


def _require(spreads):
    """Skip with an actionable reason when the fetched yields are absent."""
    if spreads is None:
        pytest.skip("Bund yields not present — run scripts/fetch_bund_yields.py "
                    "(not redistributed; see DATA.md)")
    return spreads


# ── the pairs are genuine exact twins ────────────────────────────────────────

def test_every_pair_is_an_exact_twin(summary):
    """
    The whole methodological claim rests on this.

    If a pair's coupon or maturity differs, the yield difference is no longer the
    greenium by construction and the estimate inherits a matching assumption.
    Read from the published summary, which records the basis of every pair it
    reports, so the claim is checked against what was actually published.
    """
    pairs = summary.loc[summary["Pair"] != "POOLED"]
    assert len(pairs) == PUBLISHED_N_PAIRS
    assert (pairs["Basis"] == "exact twin").all(), (
        "a pair the summary does not call an exact twin: "
        + ", ".join(pairs.loc[pairs["Basis"] != "exact twin", "Pair"]))


def test_pooled_row_covers_only_exact_twins(summary, pooled_row):
    """The pooled figure must not quietly mix in a non-twin pair."""
    assert pooled_row["Basis"] == "all exact twins"
    pairs = summary.loc[summary["Pair"] != "POOLED"]
    assert pooled_row["Obs"] == pairs["Obs"].sum(), (
        "pooled observation count does not equal the sum of its pairs")


def test_pair_ids_are_distinct_and_well_formed(summary):
    """Each pair is identified by its maturity and coupon, and appears once."""
    pairs = summary.loc[summary["Pair"] != "POOLED", "Pair"]
    assert pairs.nunique() == len(pairs)
    assert pairs.str.match(r"^\d{4}-\d{2}_\d+\.\d+pct$").all(), (
        "malformed pair id: " + ", ".join(
            pairs[~pairs.str.match(r"^\d{4}-\d{2}_\d+\.\d+pct$")]))


def test_pair_registry_is_genuine_when_present(spreads):
    """
    With a fetched registry present, re-verify the twin structure from the ISINs.

    This is the check the published summary cannot make for itself: that both
    legs are distinct German federal securities. It needs the registry, which is
    regenerated by the fetcher rather than committed.
    """
    _require(spreads)
    pairs = G.load_pairs(str(PAIRS), strict=True)   # strict=True raises on non-twins
    assert len(pairs) == PUBLISHED_N_PAIRS
    assert bool(pairs["twin_exact"].all())
    assert (pairs["maturity_gap_days"] == 0).all()
    assert (pairs["green_isin"] != pairs["conventional_isin"]).all()
    assert pairs["green_isin"].nunique() == len(pairs)
    assert pairs["conventional_isin"].nunique() == len(pairs)
    for col in ("green_isin", "conventional_isin"):
        assert pairs[col].str.match(r"^DE[0-9A-Z]{10}$").all()


# ── the published estimate ───────────────────────────────────────────────────

def test_pooled_estimate_matches_the_published_figure(pooled_row):
    assert pooled_row["Mean (bps)"] == pytest.approx(PUBLISHED_POOLED_BPS, abs=0.25)


def test_greenium_is_negative_and_significant(pooled_row):
    """Negative and distinguishable from zero — both are required."""
    assert pooled_row["Mean (bps)"] < 0
    assert abs(pooled_row["t-stat"]) > 1.96
    assert pooled_row["Greenium at 5%"] == "yes"


def test_sample_is_large_enough_to_report(pooled_row):
    assert pooled_row["Obs"] > 5_000


def test_spread_is_negative_on_almost_every_day(pooled_row):
    """Persistence is the striking feature; a flaky sign would undercut the claim."""
    assert pooled_row["% days negative"] > 95.0


def test_reported_precision_accounts_for_persistence_and_pooling(diagnostics):
    """
    The published standard error must be the panel-robust one.

    The first version stacked nine bonds' histories and applied a 10-lag
    Newey-West correction, reporting t = -28.7. That missed most of the spread's
    persistence (still 0.66 autocorrelated at 120 trading days) and treated pairs
    quoted on the same date as independent. If the headline t-statistic drifts
    back towards the stacked figure, the method has regressed.
    """
    assert diagnostics["bandwidth_lags"] >= 120
    assert "Driscoll-Kraay" in diagnostics["se_method"]
    assert abs(diagnostics["pooled_t"]) < abs(diagnostics["superseded_stacked_nw_t"]) / 3
    assert abs(diagnostics["superseded_stacked_nw_t"]) < abs(diagnostics["pooled_ordinary_t"])
    assert diagnostics["daily_average_autocorr"]["lag_120"] > 0.5, (
        "the long bandwidth is justified by long-lived dependence; if that has "
        "gone, revisit the bandwidth rather than keep it by default")


def test_sign_survives_every_inference_choice(diagnostics):
    """
    The claim the write-up makes is the sign, not the precision.

    It must hold at every bandwidth reported and under the bandwidth-free t-test
    across pair means.
    """
    for label, t in diagnostics["pooled_t_by_bandwidth"].items():
        assert t < -1.96, f"greenium not significant at bandwidth {label}: t = {t}"
    assert diagnostics["pair_means_t"] < -2.31   # 5% two-sided, 8 df
    assert diagnostics["pair_means_df"] == PUBLISHED_N_PAIRS - 1


def test_headline_depends_on_weighting_and_says_so(diagnostics):
    """The alternative weightings are published, and all three are negative."""
    for key in ("pooled_mean_bps", "equal_weight_per_pair_mean_bps",
                "equal_weight_per_date_mean_bps"):
        assert diagnostics[key] < 0


def test_robust_estimator_reproduces_the_published_se(spreads, diagnostics):
    """With the yields present, recompute the Driscoll-Kraay standard error end to end."""
    _require(spreads)
    assert G.driscoll_kraay_se(spreads, G.LONG_RUN_LAGS) == pytest.approx(
        diagnostics["pooled_se_bps"], abs=0.01)


def test_every_pair_shows_a_negative_mean(summary):
    """The brief states the per-pair range as -0.65 to -2.40bps, all negative."""
    per_pair = summary.loc[summary["Pair"] != "POOLED", "Mean (bps)"]
    assert (per_pair < 0).all()
    assert per_pair.min() > -5.0      # no pair is an outlier by an order of magnitude
    assert per_pair.max() <= -0.5     # and none is indistinguishable from zero


def test_no_strong_maturity_pattern(diagnostics):
    """
    The brief reports a correlation of 0.11 between years-to-maturity and pair
    means. Across nine pairs that only rules out a strong tenor pattern; it does
    not establish a pure label effect, and the brief must not say it does.
    """
    assert abs(diagnostics["maturity_vs_greenium_corr"]) < 0.5


def test_published_summary_is_reproducible(spreads, summary):
    """
    With the yields present, the committed summary must be exactly reproducible.

    This is what makes the committed output trustworthy as a stand-in for the
    data: re-running the estimator on the fetched yields reproduces it.
    """
    _require(spreads)
    fresh = G.estimate_by_pair(spreads)
    pd.testing.assert_frame_equal(
        fresh.reset_index(drop=True), summary.reset_index(drop=True),
        check_dtype=False, check_column_type=False)


# ── the compression finding ──────────────────────────────────────────────────

def test_greenium_has_compressed_since_2021(by_year):
    """
    The brief's headline trend: roughly an 80% compression from the 2021 peak.

    This is the finding most worth protecting, because it is the one a reader is
    most likely to quote.
    """
    means = by_year.set_index("Year")["Mean (bps)"]
    assert 2021 in means.index and 2025 in means.index
    assert means.loc[2021] < -3.0      # clearly wide in 2021
    assert means.loc[2025] > -1.5      # clearly narrow by 2025
    assert means.loc[2025] > means.loc[2021]
    compression = 1 - means.loc[2025] / means.loc[2021]
    assert compression == pytest.approx(0.8, abs=0.1), (
        f"the brief claims roughly 80% compression; this is {compression:.0%}")


def test_yearly_series_reconciles_with_the_pooled_row(by_year, pooled_row):
    """The yearly breakdown must account for every pooled observation."""
    assert by_year["Obs"].sum() == pooled_row["Obs"]
    assert by_year["Year"].is_monotonic_increasing
    assert (by_year["Mean (bps)"] < 0).all(), "every year shows a greenium"


def test_brief_quotes_the_yearly_series(by_year):
    """
    Every row of the brief's compression table must match the computed series.

    The table is the brief's most quotable exhibit, so each figure in it is
    pinned rather than just the trend direction.
    """
    if not BRIEF.exists():
        pytest.skip("brief not present")
    text = BRIEF.read_text(encoding="utf-8").replace("\u2212", "-")
    for _, row in by_year.iterrows():
        assert f"{row['Mean (bps)']:.2f}bps" in text, (
            f"brief does not quote the {int(row['Year'])} mean "
            f"{row['Mean (bps)']:.2f}bps")
        assert f"{int(row['Obs']):,}" in text, (
            f"brief does not quote the {int(row['Year'])} observation count")


def test_published_yearly_series_is_reproducible(spreads, by_year):
    """With the yields present, the committed yearly series must reproduce."""
    _require(spreads)
    fresh = G.estimate_by_year(spreads)
    pd.testing.assert_frame_equal(
        fresh.reset_index(drop=True), by_year.reset_index(drop=True),
        check_dtype=False, check_column_type=False)


# ── the brief must quote what the data says ──────────────────────────────────

def test_brief_quotes_the_computed_estimate(pooled_row, diagnostics):
    if not BRIEF.exists():
        pytest.skip("brief not present")
    # The brief uses a typographic minus (U+2212); normalise before comparing.
    text = BRIEF.read_text(encoding="utf-8").replace("\u2212", "-")
    assert f"{pooled_row['Mean (bps)']:.2f}" in text, (
        f"brief does not quote the pooled estimate {pooled_row['Mean (bps)']:.2f}bps")
    assert f"{int(pooled_row['Obs']):,}" in text, "brief does not quote the observation count"
    assert f"{abs(pooled_row['t-stat']):.1f}" in text, "brief does not quote the t-statistic"
    assert f"{diagnostics['n_pairs']}" in text, "brief does not quote the pair count"


# Matches any form of "no empirical/greenium estimate is claimed". The earlier
# guard pinned one exact sentence, so the same claim reworded in another section
# slipped through — which is how the brief ended up stating a result in section 4
# and disclaiming one in section 5.
STALE_DISCLAIMER = re.compile(
    r"no\s+(global\s+)?(empirical|greenium)[^.]{0,40}\b(estimate|claim)", re.I)

# A qualified disclaimer is correct and must stay: the estimate really is German
# sovereign only. Only the unqualified form is the contradiction.
QUALIFIED = re.compile(r"german|sovereign only|does not generalise", re.I)


def _unqualified_matches(text: str) -> list[str]:
    """
    Every unqualified disclaimer in ``text``, scoped to the sentence it sits in.

    Checking qualification across a whole cell or paragraph is too coarse: a long
    workbook note can disclaim an estimate in one sentence and say "German
    sovereign only" three sentences later, and the second would wrongly excuse
    the first. Mutation testing caught exactly that.
    """
    found = []
    for match in STALE_DISCLAIMER.finditer(text):
        start = max(text.rfind(".", 0, match.start()) + 1, 0)
        end = text.find(".", match.end())
        sentence = text[start:end if end != -1 else len(text)].strip()
        if not QUALIFIED.search(sentence):
            found.append(" ".join(sentence.split())[:110])
    return found


@pytest.mark.parametrize("rel", [
    "project1-green-bond-analysis/brief/Green_Bond_Market_Brief.md",
    "project1-green-bond-analysis/README.md",
    "README.md",
    "FINDINGS.md",
    "project1-green-bond-analysis/scripts/greenium.py",
    "project1-green-bond-analysis/scripts/process_data.py",
])
def test_no_unqualified_disclaimer_of_the_estimate(rel):
    """
    No document may still say an estimate is not claimed.

    The repository now publishes one. A qualified statement ("German sovereign
    only") is fine and expected; an unqualified one contradicts the result.
    """
    path = ROOT / rel
    if not path.exists():
        pytest.skip(f"{rel} not present")
    offending = _unqualified_matches(path.read_text(encoding="utf-8"))
    assert not offending, f"stale disclaimer in {rel}:\n  " + "\n  ".join(offending)


def test_workbook_cells_do_not_disclaim_the_estimate():
    """
    The generated workbook is checked too, because its text is invisible to a
    plain file search — the same blind spot that hid four vendor references
    inside this spreadsheet for months.
    """
    workbook = ROOT / "project1-green-bond-analysis" / "Green_Bond_Market_Analysis.xlsx"
    if not workbook.exists():
        pytest.skip("workbook not present")
    from openpyxl import load_workbook
    offending = []
    for sheet in load_workbook(workbook).worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if not isinstance(cell.value, str):
                    continue
                for hit in _unqualified_matches(cell.value):
                    offending.append(f"{sheet.title}!{cell.coordinate}: {hit}")
    assert not offending, "stale disclaimer in workbook cells:\n  " + "\n  ".join(offending)


def test_the_qualified_limitation_is_still_stated():
    """
    The opposite failure: silently dropping the caveat would overclaim.
    The estimate is German sovereign only and the brief must say so.
    """
    if not BRIEF.exists():
        pytest.skip("brief not present")
    text = BRIEF.read_text(encoding="utf-8").lower()
    assert "german sovereign only" in text or "german sovereign" in text
