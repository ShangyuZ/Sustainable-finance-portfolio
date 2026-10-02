"""Shared fixtures and import paths for the portfolio test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
PROJECT1 = ROOT / "project1-green-bond-analysis"
PROJECT2 = ROOT / "project2-sll-structuring"
PROJECT3 = ROOT / "project3-climate-dashboard"

# These are plain scripts rather than installed packages.
sys.path.insert(0, str(PROJECT1 / "scripts"))
sys.path.insert(0, str(PROJECT2 / "scripts"))
sys.path.insert(0, str(PROJECT3))


@pytest.fixture(scope="session")
def cbi_csv() -> Path:
    """Path to the committed CBI extract."""
    path = PROJECT1 / "data" / "cbi_newsmakers.csv"
    if not path.exists():
        pytest.skip(f"source extract not present: {path}")
    return path


@pytest.fixture(scope="session")
def bonds(cbi_csv: Path) -> pd.DataFrame:
    """The cleaned bond dataset, loaded once per session."""
    import clean

    return clean.load(str(cbi_csv))


@pytest.fixture
def dirty_bonds() -> pd.DataFrame:
    """
    A small frame reproducing every defect the cleaner is supposed to handle.

    Deliberately includes the "0" sector sentinel, a NaN sector, duplicate
    country labels, a trailing-space country, and an issuer case variant.
    """
    return pd.DataFrame({
        "Issuer Name": ["GoodLeap LLC", "GoodLeap LLC", "Goodleap LLC", "Acme SA",
                        "Banco Uno", "Banco Uno"],
        "Theme": ["Green", "Green", "Green", "SLB", "Sustainability", "Social"],
        "Issue Date": ["2022-01-01", "2022-02-01", "2023-03-01", "2023-04-01",
                       "2024-05-01", "2024-06-01"],
        "Amount Issued": [1e8, 2e8, 3e8, 4e8, 5e8, 6e8],
        "Currency": ["USD"] * 6,
        "Amount (USD)": [1e8, 2e8, 3e8, 4e8, 5e8, 6e8],
        "Country": ["USA", "United States", "USA", "Netherlands ", "UK",
                    "United Kingdom"],
        "Sector": ["0", None, "Commercial Bank", "Finance", "Industry", "Sovereign"],
        "Year": [2022, 2022, 2023, 2023, 2024, 2024],
        "Amount_USD_bn": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
    })


@pytest.fixture
def dirty_csv(tmp_path: Path, dirty_bonds: pd.DataFrame) -> Path:
    """The dirty frame written to disk, for testing ``clean.load`` end to end."""
    path = tmp_path / "dirty.csv"
    dirty_bonds.to_csv(path, index=False)
    return path


@pytest.fixture
def owid_like() -> pd.DataFrame:
    """
    A synthetic OWID-shaped frame: real countries, OWID aggregates, and a sparse
    final year that must not be chosen as a ranking reference year.
    """
    rows = []
    for year in (2020, 2021, 2022):
        for i in range(50):
            rows.append({
                "country": f"Country{i}",
                "iso_code": f"C{i:02d}",
                "year": year,
                "co2_per_capita": 5.0 + i * 0.1,
                "renewables_share_elec": 20.0 + i * 0.5,
                "fossil_share_elec": 50.0,
                "nuclear_share_elec": 10.0,
            })
    # Sparse newest year: only 3 countries report.
    for i in range(3):
        rows.append({
            "country": f"Country{i}", "iso_code": f"C{i:02d}", "year": 2023,
            "co2_per_capita": 4.0, "renewables_share_elec": 30.0,
            "fossil_share_elec": 50.0, "nuclear_share_elec": 10.0,
        })
    # OWID aggregates, which must be filtered out.
    for name, iso in [("Africa", "OWID_AFR"), ("World", "OWID_WRL"),
                      ("European Union (27)", "OWID_EU27")]:
        rows.append({
            "country": name, "iso_code": iso, "year": 2022,
            "co2_per_capita": 4.5, "renewables_share_elec": 25.0,
            "fossil_share_elec": 50.0, "nuclear_share_elec": 10.0,
        })
    # A row with no ISO code at all.
    rows.append({
        "country": "Kosovo", "iso_code": None, "year": 2022,
        "co2_per_capita": 4.0, "renewables_share_elec": 5.0,
        "fossil_share_elec": 90.0, "nuclear_share_elec": 0.0,
    })
    return pd.DataFrame(rows)
