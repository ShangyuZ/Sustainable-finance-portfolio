"""
Export derived aggregates from the CBI extract
==============================================
Writes the summary statistics this project actually publishes — annual totals,
sector and country breakdowns, theme mix, SLB penetration and the data-quality
report — to ``data/aggregates/``.

Why this exists
---------------
Climate Bonds Initiative's terms of use prohibit reproducing or storing their
content without prior written permission, so the record-level extract is **not**
redistributed in this repository. What is redistributed is this: aggregate
statistics computed from it.

That keeps the thing that matters — every figure quoted in the README, the
workbook and the investment brief can still be checked against a committed file,
and the test suite does exactly that — without republishing someone else's
dataset.

Usage (requires your own copy of the source extract):
    python scripts/export_aggregates.py --input /path/to/cbi_newsmakers.csv
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import clean as C  # noqa: E402

# filename -> (callable building the frame, human description)
EXPORTS = {
    "annual_issuance.csv": (C.annual_issuance, "Deals, USD volume and both YoY series by year"),
    "by_country.csv": (lambda df: C.geographic(df, top_n=25), "Top 25 countries by USD volume"),
    "by_sector.csv": (C.sector, "Volume and deal count by normalised sector"),
    "by_theme.csv": (C.theme_totals, "Volume and deal count by bond theme"),
    "slb_vs_green.csv": (C.slb_vs_green, "SLB vs green issuance and two penetration measures"),
    "theme_by_year_deals.csv": (lambda df: C.theme_evolution(df, "deals"), "Year x theme, deal count"),
    "theme_by_year_volume.csv": (lambda df: C.theme_evolution(df, "volume"), "Year x theme, USD volume"),
    "top_issuers_slb.csv": (lambda df: C.top_issuers(df, theme="SLB", top_n=10),
                            "Largest SLB issuers by volume"),
}

# Grouping keys for the full-precision companion tables.
PRECISE = {"annual_precise.csv": "Year", "sector_precise.csv": "Sector",
           "theme_precise.csv": "Theme"}


def precise_table(df, key: str):
    """
    Unrounded deal count and volume by ``key``.

    The presentation tables round to 2dp, which is right for a workbook but
    wrong as a source for a figure quoted to 1dp: rounding an already-rounded
    number shifts it. 2022 volume is 140.3479 — 140.3 to one decimal, but the
    2dp value 140.35 rounds up to 140.4. The brief quotes 1dp figures, so its
    tests need the raw sums, and these tables carry them at full precision.
    """
    out = (df.groupby(key)
             .agg(Deals=(C.VOL, "size"), Volume_USD_bn=(C.VOL, "sum"))
             .reset_index())
    return out.sort_values(key).reset_index(drop=True)


README = """# Derived aggregates

Summary statistics computed from the Climate Bonds Initiative "News Makers"
extract. **The record-level source data is not redistributed here** — CBI's terms
of use prohibit reproducing or storing their content without prior written
permission (see ../../../DATA.md).

These files are the derived output of that analysis, not the dataset. Every
figure quoted in the project README, the Excel model and the investment brief is
computed from the same pipeline and is checked against these files by
`tests/test_aggregates.py`, so the published numbers still cannot drift
unnoticed.

Regenerate with `scripts/export_aggregates.py --input <your copy of the extract>`.

| File | Contents |
"""


def build(input_path: str, out_dir: str) -> dict:
    """Compute and write every aggregate. Returns the headline metrics."""
    df = C.load(input_path)
    metrics = C.headline_metrics(df)
    os.makedirs(out_dir, exist_ok=True)

    lines = [README, "|---|---|"]
    for name, (fn, description) in EXPORTS.items():
        frame = fn(df)
        frame.to_csv(os.path.join(out_dir, name), index=False)
        print(f"  {name:28s} {len(frame):4d} rows  — {description}")
        lines.append(f"| `{name}` | {description} |")

    for name, key in PRECISE.items():
        frame = precise_table(df, key)
        frame.to_csv(os.path.join(out_dir, name), index=False)
        print(f"  {name:28s} {len(frame):4d} rows  — unrounded sums by {key}")
        lines.append(f"| `{name}` | Unrounded deal count and volume by {key} |")

    quality = C.data_quality_report(input_path, df)
    quality.to_csv(os.path.join(out_dir, "data_quality.csv"), index=False)
    lines.append("| `data_quality.csv` | Cleaning rules applied, with records affected |")
    print(f"  {'data_quality.csv':28s} {len(quality):4d} rows")

    with open(os.path.join(out_dir, "headline_metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, sort_keys=True)
    lines.append("| `headline_metrics.json` | Totals, coverage, counts and shares |")
    print(f"  {'headline_metrics.json':28s}       — {len(metrics)} metrics")

    with open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    return metrics


def main() -> None:
    """Parse arguments and export."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(
        description="Export derived aggregates from the CBI extract",
        epilog="The source extract is not redistributed in this repository; "
               "supply your own copy with --input.")
    parser.add_argument("--input", default=os.path.join(here, "data", "cbi_newsmakers.csv"))
    parser.add_argument("--out-dir", default=os.path.join(here, "data", "aggregates"))
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise SystemExit(
            f"Source extract not found at {args.input}.\n"
            "It is deliberately not committed — see DATA.md. Supply your own copy "
            "with --input.")

    metrics = build(args.input, args.out_dir)
    print(f"\n{metrics['total_deals']:,} deals · ${metrics['total_volume_usd_bn']:,.2f}bn · "
          f"{metrics['year_min']}–{metrics['year_max']} → {args.out_dir}")


if __name__ == "__main__":
    main()
