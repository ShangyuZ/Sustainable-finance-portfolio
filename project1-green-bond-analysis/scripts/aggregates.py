"""
Aggregates — the single set of tables the workbook and tests are built from
==========================================================================
One container, two sources.

``Aggregates.from_raw`` computes everything from the source extract via
``clean.py``. ``Aggregates.from_dir`` reads the same tables back from the
committed CSVs in ``data/aggregates/``.

Why the indirection: Climate Bonds Initiative's terms of use prohibit
reproducing or storing their content without prior written permission, so the
record-level extract is not redistributed in this repository (see DATA.md).
Routing the presentation layer through this container means the workbook, the
brief and the test suite all run off the committed aggregates — the published
figures stay reproducible and verifiable — while the raw records stay with
whoever licensed them.

``from_raw`` and ``from_dir`` return byte-identical tables for the same input;
``tests/test_aggregates.py`` asserts it whenever the extract is available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, fields

import pandas as pd

import clean as C

DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "aggregates")

# field name -> committed filename
TABLES = {
    "annual": "annual_issuance.csv",
    "country": "by_country.csv",
    "sector": "by_sector.csv",
    "theme": "by_theme.csv",
    "slb": "slb_vs_green.csv",
    "theme_deals": "theme_by_year_deals.csv",
    "theme_volume": "theme_by_year_volume.csv",
    "top_slb": "top_issuers_slb.csv",
    "quality": "data_quality.csv",
    "annual_precise": "annual_precise.csv",
    "sector_precise": "sector_precise.csv",
    "theme_precise": "theme_precise.csv",
}

# Grouping key of each full-precision companion table.
PRECISE_KEYS = {"annual_precise": "Year", "sector_precise": "Sector",
                "theme_precise": "Theme"}
METRICS_FILE = "headline_metrics.json"

# Countries kept in the committed geography table. The full extract has 64;
# every published ranking is a prefix of the top 25, so the tail is not needed.
COUNTRY_TOP_N = 25


def _precise(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    Unrounded deal count and volume by ``key``.

    The presentation tables round to 2dp, which is right for a workbook but
    wrong as the source for a figure quoted to 1dp: rounding an already-rounded
    number shifts it. 2022 volume is 140.3479 — 140.3 to one decimal, but the
    2dp value 140.35 rounds up to 140.4. These tables keep full precision so the
    brief's figures are checked against the real sums.
    """
    out = (df.groupby(key)
             .agg(Deals=(C.VOL, "size"), Volume_USD_bn=(C.VOL, "sum"))
             .reset_index())
    return out.sort_values(key).reset_index(drop=True)


@dataclass(frozen=True)
class Aggregates:
    """Every table the workbook presents, plus the headline metrics."""

    annual: pd.DataFrame
    country: pd.DataFrame
    sector: pd.DataFrame
    theme: pd.DataFrame
    slb: pd.DataFrame
    theme_deals: pd.DataFrame
    theme_volume: pd.DataFrame
    top_slb: pd.DataFrame
    quality: pd.DataFrame
    annual_precise: pd.DataFrame
    sector_precise: pd.DataFrame
    theme_precise: pd.DataFrame
    metrics: dict

    @classmethod
    def from_raw(cls, input_path: str, min_year: int = 2015) -> "Aggregates":
        """Compute every table from the source extract."""
        df = C.load(input_path, min_year=min_year)
        return cls(
            annual=C.annual_issuance(df),
            country=C.geographic(df, top_n=COUNTRY_TOP_N),
            sector=C.sector(df),
            theme=C.theme_totals(df),
            slb=C.slb_vs_green(df),
            theme_deals=C.theme_evolution(df, "deals"),
            theme_volume=C.theme_evolution(df, "volume"),
            top_slb=C.top_issuers(df, theme="SLB", top_n=10),
            quality=C.data_quality_report(input_path, df),
            annual_precise=_precise(df, "Year"),
            sector_precise=_precise(df, "Sector"),
            theme_precise=_precise(df, "Theme"),
            metrics=C.headline_metrics(df),
        )

    @classmethod
    def from_dir(cls, path: str = DEFAULT_DIR) -> "Aggregates":
        """Read every table back from the committed CSVs."""
        missing = [f for f in list(TABLES.values()) + [METRICS_FILE]
                   if not os.path.exists(os.path.join(path, f))]
        if missing:
            raise FileNotFoundError(
                f"Missing aggregate files in {path}: {', '.join(missing)}. "
                "Regenerate with scripts/export_aggregates.py --input <extract>.")

        tables = {name: pd.read_csv(os.path.join(path, fname))
                  for name, fname in TABLES.items()}
        with open(os.path.join(path, METRICS_FILE), encoding="utf-8") as fh:
            tables["metrics"] = json.load(fh)
        return cls(**tables)

    @classmethod
    def load(cls, raw_path: str | None = None, agg_dir: str = DEFAULT_DIR,
             min_year: int = 2015) -> "Aggregates":
        """Prefer the raw extract when one is supplied, else the committed aggregates."""
        if raw_path and os.path.exists(raw_path):
            return cls.from_raw(raw_path, min_year=min_year)
        return cls.from_dir(agg_dir)

    def countries(self, top_n: int) -> pd.DataFrame:
        """Top ``top_n`` countries. Shares are of total volume, so slicing is safe."""
        if top_n > len(self.country):
            raise ValueError(
                f"Committed geography table holds {len(self.country)} countries; "
                f"{top_n} requested.")
        return self.country.head(top_n).reset_index(drop=True)

    def row(self, table: str, key_column: str, key) -> pd.Series:
        """One row of a table, looked up by value — raises rather than returning NaN."""
        frame = getattr(self, table)
        hit = frame.loc[frame[key_column] == key]
        if hit.empty:
            raise KeyError(f"No {key_column}={key!r} in {table}")
        return hit.iloc[0]

    def precise(self, table: str, key) -> pd.Series:
        """One row of a full-precision companion table, by its grouping key."""
        return self.row(table, PRECISE_KEYS[table], key)

    def total_volume(self) -> float:
        """Dataset volume at full precision, from the unrounded annual table."""
        return float(self.annual_precise["Volume_USD_bn"].sum())

    def to_dir(self, path: str) -> None:
        """Write every table out in the committed layout."""
        os.makedirs(path, exist_ok=True)
        for name, fname in TABLES.items():
            getattr(self, name).to_csv(os.path.join(path, fname), index=False)
        with open(os.path.join(path, METRICS_FILE), "w", encoding="utf-8") as fh:
            json.dump(self.metrics, fh, indent=2, sort_keys=True)

    def frames(self) -> dict:
        """Every table by name, metrics excluded."""
        return {f.name: getattr(self, f.name) for f in fields(self) if f.name != "metrics"}
