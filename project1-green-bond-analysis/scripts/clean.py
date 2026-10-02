"""
Green Bond Market Analysis — data cleaning & aggregation
========================================================
Pure-pandas layer: loading, normalisation and aggregation. No Excel concerns
here, so every function below is directly unit-testable.

The CBI News Makers extract is dirty in four specific ways, all handled here and
documented on the "1. Data Quality" sheet of the generated workbook:

  1. ``Sector`` uses the string ``"0"`` as a missing-value sentinel (64 rows) and
     has one true NaN.
  2. ``Sector`` taxonomy is fragmented — "Financials" / "Financial" / "Finance" /
     "Banks" / "Commercial Bank" / "Diversified Banks" / "Financial Institution"
     all denote the same group.
  3. ``Country`` carries duplicate labels for one country: "USA" vs
     "United States", "UK" vs "United Kingdom", ``"Netherlands "`` (trailing
     space) vs "Netherlands", and "Supernational" (misspelt) vs "Supranational".
  4. ``Issuer Name`` has case variants ("GoodLeap LLC" vs "Goodleap LLC").

Left un-normalised, (2) and (3) split real volume across separate rows and
understate both the sector and the country rankings.
"""

from __future__ import annotations

import pandas as pd

# Column holding USD volume in billions, as produced by the CSV extract.
VOL = "Amount_USD_bn"

# ── normalisation maps ────────────────────────────────────────────────────────
# Each key is a raw label as it appears in the source extract; each value is the
# canonical label used throughout the analysis. Mappings are deliberately
# explicit (rather than fuzzy-matched) so a reviewer can audit every decision.

SECTOR_MAP: dict[str, str] = {
    # Sovereign & public sector
    "Sovereign": "Sovereign",
    "Government": "Sovereign",
    # Financials — incl. leasing, which is balance-sheet lending
    "Commercial Bank": "Financials",
    "Banks": "Financials",
    "Diversified Banks": "Financials",
    "Financials": "Financials",
    "Financial": "Financials",
    "Finance": "Financials",
    "Financial Institution": "Financials",
    "Investment Company": "Financials",
    "Leasing": "Financials",
    # Industrials — "Industry (Transport)" keeps the source's primary label
    # ("Industry") rather than being reclassified on the parenthetical.
    "Industry": "Industrials",
    "Industrials": "Industrials",
    "Industry (Transport)": "Industrials",
    # Transport & logistics
    "Transport": "Transport & Logistics",
    "Shipping": "Transport & Logistics",
    "Airport": "Transport & Logistics",
    "Automobiles": "Transport & Logistics",
    # Energy & utilities
    "Utilities": "Utilities",
    "Energy": "Energy",
    "Oil & Gas": "Energy",
    "Renewable Energy": "Energy",
    # Materials
    "Materials": "Materials",
    "Chemicals": "Materials",
    "Paper and Pulp": "Materials",
    # Consumer & agri
    "Agri & Food": "Consumer & Agri",
    "Food & Beverage": "Consumer & Agri",
    "Food": "Consumer & Agri",
    "Consumer Discretionary": "Consumer & Agri",
    # Other
    "Real Estate": "Real Estate",
    "Communications": "Technology & Communications",
    "Hardware": "Technology & Communications",
    "Technology": "Technology & Communications",
    "Health Care": "Health Care",
}

COUNTRY_MAP: dict[str, str] = {
    "United States": "USA",
    "United Kingdom": "UK",
    "China_HK": "Hong Kong SAR",
    "Supernational": "Supranational",  # source misspelling
}

# Sentinel used by the source for "sector not disclosed".
SECTOR_MISSING = "Unclassified"

# Not a sovereign state — excluded from country counts, kept in volume totals.
NON_SOVEREIGN = {"Supranational"}


# ── loading & cleaning ───────────────────────────────────────────────────────

def normalise_sector(raw: pd.Series) -> pd.Series:
    """
    Map the fragmented source sector taxonomy onto canonical groups.

    The literal string ``"0"`` and true NaNs both become ``"Unclassified"``.
    Any label absent from :data:`SECTOR_MAP` is passed through unchanged so new
    source labels surface in the output rather than being silently dropped.
    """
    s = raw.astype("string").str.strip()
    s = s.mask(s.isin(["0", "", "nan"]))          # "0" sentinel -> missing
    return s.map(lambda v: SECTOR_MAP.get(v, v) if pd.notna(v) else v).fillna(
        SECTOR_MISSING
    )


def normalise_country(raw: pd.Series) -> pd.Series:
    """Strip whitespace and fold duplicate country labels onto one spelling."""
    s = raw.astype("string").str.strip()
    return s.replace(COUNTRY_MAP)


def normalise_issuer(raw: pd.Series) -> pd.Series:
    """
    Collapse issuer-name case variants onto their most frequent spelling.

    "GoodLeap LLC" (29 deals) and "Goodleap LLC" (4) are one issuer; keeping both
    would overstate the unique-issuer count.
    """
    s = raw.astype("string").str.strip()
    key = s.str.casefold()
    canonical = (
        pd.DataFrame({"key": key, "name": s})
        .groupby("key")["name"]
        .agg(lambda g: g.mode().iat[0])
    )
    return key.map(canonical)


def load(path: str, min_year: int = 2015) -> pd.DataFrame:
    """
    Load and clean the CBI News Makers extract.

    Coerces ``Year`` and volume to numeric, normalises the sector, country and
    issuer columns, and restricts to ``min_year`` onwards. Returns a frame with
    the canonical columns used by every aggregation below.
    """
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df[VOL] = pd.to_numeric(df[VOL], errors="coerce")

    df["Theme"] = df["Theme"].astype("string").str.strip()
    df["Sector"] = normalise_sector(df["Sector"])
    df["Country"] = normalise_country(df["Country"])
    df["Issuer Name"] = normalise_issuer(df["Issuer Name"])

    df = df.dropna(subset=["Year"])
    df = df[df["Year"] >= min_year]
    df["Year"] = df["Year"].astype(int)
    return df.reset_index(drop=True)


# ── aggregations ─────────────────────────────────────────────────────────────

def annual_issuance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate by year.

    Columns: Year, Deals, Volume_USD_bn, YoY_Deals_Pct, YoY_Volume_Pct.
    """
    agg = (
        df.groupby("Year")
        .agg(Deals=("Year", "size"), Volume_USD_bn=(VOL, "sum"))
        .reset_index()
        .sort_values("Year")
    )
    agg["YoY_Deals_Pct"] = agg["Deals"].pct_change() * 100
    agg["YoY_Volume_Pct"] = agg["Volume_USD_bn"].pct_change() * 100
    return agg.round(2).reset_index(drop=True)


def geographic(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Top ``top_n`` countries by USD volume, with deal count and volume share."""
    agg = (
        df.groupby("Country")
        .agg(Deals=("Country", "size"), Volume_USD_bn=(VOL, "sum"))
        .sort_values("Volume_USD_bn", ascending=False)
        .reset_index()
    )
    agg["Share_of_Volume_Pct"] = agg["Volume_USD_bn"] / agg["Volume_USD_bn"].sum() * 100
    return agg.head(top_n).round(2)


def sector(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate by canonical sector, sorted by USD volume descending."""
    agg = (
        df.groupby("Sector")
        .agg(Deals=("Sector", "size"), Volume_USD_bn=(VOL, "sum"))
        .sort_values("Volume_USD_bn", ascending=False)
        .reset_index()
    )
    agg["Share_of_Volume_Pct"] = agg["Volume_USD_bn"] / agg["Volume_USD_bn"].sum() * 100
    return agg.round(2)


def theme_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate by bond theme, sorted by USD volume descending."""
    agg = (
        df.groupby("Theme")
        .agg(Deals=("Theme", "size"), Volume_USD_bn=(VOL, "sum"))
        .sort_values("Volume_USD_bn", ascending=False)
        .reset_index()
    )
    agg["Share_of_Volume_Pct"] = agg["Volume_USD_bn"] / agg["Volume_USD_bn"].sum() * 100
    agg["Share_of_Deals_Pct"] = agg["Deals"] / agg["Deals"].sum() * 100
    return agg.round(2)


def theme_evolution(df: pd.DataFrame, values: str = "deals") -> pd.DataFrame:
    """
    Pivot Year x Theme to show how the instrument mix has shifted.

    ``values="deals"`` counts transactions; ``values="volume"`` sums USD bn.
    """
    if values not in {"deals", "volume"}:
        raise ValueError("values must be 'deals' or 'volume'")
    if values == "deals":
        out = df.pivot_table(
            index="Year", columns="Theme", values=VOL, aggfunc="size", fill_value=0
        )
    else:
        out = df.pivot_table(
            index="Year", columns="Theme", values=VOL, aggfunc="sum", fill_value=0
        ).round(2)
    out.columns.name = None
    return out.reset_index()


def slb_vs_green(df: pd.DataFrame) -> pd.DataFrame:
    """
    SLB vs green issuance by year, with SLB share measured two ways.

    ``SLB_Share_of_Green_SLB_Pct`` is SLB / (Green + SLB) — the like-for-like
    comparison. ``SLB_Share_of_All_Pct`` is SLB / all labelled issuance that
    year, which is the figure to quote for market penetration.
    """
    vol = df.pivot_table(index="Year", columns="Theme", values=VOL, aggfunc="sum",
                         fill_value=0.0)
    total = df.groupby("Year")[VOL].sum()
    green = vol.get("Green", pd.Series(0.0, index=vol.index))
    slb = vol.get("SLB", pd.Series(0.0, index=vol.index))

    out = pd.DataFrame({
        "Year": vol.index,
        "Green_USD_bn": green.values,
        "SLB_USD_bn": slb.values,
        "All_Themes_USD_bn": total.reindex(vol.index).values,
    })
    pair = out["Green_USD_bn"] + out["SLB_USD_bn"]
    out["SLB_Share_of_Green_SLB_Pct"] = (out["SLB_USD_bn"] / pair * 100).where(pair > 0, 0.0)
    out["SLB_Share_of_All_Pct"] = (
        out["SLB_USD_bn"] / out["All_Themes_USD_bn"] * 100
    ).where(out["All_Themes_USD_bn"] > 0, 0.0)
    return out.round(2).reset_index(drop=True)


def top_issuers(df: pd.DataFrame, theme: str | None = None, top_n: int = 10) -> pd.DataFrame:
    """Top issuers by USD volume, optionally restricted to a single theme."""
    sub = df if theme is None else df[df["Theme"] == theme]
    return (
        sub.groupby("Issuer Name")
        .agg(Deals=("Issuer Name", "size"), Volume_USD_bn=(VOL, "sum"),
             Country=("Country", lambda s: s.mode().iat[0] if len(s) else ""))
        .sort_values("Volume_USD_bn", ascending=False)
        .head(top_n)
        .reset_index()
        .round(2)
    )


def data_quality_report(raw_path: str, clean: pd.DataFrame) -> pd.DataFrame:
    """
    Compare the raw extract against the cleaned frame.

    Returns one row per cleaning rule with the number of records affected, so the
    workbook can show exactly what the pipeline changed and why.
    """
    raw = pd.read_csv(raw_path)
    raw_sector = raw["Sector"].astype("string").str.strip()
    raw_country = raw["Country"].astype("string").str.strip()

    n_sentinel = int((raw_sector == "0").sum())
    n_null_sector = int(raw_sector.isna().sum())
    n_country_dupes = int(raw_country.isin(COUNTRY_MAP).sum())
    n_ws = int((raw["Country"].astype("string") != raw_country).sum())
    n_issuer_dupes = int(
        raw["Issuer Name"].nunique() - raw["Issuer Name"].str.strip().str.casefold().nunique()
    )
    # Records whose sector label was renamed by the fold (excludes the "0"/NaN
    # rows, which are counted separately above).
    n_sector_folded = int(
        raw_sector.isin([k for k, v in SECTOR_MAP.items() if k != v]).sum()
    )

    rows = [
        ("Sector sentinel \"0\" -> Unclassified", n_sentinel,
         "Source encodes undisclosed sector as the string \"0\"; left as-is it "
         "appears as a sector named \"0\" in the breakdown."),
        ("Sector missing (true NaN) -> Unclassified", n_null_sector,
         "Grouped with the sentinel rows so unclassified volume is explicit."),
        (f"Sector labels folded ({len(SECTOR_MAP)} raw -> "
         f"{len(set(SECTOR_MAP.values()))} canonical)", n_sector_folded,
         "e.g. Financials/Financial/Finance/Banks/Commercial Bank all denote the "
         "same group; unfolded they split one sector across several rows."),
        ("Country duplicate labels folded", n_country_dupes,
         "USA/United States, UK/United Kingdom, China_HK, Supernational/"
         "Supranational — split volume across rows and inflated the country count."),
        ("Country whitespace stripped", n_ws,
         "\"Netherlands \" (trailing space) was aggregating separately from "
         "\"Netherlands\"."),
        ("Issuer name case variants folded", n_issuer_dupes,
         "GoodLeap LLC / Goodleap LLC — one issuer counted twice."),
    ]
    return pd.DataFrame(rows, columns=["Cleaning rule", "Records affected", "Why it matters"])


def headline_metrics(df: pd.DataFrame) -> dict[str, object]:
    """Compute the dashboard KPIs from the cleaned frame, so nothing is hardcoded."""
    agg = annual_issuance(df)
    themes = theme_totals(df)
    countries = df.loc[~df["Country"].isin(NON_SOVEREIGN), "Country"].nunique()
    green = themes.loc[themes["Theme"] == "Green"]
    peak = agg.loc[agg["Volume_USD_bn"].idxmax()]
    return {
        "total_volume_usd_bn": round(float(df[VOL].sum()), 2),
        "total_deals": int(len(df)),
        "year_min": int(df["Year"].min()),
        "year_max": int(df["Year"].max()),
        "n_years": int(df["Year"].nunique()),
        "countries": int(countries),
        "issuers": int(df["Issuer Name"].nunique()),
        "green_share_deals_pct": round(float(green["Share_of_Deals_Pct"].iat[0]), 1) if len(green) else 0.0,
        "green_share_volume_pct": round(float(green["Share_of_Volume_Pct"].iat[0]), 1) if len(green) else 0.0,
        "peak_volume_year": int(peak["Year"]),
        "peak_volume_usd_bn": round(float(peak["Volume_USD_bn"]), 2),
        "unclassified_volume_usd_bn": round(
            float(df.loc[df["Sector"] == SECTOR_MISSING, VOL].sum()), 2),
    }
