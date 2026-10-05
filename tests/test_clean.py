"""
Tests for the green bond cleaning and aggregation layer.

These cover the specific source defects that silently distorted the analysis
before cleaning was added, plus the reconciliation invariants that every
aggregation must satisfy.
"""

from __future__ import annotations

import pandas as pd
import pytest

import clean


# ── normalisation ────────────────────────────────────────────────────────────

def test_sector_sentinel_zero_becomes_unclassified():
    """The source encodes "sector not disclosed" as the string "0"."""
    out = clean.normalise_sector(pd.Series(["0", "Sovereign", "0"]))
    assert out.tolist() == [clean.SECTOR_MISSING, "Sovereign", clean.SECTOR_MISSING]


def test_sector_null_becomes_unclassified():
    out = clean.normalise_sector(pd.Series([None, "Sovereign"]))
    assert out.iloc[0] == clean.SECTOR_MISSING


@pytest.mark.parametrize("raw", [
    "Commercial Bank", "Banks", "Diversified Banks", "Financials", "Financial",
    "Finance", "Financial Institution", "Investment Company", "Leasing",
])
def test_financial_labels_fold_to_one_sector(raw):
    """Seven source spellings denote the same sector; unfolded they each rank separately."""
    assert clean.normalise_sector(pd.Series([raw])).iloc[0] == "Financials"


@pytest.mark.parametrize("raw", ["Industry", "Industrials", "Industry (Transport)"])
def test_industry_labels_fold(raw):
    assert clean.normalise_sector(pd.Series([raw])).iloc[0] == "Industrials"


def test_unknown_sector_passes_through():
    """A label absent from the map must surface, not be silently dropped."""
    out = clean.normalise_sector(pd.Series(["Quantum Widgets"]))
    assert out.iloc[0] == "Quantum Widgets"


@pytest.mark.parametrize("raw,expected", [
    ("United States", "USA"),
    ("USA", "USA"),
    ("United Kingdom", "UK"),
    ("UK", "UK"),
    ("China_HK", "Hong Kong SAR"),
    ("Supernational", "Supranational"),
    ("Netherlands ", "Netherlands"),   # trailing space in the source
    ("Germany", "Germany"),
])
def test_country_label_folding(raw, expected):
    assert clean.normalise_country(pd.Series([raw])).iloc[0] == expected


def test_issuer_case_variants_fold_to_most_common_spelling():
    raw = pd.Series(["GoodLeap LLC"] * 3 + ["Goodleap LLC"])
    out = clean.normalise_issuer(raw)
    assert out.nunique() == 1
    assert out.iloc[0] == "GoodLeap LLC"   # the majority spelling wins


# ── loading ──────────────────────────────────────────────────────────────────

def test_load_applies_all_normalisations(dirty_csv):
    df = clean.load(str(dirty_csv))
    assert set(df["Country"]) == {"USA", "Netherlands", "UK"}
    assert df["Issuer Name"].nunique() == 3          # GoodLeap folded
    assert clean.SECTOR_MISSING in set(df["Sector"])
    assert "0" not in set(df["Sector"])


def test_load_respects_min_year(dirty_csv):
    df = clean.load(str(dirty_csv), min_year=2023)
    assert df["Year"].min() >= 2023
    assert len(df) == 4


def test_load_year_is_integer(bonds):
    assert bonds["Year"].dtype.kind == "i"


# ── aggregations ─────────────────────────────────────────────────────────────

def test_annual_issuance_columns_and_order(bonds):
    agg = clean.annual_issuance(bonds)
    assert list(agg.columns) == [
        "Year", "Deals", "Volume_USD_bn", "YoY_Deals_Pct", "YoY_Volume_Pct"]
    assert agg["Year"].is_monotonic_increasing


def test_annual_first_year_has_no_yoy(bonds):
    agg = clean.annual_issuance(bonds)
    assert pd.isna(agg["YoY_Deals_Pct"].iloc[0])
    assert pd.isna(agg["YoY_Volume_Pct"].iloc[0])


def test_annual_yoy_is_arithmetically_correct(bonds):
    agg = clean.annual_issuance(bonds)
    for i in range(1, len(agg)):
        prev, cur = agg["Deals"].iloc[i - 1], agg["Deals"].iloc[i]
        expected = (cur / prev - 1) * 100
        assert agg["YoY_Deals_Pct"].iloc[i] == pytest.approx(expected, abs=0.01)


def test_annual_deals_reconcile_to_row_count(bonds):
    assert clean.annual_issuance(bonds)["Deals"].sum() == len(bonds)


@pytest.mark.parametrize("fn", [clean.sector, clean.theme_totals])
def test_aggregation_volume_reconciles_to_total(bonds, fn):
    """Every breakdown must sum back to the dataset total — no dropped rows."""
    agg = fn(bonds)
    assert agg["Volume_USD_bn"].sum() == pytest.approx(bonds[clean.VOL].sum(), abs=0.05)
    assert agg["Deals"].sum() == len(bonds)


def test_sector_shares_sum_to_100(bonds):
    assert clean.sector(bonds)["Share_of_Volume_Pct"].sum() == pytest.approx(100.0, abs=0.1)


def test_theme_shares_sum_to_100(bonds):
    themes = clean.theme_totals(bonds)
    assert themes["Share_of_Volume_Pct"].sum() == pytest.approx(100.0, abs=0.1)
    assert themes["Share_of_Deals_Pct"].sum() == pytest.approx(100.0, abs=0.1)


def test_geographic_is_sorted_by_volume_and_capped(bonds):
    geo = clean.geographic(bonds, top_n=5)
    assert len(geo) == 5
    assert geo["Volume_USD_bn"].is_monotonic_decreasing


def test_geographic_folds_split_country_labels(bonds):
    """USA and United States must not both appear."""
    countries = set(clean.geographic(bonds, top_n=100)["Country"])
    assert "United States" not in countries
    assert "United Kingdom" not in countries
    assert not any(c.endswith(" ") for c in countries)


def test_theme_evolution_deals_match_annual_totals(bonds):
    ev = clean.theme_evolution(bonds, "deals")
    annual = clean.annual_issuance(bonds).set_index("Year")["Deals"]
    per_year = ev.set_index("Year").sum(axis=1)
    assert per_year.reindex(annual.index).equals(annual.astype(per_year.dtype))


def test_theme_evolution_volume_reconciles(bonds):
    ev = clean.theme_evolution(bonds, "volume")
    total = ev.drop(columns=["Year"]).to_numpy().sum()
    assert total == pytest.approx(bonds[clean.VOL].sum(), abs=0.5)


def test_theme_evolution_rejects_bad_values_argument(bonds):
    with pytest.raises(ValueError):
        clean.theme_evolution(bonds, "nonsense")


def test_slb_share_denominators_differ_and_are_bounded(bonds):
    slb = clean.slb_vs_green(bonds)
    assert (slb["SLB_Share_of_All_Pct"] <= 100.0001).all()
    assert (slb["SLB_Share_of_Green_SLB_Pct"] <= 100.0001).all()
    # Share of all issuance can only be <= share of the green+SLB subset.
    assert (slb["SLB_Share_of_All_Pct"] <= slb["SLB_Share_of_Green_SLB_Pct"] + 1e-6).all()


def test_slb_share_is_zero_not_nan_when_no_issuance(bonds):
    """A year with no SLB and no green issuance must give 0, not NaN."""
    slb = clean.slb_vs_green(bonds)
    assert slb["SLB_Share_of_Green_SLB_Pct"].notna().all()
    assert slb["SLB_Share_of_All_Pct"].notna().all()


def test_top_issuers_respects_theme_filter(bonds):
    top = clean.top_issuers(bonds, theme="SLB", top_n=5)
    assert len(top) <= 5
    assert top["Volume_USD_bn"].is_monotonic_decreasing
    slb_total = bonds.loc[bonds["Theme"] == "SLB", clean.VOL].sum()
    assert top["Volume_USD_bn"].sum() <= slb_total + 1e-6


# ── headline metrics ─────────────────────────────────────────────────────────

def test_headline_metrics_match_the_dataset(bonds):
    m = clean.headline_metrics(bonds)
    assert m["total_deals"] == len(bonds)
    assert m["total_volume_usd_bn"] == pytest.approx(bonds[clean.VOL].sum(), abs=0.01)
    assert m["year_min"] == int(bonds["Year"].min())
    assert m["year_max"] == int(bonds["Year"].max())
    assert m["n_years"] == bonds["Year"].nunique()


def test_country_count_excludes_supranational(bonds):
    """Supranational issuers are in the volume totals but are not countries."""
    m = clean.headline_metrics(bonds)
    raw_nunique = bonds["Country"].nunique()
    has_supra = bool(bonds["Country"].isin(clean.NON_SOVEREIGN).any())
    assert m["countries"] == raw_nunique - (1 if has_supra else 0)


def test_green_shares_are_percentages(bonds):
    m = clean.headline_metrics(bonds)
    assert 0 < m["green_share_deals_pct"] <= 100
    assert 0 < m["green_share_volume_pct"] <= 100


# ── data quality report ──────────────────────────────────────────────────────

def test_data_quality_report_counts_records_not_labels(dirty_csv):
    df = clean.load(str(dirty_csv))
    dq = clean.data_quality_report(str(dirty_csv), df)
    counts = dict(zip(dq["Cleaning rule"], dq["Records affected"]))

    sentinel = next(k for k in counts if "sentinel" in k)
    assert counts[sentinel] == 1          # one "0" row in the fixture

    country = next(k for k in counts if "Country duplicate" in k)
    assert counts[country] == 2           # United States + United Kingdom

    ws = next(k for k in counts if "whitespace" in k)
    assert counts[ws] == 1                # "Netherlands "

    issuer = next(k for k in counts if "Issuer name" in k)
    assert counts[issuer] == 1            # GoodLeap / Goodleap


def test_data_quality_report_is_nonempty_for_real_data(agg):
    """
    The published cleaning report must document real corrections, not be empty.

    Checked against the committed table rather than recomputed: that table is
    what ships in the workbook, and the source extract it was computed from is
    not redistributable (see DATA.md).
    """
    dq = agg.quality
    assert len(dq) > 0
    assert (dq["Records affected"] >= 0).all()
    assert (dq["Records affected"] > 0).any(), "a report with no corrections is not a report"
    assert dq["Why it matters"].str.len().gt(20).all(), "every rule needs a stated reason"
