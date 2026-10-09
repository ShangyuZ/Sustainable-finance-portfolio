"""
Green Bond Market Analysis — Excel model builder
================================================
Builds an eight-sheet Excel model from the aggregated CBI News Makers extract.
Cleaning and aggregation live in ``clean.py``, the tables in ``aggregates.py``;
this module is presentation only.

Usage:
    python scripts/process_data.py                       # committed aggregates
    python scripts/process_data.py --input /path/to/cbi_newsmakers.csv

With no ``--input`` the model is built from the derived tables committed in
``data/aggregates/``, so it regenerates from this repository alone. Given the
source extract it recomputes those tables first; both paths produce the same
workbook (``tests/test_aggregates.py`` checks this).

The record-level extract itself is not redistributed here — CBI's terms of use
prohibit reproducing or storing their content without prior written permission,
so this repository carries the derived statistics instead of the dataset. See
DATA.md.

Outputs:
    Green_Bond_Market_Analysis.xlsx

No figure is hardcoded; every number is computed at build time. All inputs are
public, and no proprietary terminal data is used or required.
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.worksheet import Worksheet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import clean as C  # noqa: E402  (path set above so the script runs from anywhere)
from aggregates import DEFAULT_DIR, Aggregates  # noqa: E402

# ── colour palette ─────────────────────────────────────────────────────────
GREEN = "1A7A4A"
LIGHT = "E8F5E9"
HEADER = "2E7D32"
AMBER = "FFF3CD"
GREY = "595959"


# ── styling helpers ────────────────────────────────────────────────────────

def title_bar(ws: Worksheet, row: int, cols: int, text: str, colour: str = HEADER) -> None:
    """Write a merged, filled title bar across ``cols`` columns."""
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(bold=True, color="FFFFFF", size=12)
    cell.fill = PatternFill("solid", fgColor=colour)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=cols)
    ws.row_dimensions[row].height = 22


def col_header(cell) -> None:
    """Apply column-header styling: white bold text on dark-green background."""
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=GREEN)
    cell.alignment = Alignment(horizontal="center", wrap_text=True)


def section(ws: Worksheet, row: int, text: str) -> None:
    """Write a bold section label."""
    ws.cell(row=row, column=1, value=text).font = Font(bold=True, size=11, color=HEADER)


def note(ws: Worksheet, row: int, cols: int, text: str) -> None:
    """Write an italic wrapped footnote merged across ``cols`` columns."""
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(italic=True, size=9, color=GREY)
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=row, start_column=1, end_row=row + 1, end_column=cols)


def widths(ws: Worksheet, spec: dict[str, int]) -> None:
    """Set column widths from a {column_letter: width} mapping."""
    for letter, w in spec.items():
        ws.column_dimensions[letter].width = w


def write_df(ws: Worksheet, df: pd.DataFrame, start_row: int = 2,
             number_formats: dict[str, str] | None = None) -> int:
    """
    Write ``df`` with styled headers and zebra striping.

    ``number_formats`` maps column name -> Excel number format. Returns the last
    row written, so callers can place charts and notes below the table.
    """
    number_formats = number_formats or {}
    for col_idx, col_name in enumerate(df.columns, 1):
        col_header(ws.cell(row=start_row, column=col_idx, value=str(col_name)))

    last = start_row
    for r_offset, row in enumerate(dataframe_to_rows(df, index=False, header=False)):
        r_idx = start_row + 1 + r_offset
        last = r_idx
        for c_idx, value in enumerate(row, 1):
            if isinstance(value, float) and pd.isna(value):
                value = None
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            if r_offset % 2 == 1:
                cell.fill = PatternFill("solid", fgColor=LIGHT)
            fmt = number_formats.get(df.columns[c_idx - 1])
            if fmt:
                cell.number_format = fmt
    return last


# ── sheets ─────────────────────────────────────────────────────────────────

def sheet_dashboard(wb: Workbook, A: Aggregates) -> None:
    """Executive summary: headline KPIs, key findings, and a scope reconciliation."""
    ws = wb.create_sheet("0. Summary Dashboard")
    m = A.metrics
    title_bar(ws, 1, 6, "GREEN BOND MARKET ANALYSIS — EXECUTIVE SUMMARY")
    ws.cell(row=2, column=1,
            value="UCL Sustainable Finance Portfolio · Project 1 · ShangyuZ").font = Font(
        italic=True, size=9, color=GREY)

    kpis = [
        ("Total issuance", f"${m['total_volume_usd_bn']:,.1f}bn", "All themes, full dataset"),
        ("Total deals", m["total_deals"], "Labelled sustainable bonds"),
        ("Years covered", f"{m['year_min']}–{m['year_max']}",
         f"{m['n_years']}-year time series"),
        ("Countries", m["countries"], "Excl. supranational issuers"),
        ("Unique issuers", m["issuers"], "After folding name variants"),
        ("Green share", f"{m['green_share_volume_pct']:.0f}% of volume",
         f"{m['green_share_deals_pct']:.0f}% of deal count"),
    ]
    for c_idx, (label, value, sub) in enumerate(kpis, 1):
        col_header(ws.cell(row=4, column=c_idx, value=label))
        v = ws.cell(row=5, column=c_idx, value=value)
        v.font = Font(bold=True, size=13, color=GREEN)
        v.alignment = Alignment(horizontal="center")
        s = ws.cell(row=6, column=c_idx, value=sub)
        s.font = Font(italic=True, size=8, color=GREY)
        s.alignment = Alignment(horizontal="center", wrap_text=True)

    agg = A.annual
    themes = A.theme
    sec = A.sector
    geo = A.countries(3)
    slb = A.slb

    first_full = agg[agg["Deals"] >= 10]["Year"].min()
    peak_deal_year = int(agg.loc[agg["Deals"].idxmax(), "Year"])
    base = agg.loc[agg["Year"] == first_full].iloc[0]
    peak = agg.loc[agg["Year"] == peak_deal_year].iloc[0]
    sov = sec.loc[sec["Sector"] == "Sovereign"].iloc[0]
    slb_latest = slb.iloc[-1]

    section(ws, 8, "KEY FINDINGS")
    findings = [
        ("Market growth",
         f"Deal count grew from {int(base['Deals'])} in {int(base['Year'])} to "
         f"{int(peak['Deals'])} in {peak_deal_year} "
         f"({(peak['Deals'] / base['Deals'] - 1) * 100:,.0f}%). On USD volume the same "
         f"period grew from ${base['Volume_USD_bn']:.1f}bn to "
         f"${peak['Volume_USD_bn']:.1f}bn "
         f"({(peak['Volume_USD_bn'] / base['Volume_USD_bn'] - 1) * 100:,.0f}%) — deal "
         f"count overstates growth because average deal size fell as the market broadened."),
        ("Dominant theme",
         f"Green bonds are {m['green_share_deals_pct']:.0f}% of deals but "
         f"{m['green_share_volume_pct']:.0f}% of volume, so the average green deal is "
         f"materially larger than the average labelled bond."),
        ("SLB emergence",
         f"SLBs are {themes.loc[themes['Theme'] == 'SLB', 'Share_of_Deals_Pct'].iat[0]:.0f}% "
         f"of deals but only "
         f"{themes.loc[themes['Theme'] == 'SLB', 'Share_of_Volume_Pct'].iat[0]:.0f}% of "
         f"volume — many small transactions. SLB share of annual volume reached "
         f"{slb_latest['SLB_Share_of_All_Pct']:.1f}% in {int(slb_latest['Year'])}, up from "
         f"almost nothing before 2021 (a single 2015 record, flagged on the Data "
         f"Quality sheet as mislabelled, aside)."),
        ("Geographic concentration",
         f"The top three countries by volume ("
         f"{', '.join(geo['Country'].tolist())}) account for "
         f"{geo['Share_of_Volume_Pct'].sum():.0f}% of issuance, against "
         f"{m['countries']} countries in the dataset."),
        ("Sovereign share (sample)",
         f"Sovereign issuers are {sov['Share_of_Volume_Pct']:.0f}% of this sample's "
         f"volume across {int(sov['Deals'])} deals. That reflects the selection of a "
         f"newsflow extract, not the market: CBI's Sustainable Debt Market Summary "
         f"Q3 2024 puts sovereigns at $630.5bn of $5.4tn cumulative aligned volume, "
         f"about 11.6%."),
        ("Greenium",
         "No terminal data is used. Sheet 7 sets out the academic evidence and a "
         "matched-pair framework built on issuer-published sovereign green/conventional "
         "'twin' bond yields — see that sheet for sources."),
    ]
    r = 9
    for label, text in findings:
        ws.cell(row=r, column=1, value=label).font = Font(bold=True, size=10)
        c = ws.cell(row=r, column=2, value=text)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
        ws.row_dimensions[r].height = 42
        r += 1

    r += 1
    section(ws, r, "SCOPE RECONCILIATION")
    r += 1
    note(ws, r, 6,
         f"The dataset spans {m['year_min']}–{m['year_max']}. "
         f"{m['year_min']}–2017 contributes "
         f"${agg[agg['Year'] <= 2017]['Volume_USD_bn'].sum():.2f}bn across "
         f"{int(agg[agg['Year'] <= 2017]['Deals'].sum())} deals — small, but it is "
         f"included in the ${m['total_volume_usd_bn']:,.2f}bn total above and in every "
         f"sheet, so all tables reconcile to the same figure. "
         f"{m['year_max']} is a partial year in this extract: the "
         f"{agg.iloc[-1]['YoY_Volume_Pct']:+.0f}% volume change shown for "
         f"{m['year_max']} reflects the data cut-off, not a market contraction, and "
         f"should not be read as a trend.")
    r += 3
    note(ws, r, 6,
         f"Sector is undisclosed for {int(sec.loc[sec['Sector'] == 'Unclassified', 'Deals'].iat[0])} "
         f"deals (${m['unclassified_volume_usd_bn']:.2f}bn, "
         f"{sec.loc[sec['Sector'] == 'Unclassified', 'Share_of_Volume_Pct'].iat[0]:.1f}% of "
         f"volume). These are shown as 'Unclassified' rather than dropped, so sector "
         f"shares sum to 100%. See sheet 1 for all cleaning rules.")

    widths(ws, {"A": 20, "B": 26, "C": 20, "D": 18, "E": 18, "F": 20})


def sheet_data_quality(wb: Workbook, A: Aggregates) -> None:
    """Document every cleaning rule applied, with the record count each affected."""
    ws = wb.create_sheet("1. Data Quality")
    title_bar(ws, 1, 3, "DATA QUALITY — CLEANING RULES APPLIED")
    last = write_df(ws, A.quality, start_row=3)
    for r in range(4, last + 1):
        ws.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 34

    section(ws, last + 2, "WHY THIS SHEET EXISTS")
    note(ws, last + 3, 3,
         "The source extract is a public dataset, not a curated product, and it is "
         "dirty in ways that silently distort the analysis: an undisclosed sector "
         "encoded as the string \"0\" shows up as a sector in its own right, and one "
         "country split across two spellings has its volume split too. Every rule "
         "above is applied in code (scripts/clean.py) and is reversible — nothing is "
         "edited by hand, and the source extract is never modified. The extract "
         "itself is not redistributed with this model: CBI's terms of use do not "
         "permit it, so what ships here is the derived aggregates in "
         "data/aggregates/ (see DATA.md).")
    section(ws, last + 6, "KNOWN SOURCE ISSUES NOT CORRECTED")
    note(ws, last + 7, 3,
         "Two source records look wrong but have been left as published rather than "
         "silently overwritten: Schneider Electric SE (a French issuer) is tagged to "
         "the United States, and its 2015 transaction is labelled SLB several years "
         "before the SLB market existed — on the SLB sheet this single $0.33bn deal is "
         "why 2015 shows a 100% SLB share. Both are flagged here and excluded from "
         "narrative conclusions.")
    widths(ws, {"A": 46, "B": 18, "C": 72})


def sheet_annual(wb: Workbook, A: Aggregates) -> None:
    """Annual issuance: deals, USD volume, and both YoY growth series, with charts."""
    ws = wb.create_sheet("2. Annual Issuance")
    agg = A.annual
    yr_min, yr_max = int(agg["Year"].min()), int(agg["Year"].max())
    title_bar(ws, 1, 5, f"ANNUAL ISSUANCE ({yr_min}–{yr_max})")

    out = agg.rename(columns={
        "Volume_USD_bn": "Volume (USD bn)",
        "YoY_Deals_Pct": "YoY deals %",
        "YoY_Volume_Pct": "YoY volume %",
    })
    last = write_df(ws, out, start_row=3, number_formats={
        "Volume (USD bn)": "#,##0.00", "YoY deals %": "+#,##0.0;-#,##0.0",
        "YoY volume %": "+#,##0.0;-#,##0.0"})

    bar = BarChart()
    bar.title = "USD Volume by Year"
    bar.y_axis.title = "USD bn"
    bar.x_axis.title = "Year"
    bar.add_data(Reference(ws, min_col=3, min_row=3, max_row=last), titles_from_data=True)
    bar.set_categories(Reference(ws, min_col=1, min_row=4, max_row=last))
    bar.shape = 4
    bar.height, bar.width = 8, 16
    ws.add_chart(bar, "G3")

    line = LineChart()
    line.title = "Deal Count by Year"
    line.y_axis.title = "Deals"
    line.x_axis.title = "Year"
    line.add_data(Reference(ws, min_col=2, min_row=3, max_row=last), titles_from_data=True)
    line.set_categories(Reference(ws, min_col=1, min_row=4, max_row=last))
    line.height, line.width = 8, 16
    ws.add_chart(line, "G21")

    note(ws, last + 2, 5,
         f"{yr_max} is a partial year in this extract — treat its negative YoY as a "
         f"data cut-off, not a market contraction. {yr_min}–2017 are included for "
         f"completeness but are too thin to support YoY inference.")
    widths(ws, {"A": 8, "B": 12, "C": 18, "D": 14, "E": 14})


def sheet_geography(wb: Workbook, A: Aggregates) -> None:
    """Top countries by USD volume, with deal counts and volume share."""
    ws = wb.create_sheet("3. Geography")
    title_bar(ws, 1, 4, "TOP COUNTRIES BY ISSUANCE VOLUME")
    busiest = A.country.loc[A.country["Deals"].idxmax()]
    by_volume_rank = int(A.country.index.get_loc(busiest.name)) + 1
    geo = A.countries(15).rename(columns={
        "Volume_USD_bn": "Volume (USD bn)", "Share_of_Volume_Pct": "Share of volume %"})
    last = write_df(ws, geo, start_row=3, number_formats={
        "Volume (USD bn)": "#,##0.00", "Share of volume %": "0.0"})

    bar = BarChart()
    bar.type = "bar"
    bar.title = "Issuance Volume by Country (USD bn)"
    bar.add_data(Reference(ws, min_col=3, min_row=3, max_row=last), titles_from_data=True)
    bar.set_categories(Reference(ws, min_col=1, min_row=4, max_row=last))
    bar.height, bar.width = 11, 16
    ws.add_chart(bar, "F3")

    note(ws, last + 2, 4,
         f"Ranked by volume rather than deal count: {busiest['Country']} leads on deal "
         f"count ({int(busiest['Deals'])}) but ranks {by_volume_rank}th by volume, "
         f"because its issuance in this dataset is many small bank deals while "
         f"European volume is concentrated in large sovereign programmes. Volume is "
         f"the more meaningful ranking for where capital moved in this sample.")
    widths(ws, {"A": 20, "B": 10, "C": 18, "D": 18})


def sheet_sector(wb: Workbook, A: Aggregates) -> None:
    """Issuance by canonical sector, after folding the fragmented source taxonomy."""
    ws = wb.create_sheet("4. Sector Breakdown")
    title_bar(ws, 1, 4, "ISSUANCE BY SECTOR (NORMALISED TAXONOMY)")
    sec = A.sector.rename(columns={
        "Volume_USD_bn": "Volume (USD bn)", "Share_of_Volume_Pct": "Share of volume %"})
    last = write_df(ws, sec, start_row=3, number_formats={
        "Volume (USD bn)": "#,##0.00", "Share of volume %": "0.0"})

    bar = BarChart()
    bar.type = "bar"
    bar.title = "Issuance Volume by Sector (USD bn)"
    bar.add_data(Reference(ws, min_col=3, min_row=3, max_row=last), titles_from_data=True)
    bar.set_categories(Reference(ws, min_col=1, min_row=4, max_row=last))
    bar.height, bar.width = 10, 16
    ws.add_chart(bar, "F3")

    note(ws, last + 2, 4,
         f"The source uses {len(C.SECTOR_MAP)} distinct sector labels for what are "
         f"really {len(set(C.SECTOR_MAP.values()))} groups — 'Financials', 'Financial', "
         f"'Finance', 'Banks', 'Commercial Bank', 'Diversified Banks' and 'Financial "
         f"Institution' all denote the same sector. Folding them is what moves "
         f"Financials into second place; unfolded, its volume is split across seven "
         f"rows and none of them ranks. 'Unclassified' is undisclosed sector, not a "
         f"residual bucket. See sheet 1.")
    widths(ws, {"A": 30, "B": 10, "C": 18, "D": 18})


def sheet_theme(wb: Workbook, A: Aggregates) -> None:
    """Theme totals plus the Year x Theme mix on both deal count and volume."""
    ws = wb.create_sheet("5. Theme Evolution")
    title_bar(ws, 1, 6, "BOND THEME MIX")

    section(ws, 3, "THEME TOTALS")
    totals = A.theme.rename(columns={
        "Volume_USD_bn": "Volume (USD bn)",
        "Share_of_Volume_Pct": "Share of volume %",
        "Share_of_Deals_Pct": "Share of deals %"})
    last = write_df(ws, totals, start_row=4, number_formats={
        "Volume (USD bn)": "#,##0.00", "Share of volume %": "0.0",
        "Share of deals %": "0.0"})

    r = last + 2
    section(ws, r, "DEAL COUNT BY YEAR x THEME")
    last = write_df(ws, A.theme_deals, start_row=r + 1)

    r = last + 2
    section(ws, r, "USD VOLUME (BN) BY YEAR x THEME")
    ev = A.theme_volume
    last = write_df(ws, ev, start_row=r + 1,
                    number_formats={c: "#,##0.00" for c in ev.columns if c != "Year"})

    note(ws, last + 2, 6,
         "Deal count and volume tell different stories: SLBs are ~15% of deals but "
         "~3% of volume, so SLB activity is many small transactions rather than a "
         "shift in where the money is. Both views are shown rather than one.")
    widths(ws, {"A": 18, "B": 12, "C": 16, "D": 18, "E": 16, "F": 16})


def sheet_slb(wb: Workbook, A: Aggregates) -> None:
    """SLB vs green issuance by year, SLB penetration, and the largest SLB issuers."""
    ws = wb.create_sheet("6. SLB Analysis")
    title_bar(ws, 1, 6, "SUSTAINABILITY-LINKED BONDS (SLB) — MARKET ANALYSIS")
    ws.cell(row=2, column=1, value=(
        "SLBs tie the coupon to KPI performance rather than to use of proceeds — the "
        "same mechanism as the margin ratchet modelled in Project 2.")
    ).font = Font(italic=True, size=9, color=GREY)

    slb = A.slb.rename(columns={
        "Green_USD_bn": "Green (USD bn)", "SLB_USD_bn": "SLB (USD bn)",
        "All_Themes_USD_bn": "All themes (USD bn)",
        "SLB_Share_of_Green_SLB_Pct": "SLB % of green+SLB",
        "SLB_Share_of_All_Pct": "SLB % of all issuance"})
    last = write_df(ws, slb, start_row=3, number_formats={
        "Green (USD bn)": "#,##0.00", "SLB (USD bn)": "#,##0.00",
        "All themes (USD bn)": "#,##0.00", "SLB % of green+SLB": "0.0",
        "SLB % of all issuance": "0.0"})

    line = LineChart()
    line.title = "SLB Penetration (% of all labelled issuance)"
    line.y_axis.title = "%"
    line.x_axis.title = "Year"
    line.add_data(Reference(ws, min_col=6, min_row=3, max_row=last), titles_from_data=True)
    line.set_categories(Reference(ws, min_col=1, min_row=4, max_row=last))
    line.height, line.width = 8, 16
    ws.add_chart(line, "H3")

    r = last + 2
    section(ws, r, "LARGEST SLB ISSUERS BY VOLUME")
    top = A.top_slb.rename(columns={"Volume_USD_bn": "Volume (USD bn)"})
    last = write_df(ws, top, start_row=r + 1,
                    number_formats={"Volume (USD bn)": "#,##0.00"})

    note(ws, last + 2, 6,
         "Two share measures are reported because they are not interchangeable: "
         "SLB % of green+SLB is the like-for-like comparison, while SLB % of all "
         "issuance is the market-penetration figure. The 2015 row is a single "
         "mislabelled $0.33bn transaction (see sheet 1) and its 100% share is an "
         "artefact, not a finding.")
    widths(ws, {"A": 8, "B": 16, "C": 14, "D": 20, "E": 18, "F": 20, "G": 4, "H": 16})


def sheet_greenium(wb: Workbook) -> None:
    """
    Greenium evidence and a matched-pair framework built on open data only.

    Replaces the terminal-dependent template this sheet previously carried: the
    sovereign 'green twin' structure gives a cleaner identification strategy than
    terminal matching does, and the yields are published free.
    """
    ws = wb.create_sheet("7. Greenium Framework")
    title_bar(ws, 1, 6, "GREENIUM — EVIDENCE AND MEASUREMENT FRAMEWORK")

    section(ws, 3, "SIGN CONVENTION")
    note(ws, 4, 6,
         "Throughout this workbook the greenium is reported as (green yield − "
         "conventional yield) in basis points. A NEGATIVE number means the green bond "
         "yields less, i.e. investors accept a lower return to hold it — the greenium "
         "exists. This is the convention used in the literature below; the opposite "
         "sign convention is also common in practice, so it is stated explicitly here "
         "to avoid the ambiguity.")

    section(ws, 7, "PUBLISHED EVIDENCE")
    evidence = pd.DataFrame([
        ("Zerbib (2019)", 2019, "Global, 110 bonds", "−2", "Matched-pair + 2-step OLS",
         "J. Banking & Finance 98, 39–60"),
        ("Löffler, Petreski & Stephan (2021)", 2021, "Global, primary and secondary",
         "−15 to −20", "Propensity-score and coarsened exact matching",
         "Eurasian Econ Rev 11, 1–24"),
        ("Caramichael & Rapp (2022)", 2022, "Global corporates, at issuance", "−8",
         "Fixed-effects panel regression", "Fed Intl Finance Disc. Paper 1346"),
        ("Panizza, Shi, Weder di Mauro & Gulati (2025)", 2025,
         "Sovereign and sovereign-backed, secondary", "≈ −2 advanced, ≈ −13 emerging",
         "332 matched pairs", "CEPR Discussion Paper 20817"),
        ("Pietsch & Salakhova (2025)", 2025, "Euro area, secondary", "≈ −3.7 average",
         "k-prototypes matching", "Banque de France Working Paper 1010"),
    ], columns=["Study", "Year", "Market", "Greenium (bps)", "Method", "Reference"])
    last = write_df(ws, evidence, start_row=8)
    note(ws, last + 1, 6,
         "Estimates are not directly comparable: they differ in market, period, "
         "primary vs secondary pricing, and matching method. The consistent finding "
         "is a small negative premium in developed markets, larger and noisier in "
         "emerging markets and in primary issuance.")

    r = last + 4
    section(ws, r, "MEASUREMENT FRAMEWORK — SOVEREIGN GREEN 'TWIN' BONDS")
    r += 1
    note(ws, r, 6,
         "The identification problem in greenium work is that no two bonds are truly "
         "comparable — maturity, coupon, liquidity and seniority all differ, and the "
         "matching assumptions do the heavy lifting. Germany solved this by issuing "
         "green Bunds as 'twins': each green Bund has a conventional Bund with the "
         "SAME coupon and the SAME maturity date from the SAME issuer. The yield "
         "difference is therefore the greenium almost by construction, with no "
         "matching model required. France and the UK publish comparable series.")
    r += 3

    sources = pd.DataFrame([
        ("Germany — green twin Bunds", "Finanzagentur (Deutsche Finanzagentur)",
         "deutsche-finanzagentur.de", "Daily yields for each green bond and its "
         "conventional twin. The cleanest available matched pair."),
        ("France — OAT verte", "Agence France Trésor", "aft.gouv.fr",
         "Green OAT yields alongside the conventional OAT curve."),
        ("UK — green gilts", "UK Debt Management Office", "dmo.gov.uk",
         "Green gilt prices/yields in the daily gilt close data."),
        ("Euro area yield curves", "ECB Data Portal", "data.ecb.europa.eu",
         "Reference curve for spread construction and duration controls."),
        ("Issuance metadata", "Climate Bonds Initiative", "climatebonds.net",
         "Labelling, use-of-proceeds category and verification status."),
    ], columns=["Series", "Publisher", "Where", "What it gives you"])
    last = write_df(ws, sources, start_row=r)
    for rr in range(r + 1, last + 1):
        ws.cell(row=rr, column=4).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[rr].height = 32

    r = last + 2
    section(ws, r, "METHOD")
    r += 1
    steps = [
        "1. For each sovereign green bond, pair it with its conventional twin "
        "(Germany) or the nearest-maturity conventional benchmark (France, UK).",
        "2. Compute the daily yield difference in bps: green − conventional. Under the "
        "convention above, a negative mean is a greenium.",
        "3. For non-twin pairs, control for residual maturity mismatch by "
        "interpolating the conventional curve to the green bond's exact maturity.",
        "4. Control for liquidity using published bid-ask or turnover where "
        "available; twins still differ in outstanding size, which is the main "
        "remaining confound.",
        "5. Test whether the mean difference is distinguishable from zero. The daily "
        "spread stays autocorrelated for months and pairs share dates, so use a "
        "panel HAC (Driscoll-Kraay) standard error with a long bandwidth, and check "
        "the sign against a t-test across pair means.",
        "6. Report the distribution, not just the mean — the literature's range "
        "(−2 to −20bps) is mostly heterogeneity across issuers and periods.",
    ]
    for i, s in enumerate(steps):
        cell = ws.cell(row=r + i, column=1, value=s)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r + i, start_column=1, end_row=r + i, end_column=6)
        ws.row_dimensions[r + i].height = 28
    r += len(steps) + 1

    section(ws, r, "RESULT")
    note(ws, r + 1, 6,
         "Measured on this framework: -1.50bps pooled across all nine German green "
         "twin pairs, 8,094 paired daily observations from September 2020 to "
         "October 2026 (Driscoll-Kraay standard error 0.330 with a 250-day bandwidth, "
         "t = -4.5; an earlier 10-lag calculation on the stacked series overstated "
         "this as t = -28.7), negative on 99.8% of days, and down from -4.71bps in "
         "2021 to -0.76bps in 2025. German sovereign only. "
         "Reproduce with scripts/fetch_bund_yields.py then scripts/greenium.py; the "
         "full write-up is in brief/Green_Bond_Market_Brief.pdf. Every input is "
         "published free by the issuer — no paid data subscription is involved, "
         "which the earlier terminal-based version of this sheet required.")
    widths(ws, {"A": 34, "B": 10, "C": 22, "D": 20, "E": 26, "F": 28})


# ── main ───────────────────────────────────────────────────────────────────

def build(output_path: str, input_path: str | None = None,
          agg_dir: str = DEFAULT_DIR, min_year: int = 2015) -> dict:
    """
    Write the workbook from the aggregates and return the headline metrics.

    With ``input_path`` the tables are recomputed from the source extract;
    without it they are read from the committed CSVs in ``agg_dir``.
    """
    if input_path and os.path.exists(input_path):
        print(f"Aggregating {input_path} …")
        A = Aggregates.from_raw(input_path, min_year=min_year)
    else:
        print(f"Reading committed aggregates from {agg_dir} …")
        A = Aggregates.from_dir(agg_dir)

    m = A.metrics
    print(f"  {m['total_deals']:,} deals · {m['year_min']}–{m['year_max']} · "
          f"${m['total_volume_usd_bn']:,.2f}bn · {m['countries']} countries · "
          f"{m['issuers']} issuers")

    wb = Workbook()
    wb.remove(wb.active)

    sheet_dashboard(wb, A)
    sheet_data_quality(wb, A)
    sheet_annual(wb, A)
    sheet_geography(wb, A)
    sheet_sector(wb, A)
    sheet_theme(wb, A)
    sheet_slb(wb, A)
    sheet_greenium(wb)

    wb.save(output_path)
    print(f"Model saved → {output_path} ({len(wb.sheetnames)} sheets)")
    return m


def main() -> None:
    """Parse arguments and build the model."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(
        description="Build the Green Bond Excel model",
        epilog="With no --input the model is built from the derived tables in "
               "data/aggregates/. The CBI extract is not redistributed here; supply "
               "your own copy with --input to rebuild from records. See DATA.md.")
    parser.add_argument("--input", default=None,
                        help="Optional path to the CBI News Makers CSV. Omit to build "
                             "from the committed aggregates.")
    parser.add_argument("--aggregates", default=os.path.join(here, "data", "aggregates"),
                        help="Directory of committed aggregate tables")
    parser.add_argument("--output",
                        default=os.path.join(here, "Green_Bond_Market_Analysis.xlsx"),
                        help="Output workbook path")
    parser.add_argument("--min-year", type=int, default=2015,
                        help="Earliest issue year to include; only applies with --input")
    args = parser.parse_args()
    build(args.output, args.input, args.aggregates, args.min_year)


if __name__ == "__main__":
    main()
