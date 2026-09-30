# Kreditzinsen in Deutschland vs. EZB-Leitzins

**Sprachen:** Deutsch · [English](README.en.md)

Analyse der Kreditzinsen für Konsumenten- und Unternehmenskredite (Neugeschäft) in Deutschland im Vergleich zu den EZB-Leitzinsen, Zeitraum Januar 2020 bis September 2026 (Kreditzinsen bis Juli 2026). Datenbasis: offizielle Bundesbank-Zeitreihen, automatisiert über die SDMX-REST-API abgerufen.

**Live-Demo:** [https://german-credit-rates-vs-ecb-rate-ywntxevqbxdtuaskipepzy.streamlit.app](https://german-credit-rates-vs-ecb-rate-ywntxevqbxdtuaskipepzy.streamlit.app/)

**Hinweis:** Dieses Projekt wurde mit Unterstützung von KI (Claude) entwickelt — bei Code-Struktur, Debugging und Dokumentation. Ich sehe mich nicht als professionellen Software-Entwickler. Mein Fokus liegt auf Datenanalyse.

---

## Screenshots

### Notebook: Zinsentwicklung über Zeit
![Zinsentwicklung](images/notebook_zinsentwicklung.png)

---

### Notebook: Korrelation mit dem Leitzins
![Korrelation](images/notebook_korrelation_heatmap.png)

---

### Dashboard: Zinsentwicklung über Zeit
![Dashboard Zeitverlauf](images/dashboard_zinsentwicklung.png)

---

### Dashboard: Zinsspanne
![Dashboard Zinsspanne](images/dashboard_zinsspanne.png)

---

## Datenquelle

[Bundesbank SDMX Web Service](https://api.statistiken.bundesbank.de) — öffentlich, keine Anmeldung nötig.

| Zeitreihe | Dataflow | Series Key |
|---|---|---|
| Konsumkredit, gesamt | BBIM1 | M.DE.B.A2B.A.C.A.2250.EUR.N |
| Konsumkredit, bis 1 Jahr | BBIM1 | M.DE.B.A2B.F.R.A.2250.EUR.N |
| Konsumkredit, 1–5 Jahre | BBIM1 | M.DE.B.A2B.I.R.A.2250.EUR.N |
| Konsumkredit, über 5 Jahre | BBIM1 | M.DE.B.A2B.J.R.A.2250.EUR.N |
| Unternehmenskredit, gesamt | BBIM1 | M.DE.B.A2A.A.R.A.2240.EUR.N |
| Hauptrefinanzierungssatz | BBIN1 | M.D0.ECB.ECBMIN.EUR.ME |
| Einlagefazilität | BBIN1 | M.D0.ECB.ECBFAC.EUR.ME |
| Spitzenrefinanzierung | BBIN1 | M.D0.ECB.ECBREF.EUR.ME |

Die fünf Kreditzinsreihen betreffen das Neugeschäft (keine Bestandskredite). Alle Reihen sind Monatswerte.

---

## Architektur

```
Bundesbank SDMX-API
        │
        ▼
Jupyter Notebook  (Abruf, Bereinigung, EDA)
        │
        ▼
Star-Schema-Export (3 CSVs, Keys statt breiter Tabelle)
        │
        ▼
Streamlit-Dashboard (dashboard.py)
```

## Repo-Struktur

```
├── bundesbank_kreditzinsen_analysis.ipynb   # Datenabruf + EDA, exportiert die 3 Star-Schema-CSVs
├── dashboard.py                             # Streamlit-Dashboard
├── requirements.txt                         # Abhängigkeiten des Dashboards
├── dim_zeit.csv                             # Dimension: Zeit
├── dim_zinsart.csv                          # Dimension: Zinsart
├── fact_zinssaetze.csv                      # Faktentabelle
├── kreditzinsen_leitzins_seit_2020.csv      # breite Tabelle mit denselben Werten (wird weder vom
│                                            #   aktuellen Notebook erzeugt noch vom Dashboard verwendet)
├── images/                                  # Screenshots für die README
├── README.md                                # deutsche Version (diese Datei)
└── README.en.md                             # englische Version
```

---

## Datenmodell (Star-Schema)

Statt einer breiten Tabelle: eine Fact-Tabelle + zwei Dimensionstabellen, verbunden über die Schlüsselspalten `Zeit_ID` und `Zinsart_ID`. Das Notebook bezeichnet das Schema als „Star-Schema für Power BI“; ein Power-BI-Bericht ist nicht Teil dieses Repos.

- **Dim_Zeit** (81 Zeilen): eine Zeile pro Monat (01/2020–09/2026), Key `Zeit_ID` (Format `JJJJMM`), weitere Spalten: `Datum`, `Jahr`, `Quartal`, `Monat`, `Jahr_Monat`
- **Dim_Zinsart** (8 Zeilen): eine Zeile pro Zinsreihe, Key `Zinsart_ID`, weitere Spalten: `Zinsart_Code`, `Kategorie` (Konsumkredit / Unternehmenskredit / Leitzins), `Laufzeit`
- **Fact_Zinssaetze** (638 Zeilen): eine Zeile pro (Monat, Zinsart) mit `Zinssatz` — nur tatsächlich vorhandene Werte. Von den 648 möglichen Kombinationen (81 × 8) fehlen 10: die fünf Kreditzinsreihen für 08/2026 und 09/2026.

CSV-Format: Trennzeichen `;`, Dezimalkomma, UTF-8 mit BOM.

---

## Setup

```bash
# Abhängigkeiten
pip install pandas numpy matplotlib requests jupyter streamlit plotly

# Notebook ausführen (ruft Daten live von der Bundesbank ab, exportiert die 3 CSVs)
jupyter lab bundesbank_kreditzinsen_analysis.ipynb

# Dashboard starten (im Repo-Ordner ausführen, dort werden die 3 CSVs gelesen)
streamlit run dashboard.py
```

---

## Finanzbericht: Kernergebnisse

Alle Zahlen unten sind aus den im Repo liegenden CSV-Dateien (Bundesbank-Daten) berechnet. Die Kreditzinsreihen reichen bis 07/2026, die Leitzinsreihen bis 09/2026. Ein erneuter Notebook-Lauf holt den dann aktuellen Datenstand und kann davon abweichen.

### Leitzinszyklus seit 2020 (Hauptrefinanzierungssatz)

- **01/2020–06/2022**: konstant 0,00 % (die Einlagefazilität lag in dieser Zeit bei −0,50 %)
- **07/2022**: erste Erhöhung (+0,50 pp)
- **09/2023–05/2024**: Höchststand bei 4,50 %
- **06/2024–06/2025**: acht Senkungen, von 4,50 % auf 2,15 %
- **06/2025–05/2026**: konstant 2,15 %
- **06/2026–09/2026**: Anstieg auf 2,40 % (06/2026) und 2,65 % (09/2026)
- Insgesamt 20 Änderungen zwischen aufeinanderfolgenden Monatswerten (12 Erhöhungen, 8 Senkungen); 18 unterschiedliche Zinsniveaus seit 2020

### Zusammenhang Kreditzins ↔ Leitzins (Korrelation, Pearson r)

Basis: die 79 Monate 01/2020–07/2026, in denen alle Reihen Werte haben.

| Reihe | r (vs. Hauptrefinanzierungssatz) |
|---|---|
| Unternehmenskredit, gesamt | **0,993** |
| Konsumkredit, über 5 Jahre | 0,932 |
| Konsumkredit, 1–5 Jahre | 0,911 |
| Konsumkredit, gesamt | 0,906 |
| Konsumkredit, bis 1 Jahr | **0,077** |

- Unternehmenskredit: r = 0,993. Die Steigung der Regressionsgeraden beträgt 0,87 — im Schnitt geht ein Prozentpunkt mehr Leitzins mit 0,87 Prozentpunkten höherem Unternehmenskreditzins einher.
- Konsumkredit, gesamt: r = 0,906, Steigung 0,69.
- Konsumkredit, 1–5 Jahre und über 5 Jahre: r = 0,911 bzw. 0,932.
- Konsumkredit, bis 1 Jahr: r = 0,077, also praktisch kein linearer Zusammenhang mit dem Leitzins. Dieser Befund ist auffällig, wird hier aber nur berichtet, nicht kausal erklärt (dafür reichen die vorliegenden Daten nicht aus).

### Zinsspanne (Kreditzins minus Hauptrefinanzierungssatz, gleicher Monat)

| | 01/2020 | 07/2026 | Minimum | Maximum |
|---|---|---|---|---|
| Konsumkredit, gesamt | 6,07 pp | 6,18 pp | 3,77 pp (03/2024) | 6,40 pp (01/2026) |
| Unternehmenskredit, gesamt | 1,24 pp | 1,38 pp | 0,56 pp (02/2024) | 2,19 pp (06/2022) |

- Die Spanne ist 07/2026 bei Konsumkrediten um 0,11 pp und bei Unternehmenskrediten um 0,14 pp höher als 01/2020. Dazwischen schwankt sie deutlich; am engsten war sie im Februar (Unternehmenskredit) bzw. März 2024 (Konsumkredit).
- Die Konsumkredit-Spanne war in allen 79 Monaten größer als die Unternehmenskredit-Spanne, im Median 4,61-mal so groß (Minimum 2,74-mal in 06/2022, Maximum 7,25-mal in 02/2024).

### Aktuelle Werte

| Zinsart | Wert | Stand |
|---|---|---|
| Hauptrefinanzierungssatz | 2,65 % | 09/2026 |
| Einlagefazilität | 2,50 % | 09/2026 |
| Spitzenrefinanzierung | 2,90 % | 09/2026 |
| Konsumkredit, gesamt | 8,58 % | 07/2026 |
| Unternehmenskredit, gesamt | 3,78 % | 07/2026 |

### Einschränkungen

- Korrelation belegt keine Kausalität — die Analyse ist deskriptiv, kein ökonometrisches Modell
- Die Kreditzinsreihen enthalten keine Werte für 08/2026 und 09/2026 (im Abruf nicht vorhanden); die Leitzinsreihen reichen bis 09/2026
- Für Unternehmenskredite wird nur die Gesamtreihe verwendet (keine Aufteilung nach Laufzeit), für Konsumkredite zusätzlich drei Reihen nach Zinsbindung
- Die Reihe „Konsumkredit, gesamt“ hat im Series Key an einer Stelle den Buchstaben `C`, die übrigen vier Kreditreihen dort `R`. Laut ECB-Codeliste der MFI-Zinsstatistik steht `C` für den effektiven Jahreszins inkl. Kosten (APRC) und `R` für den vereinbarten Jahreszins bzw. eng definierten Effektivzins (AAR/NDER). Die Gesamtreihe misst daher möglicherweise nicht exakt dasselbe Zinsmaß wie die Reihen nach Zinsbindung; Vergleiche zwischen beiden sind vorsichtig zu lesen.
- Neugeschäft — keine Aussage über Bestandskredite oder individuelle Kreditkonditionen

---

## Tech Stack

Python · pandas · NumPy · Matplotlib · requests · Jupyter · Streamlit · Plotly

## Autor

Amir — [GitHub](https://github.com/Amirhouschang)
