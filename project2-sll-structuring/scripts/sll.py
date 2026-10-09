"""
Sustainability-linked loan economics
====================================
Pure calculations for the SLL structuring model — no Excel, no I/O, so the
finance can be unit-tested directly.

All figures are illustrative and relate to a fictional borrower.

Why utilisation matters
-----------------------
A revolving credit facility is rarely fully drawn, and the margin ratchet only
touches the *drawn* balance. Quoting the ratchet benefit at 100% drawdown — as
the first version of this model did — overstates it in direct proportion to the
undrawn share. The undrawn balance is not free either: it carries a commitment
fee, conventionally a fixed percentage of the margin. Both effects are modelled
here, but they answer different questions:

* **Total facility cost** — drawn interest plus the commitment fee — is what the
  borrower pays for the revolver.
* **The incremental economics of the sustainability feature** compare this
  facility with an otherwise identical conventional one. The commitment fee is
  charged on both, so it cancels; what remains is the drawn-margin adjustment and
  the incremental assurance cost (:meth:`Facility.incremental_cost_vs_conventional_m`).

The break-even utilisation is a *best-case annual pricing* break-even under the
model's assumptions: every target met, the whole assurance cost incremental, only
the drawn margin adjusted, and no other incremental costs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

BPS = 100.0  # basis points per percentage point


@dataclass(frozen=True)
class RatchetGrid:
    """
    Margin adjustment in bps for each count of SPTs met.

    A two-way ratchet (step-down for outperformance, step-up for
    underperformance) is SLLP best practice: a step-down-only structure gives the
    borrower a free option, which is a recognised greenwashing channel.
    """
    n_kpis: int = 3
    full_step_bps: float = 7.5      # all SPTs met
    partial_step_bps: float = 2.5   # all but one met
    step_up_bps: float = 7.5        # none met

    def adjustment_bps(self, spts_met: int) -> float:
        """
        Margin adjustment in bps: negative is a discount, positive a penalty.

        Raises ``ValueError`` outside ``0..n_kpis``, since a count outside the
        grid silently returning zero would hide a modelling error.
        """
        if not 0 <= spts_met <= self.n_kpis:
            raise ValueError(f"spts_met must be 0..{self.n_kpis}, got {spts_met}")
        if spts_met == self.n_kpis:
            return -self.full_step_bps
        if spts_met == self.n_kpis - 1:
            return -self.partial_step_bps
        if spts_met == 0:
            return self.step_up_bps
        return 0.0


@dataclass(frozen=True)
class Facility:
    """
    A revolving credit facility with a sustainability-linked margin ratchet.

    ``commitment_fee_pct_of_margin`` follows the market convention of setting the
    undrawn fee as a share of the drawn margin (typically 30–40% for investment
    grade) rather than as an independent number.
    """
    size_m: float = 650.0
    base_margin_bps: float = 120.0
    reference_rate_pct: float = 4.25          # SONIA
    utilisation: float = 1.0                  # 0.0–1.0 of the facility drawn
    commitment_fee_pct_of_margin: float = 0.35
    ratchet: RatchetGrid = field(default_factory=RatchetGrid)
    # Incremental annual assurance cost of the SPT verification, in £m. Fixed: it
    # does not scale with drawdown. Treated as wholly incremental, which is the
    # conservative case — under the SLLP, data already verified in the borrower's
    # annual reporting need not be verified again, which would lower it.
    verification_cost_m: float = 0.10

    def __post_init__(self) -> None:
        if not 0.0 <= self.utilisation <= 1.0:
            raise ValueError(f"utilisation must be 0.0–1.0, got {self.utilisation}")
        if self.size_m <= 0:
            raise ValueError("size_m must be positive")

    # ── balances ────────────────────────────────────────────────────────────

    @property
    def drawn_m(self) -> float:
        """Drawn balance in £m."""
        return self.size_m * self.utilisation

    @property
    def undrawn_m(self) -> float:
        """Undrawn commitment in £m, which carries the commitment fee."""
        return self.size_m * (1.0 - self.utilisation)

    @property
    def commitment_fee_bps(self) -> float:
        """Undrawn commitment fee in bps, derived from the base margin."""
        return self.base_margin_bps * self.commitment_fee_pct_of_margin

    # ── pricing ─────────────────────────────────────────────────────────────

    def margin_bps(self, spts_met: int) -> float:
        """Post-ratchet drawn margin in bps."""
        return self.base_margin_bps + self.ratchet.adjustment_bps(spts_met)

    def all_in_rate_pct(self, spts_met: int) -> float:
        """Post-ratchet all-in rate on the drawn balance, in percent."""
        return self.reference_rate_pct + self.margin_bps(spts_met) / BPS

    def drawn_cost_m(self, spts_met: int) -> float:
        """Annual interest on the drawn balance, £m."""
        return self.drawn_m * self.all_in_rate_pct(spts_met) / 100.0

    def undrawn_cost_m(self) -> float:
        """
        Annual commitment fee on the undrawn balance, £m.

        Not ratcheted here: the modelled structure links only the drawn margin.
        For the alternative, where the fee moves with the margin, see
        :meth:`linked_commitment_fee_effect_m` — its size depends on utilisation.
        """
        return self.undrawn_m * self.commitment_fee_bps / BPS / 100.0

    def total_cost_m(self, spts_met: int) -> float:
        """Total annual facility cost: drawn interest plus undrawn commitment fee."""
        return self.drawn_cost_m(spts_met) + self.undrawn_cost_m()

    # ── ratchet economics ───────────────────────────────────────────────────

    def ratchet_benefit_m(self, spts_met: int) -> float:
        """
        Annual cost change vs the no-adjustment case, £m.

        Negative is a saving. Scales with the drawn balance, so it shrinks
        linearly as utilisation falls.
        """
        no_adjust = self.base_margin_bps
        delta_bps = self.margin_bps(spts_met) - no_adjust
        return self.drawn_m * delta_bps / BPS / 100.0

    def linked_commitment_fee_effect_m(self, spts_met: int) -> float:
        """
        Annual change in the commitment fee if it were linked to the margin, £m.

        Not part of the modelled structure. Under a fee set as a share of the
        margin, the ratchet would move the fee by ``adjustment × fee share`` on the
        *undrawn* balance, so the effect is largest when the facility is least
        drawn: at 0% utilisation the drawn-margin ratchet is worth nothing while
        this term is at its maximum. Negative is a saving.
        """
        delta_fee_bps = (self.ratchet.adjustment_bps(spts_met)
                         * self.commitment_fee_pct_of_margin)
        return self.undrawn_m * delta_fee_bps / BPS / 100.0

    def incremental_cost_vs_conventional_m(self, spts_met: int) -> float:
        """
        Annual cost of this facility minus an otherwise identical conventional one, £m.

        The commitment fee is charged on both and cancels, so the difference is
        the drawn-margin adjustment plus the incremental assurance cost. Negative
        means the sustainability-linked facility is cheaper. Excludes any other
        incremental costs (legal, internal reporting, structuring fees).
        """
        return self.ratchet_benefit_m(spts_met) + self.verification_cost_m

    def max_annual_saving_m(self) -> float:
        """Saving if every SPT is met, as a positive number, £m."""
        return -self.ratchet_benefit_m(self.ratchet.n_kpis)

    def net_benefit_m(self) -> float:
        """
        Best-case saving net of the fixed annual verification cost, £m.

        Negative means the SLL costs more to run than the ratchet can return, so
        the rationale has to be something other than price.
        """
        return self.max_annual_saving_m() - self.verification_cost_m

    def breakeven_utilisation(self) -> float | None:
        """
        Best-case annual pricing break-even, as a utilisation.

        The drawdown at which the saving with every SPT met covers the incremental
        assurance cost, under the model's assumptions (see the module docstring).
        It is not a forecast of where any borrower would operate.

        Returns ``None`` if the step is zero (no ratchet, so never breaks even).
        Can exceed 1.0, which means the facility never justifies itself on price
        at any drawdown.
        """
        step_bps = self.ratchet.full_step_bps
        if step_bps <= 0:
            return None
        saving_per_unit_utilisation = self.size_m * step_bps / BPS / 100.0
        return self.verification_cost_m / saving_per_unit_utilisation

    def scenario_table(self) -> list[dict[str, float]]:
        """One row per SPT outcome, from all met to none met."""
        rows = []
        for met in range(self.ratchet.n_kpis, -1, -1):
            rows.append({
                "spts_met": met,
                "margin_adjustment_bps": self.ratchet.adjustment_bps(met),
                "margin_bps": self.margin_bps(met),
                "all_in_rate_pct": self.all_in_rate_pct(met),
                "drawn_cost_m": self.drawn_cost_m(met),
                "undrawn_cost_m": self.undrawn_cost_m(),
                "total_cost_m": self.total_cost_m(met),
                "vs_base_m": self.ratchet_benefit_m(met),
            })
        return rows

    def utilisation_sensitivity(
        self, levels: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    ) -> list[dict[str, float]]:
        """
        Best-case ratchet saving against the verification cost, by utilisation.

        This is the table that shows why utilisation is not a detail: the saving
        is proportional to drawdown while the verification cost is fixed.
        """
        rows = []
        for u in levels:
            variant = Facility(
                size_m=self.size_m,
                base_margin_bps=self.base_margin_bps,
                reference_rate_pct=self.reference_rate_pct,
                utilisation=u,
                commitment_fee_pct_of_margin=self.commitment_fee_pct_of_margin,
                ratchet=self.ratchet,
                verification_cost_m=self.verification_cost_m,
            )
            rows.append({
                "utilisation": u,
                "drawn_m": variant.drawn_m,
                "total_cost_base_m": variant.total_cost_m(1),  # 1 of 3 = no adjustment
                "max_saving_m": variant.max_annual_saving_m(),
                "verification_cost_m": variant.verification_cost_m,
                "net_benefit_m": variant.net_benefit_m(),
            })
        return rows


def linear_glide_path(baseline: float, target: float, baseline_year: int,
                      target_year: int) -> list[tuple[int, float]]:
    """
    Linear interim targets from ``baseline`` to ``target``, inclusive of both ends.

    Used for all three KPIs. A linear path is the simplest interpolation; on it
    each year moves by the same share of the *baseline*, so a 30% reduction over
    four years is 7.5% of the baseline a year, not a constant annual rate (that
    would be about 8.5% a year, compounded). Raises if the years are not ordered.
    """
    if target_year <= baseline_year:
        raise ValueError("target_year must be after baseline_year")
    n = target_year - baseline_year
    step = (target - baseline) / n
    return [(baseline_year + i, baseline + step * i) for i in range(n + 1)]


# Kept for callers that predate the generalisation; carbon is one KPI among three.
carbon_glide_path = linear_glide_path


def compound_annual_rate(baseline: float, target: float, years: int) -> float:
    """Constant annual rate of change taking ``baseline`` to ``target``."""
    if years <= 0 or baseline <= 0 or target <= 0:
        raise ValueError("years, baseline and target must be positive")
    return (target / baseline) ** (1.0 / years) - 1.0


def kpi_progress(baseline: float, current: float, target: float) -> float:
    """
    Fraction of the baseline-to-target distance achieved, as a 0–1 share.

    Direction-agnostic, so it works for a metric that must fall (carbon
    intensity) and one that must rise (renewable share). Raises if baseline
    equals target, where progress is undefined rather than zero.
    """
    if baseline == target:
        raise ValueError("baseline and target are equal — progress is undefined")
    return (current - baseline) / (target - baseline)
