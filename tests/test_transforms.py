"""
Tests for the dashboard's pure transforms.

These are the calculations that were wrong in a way no exception would reveal:
a pie chart summing to 198%, a ranking keyed to a year with no data, and a WACI
scaled by a weights shortfall.
"""

from __future__ import annotations

import pandas as pd
import pytest

import transforms as T


# ── OWID aggregate filtering ─────────────────────────────────────────────────

def test_sovereign_only_drops_owid_aggregates(owid_like):
    out = T.sovereign_only(owid_like)
    assert not out["iso_code"].str.startswith("OWID").any()
    assert "Africa" not in set(out["country"])
    assert "World" not in set(out["country"])
    assert "European Union (27)" not in set(out["country"])


def test_sovereign_only_drops_rows_without_iso_code(owid_like):
    out = T.sovereign_only(owid_like)
    assert out["iso_code"].notna().all()
    assert "Kosovo" not in set(out["country"])


def test_sovereign_only_keeps_real_countries(owid_like):
    out = T.sovereign_only(owid_like)
    assert "Country0" in set(out["country"])
    assert (out["iso_code"].str.len() == 3).all()


# ── reference-year selection ─────────────────────────────────────────────────

def test_latest_complete_year_skips_sparse_newest_year(owid_like):
    """
    2023 exists but only 3 countries report it; the ranking must fall back to
    2022. Using df["year"].max() here is what produced an empty scorecard.
    """
    df = T.sovereign_only(owid_like)
    year = T.latest_complete_year(df, ["co2_per_capita", "renewables_share_elec"],
                                  min_countries=40)
    assert year == 2022
    assert year != int(df["year"].max())


def test_latest_complete_year_returns_none_when_nothing_qualifies(owid_like):
    df = T.sovereign_only(owid_like)
    assert T.latest_complete_year(df, ["co2_per_capita"], min_countries=10_000) is None


def test_latest_complete_year_returns_none_for_missing_column(owid_like):
    assert T.latest_complete_year(owid_like, ["not_a_column"]) is None


def test_latest_complete_year_returns_none_for_empty_frame():
    empty = pd.DataFrame({"year": [], "co2_per_capita": []})
    assert T.latest_complete_year(empty, ["co2_per_capita"]) is None


def test_latest_complete_year_requires_all_columns_jointly(owid_like):
    """A year where one column is fully missing must not qualify."""
    df = T.sovereign_only(owid_like).copy()
    df.loc[df["year"] == 2022, "co2_per_capita"] = None
    year = T.latest_complete_year(df, ["co2_per_capita", "renewables_share_elec"],
                                  min_countries=40)
    assert year == 2021


# ── electricity mix: the double-counting bug ─────────────────────────────────

def test_top_level_mix_and_renewable_parts_do_not_overlap():
    """The two maps must stay disjoint, or a pie built from them double-counts."""
    assert set(T.TOP_LEVEL_MIX) & set(T.RENEWABLE_PARTS) == set()


def test_top_level_mix_excludes_renewable_components():
    """Hydro/solar/wind are inside renewables_share_elec and must not be top level."""
    for nested in ("hydro_share_elec", "solar_share_elec", "wind_share_elec"):
        assert nested not in T.TOP_LEVEL_MIX


def test_mix_shares_sums_to_100_for_a_partitioned_row():
    row = pd.Series({
        "fossil_share_elec": 38.5, "renewables_share_elec": 46.4,
        "nuclear_share_elec": 15.1,
        # Components, which must be ignored by the top-level map:
        "hydro_share_elec": 1.8, "wind_share_elec": 28.8, "solar_share_elec": 4.5,
    })
    shares = T.mix_shares(row, T.TOP_LEVEL_MIX)
    assert sum(shares.values()) == pytest.approx(100.0, abs=0.1)
    assert set(shares) == {"Fossil fuels", "Renewables", "Nuclear"}


def test_mix_shares_regression_norway_style_row_no_longer_exceeds_100():
    """
    Norway's real 2023 row summed to 198% under the old all-columns-in-one-pie
    approach. Partitioned correctly it is 100%.
    """
    row = pd.Series({
        "fossil_share_elec": 1.4, "renewables_share_elec": 98.5,
        "nuclear_share_elec": 0.0,
        "hydro_share_elec": 88.6, "wind_share_elec": 9.6, "solar_share_elec": 0.1,
        "other_renewables_share_elec": 0.2,
    })
    assert sum(T.mix_shares(row, T.TOP_LEVEL_MIX).values()) == pytest.approx(99.9, abs=0.2)
    everything = {**T.TOP_LEVEL_MIX, **T.RENEWABLE_PARTS}
    assert sum(T.mix_shares(row, everything).values()) > 150   # the old bug


def test_mix_shares_renewable_parts_sum_to_the_renewables_total():
    row = pd.Series({
        "renewables_share_elec": 46.38,
        "hydro_share_elec": 1.78, "wind_share_elec": 28.84,
        "solar_share_elec": 4.52, "other_renewables_share_elec": 11.24,
    })
    parts = T.mix_shares(row, T.RENEWABLE_PARTS)
    assert sum(parts.values()) == pytest.approx(row["renewables_share_elec"], abs=0.05)


def test_mix_shares_drops_missing_and_zero():
    row = pd.Series({"fossil_share_elec": 0.0, "renewables_share_elec": None,
                     "nuclear_share_elec": 12.0})
    assert T.mix_shares(row, T.TOP_LEVEL_MIX) == {"Nuclear": 12.0}


def test_mix_shares_tolerates_absent_columns():
    assert T.mix_shares(pd.Series({"nuclear_share_elec": 5.0}), T.TOP_LEVEL_MIX) == {
        "Nuclear": 5.0}


# ── portfolio weights ────────────────────────────────────────────────────────

@pytest.mark.parametrize("n", range(1, 21))
def test_default_weights_always_sum_to_100(n):
    """
    The naive round(100/n, 1) repeated n times misses 100 for several n (n=14
    gives 99.4), raising a spurious warning on an untouched form.
    """
    assert sum(T.default_weights(n)) == pytest.approx(100.0, abs=1e-9)


@pytest.mark.parametrize("n", range(1, 21))
def test_default_weights_length_and_positivity(n):
    w = T.default_weights(n)
    assert len(w) == n
    assert all(x > 0 for x in w)


def test_default_weights_rejects_zero():
    with pytest.raises(ValueError):
        T.default_weights(0)


def test_default_weights_naive_approach_would_fail_for_n_14():
    """Documents the specific bug this function exists to avoid."""
    naive = [round(100.0 / 14, 1)] * 14
    assert sum(naive) != pytest.approx(100.0, abs=1e-9)
    assert sum(T.default_weights(14)) == pytest.approx(100.0, abs=1e-9)


# ── WACI ─────────────────────────────────────────────────────────────────────

def test_waci_single_holding_equals_its_intensity():
    assert T.waci([100.0], [850.0]) == pytest.approx(850.0)


def test_waci_is_the_weighted_average():
    # 50% at 800 + 50% at 200 -> 500
    assert T.waci([50.0, 50.0], [800.0, 200.0]) == pytest.approx(500.0)


def test_waci_scales_with_a_weights_shortfall():
    """Half-invested at 800 gives 400 — lower, but not a lower-carbon portfolio."""
    assert T.waci([50.0], [800.0]) == pytest.approx(400.0)


def test_waci_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        T.waci([50.0, 50.0], [800.0])


def test_waci_accepts_pandas_series():
    assert T.waci(pd.Series([60.0, 40.0]), pd.Series([100.0, 50.0])) == pytest.approx(80.0)


def test_rescale_waci_restores_the_full_invested_figure():
    assert T.rescale_waci(T.waci([50.0], [800.0]), 50.0) == pytest.approx(800.0)


def test_rescale_waci_is_identity_at_100_percent():
    raw = T.waci([60.0, 40.0], [500.0, 100.0])
    assert T.rescale_waci(raw, 100.0) == pytest.approx(raw)


def test_rescale_waci_handles_zero_weight():
    assert T.rescale_waci(0.0, 0.0) == 0.0
