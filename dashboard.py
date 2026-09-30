"""
Streamlit-Dashboard: Kreditzinsen in Deutschland vs. EZB-Leitzins
Liest das Star-Schema aus dem Notebook (dim_zeit.csv, dim_zinsart.csv, fact_zinssaetze.csv).

Start: streamlit run dashboard.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# 1. Seiteneinstellungen
# ------------------------------------------------------------
st.set_page_config(page_title="Kreditzinsen vs. EZB-Leitzins", layout="wide")

# Farben aus der validierten dataviz-Palette (gleiche Werte wie im Notebook)
FARBEN = {
    "Konsumkredit": "#2a78d6",
    "Unternehmenskredit": "#eb6834",
    "Leitzins": "#4a3aa7",
}

# Kategoriale 8er-Palette (dataviz-Skill), für Charts mit mehr als 3 Serien (z. B. Laufzeit)
PALETTE_KATEGORIAL = [
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
    "#e87ba4", "#008300", "#4a3aa7", "#e34948",
]

KATEGORIE_REIHENFOLGE = ["Konsumkredit", "Unternehmenskredit", "Leitzins"]
LAUFZEIT_REIHENFOLGE = [
    "bis 1 Jahr", "1 bis 5 Jahre", "über 5 Jahre", "gesamt",
    "Hauptrefinanzierung", "Einlagefazilität", "Spitzenrefinanzierung",
]


def format_wert(wert: float) -> str:
    return f"{wert:.2f} %" if pd.notna(wert) else "–"


# ------------------------------------------------------------
# 2. Daten laden (Star-Schema zusammenführen)
# ------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    dim_zeit = pd.read_csv("dim_zeit.csv", sep=";", parse_dates=["Datum"])
    dim_zinsart = pd.read_csv("dim_zinsart.csv", sep=";")
    fact = pd.read_csv("fact_zinssaetze.csv", sep=";", decimal=",")

    df = fact.merge(dim_zeit, on="Zeit_ID").merge(dim_zinsart, on="Zinsart_ID")
    return df.sort_values("Datum")


df = load_data()

st.title("Kreditzinsen in Deutschland vs. EZB-Leitzins")
st.caption("Datenquelle: Bundesbank SDMX Web Service — Neugeschäft, seit 2020")
st.write("")  # eine Leerzeile zwischen Datenquelle und "Aktuelle Eckwerte"


# ------------------------------------------------------------
# 3. Sidebar-Filter
# ------------------------------------------------------------
st.sidebar.header("Filter")

kategorien = sorted(df["Kategorie"].unique())
gewaehlte_kategorien = st.sidebar.multiselect("Kategorie", kategorien, default=kategorien)

laufzeiten = sorted(df["Laufzeit"].unique())
gewaehlte_laufzeiten = st.sidebar.multiselect("Laufzeit", laufzeiten, default=laufzeiten)

min_datum, max_datum = df["Datum"].min(), df["Datum"].max()
zeitraum = st.sidebar.slider(
    "Zeitraum",
    min_value=min_datum.to_pydatetime(),
    max_value=max_datum.to_pydatetime(),
    value=(min_datum.to_pydatetime(), max_datum.to_pydatetime()),
    format="MM/YYYY",
)

df_filtered = df[
    df["Kategorie"].isin(gewaehlte_kategorien)
    & df["Laufzeit"].isin(gewaehlte_laufzeiten)
    & df["Datum"].between(zeitraum[0], zeitraum[1])
]


# ------------------------------------------------------------
# 4. KPI-Kacheln (aktuelle Eckwerte)
# ------------------------------------------------------------
st.subheader("Aktuelle Eckwerte")
st.write("")  # eine Leerzeile, damit die Karten nicht an der Überschrift kleben

neueste_werte = df_filtered.sort_values("Datum").groupby("Zinsart_Code")["Zinssatz"].last()
neuestes_datum = df_filtered["Datum"].max()

col1, col2, col3 = st.columns(3)
col1.metric("Leitzins (Hauptrefinanzierung)", format_wert(neueste_werte.get("Hauptrefinanzierungssatz", np.nan)))
col2.metric("Konsumkredit (gesamt)", format_wert(neueste_werte.get("Konsum_gesamt", np.nan)))
col3.metric("Unternehmenskredit (gesamt)", format_wert(neueste_werte.get("Unternehmen_gesamt", np.nan)))
letzte_daten = df_filtered.groupby("Zinsart_Code")["Datum"].max()


def stand(code: str) -> str:
    d = letzte_daten.get(code)
    return f"{d:%m/%Y}" if pd.notna(d) else "–"


st.caption(
    f"Stand: Leitzins {stand('Hauptrefinanzierungssatz')}, "
    f"Konsumkredit {stand('Konsum_gesamt')}, "
    f"Unternehmenskredit {stand('Unternehmen_gesamt')}"
)

st.divider()


# ------------------------------------------------------------
# 5. Zinsentwicklung über Zeit
# ------------------------------------------------------------
st.subheader("Zinsentwicklung über Zeit")

fig1 = px.line(
    df_filtered,
    x="Datum",
    y="Zinssatz",
    color="Laufzeit",
    line_dash="Kategorie",
    color_discrete_sequence=PALETTE_KATEGORIAL,
    category_orders={"Kategorie": KATEGORIE_REIHENFOLGE, "Laufzeit": LAUFZEIT_REIHENFOLGE},
)
fig1.update_layout(yaxis_title="Zinssatz in %", xaxis_title="", legend_title="")
st.plotly_chart(fig1, use_container_width=True)

st.divider()


# ------------------------------------------------------------
# 6. Zinsspanne: Kreditzins minus Leitzins
# ------------------------------------------------------------
st.subheader("Zinsspanne: Kreditzins minus Leitzins")

pivot_spanne = df_filtered.pivot_table(index="Datum", columns="Zinsart_Code", values="Zinssatz")
spanne_spalten = []
if "Hauptrefinanzierungssatz" in pivot_spanne.columns:
    if "Konsum_gesamt" in pivot_spanne.columns:
        pivot_spanne["Konsumkredit"] = pivot_spanne["Konsum_gesamt"] - pivot_spanne["Hauptrefinanzierungssatz"]
        spanne_spalten.append("Konsumkredit")
    if "Unternehmen_gesamt" in pivot_spanne.columns:
        pivot_spanne["Unternehmenskredit"] = pivot_spanne["Unternehmen_gesamt"] - pivot_spanne["Hauptrefinanzierungssatz"]
        spanne_spalten.append("Unternehmenskredit")

if spanne_spalten:
    spanne_lang = (
        pivot_spanne.reset_index()[["Datum"] + spanne_spalten]
        .melt(id_vars="Datum", var_name="Kategorie", value_name="Spanne")
        .dropna()
    )
    fig4 = px.line(spanne_lang, x="Datum", y="Spanne", color="Kategorie", color_discrete_map=FARBEN)
    fig4.update_layout(yaxis_title="Zinsspanne in Prozentpunkten", xaxis_title="", legend_title="")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("Filter enthält keine Leitzins-Kategorie — für diesen Chart 'Leitzins' in der Sidebar aktivieren.")

st.divider()


# ------------------------------------------------------------
# 7. Aktuellster Zinssatz je Zinsart
# ------------------------------------------------------------
st.subheader(
    f"Aktuellster Zinssatz je Zinsart "
    f"(Kredite {stand('Konsum_gesamt')}, Leitzins {stand('Hauptrefinanzierungssatz')})"
)

letzter = (
    df_filtered.sort_values("Datum")
    .groupby(["Kategorie", "Laufzeit"], as_index=False)
    .last()
)
fig2 = px.bar(
    letzter,
    x="Laufzeit",
    y="Zinssatz",
    color="Laufzeit",
    facet_col="Kategorie",
    color_discrete_sequence=PALETTE_KATEGORIAL,
    category_orders={"Kategorie": KATEGORIE_REIHENFOLGE, "Laufzeit": LAUFZEIT_REIHENFOLGE},
)
fig2.update_xaxes(matches=None, showticklabels=True, title="")
fig2.update_layout(yaxis_title="Zinssatz in %", showlegend=False)
fig2.update_traces(texttemplate="%{y:.2f}%", textposition="outside")
# Facet-Titel bereinigen: "Kategorie=Konsumkredit" -> "Konsumkredit"
fig2.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
st.plotly_chart(fig2, use_container_width=True)

st.divider()


# ------------------------------------------------------------
# 8. Kreditzins vs. EZB-Hauptrefinanzierungssatz
# ------------------------------------------------------------
st.subheader("Kreditzins vs. EZB-Hauptrefinanzierungssatz")

pivot = df_filtered.pivot_table(index="Datum", columns="Zinsart_Code", values="Zinssatz")
vorhandene_kredit_spalten = [s for s in ["Konsum_gesamt", "Unternehmen_gesamt"] if s in pivot.columns]

if "Hauptrefinanzierungssatz" in pivot.columns and vorhandene_kredit_spalten:
    scatter_df = (
        pivot.reset_index()[["Datum", "Hauptrefinanzierungssatz"] + vorhandene_kredit_spalten]
        .melt(
            id_vars=["Datum", "Hauptrefinanzierungssatz"],
            var_name="Kredit",
            value_name="Zinssatz",
        )
        .dropna()
    )

    rng = np.random.default_rng(42)
    scatter_df["x_jitter"] = scatter_df["Hauptrefinanzierungssatz"] + rng.uniform(-0.05, 0.05, size=len(scatter_df))

    farben_kredit = {"Konsum_gesamt": FARBEN["Konsumkredit"], "Unternehmen_gesamt": FARBEN["Unternehmenskredit"]}
    namen_kredit = {"Konsum_gesamt": "Konsumkredit", "Unternehmen_gesamt": "Unternehmenskredit"}

    fig3 = go.Figure()
    for kredit_code, farbe in farben_kredit.items():
        sub = scatter_df[scatter_df["Kredit"] == kredit_code]
        if sub.empty:
            continue
        fig3.add_trace(go.Scatter(
            x=sub["x_jitter"],
            y=sub["Zinssatz"],
            mode="markers",
            name=namen_kredit[kredit_code],
            marker=dict(color=farbe, opacity=0.6, size=7),
            customdata=sub["Datum"].dt.strftime("%m/%Y"),
            hovertemplate="Leitzins: %{x:.2f}%<br>Kreditzins: %{y:.2f}%<br>Datum: %{customdata}<extra></extra>",
        ))
        # Trendlinie auf den Originalwerten (ohne Jitter) berechnet
        steigung, achsenabschnitt = np.polyfit(sub["Hauptrefinanzierungssatz"], sub["Zinssatz"], 1)
        x_linie = np.linspace(sub["Hauptrefinanzierungssatz"].min(), sub["Hauptrefinanzierungssatz"].max(), 50)
        fig3.add_trace(go.Scatter(
            x=x_linie,
            y=steigung * x_linie + achsenabschnitt,
            mode="lines",
            line=dict(color=farbe, dash="dash", width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

    fig3.update_layout(
        xaxis_title="EZB-Hauptrefinanzierungssatz in %",
        yaxis_title="Effektivzinssatz Kredit in %",
        legend_title="",
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("Punkte leicht zufällig verteilt (Jitter) zur besseren Lesbarkeit — Werte selbst unverändert.")
else:
    st.info("Filter enthält keine Leitzins-Kategorie — für diesen Chart 'Leitzins' in der Sidebar aktivieren.")

st.divider()


# ------------------------------------------------------------
# 9. Rohdaten (mit eigenen Tabellen-Filtern)
# ------------------------------------------------------------
with st.expander("Rohdaten anzeigen"):
    st.caption("Zusätzliche Filter nur für diese Tabelle (unabhängig von den Diagrammen oben)")

    tab_col1, tab_col2 = st.columns(2)
    zinsart_optionen = sorted(df_filtered["Zinsart_Code"].unique())
    gewaehlte_zinsarten = tab_col1.multiselect("Zinsart", zinsart_optionen, default=zinsart_optionen)
    jahr_optionen = sorted(df_filtered["Jahr"].unique())
    gewaehlte_jahre = tab_col2.multiselect("Jahr", jahr_optionen, default=jahr_optionen)

    tabelle_gefiltert = df_filtered[
        df_filtered["Zinsart_Code"].isin(gewaehlte_zinsarten)
        & df_filtered["Jahr"].isin(gewaehlte_jahre)
    ]
    st.dataframe(tabelle_gefiltert, use_container_width=True)
