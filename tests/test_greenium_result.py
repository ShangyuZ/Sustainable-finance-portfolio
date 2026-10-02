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
import re
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
