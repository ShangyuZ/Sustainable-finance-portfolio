"""
SLL Structuring Model — Excel builder
=====================================
Generates ``SLL_Structuring_Model.xlsx`` from the calculations in ``sll.py``.

Usage:
    python scripts/build_model.py

The workbook is formula-driven, not a dump of computed values: yellow cells are
inputs and every result recalculates live in Excel. ``sll.py`` holds the same
logic in Python so it can be unit-tested, and the tests assert that the two
agree.

All figures relate to a fictional borrower and are illustrative only.
"""

from __future__ import annotations

import argparse
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sll  # noqa: E402

# ── palette ────────────────────────────────────────────────────────────────
GREEN = "1A7A4A"
HEADER = "2E7D32"
LIGHT = "E8F5E9"
INPUT = "FFF2CC"   # yellow: editable input
GREY = "595959"
RED = "C62828"

THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

RATCHET_SHEET = "3. Margin Ratchet"
# Input cell addresses on the ratchet sheet, referenced by other sheets.
R = {
    "size": "$D$5", "margin": "$D$6", "rate": "$D$7", "util": "$D$8",
    "cf_pct": "$D$9", "full": "$D$10", "partial": "$D$11", "stepup": "$D$12",
    "verif": "$D$13", "met": "$D$14",
}


def ref(key: str) -> str:
    """Absolute cross-sheet reference to a ratchet-sheet input cell."""
    return f"'{RATCHET_SHEET}'!{R[key]}"


# ── styling helpers ────────────────────────────────────────────────────────

def title_bar(ws: Worksheet, row: int, cols: int, text: str) -> None:
    """Merged, filled title bar across ``cols`` columns."""
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(bold=True, color="FFFFFF", size=12)
    cell.fill = PatternFill("solid", fgColor=HEADER)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=cols)
    ws.row_dimensions[row].height = 22


def headers(ws: Worksheet, row: int, labels: list[str], start_col: int = 1) -> None:
    """Styled column-header row."""
    for i, label in enumerate(labels, start_col):
        cell = ws.cell(row=row, column=i, value=label)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=GREEN)
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = BOX


def section(ws: Worksheet, row: int, text: str) -> None:
    """Bold section label."""
    ws.cell(row=row, column=1, value=text).font = Font(bold=True, size=11, color=HEADER)


def note(ws: Worksheet, row: int, cols: int, text: str, rows: int = 2) -> None:
    """Italic wrapped footnote merged across ``cols`` columns and ``rows`` rows."""
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(italic=True, size=9, color=GREY)
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=row, start_column=1, end_row=row + rows - 1, end_column=cols)


def input_cell(ws: Worksheet, row: int, col: int, value, fmt: str = "#,##0.00"):
    """An editable (yellow) input cell."""
    cell = ws.cell(row=row, column=col, value=value)
    cell.fill = PatternFill("solid", fgColor=INPUT)
    cell.font = Font(bold=True, color="0000CC")
    cell.number_format = fmt
    cell.border = BOX
    return cell


def result_cell(ws: Worksheet, row: int, col: int, formula: str,
                fmt: str = "#,##0.00", bold: bool = False):
    """A formula-driven output cell."""
    cell = ws.cell(row=row, column=col, value=formula)
    cell.number_format = fmt
    cell.border = BOX
    if bold:
        cell.font = Font(bold=True, color=GREEN)
    return cell


def widths(ws: Worksheet, spec: dict[str, int]) -> None:
    """Set column widths."""
    for letter, w in spec.items():
        ws.column_dimensions[letter].width = w


# ── sheets ─────────────────────────────────────────────────────────────────

def sheet_profile(wb: Workbook, f: sll.Facility) -> None:
    """Hypothetical borrower profile and a guide to the workbook."""
    ws = wb.create_sheet("0. Borrower Profile")
    title_bar(ws, 1, 2, "SLL STRUCTURING MODEL — ALBION INDUSTRIALS PLC (HYPOTHETICAL)")
    note(ws, 3, 2,
         "Fictional entity, for illustrative purposes only. No real company "
         "financial data is used anywhere in this model. All targets, rates and "
         "costs are illustrative.")

    headers(ws, 6, ["Attribute", "Value"])
    rows = [
        ("Sector", "UK Heavy Industrials (Steel & Construction Materials)"),
        ("Revenue (hypothetical)", "£2.8bn"),
        ("EBITDA margin (hypothetical)", "11%"),
        ("Existing debt (hypothetical)", f"£{f.size_m:,.0f}m revolving credit facility"),
        ("Credit rating (hypothetical)", "BBB– (investment grade)"),
        ("Scope 1+2 intensity (baseline)", "310 tCO2e per £m revenue"),
        ("Renewable energy share (baseline)", "18%"),
        ("Reference framework", "LMA/APLMA/LSTA Sustainability-Linked Loan Principles (2023)"),
    ]
    for i, (k, v) in enumerate(rows, 7):
        ws.cell(row=i, column=1, value=k).border = BOX
        c = ws.cell(row=i, column=2, value=v)
        c.border = BOX
        c.alignment = Alignment(wrap_text=True)
        if i % 2 == 0:
            for col in (1, 2):
                ws.cell(row=i, column=col).fill = PatternFill("solid", fgColor=LIGHT)

    section(ws, 16, "HOW TO USE THIS WORKBOOK")
    note(ws, 17, 2,
         "Yellow cells are inputs; everything else is a live formula. "
         "Sheet 1 tracks KPI progress. Sheet 2 calibrates the SPTs and derives "
         "the carbon glide path. Sheet 3 prices the facility — change the "
         "utilisation or any rate and the scenario table recalculates. Sheet 4 "
         "shows how the ratchet benefit varies with drawdown, and Sheet 5 asks "
         "whether the structure pays for itself at all.", rows=4)

    section(ws, 22, "REPRODUCIBILITY")
    note(ws, 23, 2,
         "This workbook is generated by scripts/build_model.py from the "
         "calculations in scripts/sll.py — it is not hand-maintained. Rebuild it "
         "with: python scripts/build_model.py", rows=2)
    widths(ws, {"A": 38, "B": 62})


def sheet_kpi_tracker(wb: Workbook) -> None:
    """Baseline / current / target per KPI with live progress formulas."""
    ws = wb.create_sheet("1. KPI Tracker")
    title_bar(ws, 1, 6, "KPI TRACKER — BASELINE VS CURRENT VS TARGET")

    headers(ws, 3, ["KPI", "Metric", "Baseline (2024)",
                    "Current (2026, hypothetical)", "Target / SPT (2028)",
                    "Progress to target"])
    kpis = [
        ("Carbon intensity", "tCO2e per £m revenue (Scope 1+2)", 310, 267, 217),
        ("Renewable energy share", "% of electricity from renewables", 18, 34, 60),
        ("Supply chain audit coverage", "% tier-1 suppliers audited to ESG standards",
         35, 52, 80),
    ]
    for i, (name, metric, base, cur, target) in enumerate(kpis, 4):
        ws.cell(row=i, column=1, value=name).border = BOX
        m = ws.cell(row=i, column=2, value=metric)
        m.border = BOX
        m.alignment = Alignment(wrap_text=True)
        ws.cell(row=i, column=3, value=base).border = BOX
        input_cell(ws, i, 4, cur, "#,##0")        # the only editable column
        ws.cell(row=i, column=5, value=target).border = BOX
        # Direction-agnostic: works whether the metric must rise or fall.
        result_cell(ws, i, 6, f"=(D{i}-C{i})/(E{i}-C{i})", "0.0%", bold=True)

    note(ws, 8, 6,
         "Only the yellow 'Current' column is editable — illustrative interim "
         "progress, not reported data. Progress is computed as "
         "(current − baseline) / (target − baseline), so it reads correctly for "
         "carbon intensity (which must fall) and for the two shares (which must "
         "rise).", rows=3)
    widths(ws, {"A": 28, "B": 40, "C": 16, "D": 22, "E": 18, "F": 18})


def sheet_spt(wb: Workbook) -> None:
    """SPT calibration and a formula-driven linear carbon glide path."""
    ws = wb.create_sheet("2. SPT Calibration")
    title_bar(ws, 1, 5, "SUSTAINABILITY PERFORMANCE TARGET CALIBRATION")

    headers(ws, 3, ["KPI", "Baseline (2024)", "Target year", "SPT", "Benchmark source"])
    rows = [
        ("Carbon intensity", "310 tCO2e/£m rev", 2028, "<=217 tCO2e/£m rev (-30%)",
         "SBTi 1.5C near-term pathway (Industrials)"),
        ("Renewable share", "18%", 2028, ">=60%",
         "UK Climate Change Committee 6th Carbon Budget"),
        ("Supply chain audit", "35%", 2027, ">=80%", "LMA SLLP best practice"),
    ]
    for i, row in enumerate(rows, 4):
        for j, val in enumerate(row, 1):
            c = ws.cell(row=i, column=j, value=val)
            c.border = BOX
            c.alignment = Alignment(wrap_text=True)
        if i % 2 == 0:
            for j in range(1, 6):
                ws.cell(row=i, column=j).fill = PatternFill("solid", fgColor=LIGHT)

    note(ws, 8, 5,
         "A 30% carbon intensity reduction over four years (~7%/yr) is consistent "
         "with the SBTi near-term pathway for Industrials. SLLP guidance requires "
         "SPTs to be a material improvement on baseline and benchmarked against a "
         "recognised pathway rather than set by the borrower alone.", rows=2)

    section(ws, 11, "CARBON INTENSITY GLIDE PATH (linear, baseline → SPT)")
    ws.cell(row=12, column=1, value="Baseline").border = BOX
    input_cell(ws, 12, 2, 310, "#,##0.0")
    ws.cell(row=13, column=1, value="2028 SPT").border = BOX
    input_cell(ws, 13, 2, 217, "#,##0.0")
    ws.cell(row=12, column=3, value="← editable").font = Font(italic=True, size=9,
                                                             color=GREY)

    years = list(range(2024, 2029))
    headers(ws, 15, [str(y) for y in years])
    n = len(years) - 1
    for i, _ in enumerate(years):
        # Linear interpolation driven by the two yellow cells above, so editing
        # either endpoint moves the whole path.
        formula = f"=$B$12+($B$13-$B$12)*{i}/{n}"
        result_cell(ws, 16, i + 1, formula, "#,##0.0", bold=(i in (0, n)))
    ws.cell(row=17, column=1, value="Annual reduction required (%)").font = Font(
        italic=True, size=9, color=GREY)
    for i in range(1, len(years)):
        col = get_column_letter(i + 1)
        prev = get_column_letter(i)
        result_cell(ws, 18, i + 1, f"={col}16/{prev}16-1", "0.0%")

    note(ws, 20, 5,
         "The glide path is formula-driven from the two yellow cells, so changing "
         "the baseline or the SPT moves every interim target. Interim SPTs matter "
         "because the ratchet is tested annually, not once at maturity.", rows=2)
    widths(ws, {"A": 30, "B": 20, "C": 14, "D": 28, "E": 42})


def sheet_ratchet(wb: Workbook, f: sll.Facility) -> None:
    """Facility pricing with utilisation, commitment fee and the ratchet."""
    ws = wb.create_sheet(RATCHET_SHEET)
    title_bar(ws, 1, 6, "MARGIN RATCHET CALCULATOR (ILLUSTRATIVE)")
    note(ws, 2, 6,
         "A revolving facility is rarely fully drawn, and the ratchet applies only "
         "to the drawn margin — so the benefit scales with utilisation. The "
         "undrawn balance carries a commitment fee, conventionally a fixed share "
         "of the margin.", rows=2)

    section(ws, 4, "INPUTS")
    inputs = [
        ("Facility size (£m)", f.size_m, "#,##0"),
        ("Base margin (bps over SONIA)", f.base_margin_bps, "#,##0.0"),
        ("SONIA reference rate (%)", f.reference_rate_pct, "#,##0.00"),
        ("Utilisation (% of facility drawn)", f.utilisation, "0%"),
        ("Commitment fee (% of margin)", f.commitment_fee_pct_of_margin, "0%"),
        ("Full step (bps) — all 3 SPTs met", f.ratchet.full_step_bps, "#,##0.0"),
        ("Partial step (bps) — 2 of 3 met", f.ratchet.partial_step_bps, "#,##0.0"),
        ("Step-up (bps) — 0 met", f.ratchet.step_up_bps, "#,##0.0"),
        ("Annual verification cost (£m)", f.verification_cost_m, "#,##0.000"),
        ("SPTs met this period (0–3)", f.ratchet.n_kpis, "0"),
    ]
    for i, (label, value, fmt) in enumerate(inputs, 5):
        ws.cell(row=i, column=1, value=label).border = BOX
        input_cell(ws, i, 4, value, fmt)

    section(ws, 16, "DERIVED")
    derived = [
        ("Drawn balance (£m)", f"={ref('size')}*{ref('util')}", "#,##0.0"),
        ("Undrawn commitment (£m)", f"={ref('size')}*(1-{ref('util')})", "#,##0.0"),
        ("Commitment fee (bps)", f"={ref('margin')}*{ref('cf_pct')}", "#,##0.0"),
        ("Margin adjustment (bps)",
         f"=IF({ref('met')}=3,-{ref('full')},IF({ref('met')}=2,-{ref('partial')},"
         f"IF({ref('met')}=1,0,{ref('stepup')})))", "+#,##0.0;-#,##0.0"),
        ("Adjusted margin (bps)", f"={ref('margin')}+$D$20", "#,##0.0"),
        ("All-in rate on drawn (%)", f"={ref('rate')}+$D$21/100", "#,##0.000"),
        ("Interest on drawn (£m)", "=$D$17*$D$22/100", "#,##0.000"),
        ("Commitment fee cost (£m)", "=$D$18*$D$19/100/100", "#,##0.000"),
        ("TOTAL ANNUAL COST (£m)", "=$D$23+$D$24", "#,##0.000"),
    ]
    for i, (label, formula, fmt) in enumerate(derived, 17):
        ws.cell(row=i, column=1, value=label).border = BOX
        result_cell(ws, i, 4, formula, fmt, bold=label.startswith("TOTAL"))

    section(ws, 27, "SCENARIO COMPARISON (at the inputs above)")
    headers(ws, 28, ["SPTs met", "Margin adj (bps)", "Margin (bps)",
                     "Interest on drawn (£m)", "Commitment fee (£m)",
                     "Total cost (£m)", "vs no adjustment (£k)"])
    for idx, met in enumerate([3, 2, 1, 0]):
        r = 29 + idx
        ws.cell(row=r, column=1, value=met).border = BOX
        result_cell(ws, r, 2,
                    f"=IF(A{r}=3,-{ref('full')},IF(A{r}=2,-{ref('partial')},"
                    f"IF(A{r}=1,0,{ref('stepup')})))", "+#,##0.0;-#,##0.0")
        result_cell(ws, r, 3, f"={ref('margin')}+B{r}", "#,##0.0")
        result_cell(ws, r, 4, f"=$D$17*({ref('rate')}+C{r}/100)/100", "#,##0.000")
        result_cell(ws, r, 5, "=$D$24", "#,##0.000")
        result_cell(ws, r, 6, f"=D{r}+E{r}", "#,##0.000")
        # Benefit is the margin delta on the drawn balance only.
        result_cell(ws, r, 7, f"=$D$17*B{r}/100/100*1000", "+#,##0.0;-#,##0.0")
        if idx % 2 == 1:
            for c in range(1, 8):
                ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=LIGHT)

    note(ws, 34, 7,
         "The commitment fee is identical across scenarios because this structure "
         "ratchets only the drawn margin. Some SLLs also ratchet the commitment "
         "fee pro rata, which would widen the spread between scenarios by roughly "
         "the commitment-fee percentage.", rows=2)
    widths(ws, {"A": 34, "B": 18, "C": 16, "D": 22, "E": 20, "F": 18, "G": 20})


def sheet_utilisation(wb: Workbook, f: sll.Facility) -> None:
    """How the ratchet benefit varies with drawdown, against a fixed cost."""
    ws = wb.create_sheet("4. Utilisation Sensitivity")
    title_bar(ws, 1, 6, "RATCHET BENEFIT BY UTILISATION")
    note(ws, 2, 6,
         "The headline ratchet saving assumes the facility is fully drawn. It is "
         "not a fixed benefit: it is proportional to the drawn balance, while the "
         "verification cost that earns it is fixed. This is the table that decides "
         "whether an SLL is worth doing on price alone.", rows=2)

    headers(ws, 5, ["Utilisation", "Drawn (£m)", "Total cost at base margin (£m)",
                    "Max annual saving (£k)", "Verification cost (£k)",
                    "Net benefit (£k)"])
    levels = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    for i, u in enumerate(levels):
        r = 6 + i
        input_cell(ws, r, 1, u, "0%")
        result_cell(ws, r, 2, f"={ref('size')}*A{r}", "#,##0.0")
        # Base-margin total: drawn interest plus the undrawn commitment fee.
        result_cell(ws, r, 3,
                    f"=B{r}*({ref('rate')}+{ref('margin')}/100)/100"
                    f"+({ref('size')}-B{r})*({ref('margin')}*{ref('cf_pct')})/100/100",
                    "#,##0.00")
        result_cell(ws, r, 4, f"=B{r}*{ref('full')}/100/100*1000", "#,##0.0")
        result_cell(ws, r, 5, f"={ref('verif')}*1000", "#,##0.0")
        c = result_cell(ws, r, 6, f"=D{r}-E{r}", "+#,##0.0;-#,##0.0", bold=True)
        if i % 2 == 1:
            for col in range(1, 7):
                ws.cell(row=r, column=col).fill = PatternFill("solid", fgColor=LIGHT)
        c.border = BOX

    be = f.breakeven_utilisation()
    section(ws, 13, "BREAK-EVEN")
    ws.cell(row=14, column=1, value="Break-even utilisation").border = BOX
    result_cell(ws, 14, 2,
                f"={ref('verif')}/({ref('size')}*{ref('full')}/100/100)", "0.0%",
                bold=True)
    ws.cell(row=14, column=3,
            value="Below this drawdown the best-case ratchet saving does not cover "
                  "the verification cost.").font = Font(italic=True, size=9, color=GREY)

    note(ws, 16, 6,
         f"At the default inputs the break-even is about {be:.0%} utilisation. "
         f"A borrower expecting to keep the facility largely undrawn — which is "
         f"the normal use of an RCF as a liquidity backstop — gets little or no "
         f"pricing benefit, and the case for the SLL has to rest on signalling, "
         f"investor relations or internal accountability rather than on cost. "
         f"That is a recognised criticism of the instrument and it is worth being "
         f"explicit about rather than quoting the full-drawdown figure.", rows=3)
    widths(ws, {"A": 14, "B": 14, "C": 28, "D": 22, "E": 20, "F": 18})


def sheet_economics(wb: Workbook, f: sll.Facility) -> None:
    """Does the structure pay for itself, and what else would have to be true."""
    ws = wb.create_sheet("5. Economics & Caveats")
    title_bar(ws, 1, 4, "IS THE STRUCTURE WORTH IT?")

    section(ws, 3, "AT THE DEFAULT INPUTS")
    headers(ws, 4, ["Measure", "Value", "Unit", "Note"])
    rows = [
        ("Facility size", f"={ref('size')}", "£m", "Committed amount"),
        ("Assumed utilisation", f"={ref('util')}", "%", "Share drawn on average"),
        ("Best-case annual saving", f"=$B$5*$B$6*{ref('full')}/100/100*1000", "£k",
         "All 3 SPTs met, on the drawn balance"),
        ("Annual verification cost", f"={ref('verif')}*1000", "£k",
         "ISAE 3000 assurance; fixed, does not scale with drawdown"),
        ("Net annual benefit", "=$B$7-$B$8", "£k",
         "Negative means the structure costs more than it returns"),
        ("Break-even utilisation",
         f"={ref('verif')}/({ref('size')}*{ref('full')}/100/100)", "%",
         "Drawdown at which saving = verification cost"),
    ]
    fmts = ["#,##0", "0%", "#,##0.0", "#,##0.0", "+#,##0.0;-#,##0.0", "0.0%"]
    for i, ((label, formula, unit, n), fmt) in enumerate(zip(rows, fmts), 5):
        ws.cell(row=i, column=1, value=label).border = BOX
        result_cell(ws, i, 2, formula, fmt, bold=label.startswith(("Net", "Break")))
        ws.cell(row=i, column=3, value=unit).border = BOX
        c = ws.cell(row=i, column=4, value=n)
        c.border = BOX
        c.alignment = Alignment(wrap_text=True)

    section(ws, 12, "WHAT THIS MODEL DELIBERATELY DOES NOT CLAIM")
    caveats = [
        "The ratchet is priced on the drawn margin only. Structures that also "
        "ratchet the commitment fee would show a larger spread.",
        "A ±7.5bps step is small relative to credit-spread volatility, so in "
        "practice the SLL label is unlikely to be the binding factor in the "
        "borrower's cost of capital.",
        "No discounting: these are single-year figures. Over a five-year facility "
        "the saving is roughly five times the annual number, less the verification "
        "cost each year.",
        "Verification cost is a single illustrative input. Real assurance costs "
        "vary with scope, and the first year is usually dearer than later ones.",
        "The two-way ratchet assumes the step-up is genuinely enforced. A "
        "step-down-only structure gives the borrower a free option and is the main "
        "greenwashing channel the SLLP guidance targets.",
        "KPI selection, not pricing, is where the real integrity risk sits: a "
        "material KPI with an unambitious SPT prices identically to a demanding "
        "one in this model.",
    ]
    for i, text in enumerate(caveats):
        r = 13 + i
        cell = ws.cell(row=r, column=1, value=f"• {text}")
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cell.font = Font(size=9)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        ws.row_dimensions[r].height = 30

    r = 13 + len(caveats) + 1
    section(ws, r, "VERIFICATION & REPORTING")
    note(ws, r + 1, 4,
         "External verifier: Big 4 assurance or a specialist ESG verifier. "
         "Reporting: annual sustainability report plus a loan anniversary "
         "compliance letter. Assurance standard: ISAE 3000 / AA1000AS. KPI data "
         "sourced from SECR disclosures (energy and carbon) and the REGO "
         "certificate registry (renewable share) — both UK statutory or "
         "registry-based, so no paid data subscription is required.", rows=3)

    r += 5
    ws.cell(row=r, column=1,
            value="All figures illustrative — hypothetical borrower, facility and "
                  "rates.").font = Font(italic=True, size=9, color=RED)
    widths(ws, {"A": 34, "B": 16, "C": 10, "D": 46})


# ── main ───────────────────────────────────────────────────────────────────

def build(output_path: str, utilisation: float = 1.0) -> sll.Facility:
    """Build the workbook. Returns the facility the defaults describe."""
    f = sll.Facility(utilisation=utilisation)
    wb = Workbook()
    wb.remove(wb.active)

    sheet_profile(wb, f)
    sheet_kpi_tracker(wb)
    sheet_spt(wb)
    sheet_ratchet(wb, f)
    sheet_utilisation(wb, f)
    sheet_economics(wb, f)

    wb.save(output_path)
    print(f"Model saved → {output_path} ({len(wb.sheetnames)} sheets)")
    print(f"  facility £{f.size_m:,.0f}m · utilisation {f.utilisation:.0%} · "
          f"max saving £{f.max_annual_saving_m() * 1000:,.1f}k · "
          f"break-even utilisation {f.breakeven_utilisation():.1%}")
    return f


def main() -> None:
    """Parse arguments and build the model."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description="Build the SLL structuring model")
    parser.add_argument("--output",
                        default=os.path.join(here, "SLL_Structuring_Model.xlsx"))
    parser.add_argument("--utilisation", type=float, default=1.0,
                        help="Default utilisation written into the workbook (0.0–1.0)")
    args = parser.parse_args()
    build(args.output, args.utilisation)


if __name__ == "__main__":
    main()
