"""
Tests for the investment brief.

The brief is the artifact most likely to be read on its own, detached from the
code that produced it — which makes it the one most dangerous to let drift. The
figure tests below recompute each headline number from the committed dataset and
assert the string actually appears in the brief, so a change in the data or the
cleaning rules fails the build rather than quietly invalidating the document.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import clean as C

ROOT = Path(__file__).resolve().parent.parent
PROJECT1 = ROOT / "project1-green-bond-analysis"
BRIEF_MD = PROJECT1 / "brief" / "Green_Bond_Market_Brief.md"


@pytest.fixture(scope="module")
def brief_text() -> str:
    if not BRIEF_MD.exists():
        pytest.skip("brief markdown not present")
    return BRIEF_MD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def figures(request) -> dict:
    """Headline figures recomputed from the committed dataset."""
    csv = PROJECT1 / "data" / "cbi_newsmakers.csv"
    if not csv.exists():
        pytest.skip("source extract not present")
    df = C.load(str(csv))
    # Aggregate from RAW sums, not from the 2dp-rounded aggregation helpers.
    # Rounding an already-rounded figure shifts it: 2022 volume is 140.3479,
    # which is 140.3 to 1dp, but the 2dp value 140.35 rounds up to 140.4.
    raw_year = df.groupby("Year").agg(deals=(C.VOL, "size"), volume=(C.VOL, "sum"))
    raw_sector = df.groupby("Sector").agg(deals=(C.VOL, "size"), volume=(C.VOL, "sum"))
    raw_theme = df.groupby("Theme").agg(deals=(C.VOL, "size"), volume=(C.VOL, "sum"))
    return {"df": df, "total": float(df[C.VOL].sum()),
            "year": raw_year, "sector": raw_sector, "theme": raw_theme,
            "metrics": C.headline_metrics(df)}


# ── the figures in the brief must match the data ──────────────────────────────

def test_totals_match(brief_text, figures):
    m = figures["metrics"]
    assert f"{m['total_deals']}" in brief_text
    assert f"${m['total_volume_usd_bn']:,.2f}bn" in brief_text


def test_sovereign_share_matches(brief_text, figures):
    share = figures["sector"].loc["Sovereign", "volume"] / figures["total"] * 100
    assert f"{share:.1f}%" in brief_text


def test_slb_volume_share_matches(brief_text, figures):
    share = figures["theme"].loc["SLB", "volume"] / figures["total"] * 100
    assert f"{share:.1f}%" in brief_text


def test_average_deal_sizes_match(brief_text, figures):
    """The green-vs-SLB size gap is the brief's central comparison."""
    theme_tbl = figures["theme"]
    for theme in ("Green", "SLB"):
        avg = theme_tbl.loc[theme, "volume"] * 1000 / theme_tbl.loc[theme, "deals"]
        assert f"{avg:,.0f}" in brief_text, f"{theme} average deal size missing"


def test_growth_figures_match(brief_text, figures):
    """Both the count figure and the volume figure must be present and correct."""
    year = figures["year"]
    count_growth = (year.loc[2023, "deals"] / year.loc[2018, "deals"] - 1) * 100
    vol_growth = (year.loc[2023, "volume"] / year.loc[2018, "volume"] - 1) * 100
    assert f"{count_growth:,.0f}%" in brief_text
    assert f"{vol_growth:,.0f}%" in brief_text


def test_annual_table_volumes_match(brief_text, figures):
    tbl = figures["year"]
    for yr in range(2018, 2025):
        assert f"{tbl.loc[yr, 'volume']:.1f}" in brief_text, f"{yr} volume"
        avg = tbl.loc[yr, "volume"] * 1000 / tbl.loc[yr, "deals"]
        assert f"{avg:,.0f}" in brief_text, f"{yr} average deal size"


def test_unclassified_is_disclosed(brief_text, figures):
    """Undisclosed sector must be stated, not quietly dropped or reallocated."""
    row = figures["sector"].loc["Unclassified"]
    assert "Unclassified" in brief_text
    assert f"{int(row['deals'])}" in brief_text


# ── claims the brief must not make ────────────────────────────────────────────

def test_brief_reports_the_greenium_with_its_uncertainty(brief_text):
    """
    The brief now makes an empirical claim, so it must carry the uncertainty
    alongside it — a point estimate with no standard error is not a result.
    """
    lowered = brief_text.lower()
    assert "hac standard error" in lowered or "hac se" in lowered
    assert "t-statistic" in lowered or "t-stat" in lowered
    assert "paired" in lowered and "observations" in lowered


def test_brief_discloses_the_autocorrelation_correction(brief_text):
    """
    The naive standard error would overstate precision threefold on this data.
    A reader cannot judge the estimate without being told that.
    """
    lowered = brief_text.lower()
    assert "autocorrelated" in lowered
    assert "newey-west" in lowered or "newey west" in lowered


def test_brief_states_the_dataset_is_not_a_census(brief_text):
    """
    The sovereign skew could be a selection effect of a newsflow dataset. That
    is the biggest threat to the brief's conclusion and must be disclosed.
    """
    lowered = brief_text.lower()
    assert "newsflow" in lowered or "not an exhaustive" in lowered
    assert "selection" in lowered or "more likely to be" in lowered


def test_brief_flags_the_partial_year(brief_text):
    assert "partial" in brief_text.lower()
    assert "cut-off" in brief_text.lower()


def test_brief_has_no_proprietary_vendor_sourcing(brief_text):
    import re
    vendors = re.compile(r"bloomberg|refinitiv|eikon|factset|capital\s*iq", re.I)
    # The brief may state that such data is NOT used; it may not cite one.
    for line in brief_text.splitlines():
        if vendors.search(line):
            assert "no proprietary" in line.lower(), f"vendor cited: {line.strip()[:90]}"


# ── the PDF build ─────────────────────────────────────────────────────────────

def test_pdf_builds_and_is_paginated(tmp_path, brief_text):
    """The PDF is generated from the markdown, so the build must work."""
    pytest.importorskip("reportlab", reason="optional: pip install reportlab")
    import build_brief

    out = tmp_path / "brief.pdf"
    build_brief.build(str(BRIEF_MD), str(out))
    assert out.exists() and out.stat().st_size > 5_000

    reader = pytest.importorskip("pypdf", reason="optional: pip install pypdf")
    pdf = reader.PdfReader(str(out))
    assert 3 <= len(pdf.pages) <= 5
    text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    # Raw Markdown must not survive into the rendered document.
    for leaked in ("**", "|---", "## "):
        assert leaked not in text, f"unrendered markdown in PDF: {leaked!r}"
    assert "Green Bond Market Brief" in text
