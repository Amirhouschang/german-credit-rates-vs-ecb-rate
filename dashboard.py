"""
Streamlit-Dashboard: Kreditzinsen in Deutschland vs. EZB-Leitzins
Streamlit dashboard: lending rates in Germany vs. ECB key interest rate

Zweisprachig (Deutsch / English), Umschalter oben in der Sidebar.
Direktlink auf Englisch: <App-URL>/?lang=en

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
# Muss der erste Streamlit-Befehl sein -> Titel deshalb zweisprachig
st.set_page_config(page_title="Kreditzinsen vs. EZB-Leitzins · Lending rates vs. ECB key rate", layout="wide")

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

# Reihenfolgen in den Original-(deutschen) Datenwerten aus den CSVs
KATEGORIE_REIHENFOLGE = ["Konsumkredit", "Unternehmenskredit", "Leitzins"]
LAUFZEIT_REIHENFOLGE = [
    "bis 1 Jahr", "1 bis 5 Jahre", "über 5 Jahre", "gesamt",
    "Hauptrefinanzierung", "Einlagefazilität", "Spitzenrefinanzierung",
]


def format_wert(wert: float) -> str:
    return f"{wert:.2f} %" if pd.notna(wert) else "–"


# ------------------------------------------------------------
# 1b. Sprachen (Deutsch = Originaltexte, English = Übersetzung)
# ------------------------------------------------------------
TEXTE = {
    "de": {
        "language": "Sprache / Language",
        "title": "Kreditzinsen in Deutschland vs. EZB-Leitzins",
        "source": "Datenquelle: Bundesbank SDMX Web Service — Neugeschäft, seit 2020",
        "filter": "Filter",
        "category": "Kategorie",
        "term": "Laufzeit",
        "period": "Zeitraum",
        "date": "Datum",
        "rate": "Zinssatz",
        "spread": "Spanne",
        "kpi_header": "Aktuelle Eckwerte",
        "kpi_key": "Leitzins (Hauptrefinanzierung)",
        "kpi_consumer": "Konsumkredit (gesamt)",
        "kpi_corporate": "Unternehmenskredit (gesamt)",
        "asof": "Stand",
        "asof_key": "Leitzins",
        "asof_consumer": "Konsumkredit",
        "asof_corporate": "Unternehmenskredit",
        "dev_header": "Zinsentwicklung über Zeit",
        "rate_axis": "Zinssatz in %",
        "spread_header": "Zinsspanne: Kreditzins minus Leitzins",
        "spread_axis": "Zinsspanne in Prozentpunkten",
        "need_key": "Filter enthält keine Leitzins-Kategorie — für diesen Chart '{kat}' in der Sidebar aktivieren.",
        "latest_header": "Aktuellster Zinssatz je Zinsart",
        "latest_loans": "Kredite",
        "latest_key": "Leitzins",
        "scatter_header": "Kreditzins vs. EZB-Hauptrefinanzierungssatz",
        "scatter_x": "EZB-Hauptrefinanzierungssatz in %",
        "scatter_y": "Effektivzinssatz Kredit in %",
        "hover_key": "Leitzins",
        "hover_loan": "Kreditzins",
        "hover_date": "Datum",
        "jitter_note": "Punkte leicht zufällig verteilt (Jitter) zur besseren Lesbarkeit — Werte selbst unverändert.",
        "raw_expander": "Rohdaten anzeigen",
        "raw_note": "Zusätzliche Filter nur für diese Tabelle (unabhängig von den Diagrammen oben)",
        "raw_type": "Zinsart",
        "raw_year": "Jahr",
    },
    "en": {
        "language": "Sprache / Language",
        "title": "Lending Rates in Germany vs. ECB Key Interest Rate",
        "source": "Data source: Bundesbank SDMX Web Service — new business, since 2020",
        "filter": "Filters",
        "category": "Category",
        "term": "Term",
        "period": "Period",
        "date": "Date",
        "rate": "Interest rate",
        "spread": "Spread",
        "kpi_header": "Current key figures",
        "kpi_key": "Key interest rate (main refinancing)",
        "kpi_consumer": "Consumer credit (total)",
        "kpi_corporate": "Corporate credit (total)",
        "asof": "As of",
        "asof_key": "key rate",
        "asof_consumer": "consumer credit",
        "asof_corporate": "corporate credit",
        "dev_header": "Interest rate development over time",
        "rate_axis": "Interest rate in %",
        "spread_header": "Spread: loan rate minus key interest rate",
        "spread_axis": "Spread in percentage points",
        "need_key": "Filter contains no key interest rate category — enable '{kat}' in the sidebar for this chart.",
        "latest_header": "Latest rate by type",
        "latest_loans": "loans",
        "latest_key": "key rate",
        "scatter_header": "Loan rate vs. ECB main refinancing rate",
        "scatter_x": "ECB main refinancing rate in %",
        "scatter_y": "Effective loan rate in %",
        "hover_key": "Key rate",
        "hover_loan": "Loan rate",
        "hover_date": "Date",
        "jitter_note": "Points are slightly randomly spread (jitter) for readability — the values themselves are unchanged.",
        "raw_expander": "Show raw data",
        "raw_note": "Additional filters for this table only (independent of the charts above)",
        "raw_type": "Rate type",
        "raw_year": "Year",
    },
}

# Anzeigenamen der Datenwerte (nur für English; Deutsch = Originalwerte aus den CSVs)
KATEGORIE_NAMEN = {
    "en": {
        "Konsumkredit": "Consumer credit",
        "Unternehmenskredit": "Corporate credit",
        "Leitzins": "Key interest rate",
    },
}
LAUFZEIT_NAMEN = {
    "en": {
        "bis 1 Jahr": "up to 1 year",
        "1 bis 5 Jahre": "1 to 5 years",
        "über 5 Jahre": "over 5 years",
        "gesamt": "total",
        "Hauptrefinanzierung": "Main refinancing",
        "Einlagefazilität": "Deposit facility",
        "Spitzenrefinanzierung": "Marginal lending facility",
    },
}
ZINSART_NAMEN = {
    "en": {
        "Konsum_gesamt": "Consumer_total",
        "Konsum_bis_1J": "Consumer_up_to_1Y",
        "Konsum_1_bis_5J": "Consumer_1_to_5Y",
        "Konsum_ueber_5J": "Consumer_over_5Y",
        "Unternehmen_gesamt": "Corporate_total",
        "Hauptrefinanzierungssatz": "Main_refinancing_rate",
        "Einlagefazilitaet": "Deposit_facility_rate",
        "Spitzenrefinanzierung": "Marginal_lending_rate",
    },
}
SPALTEN_NAMEN = {
    "en": {
        "Zeit_ID": "Time_ID",
        "Zinsart_ID": "Rate_type_ID",
        "Zinssatz": "Interest_rate",
        "Datum": "Date",
        "Jahr": "Year",
        "Quartal": "Quarter",
        "Monat": "Month",
        "Jahr_Monat": "Year_Month",
        "Zinsart_Code": "Rate_type_code",
        "Kategorie": "Category",
        "Laufzeit": "Term",
    },
}


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

# ------------------------------------------------------------
# Sprachumschalter (oben in der Sidebar); ?lang=en wählt Englisch vor
# ------------------------------------------------------------
SPRACHEN = {"Deutsch": "de", "English": "en"}
startsprache = 1 if str(st.query_params.get("lang", "de")).lower().startswith("en") else 0
lang = SPRACHEN[
    st.sidebar.radio(TEXTE["de"]["language"], list(SPRACHEN), index=startsprache, horizontal=True)
]
T = TEXTE[lang]


def kat(wert: str) -> str:
    return KATEGORIE_NAMEN.get(lang, {}).get(wert, wert)


def laufzeit(wert: str) -> str:
    return LAUFZEIT_NAMEN.get(lang, {}).get(wert, wert)


def zinsart(wert: str) -> str:
    return ZINSART_NAMEN.get(lang, {}).get(wert, wert)


KATEGORIE_REIHENFOLGE_ANZ = [kat(k) for k in KATEGORIE_REIHENFOLGE]
LAUFZEIT_REIHENFOLGE_ANZ = [laufzeit(l) for l in LAUFZEIT_REIHENFOLGE]
FARBEN_ANZ = {kat(k): farbe for k, farbe in FARBEN.items()}

st.title(T["title"])
st.caption(T["source"])
st.write("")  # eine Leerzeile zwischen Datenquelle und "Aktuelle Eckwerte"


# ------------------------------------------------------------
# 3. Sidebar-Filter
# ------------------------------------------------------------
st.sidebar.header(T["filter"])

kategorien = sorted(df["Kategorie"].unique())
gewaehlte_kategorien = st.sidebar.multiselect(
    T["category"], kategorien, default=kategorien, format_func=kat, key="filter_kategorie"
)

laufzeiten = sorted(df["Laufzeit"].unique())
gewaehlte_laufzeiten = st.sidebar.multiselect(
    T["term"], laufzeiten, default=laufzeiten, format_func=laufzeit, key="filter_laufzeit"
)

min_datum, max_datum = df["Datum"].min(), df["Datum"].max()
zeitraum = st.sidebar.slider(
    T["period"],
    min_value=min_datum.to_pydatetime(),
    max_value=max_datum.to_pydatetime(),
    value=(min_datum.to_pydatetime(), max_datum.to_pydatetime()),
    format="MM/YYYY",
    key="filter_zeitraum",
)

df_filtered = df[
    df["Kategorie"].isin(gewaehlte_kategorien)
    & df["Laufzeit"].isin(gewaehlte_laufzeiten)
    & df["Datum"].between(zeitraum[0], zeitraum[1])
]

# Anzeige-Kopie: Kategorie/Laufzeit in der gewählten Sprache (Berechnungen laufen auf df_filtered)
df_view = df_filtered.copy()
df_view["Kategorie"] = df_view["Kategorie"].map(kat)
df_view["Laufzeit"] = df_view["Laufzeit"].map(laufzeit)
LABELS = {"Kategorie": T["category"], "Laufzeit": T["term"], "Datum": T["date"], "Zinssatz": T["rate"]}


# ------------------------------------------------------------
# 4. KPI-Kacheln (aktuelle Eckwerte)
# ------------------------------------------------------------
st.subheader(T["kpi_header"])
st.write("")  # eine Leerzeile, damit die Karten nicht an der Überschrift kleben

neueste_werte = df_filtered.sort_values("Datum").groupby("Zinsart_Code")["Zinssatz"].last()
neuestes_datum = df_filtered["Datum"].max()

col1, col2, col3 = st.columns(3)
col1.metric(T["kpi_key"], format_wert(neueste_werte.get("Hauptrefinanzierungssatz", np.nan)))
col2.metric(T["kpi_consumer"], format_wert(neueste_werte.get("Konsum_gesamt", np.nan)))
col3.metric(T["kpi_corporate"], format_wert(neueste_werte.get("Unternehmen_gesamt", np.nan)))
letzte_daten = df_filtered.groupby("Zinsart_Code")["Datum"].max()


def stand(code: str) -> str:
    d = letzte_daten.get(code)
    return f"{d:%m/%Y}" if pd.notna(d) else "–"


st.caption(
    f"{T['asof']}: {T['asof_key']} {stand('Hauptrefinanzierungssatz')}, "
    f"{T['asof_consumer']} {stand('Konsum_gesamt')}, "
    f"{T['asof_corporate']} {stand('Unternehmen_gesamt')}"
)

st.divider()


# ------------------------------------------------------------
# 5. Zinsentwicklung über Zeit
# ------------------------------------------------------------
st.subheader(T["dev_header"])

fig1 = px.line(
    df_view,
    x="Datum",
    y="Zinssatz",
    color="Laufzeit",
    line_dash="Kategorie",
    color_discrete_sequence=PALETTE_KATEGORIAL,
    category_orders={"Kategorie": KATEGORIE_REIHENFOLGE_ANZ, "Laufzeit": LAUFZEIT_REIHENFOLGE_ANZ},
    labels=LABELS,
)
fig1.update_layout(yaxis_title=T["rate_axis"], xaxis_title="", legend_title="")
st.plotly_chart(fig1, use_container_width=True)

st.divider()


# ------------------------------------------------------------
# 6. Zinsspanne: Kreditzins minus Leitzins
# ------------------------------------------------------------
st.subheader(T["spread_header"])

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
    spanne_lang["Kategorie"] = spanne_lang["Kategorie"].map(kat)
    fig4 = px.line(
        spanne_lang,
        x="Datum",
        y="Spanne",
        color="Kategorie",
        color_discrete_map=FARBEN_ANZ,
        labels={"Kategorie": T["category"], "Datum": T["date"], "Spanne": T["spread"]},
    )
    fig4.update_layout(yaxis_title=T["spread_axis"], xaxis_title="", legend_title="")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info(T["need_key"].format(kat=kat("Leitzins")))

st.divider()


# ------------------------------------------------------------
# 7. Aktuellster Zinssatz je Zinsart
# ------------------------------------------------------------
st.subheader(
    f"{T['latest_header']} "
    f"({T['latest_loans']} {stand('Konsum_gesamt')}, {T['latest_key']} {stand('Hauptrefinanzierungssatz')})"
)

letzter = (
    df_filtered.sort_values("Datum")
    .groupby(["Kategorie", "Laufzeit"], as_index=False)
    .last()
)
letzter["Kategorie"] = letzter["Kategorie"].map(kat)
letzter["Laufzeit"] = letzter["Laufzeit"].map(laufzeit)
fig2 = px.bar(
    letzter,
    x="Laufzeit",
    y="Zinssatz",
    color="Laufzeit",
    facet_col="Kategorie",
    color_discrete_sequence=PALETTE_KATEGORIAL,
    category_orders={"Kategorie": KATEGORIE_REIHENFOLGE_ANZ, "Laufzeit": LAUFZEIT_REIHENFOLGE_ANZ},
    labels=LABELS,
)
fig2.update_xaxes(matches=None, showticklabels=True, title="")
fig2.update_layout(yaxis_title=T["rate_axis"], showlegend=False)
fig2.update_traces(texttemplate="%{y:.2f}%", textposition="outside")
# Facet-Titel bereinigen: "Kategorie=Konsumkredit" -> "Konsumkredit"
fig2.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
st.plotly_chart(fig2, use_container_width=True)

st.divider()


# ------------------------------------------------------------
# 8. Kreditzins vs. EZB-Hauptrefinanzierungssatz
# ------------------------------------------------------------
st.subheader(T["scatter_header"])

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
    namen_kredit = {"Konsum_gesamt": kat("Konsumkredit"), "Unternehmen_gesamt": kat("Unternehmenskredit")}

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
            hovertemplate=(
                f"{T['hover_key']}: %{{x:.2f}}%<br>{T['hover_loan']}: %{{y:.2f}}%"
                f"<br>{T['hover_date']}: %{{customdata}}<extra></extra>"
            ),
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
        xaxis_title=T["scatter_x"],
        yaxis_title=T["scatter_y"],
        legend_title="",
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.caption(T["jitter_note"])
else:
    st.info(T["need_key"].format(kat=kat("Leitzins")))

st.divider()


# ------------------------------------------------------------
# 9. Rohdaten (mit eigenen Tabellen-Filtern)
# ------------------------------------------------------------
with st.expander(T["raw_expander"]):
    st.caption(T["raw_note"])

    tab_col1, tab_col2 = st.columns(2)
    zinsart_optionen = sorted(df_filtered["Zinsart_Code"].unique())
    gewaehlte_zinsarten = tab_col1.multiselect(
        T["raw_type"], zinsart_optionen, default=zinsart_optionen, format_func=zinsart, key="roh_zinsart"
    )
    jahr_optionen = sorted(df_filtered["Jahr"].unique())
    gewaehlte_jahre = tab_col2.multiselect(
        T["raw_year"], jahr_optionen, default=jahr_optionen, key="roh_jahr"
    )

    tabelle_gefiltert = df_filtered[
        df_filtered["Zinsart_Code"].isin(gewaehlte_zinsarten)
        & df_filtered["Jahr"].isin(gewaehlte_jahre)
    ].copy()

    # Anzeige in der gewählten Sprache (Werte und Spaltennamen)
    tabelle_gefiltert["Kategorie"] = tabelle_gefiltert["Kategorie"].map(kat)
    tabelle_gefiltert["Laufzeit"] = tabelle_gefiltert["Laufzeit"].map(laufzeit)
    tabelle_gefiltert["Zinsart_Code"] = tabelle_gefiltert["Zinsart_Code"].map(zinsart)
    tabelle_gefiltert = tabelle_gefiltert.rename(columns=SPALTEN_NAMEN.get(lang, {}))
    st.dataframe(tabelle_gefiltert, use_container_width=True)
