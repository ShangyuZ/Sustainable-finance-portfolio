"""
Climate & Energy Transition Dashboard
======================================
Freely licensed data only — no API keys required:
  • Our World in Data  (CC BY)  — energy & emissions by country
  • Bundled EUA prices (compiled from public sources) — EU carbon price history

Run:  streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── paths ──────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
EUA_CSV  = DATA_DIR / "eua_prices.csv"

OWID_ENERGY_URL = (
    "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
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
    """
    Load the OWID energy dataset.
    Filters to real countries only by requiring a 3-letter ISO code that
    does NOT start with 'OWID' (which OWID uses for aggregate regions).
    """
    try:
        df = pd.read_csv(OWID_ENERGY_URL, low_memory=False)
    except Exception as exc:
        st.error(f"Could not load OWID data: {exc}")
        return pd.DataFrame()

    # Keep only sovereign countries (3-letter ISO code, no OWID_ aggregates)
    df = df[
        df["iso_code"].notna()
        & (df["iso_code"].str.len() == 3)
        & ~df["iso_code"].str.startswith("OWID")
    ]
    df = df[df["year"] >= 2000].reset_index(drop=True)
    return df


@st.cache_data(ttl=3_600)
def load_eua_prices() -> pd.DataFrame:
    """
    Load EU ETS EUA spot price history from the bundled CSV.
    Falls back to an illustrative trajectory if the file is missing.
    """
    if EUA_CSV.exists():
        df = pd.read_csv(EUA_CSV)
        df["date"] = pd.to_datetime(df["date"])
        df = df.rename(columns={"date": "Date", "price_eur_t": "Price (€/tCO₂)"})
        return df.sort_values("Date").reset_index(drop=True)

    # Fallback — should never be reached if data/ folder is present
    import numpy as np
    np.random.seed(42)
    dates  = pd.date_range("2018-01-01", "2026-06-01", freq="W")
    prices = (8 + np.linspace(0, 80, len(dates))).clip(min=4).round(2)
    return pd.DataFrame({"Date": dates, "Price (€/tCO₂)": prices})


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
    "[Our World in Data](https://ourworldindata.org/energy) (CC BY 4.0)\n\n"
    "EUA prices compiled from public sources"
)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 1 — EU Carbon Price
# ══════════════════════════════════════════════════════════════════════════

if section == "🏭 EU Carbon Price":
    st.title("EU ETS Carbon Price")
    st.caption(
        "European Union Allowance (EUA) weekly spot price — "
        "compiled from public sources. Updated as new data becomes available."
    )

    df = load_eua_prices()

    # Guard: should always have data, but be safe
    if df.empty or "Price (€/tCO₂)" not in df.columns:
        st.error("EUA price data unavailable.")
        st.stop()

    latest     = float(df["Price (€/tCO₂)"].iloc[-1])
    all_time_h = float(df["Price (€/tCO₂)"].max())
    this_year  = int(df["Date"].dt.year.max())
    yr_start   = df[df["Date"].dt.year == this_year]["Price (€/tCO₂)"].iloc[0]
    ytd_pct    = (latest / yr_start - 1) * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Latest Price",  f"€{latest:.1f} / tCO₂")
    c2.metric("YTD Change",    f"{ytd_pct:+.1f}%")
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
    st.plotly_chart(fig, use_container_width=True)

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

    df = load_owid()
    if df.empty:
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
            yr_range = st.slider("Year range", 2000, int(df["year"].max()), (2000, int(df["year"].max())), key="ren_yr")

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
                st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2: CO₂ Emissions ──────────────────────────────────────────────
    with tab2:
        # OWID column is 'co2' (million tonnes)
        co2_col = "co2" if "co2" in df.columns else next(
            (c for c in df.columns if c.startswith("co2") and "per" not in c and "cumul" not in c), None
        )
        if not co2_col:
            st.warning("CO₂ column not found.")
        else:
            st.subheader("Annual CO₂ emissions from energy (Mt)")
            defaults2 = [c for c in ["China","United States","India","Germany","United Kingdom"] if c in countries_all]
            selected2 = st.multiselect("Countries", countries_all, default=defaults2, key="co2_sel")
            yr_range2 = st.slider("Year range", 2000, int(df["year"].max()), (2000, int(df["year"].max())), key="co2_yr")

            filt2 = df[df["country"].isin(selected2) & df["year"].between(*yr_range2) & df[co2_col].notna()]
            fig2 = px.line(
                filt2, x="year", y=co2_col, color="country",
                labels={co2_col: "CO₂ (Mt)", "year": "Year"},
                title="Annual CO₂ Emissions from Energy",
            )
            fig2.update_layout(plot_bgcolor="white", hovermode="x unified")
            fig2.update_traces(line_width=2)
            st.plotly_chart(fig2, use_container_width=True)

    # ── Tab 3: Energy Mix ─────────────────────────────────────────────────
    with tab3:
        st.subheader("Energy mix breakdown — latest available year")

        mix_cols = {
            "renewables_share_elec": "Renewables",
            "fossil_share_elec":     "Fossil fuels",
            "nuclear_share_elec":    "Nuclear",
            "hydro_share_elec":      "Hydro",
            "solar_share_elec":      "Solar",
            "wind_share_elec":       "Wind",
        }
        available_mix = {k: v for k, v in mix_cols.items() if k in df.columns}

        country_choice = st.selectbox("Select country", countries_all,
                                       index=countries_all.index("United Kingdom") if "United Kingdom" in countries_all else 0)
        cdf = df[df["country"] == country_choice].sort_values("year")
        cdf_clean = cdf.dropna(subset=list(available_mix.keys()), how="all")

        if cdf_clean.empty:
            st.info(f"No energy mix data for {country_choice}.")
        else:
            latest_row = cdf_clean.iloc[-1]
            mix_data = {v: latest_row.get(k, 0) for k, v in available_mix.items()}
            mix_data = {k: v for k, v in mix_data.items() if pd.notna(v) and v > 0}

            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.markdown(f"**{country_choice}** — {int(latest_row['year'])}")
                for label, val in sorted(mix_data.items(), key=lambda x: -x[1]):
                    st.markdown(f"- {label}: **{val:.1f}%**")
            with col_b:
                fig3 = px.pie(
                    names=list(mix_data.keys()),
                    values=list(mix_data.values()),
                    title=f"{country_choice} electricity mix",
                    color_discrete_sequence=px.colors.qualitative.Safe,
                )
                st.plotly_chart(fig3, use_container_width=True)


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

    df = load_owid()
    if df.empty:
        st.stop()

    latest_year = int(df["year"].max())
    prev_year   = latest_year - 5   # 5-year change

    needed = ["co2_per_capita", "renewables_share_elec"]
    if not all(c in df.columns for c in needed):
        st.warning("Required columns not found in dataset version.")
        st.stop()

    def get_year(year: int) -> pd.DataFrame:
        return (
            df[df["year"] == year][["country", "iso_code"] + needed]
            .dropna(subset=needed)
            .set_index("country")
        )

    latest_df = get_year(latest_year)
    prev_df   = get_year(prev_year)

    scorecard = latest_df.copy()
    scorecard.columns = ["iso_code", "CO₂ per capita (t)", "Renewables (% elec)"]

    # 5-year change
    co2_change  = (latest_df["co2_per_capita"] - prev_df["co2_per_capita"]).rename("CO₂ change (5yr, t)")
    ren_change  = (latest_df["renewables_share_elec"] - prev_df["renewables_share_elec"]).rename("Renewables change (5yr, pp)")

    scorecard = scorecard.join(co2_change).join(ren_change)
    scorecard = scorecard.drop(columns=["iso_code"]).round(2).reset_index()

    tab_a, tab_b, tab_c = st.tabs(["Rankings Table", "CO₂ vs Renewables", "Decarbonisation Rate"])

    with tab_a:
        sort_by = st.selectbox("Sort by", ["CO₂ per capita (t)", "Renewables (% elec)",
                                            "CO₂ change (5yr, t)", "Renewables change (5yr, pp)"])
        asc = sort_by.startswith("CO₂")
        top_n = st.slider("Show top N countries", 10, len(scorecard), 30)

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
        st.dataframe(styled, use_container_width=True, height=500)

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
        st.plotly_chart(fig_sc, use_container_width=True)

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
        st.plotly_chart(fig_d, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 4 — Portfolio Carbon Calculator
# ══════════════════════════════════════════════════════════════════════════

else:
    st.title("Portfolio Carbon Intensity Calculator")
    st.caption(
        "Weighted Average Carbon Intensity (WACI) using TCFD-aligned sector benchmarks. "
        "No company-specific or proprietary data required."
    )

    # Sector carbon intensity benchmarks (tCO₂e per $m revenue)
    # Source: MSCI TCFD sector guidance — publicly available
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
        "Uses **sector-average** benchmarks (tCO₂e per $m revenue). "
        "For company-level precision, use CDP or MSCI ESG data."
    )

    n_hold = int(st.number_input("Number of holdings", min_value=1, max_value=20, value=4))
    default_w = round(100.0 / n_hold, 1)

    hdr = st.columns([3, 2, 3])
    hdr[0].markdown("**Ticker / Name**")
    hdr[1].markdown("**Weight (%)**")
    hdr[2].markdown("**Sector**")

    holdings: list[dict] = []
    total_w = 0.0

    for i in range(n_hold):
        c1, c2, c3 = st.columns([3, 2, 3])
        ticker = c1.text_input("name", placeholder="e.g. BP", key=f"t{i}", label_visibility="collapsed")
        weight = c2.number_input("weight", 0.0, 100.0, default_w, step=0.1, key=f"w{i}", label_visibility="collapsed")
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
        waci = float((df_h["Weight (%)"] / 100 * df_h["Intensity"]).sum())

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Portfolio WACI", f"{waci:.0f} tCO₂e / $m rev")
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
        st.plotly_chart(fig, use_container_width=True)

        if abs(total_w - 100) < 0.5:
            if waci > 300:
                st.warning(f"⚠️ High-carbon portfolio — WACI {waci:.0f}. Heavy exposure to fossil-fuel sectors.")
            elif waci < 80:
                st.success(f"🌿 Low-carbon portfolio — WACI {waci:.0f}.")
            else:
                st.info(f"Portfolio WACI: {waci:.0f} tCO₂e / $m revenue.")
        else:
            st.warning(f"Weights sum to {total_w:.1f}% — adjust to 100% for a valid WACI.")

        st.caption(
            "**Methodology:** WACI = Σ (portfolio weight × sector carbon intensity benchmark). "
            "Benchmarks from MSCI / TCFD sector guidance (publicly available)."
        )
