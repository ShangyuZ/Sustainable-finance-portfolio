"""
Climate & Energy Transition Dashboard
======================================
Uses entirely open, freely licensed datasets:
  - Our World in Data  (CC BY)  — energy & emissions
  - Ember Climate      (CC BY)  — EU ETS carbon prices
  - No API keys required

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Climate Finance Dashboard",
    page_icon="🌿",
    layout="wide",
)

# ── constants ──────────────────────────────────────────────────────────────

OWID_ENERGY_URL = (
    "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
)

EMBER_ETS_URL = (
    "https://raw.githubusercontent.com/ember-climate/carbon-price-viewer/"
    "main/data/carbon-prices.csv"
)

REGIONS_EXCLUDE = {
    "World", "Europe", "Asia", "Africa", "North America", "South America",
    "Oceania", "European Union (27)", "High-income countries",
    "Low-income countries", "Upper-middle-income countries",
    "Lower-middle-income countries", "OECD (Ember)",
}

# ── data loaders ──────────────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner="Loading energy data from Our World in Data…")
def load_owid() -> pd.DataFrame:
    df = pd.read_csv(OWID_ENERGY_URL, low_memory=False)
    df = df[~df["country"].isin(REGIONS_EXCLUDE)]
    df = df[df["year"] >= 2000]
    return df


@st.cache_data(ttl=3600, show_spinner="Loading carbon price data…")
def load_carbon_prices() -> pd.DataFrame:
    """
    Try to load Ember's carbon price data. Falls back to illustrative
    EUA price trajectory if the URL is unavailable.
    """
    try:
        df = pd.read_csv(EMBER_ETS_URL)
        # normalise column names — Ember schema may vary
        df.columns = df.columns.str.strip()
        if "date" in df.columns:
            df["Date"] = pd.to_datetime(df["date"])
        elif "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
        # filter to EU ETS
        if "system" in df.columns:
            df = df[df["system"].str.contains("EU", na=False)]
        if "price" in df.columns:
            df = df.rename(columns={"price": "Price (€/tCO₂)"})
        return df[["Date", "Price (€/tCO₂)"]].dropna().sort_values("Date")
    except Exception:
        # fallback — approximate EUA trajectory for illustration
        import numpy as np
        np.random.seed(42)
        dates = pd.date_range("2018-01-01", "2026-06-01", freq="W")
        prices = (
            8 + np.linspace(0, 80, len(dates))
            + (np.random.normal(0, 1.5, len(dates)).cumsum() * 0.1)
        ).clip(min=4)
        return pd.DataFrame({
            "Date": dates,
            "Price (€/tCO₂)": prices.round(2),
            "_fallback": True,
        })


# ── sidebar ────────────────────────────────────────────────────────────────

st.sidebar.title("🌿 Climate Finance")
st.sidebar.caption("ShangyuZ · UCL · BSc Stats, Economics & Finance")
st.sidebar.divider()
section = st.sidebar.radio(
    "Dashboard section",
    ["🏭 EU Carbon Price", "⚡ Energy Transition", "🌍 Portfolio Carbon Calculator"],
)
st.sidebar.divider()
st.sidebar.caption(
    "Data: [Our World in Data](https://ourworldindata.org/energy) (CC BY) · "
    "[Ember Climate](https://ember-climate.org) (CC BY)"
)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 1 — EU Carbon Price
# ══════════════════════════════════════════════════════════════════════════

if section == "🏭 EU Carbon Price":
    st.title("EU ETS Carbon Price")
    st.caption("European Union Allowance (EUA) spot price — Source: Ember Climate (CC BY)")

    df = load_carbon_prices()
    is_fallback = "_fallback" in df.columns

    if is_fallback:
        st.info(
            "ℹ️ Live Ember data unavailable — showing an illustrative EUA price trajectory. "
            "Deploy with internet access for real prices."
        )
        df = df.drop(columns=["_fallback"])

    # key policy events
    events = {
        "2019-01-01": "MSR reform",
        "2021-07-14": "Fit for 55",
        "2022-03-01": "Ukraine shock",
        "2023-04-25": "ETS reform (CBAM)",
    }

    latest = df["Price (€/tCO₂)"].iloc[-1]
    year_start = df[df["Date"].dt.year == df["Date"].dt.year.max()]["Price (€/tCO₂)"].iloc[0]
    ytd_pct = (latest / year_start - 1) * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Latest Price", f"€{latest:.1f} / tCO₂")
    c2.metric("YTD Change", f"{ytd_pct:+.1f}%")
    c3.metric("All-time High", f"€{df['Price (€/tCO₂)'].max():.1f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Price (€/tCO₂)"],
        mode="lines", line=dict(color="#1A7A4A", width=2),
        fill="tozeroy", fillcolor="rgba(26,122,74,0.08)",
        name="EUA price",
    ))
    for date_str, label in events.items():
        d = pd.to_datetime(date_str)
        row = df[df["Date"] >= d]
        if not row.empty:
            price = row["Price (€/tCO₂)"].iloc[0]
            fig.add_vline(x=d, line_dash="dot", line_color="#999", opacity=0.6)
            fig.add_annotation(x=d, y=price + 3, text=label,
                               showarrow=False, font=dict(size=9, color="#555"),
                               textangle=-25)
    fig.update_layout(
        title="EUA Spot Price History",
        yaxis_title="€ per tCO₂",
        xaxis_title="",
        plot_bgcolor="white",
        hovermode="x unified",
        margin=dict(t=40),
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 2 — Energy Transition
# ══════════════════════════════════════════════════════════════════════════

elif section == "⚡ Energy Transition":
    st.title("Global Energy Transition")
    st.caption("Source: Our World in Data — Energy dataset (CC BY) · Updated annually")

    df = load_owid()

    tab1, tab2, tab3 = st.tabs(["Renewable Share", "CO₂ Emissions", "Country Comparison"])

    # ── Tab 1: Renewable Share ─────────────────────────────────────────────
    with tab1:
        st.subheader("Renewables as share of electricity generation")
        col = "renewables_share_elec"
        if col not in df.columns:
            st.warning("Column not found in OWID dataset. Check dataset version.")
        else:
            countries = sorted(df["country"].dropna().unique())
            defaults = ["United Kingdom", "Germany", "China", "United States", "Denmark"]
            defaults = [c for c in defaults if c in countries]
            selected = st.multiselect("Select countries", countries, default=defaults)
            years = st.slider("Year range", int(df["year"].min()), int(df["year"].max()),
                              (2000, int(df["year"].max())))

            filtered = df[
                df["country"].isin(selected) &
                df["year"].between(*years) &
                df[col].notna()
            ]
            fig = px.line(filtered, x="year", y=col, color="country",
                          labels={col: "Renewables (% of electricity)", "year": "Year"},
                          title="Renewable Share of Electricity Generation (%)")
            fig.update_layout(plot_bgcolor="white", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2: CO₂ Emissions ──────────────────────────────────────────────
    with tab2:
        st.subheader("CO₂ emissions from energy (million tonnes)")
        col = "co2"
        if col not in df.columns:
            # try alternative column name
            col_candidates = [c for c in df.columns if "co2" in c.lower() and "per" not in c.lower()]
            col = col_candidates[0] if col_candidates else None

        if col:
            countries = sorted(df["country"].dropna().unique())
            defaults = ["China", "United States", "India", "Germany", "United Kingdom"]
            defaults = [c for c in defaults if c in countries]
            selected2 = st.multiselect("Select countries", countries, default=defaults, key="co2_sel")
            years2 = st.slider("Year range", 2000, int(df["year"].max()), (2000, int(df["year"].max())), key="co2_yr")

            filtered2 = df[
                df["country"].isin(selected2) &
                df["year"].between(*years2) &
                df[col].notna()
            ]
            fig2 = px.line(filtered2, x="year", y=col, color="country",
                           labels={col: "CO₂ (Mt)", "year": "Year"},
                           title="Annual CO₂ Emissions from Energy")
            fig2.update_layout(plot_bgcolor="white", hovermode="x unified")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("CO₂ column not found.")

    # ── Tab 3: Country Snapshot ────────────────────────────────────────────
    with tab3:
        st.subheader("Country energy snapshot — latest year")
        latest_year = int(df["year"].max())
        snap_cols = {
            "renewables_share_elec": "Renewables % of electricity",
            "solar_share_elec": "Solar %",
            "wind_share_elec": "Wind %",
            "co2_per_capita": "CO₂ per capita (t)",
            "energy_per_capita": "Energy per capita (kWh)",
        }
        available = {k: v for k, v in snap_cols.items() if k in df.columns}
        snap = (
            df[df["year"] == latest_year][["country"] + list(available.keys())]
            .dropna(subset=list(available.keys()), how="all")
            .rename(columns=available)
            .sort_values("Renewables % of electricity", ascending=False)
            .reset_index(drop=True)
        )
        snap.index += 1
        st.dataframe(snap, use_container_width=True, height=450)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 3 — Portfolio Carbon Calculator
# ══════════════════════════════════════════════════════════════════════════

else:
    st.title("Portfolio Carbon Intensity Calculator")
    st.caption(
        "Weighted Average Carbon Intensity (WACI) using TCFD-aligned sector benchmarks. "
        "Replace with MSCI ESG / CDP data for company-level precision."
    )

    SECTOR_INTENSITY = {
        "Energy — Oil & Gas":        850,
        "Utilities":                  540,
        "Materials":                  430,
        "Industrials":                210,
        "Consumer Staples":           120,
        "Consumer Discretionary":      95,
        "Healthcare":                  60,
        "Information Technology":      35,
        "Communication Services":      30,
        "Financials":                  20,
        "Real Estate":                 80,
    }

    st.info(
        "This uses **sector-average** carbon intensity benchmarks (tCO₂e per $m revenue). "
        "No company-specific or proprietary data is required."
    )

    n = st.number_input("Number of holdings", 1, 20, 4)
    holdings = []
    total_w = 0.0

    hdr = st.columns([3, 2, 3])
    hdr[0].markdown("**Ticker / Name**")
    hdr[1].markdown("**Weight (%)**")
    hdr[2].markdown("**Sector**")

    for i in range(int(n)):
        c1, c2, c3 = st.columns([3, 2, 3])
        ticker = c1.text_input("", placeholder=f"e.g. BP", key=f"t{i}", label_visibility="collapsed")
        weight = c2.number_input("", 0.0, 100.0, round(100 / int(n), 1), key=f"w{i}", label_visibility="collapsed")
        sector = c3.selectbox("", list(SECTOR_INTENSITY.keys()), key=f"s{i}", label_visibility="collapsed")
        if ticker:
            holdings.append({"Holding": ticker, "Weight (%)": weight,
                              "Sector": sector, "Intensity": SECTOR_INTENSITY[sector]})
            total_w += weight

    if holdings:
        df_h = pd.DataFrame(holdings)
        waci = (df_h["Weight (%)"] / 100 * df_h["Intensity"]).sum()

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Portfolio WACI", f"{waci:.0f} tCO₂e / $m rev")
        m2.metric("Total weight", f"{total_w:.1f}%",
                  delta=f"{total_w-100:+.1f}% vs 100%",
                  delta_color="inverse" if abs(total_w-100) > 0.5 else "off")
        m3.metric("Holdings", len(holdings))

        fig = px.bar(
            df_h.sort_values("Intensity", ascending=False),
            x="Holding", y="Intensity", color="Sector",
            title="Carbon Intensity by Holding (sector benchmark)",
            labels={"Intensity": "tCO₂e per $m revenue"},
        )
        fig.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

        if abs(total_w - 100) < 0.5:
            if waci > 300:
                st.warning(f"⚠️ High-carbon portfolio (WACI: {waci:.0f}). Consider reducing exposure to heavy sectors.")
            elif waci < 80:
                st.success(f"🌿 Low-carbon portfolio (WACI: {waci:.0f}).")
            else:
                st.info(f"Portfolio WACI: {waci:.0f} tCO₂e / $m revenue.")

        st.caption(
            "**Methodology:** WACI = Σ (weight × sector intensity). "
            "Sector benchmarks sourced from MSCI and TCFD sector guidance (publicly available). "
            "For company-level analysis, use CDP or MSCI ESG data."
        )
