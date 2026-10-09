"""
Climate & Energy Transition Dashboard
======================================
No API keys required. Data:
  • Our World in Data — energy dataset (CC BY 4.0) — electricity mix by country
  • Our World in Data — CO2 dataset   (CC BY 4.0) — emissions by country
  • Bundled EUA prices — indicative and uncited (see DATA.md), not a reference series
  • Sector carbon intensities in the calculator — assumed illustrative inputs

Note on the two OWID datasets: emissions columns (``co2``, ``co2_per_capita``)
live in OWID's co2-data repository, NOT in the energy dataset. They are loaded
separately and merged on (country, year); reading them off the energy dataset
silently yields nothing.

Run:  streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from transforms import (
    MIN_COUNTRIES_FOR_RANKING,
    RENEWABLE_PARTS,
    TOP_LEVEL_MIX,
    default_weights,
    latest_complete_year,
    mix_shares,
    rescale_waci,
    sovereign_only,
    waci as compute_waci,
)

# ── paths ──────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
EUA_CSV  = DATA_DIR / "eua_prices.csv"

OWID_ENERGY_URL = (
    "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
)
OWID_CO2_URL = (
    "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
)


# ── page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Climate Finance Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── data loaders ──────────────────────────────────────────────────────────

@st.cache_data(ttl=86_400, show_spinner="Loading energy data from Our World in Data…")
def load_owid() -> pd.DataFrame:
    """Load the OWID energy dataset (electricity mix, renewables shares)."""
    try:
        df = pd.read_csv(OWID_ENERGY_URL, low_memory=False)
    except Exception as exc:
        st.error(f"Could not load OWID energy data: {exc}")
        return pd.DataFrame()
    return sovereign_only(df)[lambda d: d["year"] >= 2000].reset_index(drop=True)


@st.cache_data(ttl=86_400, show_spinner="Loading emissions data from Our World in Data…")
def load_owid_co2() -> pd.DataFrame:
    """
    Load the OWID CO2 dataset.

    Separate from the energy dataset: ``co2`` and ``co2_per_capita`` exist only
    here. Only the columns actually used are read, since the full file is ~14MB.
    """
    want = ["country", "year", "iso_code", "population", "co2", "co2_per_capita"]
    try:
        df = pd.read_csv(OWID_CO2_URL, usecols=want, low_memory=False)
    except Exception as exc:
        st.error(f"Could not load OWID CO2 data: {exc}")
        return pd.DataFrame()
    return sovereign_only(df)[lambda d: d["year"] >= 2000].reset_index(drop=True)


@st.cache_data(ttl=86_400, show_spinner="Combining energy and emissions data…")
def load_climate() -> pd.DataFrame:
    """
    Inner-join the energy and CO2 datasets on (country, year).

    Returns an empty frame if either source failed, so callers need only one
    emptiness check.
    """
    energy, co2 = load_owid(), load_owid_co2()
    if energy.empty or co2.empty:
        return pd.DataFrame()
    return energy.merge(
        co2.drop(columns=["iso_code"]), on=["country", "year"], how="inner"
    )


@st.cache_data(ttl=3_600)
def load_eua_prices() -> pd.DataFrame:
    """
    Load EU ETS EUA spot price history from the bundled CSV.

    Falls back to an illustrative synthetic trajectory only if the bundled file
    is missing, so the app still renders rather than crashing; the caption on the
    chart tells the reader which of the two they are looking at.
    """
    if EUA_CSV.exists():
        df = pd.read_csv(EUA_CSV)
        df["date"] = pd.to_datetime(df["date"])
        df = df.rename(columns={"date": "Date", "price_eur_t": "Price (€/tCO₂)"})
        df.attrs["synthetic"] = False
        return df.sort_values("Date").reset_index(drop=True)

    # Fallback — should never be reached if data/ is present.
    import numpy as np
    np.random.seed(42)
    dates = pd.date_range("2018-01-01", "2026-06-01", freq="W")
    prices = (8 + np.linspace(0, 80, len(dates))).clip(min=4).round(2)
    out = pd.DataFrame({"Date": dates, "Price (€/tCO₂)": prices})
    out.attrs["synthetic"] = True
    return out


# ── sidebar ────────────────────────────────────────────────────────────────

st.sidebar.title("🌿 Climate Finance")
st.sidebar.caption("ShangyuZ · UCL · BSc Stats, Economics & Finance")
st.sidebar.divider()

SECTIONS = [
    "🏭 EU Carbon Price",
    "⚡ Energy Transition",
    "🏆 Country Climate Scorecard",
    "🌍 Portfolio Carbon Calculator",
]
section = st.sidebar.radio("Dashboard section", SECTIONS)

st.sidebar.divider()
st.sidebar.caption(
    "**Data sources**\n\n"
    "[OWID energy dataset](https://github.com/owid/energy-data) (CC BY 4.0)\n\n"
    "[OWID CO2 dataset](https://github.com/owid/co2-data) (CC BY 4.0)\n\n"
    "EUA prices: indicative, uncited series (see DATA.md)\n\n"
    "Carbon calculator: assumed sector intensities"
)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 1 — EU Carbon Price
# ══════════════════════════════════════════════════════════════════════════

if section == "🏭 EU Carbon Price":
    st.title("EU ETS Carbon Price")
    st.caption(
        "European Union Allowance (EUA) weekly spot price — indicative series "
        "compiled from public sources, not a reference price. It tracks the broad "
        "path of the market but is approximate: it understates the March 2022 "
        "post-invasion drawdown and the February 2023 peak. See DATA.md."
    )

    df = load_eua_prices()

    # Guard: should always have data, but be safe
    if df.empty or "Price (€/tCO₂)" not in df.columns:
        st.error("EUA price data unavailable.")
        st.stop()

    # Never present the synthetic fallback as if it were real market data.
    if df.attrs.get("synthetic"):
        st.warning(
            "**Illustrative data.** `data/eua_prices.csv` is missing, so the chart "
            "below shows a synthetic trajectory, not real EUA prices. Restore the "
            "bundled file for actual history."
        )

    latest     = float(df["Price (€/tCO₂)"].iloc[-1])
    all_time_h = float(df["Price (€/tCO₂)"].max())
    this_year  = int(df["Date"].dt.year.max())
    ytd        = df[df["Date"].dt.year == this_year]["Price (€/tCO₂)"]
    yr_start   = float(ytd.iloc[0])
    # A single observation in the latest year gives a meaningless 0.0% YTD.
    ytd_pct    = (latest / yr_start - 1) * 100 if len(ytd) > 1 and yr_start else None

    c1, c2, c3 = st.columns(3)
    c1.metric("Latest Price",  f"€{latest:.1f} / tCO₂")
    c2.metric(f"YTD Change ({this_year})",
              "n/a" if ytd_pct is None else f"{ytd_pct:+.1f}%")
    c3.metric("All-time High", f"€{all_time_h:.1f}")

    # Policy event annotations
    events = {
        "2019-01-14": "MSR reform live",
        "2021-07-14": "Fit for 55 package",
        "2022-02-24": "Ukraine invasion",
        "2023-04-18": "ETS reform + CBAM agreed",
    }

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Price (€/tCO₂)"],
        mode="lines",
        line=dict(color="#1A7A4A", width=2),
        fill="tozeroy",
        fillcolor="rgba(26,122,74,0.08)",
        name="EUA price",
        hovertemplate="%{x|%d %b %Y}<br>€%{y:.2f}<extra></extra>",
    ))

    for date_str, label in events.items():
        d = pd.to_datetime(date_str)
        row = df[df["Date"] >= d]
        if row.empty:
            continue
        price = float(row["Price (€/tCO₂)"].iloc[0])
        fig.add_vline(x=d, line_dash="dot", line_color="#aaa", opacity=0.7)
        fig.add_annotation(
            x=d, y=price + 4, text=label,
            showarrow=False, font=dict(size=9, color="#555"), textangle=-30,
        )

    fig.update_layout(
        title="EUA Spot Price — Weekly Close",
        yaxis_title="€ per tCO₂",
        xaxis_title="",
        plot_bgcolor="white",
        hovermode="x unified",
        margin=dict(t=50, b=30),
    )
    st.plotly_chart(fig, width="stretch")

    with st.expander("ℹ️ About EU ETS & carbon pricing"):
        st.markdown(
            """
The **EU Emissions Trading System (ETS)** is the world's largest carbon market.
Companies must hold one EU Allowance (EUA) per tonne of CO₂ they emit.
The price is set by supply and demand at auction.

**Key price drivers:**
- Energy prices (gas → coal switching demand)
- Macroeconomic conditions (industrial output)
- Policy: Market Stability Reserve (MSR) removes surplus allowances
- The 2022 spike reached ~€96/t in February before the Ukraine war disrupted energy markets
- The 2023 ETS reform introduced CBAM (Carbon Border Adjustment Mechanism) and
  accelerated the cap reduction trajectory toward net-zero
"""
        )


# ══════════════════════════════════════════════════════════════════════════
# SECTION 2 — Energy Transition
# ══════════════════════════════════════════════════════════════════════════

elif section == "⚡ Energy Transition":
    st.title("Global Energy Transition")
    st.caption("Source: Our World in Data — Energy dataset (CC BY 4.0)")

    # Merged frame: the CO₂ tab needs emissions columns, which are not in the
    # energy dataset.
    df = load_climate()
    if df.empty:
        st.warning("Could not load the OWID datasets — check your connection.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Renewable Share", "CO₂ Emissions", "Energy Mix"])

    countries_all = sorted(df["country"].dropna().unique())

    # ── Tab 1: Renewable Share ─────────────────────────────────────────────
    with tab1:
        col_name = "renewables_share_elec"
        if col_name not in df.columns:
            st.warning("Renewables share column not found in this version of the OWID dataset.")
        else:
            st.subheader("Renewables as % of electricity generation")
            defaults = [c for c in ["United Kingdom","Germany","China","United States","Denmark","India"] if c in countries_all]
            selected = st.multiselect("Countries", countries_all, default=defaults, key="ren_sel")
            yr_max = int(df.loc[df[col_name].notna(), "year"].max())
            yr_range = st.slider("Year range", 2000, yr_max, (2000, yr_max), key="ren_yr")

            filt = df[df["country"].isin(selected) & df["year"].between(*yr_range) & df[col_name].notna()]
            if filt.empty:
                st.info("No data for this selection.")
            else:
                fig = px.line(
                    filt, x="year", y=col_name, color="country",
                    labels={col_name: "Renewables (% of electricity)", "year": "Year"},
                    title="Renewable Share of Electricity Generation",
                )
                fig.update_layout(plot_bgcolor="white", hovermode="x unified")
                fig.update_traces(line_width=2)
                st.plotly_chart(fig, width="stretch")

    # ── Tab 2: CO₂ Emissions ──────────────────────────────────────────────
    with tab2:
        # 'co2' is total annual territorial CO₂ in million tonnes, from the OWID
        # CO2 dataset merged in above.
        metric = st.radio(
            "Measure", ["Total (Mt)", "Per capita (t)"], horizontal=True, key="co2_metric"
        )
        co2_col = "co2" if metric.startswith("Total") else "co2_per_capita"
        axis_label = "CO₂ (Mt)" if co2_col == "co2" else "CO₂ per capita (t)"

        if co2_col not in df.columns:
            st.warning(f"Column '{co2_col}' not present in this version of the dataset.")
        else:
            st.subheader(f"Annual CO₂ emissions — {metric.lower()}")
            defaults2 = [c for c in ["China","United States","India","Germany","United Kingdom"] if c in countries_all]
            selected2 = st.multiselect("Countries", countries_all, default=defaults2, key="co2_sel")
            yr_max2 = int(df.loc[df[co2_col].notna(), "year"].max())
            yr_range2 = st.slider("Year range", 2000, yr_max2, (2000, yr_max2), key="co2_yr")

            filt2 = df[df["country"].isin(selected2) & df["year"].between(*yr_range2) & df[co2_col].notna()]
            if filt2.empty:
                st.info("No data for this selection.")
            else:
                fig2 = px.line(
                    filt2, x="year", y=co2_col, color="country",
                    labels={co2_col: axis_label, "year": "Year"},
                    title=f"Annual CO₂ Emissions — {metric}",
                )
                fig2.update_layout(plot_bgcolor="white", hovermode="x unified")
                fig2.update_traces(line_width=2)
                st.plotly_chart(fig2, width="stretch")
                st.caption(
                    "Territorial (production-based) CO₂ from fossil fuels and industry. "
                    "Source: Our World in Data CO2 dataset (CC BY 4.0)."
                )

    # ── Tab 3: Energy Mix ─────────────────────────────────────────────────
    with tab3:
        st.subheader("Electricity mix breakdown — latest available year")

        # TOP_LEVEL_MIX partitions generation and sums to ~100%. Hydro, solar and
        # wind are COMPONENTS of renewables, so putting them in the same pie as
        # "Renewables" double-counts them — for Norway that produced a pie
        # summing to 198%. They get their own breakdown below instead.
        top_avail = {k: v for k, v in TOP_LEVEL_MIX.items() if k in df.columns}
        part_avail = {k: v for k, v in RENEWABLE_PARTS.items() if k in df.columns}

        country_choice = st.selectbox("Select country", countries_all,
                                       index=countries_all.index("United Kingdom") if "United Kingdom" in countries_all else 0)
        cdf = df[df["country"] == country_choice].sort_values("year")
        cdf_clean = cdf.dropna(subset=list(top_avail.keys()), how="all")

        if cdf_clean.empty:
            st.info(f"No electricity mix data for {country_choice}.")
        else:
            latest_row = cdf_clean.iloc[-1]

            mix_data = mix_shares(latest_row, top_avail)
            parts_data = mix_shares(latest_row, part_avail)

            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.markdown(f"**{country_choice}** — {int(latest_row['year'])}")
                for label, val in sorted(mix_data.items(), key=lambda x: -x[1]):
                    st.markdown(f"- {label}: **{val:.1f}%**")
                total = sum(mix_data.values())
                st.caption(f"Sums to {total:.1f}% of generation.")
                if parts_data:
                    st.markdown("**Renewables breakdown**")
                    for label, val in sorted(parts_data.items(), key=lambda x: -x[1]):
                        st.markdown(f"- {label}: **{val:.1f}%**")
            with col_b:
                if mix_data:
                    fig3 = px.pie(
                        names=list(mix_data.keys()),
                        values=list(mix_data.values()),
                        title=f"{country_choice} electricity mix — {int(latest_row['year'])}",
                        color_discrete_map={
                            "Fossil fuels": "#8D6E63",
                            "Renewables":   "#1A7A4A",
                            "Nuclear":      "#5C6BC0",
                        },
                    )
                    fig3.update_traces(textinfo="label+percent", sort=False)
                    st.plotly_chart(fig3, width="stretch")
                if parts_data:
                    fig4 = px.bar(
                        x=list(parts_data.values()), y=list(parts_data.keys()),
                        orientation="h",
                        title="Renewables, by source (% of total generation)",
                        labels={"x": "% of electricity generation", "y": ""},
                        color_discrete_sequence=["#1A7A4A"],
                    )
                    fig4.update_layout(plot_bgcolor="white", showlegend=False,
                                       yaxis=dict(categoryorder="total ascending"),
                                       height=260, margin=dict(t=50, b=30))
                    st.plotly_chart(fig4, width="stretch")

            st.caption(
                "Fossil / renewables / nuclear partition total generation. Hydro, "
                "wind, solar and other renewables are sub-components of the "
                "renewables slice, so they are shown separately rather than mixed "
                "into the same pie."
            )


# ══════════════════════════════════════════════════════════════════════════
# SECTION 3 — Country Climate Scorecard  (NEW)
# ══════════════════════════════════════════════════════════════════════════

elif section == "🏆 Country Climate Scorecard":
    st.title("Country Climate Scorecard")
    st.caption(
        "Ranks countries by key climate metrics — CO₂ per capita, "
        "renewable share, and rate of decarbonisation. "
        "Source: Our World in Data (CC BY 4.0)"
    )

    # Needs both datasets: co2_per_capita is not in the energy dataset.
    df = load_climate()
    if df.empty:
        st.warning("Could not load the OWID datasets — check your connection.")
        st.stop()

    needed = ["co2_per_capita", "renewables_share_elec"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        st.warning(f"Required columns missing from the dataset: {', '.join(missing)}.")
        st.stop()

    # Not df["year"].max(): OWID's newest year covers only a partial set of
    # reporters, which would leave this ranking empty or unrepresentative.
    latest_year = latest_complete_year(df, needed)
    if latest_year is None:
        st.warning(
            "No year in the dataset has enough countries reporting both CO₂ per "
            "capita and renewable share to build a ranking."
        )
        st.stop()
    prev_year = latest_year - 5   # 5-year change

    def get_year(year: int) -> pd.DataFrame:
        return (
            df[df["year"] == year][["country"] + needed]
            .dropna(subset=needed)
            .drop_duplicates(subset="country")
            .set_index("country")
        )

    latest_df = get_year(latest_year)
    prev_df   = get_year(prev_year)

    scorecard = latest_df.rename(columns={
        "co2_per_capita": "CO₂ per capita (t)",
        "renewables_share_elec": "Renewables (% elec)",
    })

    # 5-year change — index-aligned, so countries absent from prev_year get NaN
    co2_change = (latest_df["co2_per_capita"] - prev_df["co2_per_capita"]).rename("CO₂ change (5yr, t)")
    ren_change = (latest_df["renewables_share_elec"] - prev_df["renewables_share_elec"]).rename("Renewables change (5yr, pp)")

    scorecard = scorecard.join(co2_change).join(ren_change).round(2).reset_index()

    st.caption(
        f"Reference year **{latest_year}** — the most recent year with at least "
        f"{MIN_COUNTRIES_FOR_RANKING} countries reporting both metrics "
        f"({len(scorecard)} countries shown). Change columns compare against {prev_year}."
    )

    tab_a, tab_b, tab_c = st.tabs(["Rankings Table", "CO₂ vs Renewables", "Decarbonisation Rate"])

    with tab_a:
        sort_by = st.selectbox("Sort by", ["CO₂ per capita (t)", "Renewables (% elec)",
                                            "CO₂ change (5yr, t)", "Renewables change (5yr, pp)"])
        asc = sort_by.startswith("CO₂")
        # Clamp: a hardcoded (10, len, 30) raises when fewer than 30 countries
        # report both metrics, since the default would exceed the max.
        n_rows = len(scorecard)
        if n_rows <= 10:
            top_n = n_rows
            st.caption(f"Showing all {n_rows} countries with data.")
        else:
            top_n = st.slider("Show top N countries", 10, n_rows, min(30, n_rows))

        ranked = scorecard.sort_values(sort_by, ascending=asc).head(top_n).reset_index(drop=True)
        ranked.index += 1

        def colour_co2(val):
            if pd.isna(val):
                return ""
            if val < 4:
                return "background-color: #C8E6C9"
            elif val < 8:
                return "background-color: #FFF9C4"
            return "background-color: #FFCDD2"

        def colour_ren(val):
            if pd.isna(val):
                return ""
            if val >= 60:
                return "background-color: #C8E6C9"
            elif val >= 30:
                return "background-color: #FFF9C4"
            return "background-color: #FFCDD2"

        styled = ranked.style.map(colour_co2, subset=["CO₂ per capita (t)"]) \
                             .map(colour_ren, subset=["Renewables (% elec)"])
        st.dataframe(styled, width="stretch", height=500)

    with tab_b:
        st.subheader(f"CO₂ per capita vs Renewable share ({latest_year})")
        highlight = st.multiselect(
            "Highlight countries",
            scorecard["country"].tolist(),
            default=[c for c in ["United Kingdom","Germany","France","China","United States","India","Sweden","Norway"] if c in scorecard["country"].values],
        )
        plot_df = scorecard.copy()
        plot_df["Highlighted"] = plot_df["country"].isin(highlight)

        fig_sc = px.scatter(
            plot_df,
            x="Renewables (% elec)",
            y="CO₂ per capita (t)",
            hover_name="country",
            color="Highlighted",
            color_discrete_map={True: "#1A7A4A", False: "#cccccc"},
            size_max=10,
            title=f"CO₂ per capita vs Renewable electricity share ({latest_year})",
            labels={"Renewables (% elec)": "Renewables (% of electricity)", "CO₂ per capita (t)": "CO₂ per capita (tonnes)"},
        )
        fig_sc.update_traces(marker=dict(size=8, opacity=0.8))
        fig_sc.update_layout(plot_bgcolor="white", showlegend=False)

        # Annotate highlighted countries
        for _, row in plot_df[plot_df["Highlighted"]].iterrows():
            fig_sc.add_annotation(
                x=row["Renewables (% elec)"], y=row["CO₂ per capita (t)"],
                text=row["country"], showarrow=False,
                font=dict(size=9, color="#1A7A4A"), yshift=10,
            )
        st.plotly_chart(fig_sc, width="stretch")

    with tab_c:
        st.subheader(f"5-year decarbonisation: CO₂ change ({prev_year}→{latest_year})")
        decarb = scorecard.dropna(subset=["CO₂ change (5yr, t)"]) \
                          .sort_values("CO₂ change (5yr, t)") \
                          .head(25)

        fig_d = px.bar(
            decarb, x="CO₂ change (5yr, t)", y="country", orientation="h",
            title=f"Top 25 countries — CO₂ per capita reduction ({prev_year}→{latest_year})",
            labels={"CO₂ change (5yr, t)": "Change in CO₂ per capita (t)", "country": ""},
            color="CO₂ change (5yr, t)",
            color_continuous_scale=["#1A7A4A", "#FFF9C4", "#C62828"],
            color_continuous_midpoint=0,
        )
        fig_d.update_layout(plot_bgcolor="white", coloraxis_showscale=False,
                             yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig_d, width="stretch")


# ══════════════════════════════════════════════════════════════════════════
# SECTION 4 — Portfolio Carbon Calculator
# ══════════════════════════════════════════════════════════════════════════

else:
    st.title("Portfolio Carbon Intensity Calculator (illustrative)")
    st.caption(
        "An illustrative, sector-based calculator of Weighted Average Carbon "
        "Intensity (WACI), the portfolio metric recommended by the TCFD. The "
        "sector intensities are assumed inputs, not sourced figures."
    )

    # Assumed sector carbon intensities (tCO₂e per $m revenue). Round illustrative
    # numbers chosen to show the calculation, not taken from a specific
    # publication, table, date or emissions boundary.
    SECTOR_INTENSITY: dict[str, int] = {
        "Energy — Oil & Gas":        850,
        "Utilities":                  540,
        "Materials":                  430,
        "Industrials":                210,
        "Consumer Staples":           120,
        "Consumer Discretionary":      95,
        "Real Estate":                 80,
        "Healthcare":                  60,
        "Information Technology":      35,
        "Communication Services":      30,
        "Financials":                  20,
    }

    st.info(
        "Each holding is assigned the **assumed** intensity of the sector you "
        "select (tCO₂e per $m revenue). Names are labels only and do not affect "
        "the calculation. A real WACI needs each company's reported emissions "
        "and revenue."
    )

    n_hold = int(st.number_input("Number of holdings", min_value=1, max_value=20, value=4))

    weights_default = default_weights(n_hold)

    hdr = st.columns([3, 2, 3])
    hdr[0].markdown("**Ticker / Name**")
    hdr[1].markdown("**Weight (%)**")
    hdr[2].markdown("**Sector**")

    holdings: list[dict] = []
    total_w = 0.0

    for i in range(n_hold):
        c1, c2, c3 = st.columns([3, 2, 3])
        ticker = c1.text_input("name", placeholder="e.g. BP", key=f"t{i}", label_visibility="collapsed")
        weight = c2.number_input("weight", 0.0, 100.0, weights_default[i], step=0.1,
                                 key=f"w{i}", label_visibility="collapsed")
        sector = c3.selectbox("sector", list(SECTOR_INTENSITY.keys()), key=f"s{i}", label_visibility="collapsed")
        if ticker.strip():
            holdings.append({
                "Holding": ticker.strip(),
                "Weight (%)": weight,
                "Sector": sector,
                "Intensity": SECTOR_INTENSITY[sector],
            })
            total_w += weight

    if holdings:
        df_h = pd.DataFrame(holdings)
        waci = compute_waci(df_h["Weight (%)"], df_h["Intensity"])
        # WACI is only comparable at 100% weights; below that it is scaled down by
        # the shortfall rather than being a lower-carbon portfolio.
        waci_norm = rescale_waci(waci, total_w)

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Portfolio WACI", f"{waci:.0f} tCO₂e / $m rev",
                  help="Σ (weight × sector intensity). Comparable only when weights total 100%.")
        m2.metric(
            "Total weight entered", f"{total_w:.1f}%",
            delta=f"{total_w - 100:+.1f}% vs 100%",
            delta_color="inverse" if abs(total_w - 100) > 0.5 else "off",
        )
        m3.metric("Holdings entered", len(holdings))

        fig = px.bar(
            df_h.sort_values("Intensity", ascending=False),
            x="Holding", y="Intensity", color="Sector",
            title="Carbon Intensity by Holding (sector benchmark)",
            labels={"Intensity": "tCO₂e per $m revenue"},
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig, width="stretch")

        # No "high-carbon" or "low-carbon" label: there is no documented benchmark
        # behind any threshold, and the inputs themselves are assumed.
        if abs(total_w - 100) < 0.5:
            st.info(f"Illustrative portfolio WACI: {waci:.0f} tCO₂e / $m revenue.")
        else:
            st.warning(
                f"Weights sum to {total_w:.1f}%, so the WACI above is scaled by that "
                f"same shortfall and is not comparable to a benchmark. Rescaled to "
                f"100% it would be **{waci_norm:.0f}** tCO₂e / $m revenue."
            )

        st.caption(
            "**Methodology:** WACI = Σ (portfolio weight × sector carbon intensity). "
            "The sector intensities are assumed illustrative inputs; the result "
            "demonstrates the calculation, not any real portfolio's footprint."
        )
