"""
Tests for the committed aggregates.

These files are what the repository publishes in place of the source extract,
which CBI's terms of use do not permit redistributing (see DATA.md). That makes
them the thing worth testing hardest: every figure in the README, the workbook
and the investment brief is computed from them, so if they are wrong or
internally inconsistent, every published number is wrong with them.

Three layers:

1. **Invariants** — breakdowns reconcile to the same total, shares sum to 100,
   rankings are ordered, the precise and rounded tables agree. These hold
   without any access to the source data, so they run everywhere.
2. **Published figures** — the specific numbers the write-ups quote are pinned,
   so refreshing the data fails the build rather than silently invalidating the
   documents.
3. **Round-trip** — given a licensed copy of the extract, recomputing every
   table reproduces the committed files exactly. This is what justifies using
   the aggregates as a stand-in for the data, and it skips when the extract is
   absent because then there is nothing to compare against.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from aggregates import METRICS_FILE, PRECISE_KEYS, TABLES, Aggregates

ROOT = Path(__file__).resolve().parent.parent
PROJECT1 = ROOT / "project1-green-bond-analysis"
AGG_DIR = PROJECT1 / "data" / "aggregates"

# The figures the README, the workbook and the brief quote.
PUBLISHED_DEALS = 732
PUBLISHED_VOLUME_BN = 650.04
PUBLISHED_SOVEREIGN_SHARE = 82.49
PUBLISHED_YEARS = (2015, 2024)


# ── the files are all present and readable ───────────────────────────────────

@pytest.mark.parametrize("filename", sorted(TABLES.values()) + [METRICS_FILE])
def test_every_aggregate_file_is_committed(filename):
    """A missing file would make the model unbuildable from a fresh clone."""
    assert (AGG_DIR / filename).exists(), (
        f"{filename} is missing — regenerate with scripts/export_aggregates.py")


def test_aggregates_directory_documents_itself():
    """Anyone finding these files needs to know what they are and are not."""
    readme = (AGG_DIR / "README.md").read_text(encoding="utf-8").lower()
    assert "not redistributed" in readme
    assert "climate bonds" in readme
    assert "export_aggregates" in readme, "the README must say how to regenerate them"


def test_no_table_is_empty(agg):
    for name, frame in agg.frames().items():
        assert len(frame) > 0, f"{name} is empty"


# ── invariants ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("table", ["sector", "theme"])
def test_breakdowns_reconcile_to_the_headline_total(agg, table):
    """Every breakdown must sum back to the published total — no dropped rows."""
    frame = getattr(agg, table)
    assert frame["Volume_USD_bn"].sum() == pytest.approx(
        agg.metrics["total_volume_usd_bn"], abs=0.05)
    assert frame["Deals"].sum() == agg.metrics["total_deals"]


def test_annual_reconciles_to_the_headline_total(agg):
    assert agg.annual["Deals"].sum() == agg.metrics["total_deals"]
    assert agg.annual["Volume_USD_bn"].sum() == pytest.approx(
        agg.metrics["total_volume_usd_bn"], abs=0.05)


@pytest.mark.parametrize("table", ["sector", "theme"])
def test_shares_sum_to_100(agg, table):
    frame = getattr(agg, table)
    assert frame["Share_of_Volume_Pct"].sum() == pytest.approx(100.0, abs=0.1)


def test_theme_deal_shares_sum_to_100(agg):
    assert agg.theme["Share_of_Deals_Pct"].sum() == pytest.approx(100.0, abs=0.1)


def test_country_table_is_a_ranked_prefix(agg):
    """Ranked by volume, and its shares are of the whole dataset, not of itself."""
    assert agg.country["Volume_USD_bn"].is_monotonic_decreasing
    assert agg.country["Share_of_Volume_Pct"].sum() < 100.0, (
        "a top-N table whose shares sum to 100 is normalised to itself, "
        "which would misstate concentration")


def test_country_table_has_no_split_labels(agg):
    """The normalisation must have folded the duplicate spellings."""
    countries = set(agg.country["Country"])
    for unfolded in ("United States", "United Kingdom", "China_HK", "Supernational"):
        assert unfolded not in countries, f"unfolded country label: {unfolded}"
    assert not any(c != c.strip() for c in countries), "country label with whitespace"


def test_annual_is_ordered_and_covers_the_published_range(agg):
    assert agg.annual["Year"].is_monotonic_increasing
    assert int(agg.annual["Year"].min()) == PUBLISHED_YEARS[0]
    assert int(agg.annual["Year"].max()) == PUBLISHED_YEARS[1]


def test_annual_first_year_has_no_yoy(agg):
    assert pd.isna(agg.annual["YoY_Deals_Pct"].iloc[0])
    assert pd.isna(agg.annual["YoY_Volume_Pct"].iloc[0])


def test_annual_yoy_is_arithmetically_correct(agg):
    """
    The growth columns must follow from the level columns, not float free.

    Compared against the full-precision levels, because that is what the growth
    is computed from: 2016 volume growth is 133.75% on the real sums
    (0.7791/0.3333), but 136.36% on the 2dp levels (0.78/0.33). Checking against
    the rounded table would fail a correct figure.
    """
    rows = agg.annual.set_index("Year")
    precise = agg.annual_precise.set_index("Year")
    years = list(rows.index)
    for prev_year, year in zip(years, years[1:]):
        for level, growth in (("Deals", "YoY_Deals_Pct"),
                              ("Volume_USD_bn", "YoY_Volume_Pct")):
            prev = float(precise.loc[prev_year, level])
            cur = float(precise.loc[year, level])
            expected = (cur / prev - 1) * 100
            assert rows[growth].loc[year] == pytest.approx(expected, abs=0.05), (
                f"{int(year)} {growth}")


def test_theme_evolution_reconciles_with_the_annual_table(agg):
    """Year x theme must sum, per year, to the annual totals."""
    deals = agg.theme_deals.set_index("Year").sum(axis=1)
    annual = agg.annual.set_index("Year")["Deals"]
    assert deals.reindex(annual.index).tolist() == annual.tolist()

    volume = agg.theme_volume.set_index("Year").sum(axis=1)
    expected = agg.annual.set_index("Year")["Volume_USD_bn"]
    for year in expected.index:
        assert volume.loc[year] == pytest.approx(expected.loc[year], abs=0.05), year


def test_theme_evolution_covers_every_theme(agg):
    themes = set(agg.theme["Theme"])
    for frame in (agg.theme_deals, agg.theme_volume):
        assert themes <= set(frame.columns), "a theme is missing from the year x theme table"


def test_slb_shares_are_bounded_and_ordered(agg):
    """Share of all issuance can only be <= share of the green+SLB subset."""
    slb = agg.slb
    assert (slb["SLB_Share_of_All_Pct"] <= 100.0001).all()
    assert (slb["SLB_Share_of_Green_SLB_Pct"] <= 100.0001).all()
    assert (slb["SLB_Share_of_All_Pct"]
            <= slb["SLB_Share_of_Green_SLB_Pct"] + 1e-6).all()
    assert slb["SLB_Share_of_Green_SLB_Pct"].notna().all(), "a share is NaN, not 0"
    assert slb["SLB_Share_of_All_Pct"].notna().all()


def test_slb_table_reconciles_with_the_theme_totals(agg):
    """The SLB sheet's own totals must agree with the theme breakdown."""
    assert agg.slb["SLB_USD_bn"].sum() == pytest.approx(
        agg.row("theme", "Theme", "SLB")["Volume_USD_bn"], abs=0.05)
    assert agg.slb["Green_USD_bn"].sum() == pytest.approx(
        agg.row("theme", "Theme", "Green")["Volume_USD_bn"], abs=0.05)
    assert agg.slb["All_Themes_USD_bn"].sum() == pytest.approx(
        agg.metrics["total_volume_usd_bn"], abs=0.05)


def test_top_issuers_are_ranked_and_within_theme_total(agg):
    top = agg.top_slb
    assert top["Volume_USD_bn"].is_monotonic_decreasing
    slb_total = agg.row("theme", "Theme", "SLB")["Volume_USD_bn"]
    assert top["Volume_USD_bn"].sum() <= slb_total + 1e-6


# ── the precise and rounded tables must agree ────────────────────────────────

@pytest.mark.parametrize("table,rounded", [
    ("annual_precise", "annual"), ("sector_precise", "sector"),
    ("theme_precise", "theme")])
def test_precise_tables_round_to_the_presentation_tables(agg, table, rounded):
    """
    The full-precision companions exist so 1dp figures are not double-rounded.

    They must still describe the same data: rounding them to 2dp has to give the
    presentation table exactly, or the brief and the workbook are quoting
    different datasets.
    """
    key = PRECISE_KEYS[table]
    precise = getattr(agg, table).set_index(key)
    pres = getattr(agg, rounded).set_index(key)
    for k in pres.index:
        assert precise.loc[k, "Deals"] == pres.loc[k, "Deals"], f"{key}={k} deal count"
        assert round(float(precise.loc[k, "Volume_USD_bn"]), 2) == pytest.approx(
            float(pres.loc[k, "Volume_USD_bn"]), abs=0.011), f"{key}={k} volume"


def test_precise_total_matches_the_headline_metric(agg):
    assert agg.total_volume() == pytest.approx(
        agg.metrics["total_volume_usd_bn"], abs=0.005)


def test_precise_tables_are_not_already_rounded(agg):
    """
    If these carried 2dp values they would be useless, and silently so.

    The 1dp figures in the brief would be double-rounded again, which is the bug
    the companion tables exist to prevent.
    """
    volumes = agg.annual_precise["Volume_USD_bn"]
    assert (volumes != volumes.round(2)).any(), (
        "annual_precise.csv looks pre-rounded — regenerate it")


# ── the published figures ────────────────────────────────────────────────────

def test_headline_metrics_match_the_published_figures(agg):
    m = agg.metrics
    assert m["total_deals"] == PUBLISHED_DEALS
    assert m["total_volume_usd_bn"] == pytest.approx(PUBLISHED_VOLUME_BN, abs=0.01)
    assert (m["year_min"], m["year_max"]) == PUBLISHED_YEARS
    assert m["n_years"] == len(agg.annual)


def test_sovereign_share_matches_the_published_figure(agg):
    """The README's central claim about why this market scaled."""
    assert agg.row("sector", "Sector", "Sovereign")["Share_of_Volume_Pct"] == pytest.approx(
        PUBLISHED_SOVEREIGN_SHARE, abs=0.01)


def test_green_shares_are_percentages(agg):
    m = agg.metrics
    assert 0 < m["green_share_deals_pct"] <= 100
    assert 0 < m["green_share_volume_pct"] <= 100
    assert m["green_share_volume_pct"] > m["green_share_deals_pct"], (
        "the average green deal is larger than the average labelled deal")


def test_unclassified_sector_is_disclosed_not_dropped(agg):
    """Undisclosed sector is reported as its own row so shares still sum to 100."""
    row = agg.row("sector", "Sector", "Unclassified")
    assert row["Deals"] > 0
    assert row["Volume_USD_bn"] == pytest.approx(
        agg.metrics["unclassified_volume_usd_bn"], abs=0.01)


def test_metrics_json_is_sorted_and_plain(agg):
    """Stored sorted so a regeneration produces a readable diff, not a reshuffle."""
    raw = json.loads((AGG_DIR / METRICS_FILE).read_text(encoding="utf-8"))
    assert list(raw) == sorted(raw)
    assert set(raw) == set(agg.metrics)


# ── round-trip against the source extract ───────────────────────────────────

def test_committed_aggregates_reproduce_from_the_extract(raw_extract, agg):
    """
    Given the extract, every committed table must recompute exactly.

    This is the test that makes the rest of the suite meaningful: it is the only
    thing tying the committed numbers back to the source data. It skips without
    a licensed copy of the extract, which is the expected state in CI.
    """
    if raw_extract is None:
        pytest.skip("no licensed copy of the source extract present (expected in CI)")
    fresh = Aggregates.from_raw(str(raw_extract))
    assert fresh.metrics == agg.metrics
    for name, frame in fresh.frames().items():
        pd.testing.assert_frame_equal(
            frame.reset_index(drop=True), agg.frames()[name].reset_index(drop=True),
            check_dtype=False, check_column_type=False, check_index_type=False,
            obj=f"aggregate table {name!r}")


def test_load_prefers_the_extract_when_present(raw_extract, tmp_path):
    """``Aggregates.load`` must use the extract when given one, else the committed files."""
    from_committed = Aggregates.load(raw_path=str(tmp_path / "absent.csv"),
                                     agg_dir=str(AGG_DIR))
    assert from_committed.metrics["total_deals"] == PUBLISHED_DEALS
    if raw_extract is not None:
        assert Aggregates.load(raw_path=str(raw_extract)).metrics == from_committed.metrics


def test_from_dir_fails_loudly_on_a_missing_table(tmp_path):
    """A silent empty frame would propagate into the workbook as zeroes."""
    with pytest.raises(FileNotFoundError, match="Missing aggregate files"):
        Aggregates.from_dir(str(tmp_path))


def test_countries_refuses_to_overreach(agg):
    """Asking for more countries than the table holds must raise, not truncate."""
    with pytest.raises(ValueError, match="countries"):
        agg.countries(len(agg.country) + 1)


def test_row_lookup_raises_rather_than_returning_nan(agg):
    with pytest.raises(KeyError):
        agg.row("sector", "Sector", "NoSuchSector")


def test_to_dir_round_trips(agg, tmp_path):
    """Writing and re-reading must be lossless, or regeneration would drift."""
    agg.to_dir(str(tmp_path))
    back = Aggregates.from_dir(str(tmp_path))
    assert back.metrics == agg.metrics
    for name, frame in back.frames().items():
        pd.testing.assert_frame_equal(
            frame.reset_index(drop=True), agg.frames()[name].reset_index(drop=True),
            check_dtype=False, check_column_type=False, check_index_type=False)
