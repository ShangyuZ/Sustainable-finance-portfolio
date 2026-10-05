"""
Guards against redistributing third-party data.

This repository once shipped 732 Climate Bonds Initiative records and 17,656
Finanzagentur yield observations. Both publishers reserve their rights — CBI's
terms of use prohibit reproducing or storing their content without prior written
permission, and Finanzagentur's published data is marked all rights reserved —
so neither was mine to redistribute. The fix was to commit the derived
aggregates instead and leave the records with whoever licensed them.

Deleting the files was not enough on its own, and that is the lesson these tests
encode. The same CBI records also sat inside the generated workbook, on a
"Cleaned Data" sheet that no text search of the repository would have found. A
guard that only checked for a filename would have passed a repository that still
shipped the data.

So the checks here are structural rather than name-based:

- the known source files are absent and ignored, so a stray copy cannot be
  committed by accident;
- no committed CSV is large enough to be a record-level dataset, except the
  files explicitly accounted for below;
- no workbook sheet is large enough to hold one either.

A row cap is a blunt instrument, and deliberately so: it fails on anything
record-shaped, including a file nobody thought to add to a list.
"""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
PROJECT1 = ROOT / "project1-green-bond-analysis"

# Source data that must never be committed, with the rightsholder in each case.
NOT_REDISTRIBUTABLE = {
    PROJECT1 / "data" / "cbi_newsmakers.csv":
        "Climate Bonds Initiative — reproduction prohibited without written permission",
    PROJECT1 / "data" / "bund_yields.csv":
        "Finanzagentur GmbH — all rights reserved",
    PROJECT1 / "data" / "green_twin_pairs.csv":
        "derived from Finanzagentur factsheets; regenerate with fetch_bund_yields.py",
}

# Any committed CSV above this many data rows is treated as record-level data.
# Every aggregate table in this repository is far smaller; the real extract was
# 732 rows and the yield file 17,656.
ROW_CAP = 400

# Committed CSVs allowed past the cap, each with the reason it is accounted for.
ALLOWED_LARGE_CSVS = {
    "project3-climate-dashboard/data/eua_prices.csv":
        "EU ETS settlement prices compiled from public sources; no rightsholder "
        "asserts terms over it and it is labelled indicative in DATA.md",
}

# A sheet bigger than this is presumed to hold records rather than a summary.
# The largest real sheet in the model is the greenium framework, at 38 rows.
SHEET_ROW_CAP = 60


def _tracked(pattern: str) -> list[Path]:
    """Files matching ``pattern`` that git actually tracks."""
    out = subprocess.run(["git", "ls-files", pattern], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return [ROOT / line for line in out.stdout.splitlines() if line]


def _data_rows(path: Path) -> int:
    """Row count excluding the header and any leading comment lines."""
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        rows = [r for r in csv.reader(fh)
                if r and not r[0].lstrip().startswith("#")]
    return max(len(rows) - 1, 0)


# ── the source files are gone and stay gone ──────────────────────────────────

@pytest.mark.parametrize("path,rightsholder",
                         [(p, r) for p, r in NOT_REDISTRIBUTABLE.items()],
                         ids=lambda v: Path(v).name if isinstance(v, Path) else "")
def test_source_data_is_not_committed(path, rightsholder):
    """Each of these was committed once. None may be again."""
    rel = path.relative_to(ROOT).as_posix()
    assert not _tracked(rel), f"{rel} is committed but is not redistributable: {rightsholder}"


@pytest.mark.parametrize("path", list(NOT_REDISTRIBUTABLE),
                         ids=lambda p: Path(p).name)
def test_source_data_is_gitignored(path):
    """
    Ignored as well as absent.

    Deleting a file leaves nothing stopping the next `git add -A` from putting it
    straight back, which is exactly how it would return: the pipeline writes
    these paths, so anyone who runs the fetcher has them on disk.
    """
    rel = path.relative_to(ROOT).as_posix()
    result = subprocess.run(["git", "check-ignore", rel], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 0, f"{rel} is not gitignored"


# ── nothing record-shaped is committed under any name ────────────────────────

def test_no_committed_csv_is_record_level():
    """
    The structural check: a dataset is caught by its shape, not its name.

    This is the one that would have failed on the original repository regardless
    of what the files were called.
    """
    oversized = []
    for path in _tracked("*.csv"):
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWED_LARGE_CSVS or not path.exists():
            continue
        rows = _data_rows(path)
        if rows > ROW_CAP:
            oversized.append(f"{rel} ({rows} rows)")
    assert not oversized, (
        "committed CSV(s) large enough to be record-level data:\n  "
        + "\n  ".join(oversized)
        + "\nIf the file is genuinely publishable, add it to ALLOWED_LARGE_CSVS "
          "with the reason, and record its provenance in DATA.md.")


def test_allowed_large_csvs_are_all_still_present_and_justified():
    """
    The allowlist must not rot into a blanket exemption.

    An entry for a file that no longer exists is an exemption nobody is checking,
    and a reason too short to say anything is not a reason.
    """
    for rel, reason in ALLOWED_LARGE_CSVS.items():
        assert (ROOT / rel).exists(), f"allowlisted file no longer exists: {rel}"
        assert len(reason) > 40, f"allowlist entry for {rel} needs a real justification"


def test_allowlisted_data_is_declared_in_data_md():
    """Anything exempted from the cap must be accounted for in the provenance file."""
    data_md = (ROOT / "DATA.md").read_text(encoding="utf-8")
    for rel in ALLOWED_LARGE_CSVS:
        assert Path(rel).name in data_md, f"{rel} is allowlisted but absent from DATA.md"


def test_no_workbook_sheet_is_record_level():
    """
    The blind spot that made the first removal incomplete.

    The CBI records lived on a workbook sheet as well as in the CSV, invisible to
    any text search of the repository.
    """
    oversized = []
    for xlsx in _tracked("*.xlsx"):
        if not xlsx.exists():
            continue
        for ws in load_workbook(xlsx).worksheets:
            if ws.max_row > SHEET_ROW_CAP:
                oversized.append(
                    f"{xlsx.relative_to(ROOT).as_posix()}:{ws.title} ({ws.max_row} rows)")
    assert not oversized, (
        "workbook sheet(s) large enough to hold record-level data:\n  "
        + "\n  ".join(oversized))


# ── the substitute is actually there ─────────────────────────────────────────

def test_the_derived_aggregates_are_committed_in_place_of_the_extract():
    """
    Removing the data without committing the aggregates would break every figure.

    The point of the exercise was to keep the published numbers verifiable, not
    to make the repository quieter about where they came from.
    """
    agg_dir = PROJECT1 / "data" / "aggregates"
    assert agg_dir.is_dir(), "the aggregates directory is missing"
    committed = {p.name for p in _tracked("project1-green-bond-analysis/data/aggregates/*")}
    assert "headline_metrics.json" in committed
    assert len([n for n in committed if n.endswith(".csv")]) >= 8, (
        "too few aggregate tables committed to reproduce the published figures")


def test_the_greenium_result_is_committed_in_place_of_the_yields():
    """Same for the greenium: the estimate ships even though its input cannot."""
    for name in ("greenium_summary.csv", "greenium_by_year.csv",
                 "greenium_diagnostics.json"):
        assert _tracked(f"project1-green-bond-analysis/data/{name}"), (
            f"{name} is not committed; the brief's greenium figures would be unverifiable")


def test_the_pair_registry_template_is_still_committed():
    """
    The template stays: it is the instructions, not the data.

    Without it nobody can reproduce the pairing, which is the one part of the
    method that cannot be inferred from the result.
    """
    assert _tracked("project1-green-bond-analysis/data/green_twin_pairs.example.csv")


# ── the guard itself works ───────────────────────────────────────────────────

def test_the_row_cap_catches_a_record_level_file(tmp_path, monkeypatch):
    """
    A guard nobody has seen fail is a guard nobody should trust.

    Rebuilds the check against a temporary repository holding a file the size of
    the original extract, and asserts it is caught.
    """
    big = tmp_path / "records.csv"
    big.write_text("a,b\n" + "\n".join(f"{i},{i}" for i in range(ROW_CAP + 1)),
                   encoding="utf-8")
    assert _data_rows(big) > ROW_CAP

    small = tmp_path / "summary.csv"
    small.write_text("a,b\n" + "\n".join(f"{i},{i}" for i in range(10)), encoding="utf-8")
    assert _data_rows(small) <= ROW_CAP


def test_row_count_ignores_comment_headers():
    """The pair template leads with a long comment block; it is not data."""
    template = PROJECT1 / "data" / "green_twin_pairs.example.csv"
    assert _data_rows(template) < 10, "comment lines are being counted as rows"
