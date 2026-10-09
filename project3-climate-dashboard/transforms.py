"""
Pure data transforms for the climate dashboard
==============================================
No Streamlit, no network, no caching — every function here is a plain function
over plain data, so the logic that is easy to get wrong can be unit-tested
without spinning up an app or downloading 23MB of CSV.

``app.py`` imports from this module; the Streamlit layer keeps only I/O,
caching and layout.
"""

from __future__ import annotations

import pandas as pd

# A reference year is only usable for a cross-country ranking if enough
# countries report every column the view needs. OWID's newest year always
# covers a partial set of reporters.
MIN_COUNTRIES_FOR_RANKING = 40

# These three partition electricity generation and sum to ~100%.
TOP_LEVEL_MIX: dict[str, str] = {
    "fossil_share_elec": "Fossil fuels",
    "renewables_share_elec": "Renewables",
    "nuclear_share_elec": "Nuclear",
}

# Components of renewables_share_elec — these sum to the renewables total, so
# they must NOT be plotted in the same pie as "Renewables" itself.
RENEWABLE_PARTS: dict[str, str] = {
    "hydro_share_elec": "Hydro",
    "wind_share_elec": "Wind",
    "solar_share_elec": "Solar",
    "other_renewables_share_elec": "Other renewables",
}


def sovereign_only(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop OWID's aggregate rows, keeping sovereign countries.

    Aggregates ("Africa", "High-income countries", "European Union (27)") either
    carry no ISO code or an ``OWID_``-prefixed one, so requiring a plain
    three-letter code removes all of them. An explicit exclusion list — the
    approach this replaced — misses dozens.
    """
    # Missing codes are filled before the string tests: under pandas 2 an object
    # column returns None from ``.str`` for them, and ``~None`` raises.
    iso = df["iso_code"].fillna("").astype(str)
    return df[(iso.str.len() == 3) & ~iso.str.startswith("OWID")]


def latest_complete_year(df: pd.DataFrame, cols: list[str],
                         min_countries: int = MIN_COUNTRIES_FOR_RANKING) -> int | None:
    """
    Newest year in which at least ``min_countries`` rows report every column in ``cols``.

    ``df["year"].max()`` is the wrong choice for a ranking: OWID publishes a
    newest year covering only partial reporters (in the energy dataset, ~90
    countries and no emissions data at all), which yields an empty or badly
    unrepresentative table. Returns ``None`` if no year qualifies.
    """
    missing = [c for c in cols if c not in df.columns]
    if missing or df.empty:
        return None
    for year in sorted(df["year"].unique(), reverse=True):
        if df.loc[df["year"] == year, cols].dropna().shape[0] >= min_countries:
            return int(year)
    return None


def mix_shares(row: pd.Series, mapping: dict[str, str]) -> dict[str, float]:
    """
    Map column -> label for one country-year row, dropping missing and zero shares.

    ``mapping`` must contain only columns that partition the same total; mixing
    :data:`TOP_LEVEL_MIX` with :data:`RENEWABLE_PARTS` double-counts, because
    hydro/wind/solar are already inside the renewables share.
    """
    out: dict[str, float] = {}
    for key, label in mapping.items():
        val = row.get(key)
        if val is not None and pd.notna(val) and float(val) > 0:
            out[label] = float(val)
    return out


def default_weights(n: int) -> list[float]:
    """
    ``n`` equal portfolio weights summing to exactly 100.

    ``[round(100/n, 1)] * n`` does not sum to 100 for several n (n=14 gives
    99.4), which tripped the "adjust to 100%" warning on an untouched form. The
    rounding residual is absorbed into the first weight.
    """
    if n < 1:
        raise ValueError("n must be at least 1")
    each = round(100.0 / n, 1)
    weights = [each] * n
    weights[0] = round(each + (100.0 - each * n), 1)
    return weights


def waci(weights_pct: pd.Series | list[float],
         intensities: pd.Series | list[float]) -> float:
    """
    Weighted Average Carbon Intensity: sum(weight% / 100 x sector intensity).

    This is the TCFD-aligned definition. It is only comparable to a benchmark
    when the weights total 100 — see :func:`rescale_waci`.
    """
    w = pd.Series(list(weights_pct), dtype="float64")
    i = pd.Series(list(intensities), dtype="float64")
    if len(w) != len(i):
        raise ValueError("weights and intensities must be the same length")
    return float((w / 100.0 * i).sum())


def rescale_waci(raw_waci: float, total_weight_pct: float) -> float:
    """
    Restate a WACI as if the entered weights summed to 100.

    Weights totalling 90% scale the WACI down by a tenth, which reads as a
    lower-carbon portfolio when it is really an incomplete one.
    """
    if total_weight_pct <= 0:
        return 0.0
    return raw_waci * 100.0 / total_weight_pct
