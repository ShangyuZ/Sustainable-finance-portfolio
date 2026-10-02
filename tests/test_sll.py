"""
Tests for the SLL facility economics.

Two things are being protected here. First, the arithmetic: the scenario figures
quoted in the Project 2 README must fall out of the model rather than being
asserted in prose. Second, the agreement between the Python module and the Excel
workbook built from it — a formula-driven workbook that silently disagrees with
the code is worse than no workbook, because a reader would trust it.
"""

from __future__ import annotations

import pytest

from sll import Facility, RatchetGrid, carbon_glide_path, kpi_progress


# ── ratchet grid ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("met,expected", [
    (3, -7.5),   # all SPTs met -> full discount
    (2, -2.5),   # all but one  -> partial discount
    (1, 0.0),    # no adjustment
    (0, +7.5),   # none met     -> step-up penalty
])
def test_ratchet_adjustment(met, expected):
    assert RatchetGrid().adjustment_bps(met) == pytest.approx(expected)


@pytest.mark.parametrize("bad", [-1, 4, 99])
def test_ratchet_rejects_out_of_range(bad):
    """Silently returning zero would hide a modelling error."""
    with pytest.raises(ValueError):
        RatchetGrid().adjustment_bps(bad)


def test_ratchet_is_two_way():
    """SLLP best practice: step-down-only gives the borrower a free option."""
    grid = RatchetGrid()
    assert grid.adjustment_bps(grid.n_kpis) < 0
    assert grid.adjustment_bps(0) > 0


# ── facility validation ──────────────────────────────────────────────────────

@pytest.mark.parametrize("util", [-0.1, 1.1, 2.0])
def test_utilisation_must_be_a_fraction(util):
    with pytest.raises(ValueError):
        Facility(utilisation=util)


def test_facility_size_must_be_positive():
    with pytest.raises(ValueError):
        Facility(size_m=0)


# ── pricing at full drawdown (reconciles to the README) ──────────────────────

@pytest.fixture
def full() -> Facility:
    return Facility(utilisation=1.0)


def test_balances_at_full_drawdown(full):
    assert full.drawn_m == pytest.approx(650.0)
    assert full.undrawn_m == pytest.approx(0.0)


def test_commitment_fee_derives_from_margin(full):
    # 120bps margin x 35% convention
    assert full.commitment_fee_bps == pytest.approx(42.0)


@pytest.mark.parametrize("met,rate", [(3, 5.375), (2, 5.425), (1, 5.450), (0, 5.525)])
def test_all_in_rates(full, met, rate):
    assert full.all_in_rate_pct(met) == pytest.approx(rate)


@pytest.mark.parametrize("met,cost", [
    (3, 34.9375),   # README: ~£34.94m
    (1, 35.4250),   # README: ~£35.43m
    (0, 35.9125),   # README: ~£35.91m
])
def test_total_cost_matches_published_figures(full, met, cost):
    assert full.total_cost_m(met) == pytest.approx(cost, abs=0.0001)


def test_ratchet_delta_is_the_published_490k(full):
    """The README quotes ±£490k; the exact figure is £487.5k."""
    assert full.ratchet_benefit_m(3) * 1000 == pytest.approx(-487.5, abs=0.1)
    assert full.ratchet_benefit_m(0) * 1000 == pytest.approx(+487.5, abs=0.1)


def test_ratchet_is_symmetric_at_the_extremes(full):
    assert full.ratchet_benefit_m(3) == pytest.approx(-full.ratchet_benefit_m(0))


def test_no_adjustment_case_has_zero_benefit(full):
    assert full.ratchet_benefit_m(1) == pytest.approx(0.0)


def test_total_cost_is_drawn_plus_undrawn(full):
    for met in range(4):
        assert full.total_cost_m(met) == pytest.approx(
            full.drawn_cost_m(met) + full.undrawn_cost_m())


# ── utilisation: the point of the model ──────────────────────────────────────

def test_undrawn_facility_still_costs_the_commitment_fee():
    """An undrawn RCF is not free: £650m x 42bps."""
    f = Facility(utilisation=0.0)
    assert f.drawn_cost_m(3) == pytest.approx(0.0)
    assert f.total_cost_m(3) == pytest.approx(650.0 * 0.0042, abs=1e-9)


def test_ratchet_benefit_is_zero_when_nothing_is_drawn():
    """The ratchet touches the drawn margin only, so an undrawn facility earns nothing."""
    assert Facility(utilisation=0.0).max_annual_saving_m() == pytest.approx(0.0)


def test_ratchet_benefit_scales_linearly_with_utilisation():
    full = Facility(utilisation=1.0).max_annual_saving_m()
    half = Facility(utilisation=0.5).max_annual_saving_m()
    assert half == pytest.approx(full / 2)


def test_sixty_percent_utilisation_figures():
    """The realistic case quoted in the README."""
    f = Facility(utilisation=0.60)
    assert f.drawn_m == pytest.approx(390.0)
    assert f.undrawn_m == pytest.approx(260.0)
    assert f.undrawn_cost_m() == pytest.approx(1.092, abs=0.001)
    assert f.total_cost_m(1) == pytest.approx(22.347, abs=0.001)
    assert f.max_annual_saving_m() * 1000 == pytest.approx(292.5, abs=0.1)


def test_full_drawdown_overstates_the_saving():
    """
    The headline figure assumes 100% drawdown. At 60% the saving is 40% smaller —
    which is the whole reason utilisation is modelled.
    """
    full = Facility(utilisation=1.0).max_annual_saving_m()
    real = Facility(utilisation=0.60).max_annual_saving_m()
    assert real < full
    assert real / full == pytest.approx(0.60)


# ── break-even against verification cost ─────────────────────────────────────

def test_breakeven_utilisation():
    """£100k verification / (£650m x 7.5bps) = 20.5%."""
    assert Facility().breakeven_utilisation() == pytest.approx(0.2051, abs=0.0001)


def test_net_benefit_is_negative_below_breakeven():
    f = Facility()
    below = Facility(utilisation=f.breakeven_utilisation() - 0.05)
    assert below.net_benefit_m() < 0


def test_net_benefit_is_positive_above_breakeven():
    f = Facility()
    above = Facility(utilisation=f.breakeven_utilisation() + 0.05)
    assert above.net_benefit_m() > 0


def test_net_benefit_is_zero_at_breakeven():
    f = Facility()
    at = Facility(utilisation=f.breakeven_utilisation())
    assert at.net_benefit_m() == pytest.approx(0.0, abs=1e-9)


def test_breakeven_is_none_without_a_ratchet():
    f = Facility(ratchet=RatchetGrid(full_step_bps=0.0))
    assert f.breakeven_utilisation() is None


def test_higher_verification_cost_raises_breakeven():
    cheap = Facility(verification_cost_m=0.05).breakeven_utilisation()
    dear = Facility(verification_cost_m=0.20).breakeven_utilisation()
    assert dear > cheap


# ── tables ───────────────────────────────────────────────────────────────────

def test_scenario_table_shape_and_ordering(full):
    rows = full.scenario_table()
    assert len(rows) == 4
    assert [r["spts_met"] for r in rows] == [3, 2, 1, 0]
    # Cost rises monotonically as fewer SPTs are met.
    costs = [r["total_cost_m"] for r in rows]
    assert costs == sorted(costs)


def test_commitment_fee_is_constant_across_scenarios(full):
    """This structure ratchets only the drawn margin."""
    fees = {r["undrawn_cost_m"] for r in Facility(utilisation=0.5).scenario_table()}
    assert len(fees) == 1


def test_utilisation_sensitivity_table(full):
    rows = full.utilisation_sensitivity()
    assert [r["utilisation"] for r in rows] == [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    savings = [r["max_saving_m"] for r in rows]
    assert savings == sorted(savings)
    assert rows[0]["net_benefit_m"] == pytest.approx(-full.verification_cost_m)


def test_utilisation_sensitivity_preserves_other_inputs():
    f = Facility(size_m=500.0, base_margin_bps=200.0, verification_cost_m=0.25)
    row = f.utilisation_sensitivity(levels=(1.0,))[0]
    assert row["drawn_m"] == pytest.approx(500.0)
    assert row["verification_cost_m"] == pytest.approx(0.25)


# ── glide path and KPI progress ──────────────────────────────────────────────

def test_glide_path_endpoints_and_length():
    path = carbon_glide_path(310, 217, 2024, 2028)
    assert len(path) == 5
    assert path[0] == (2024, 310)
    assert path[-1][0] == 2028
    assert path[-1][1] == pytest.approx(217)


def test_glide_path_is_linear():
    path = carbon_glide_path(310, 217, 2024, 2028)
    steps = [path[i + 1][1] - path[i][1] for i in range(len(path) - 1)]
    assert all(s == pytest.approx(steps[0]) for s in steps)
    assert steps[0] == pytest.approx(-23.25)


def test_glide_path_rejects_bad_years():
    with pytest.raises(ValueError):
        carbon_glide_path(310, 217, 2028, 2024)
    with pytest.raises(ValueError):
        carbon_glide_path(310, 217, 2028, 2028)


def test_kpi_progress_for_a_decreasing_metric():
    """Carbon intensity must fall: 310 -> 267 against a 217 target."""
    assert kpi_progress(310, 267, 217) == pytest.approx(43 / 93, abs=1e-9)


def test_kpi_progress_for_an_increasing_metric():
    """Renewable share must rise: 18 -> 34 against a 60 target."""
    assert kpi_progress(18, 34, 60) == pytest.approx(16 / 42, abs=1e-9)


def test_kpi_progress_endpoints():
    assert kpi_progress(310, 310, 217) == pytest.approx(0.0)
    assert kpi_progress(310, 217, 217) == pytest.approx(1.0)


def test_kpi_progress_can_exceed_one_when_target_is_beaten():
    assert kpi_progress(310, 200, 217) > 1.0


def test_kpi_progress_is_negative_when_moving_backwards():
    assert kpi_progress(310, 320, 217) < 0.0


def test_kpi_progress_undefined_when_baseline_equals_target():
    with pytest.raises(ValueError):
        kpi_progress(310, 300, 310)
