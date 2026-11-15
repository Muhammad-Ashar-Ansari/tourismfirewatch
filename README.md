# 🔥 TourismFireWatch

**Global Fire Activity Monitoring & Smart Tourism Awareness**
*Explore. Analyze. Harmonize. Inform.*

NASA Space Apps Challenge 2026 · 2-day hackathon (14–15 November 2026)

TourismFireWatch is a web application that brings NASA **MODIS** and **VIIRS** satellite active-fire detections into one harmonized view and puts them next to tourism locations (parks, heritage sites, attractions, resort areas). It lets visitors and tourism planners explore recent and historical satellite fire observations around the places people travel to.

> **Note:** TourismFireWatch shows satellite fire detections near a location. It is **not** a safety advisory. Always check official local fire and tourism authorities before travelling.

---

## Features

| Tab | What it does |
|---|---|
| 🗺️ **Fire map** | Interactive map with MODIS and VIIRS as separate layers (marker size reflects pixel size: ~1 km vs ~375 m), tourism markers, and hover details (date, overpass time, FRP, confidence). |
| 📅 **Burning calendar** | GitHub-style heatmap of daily activity (detections or total fire radiative power), switchable between combined / MODIS / VIIRS. Pick any day to see its map, sensor counts and strongest fires. |
| 📈 **Trends & sensors** | Daily and monthly detections by sensor, regional totals, overpass-time pattern, confidence mix and FRP distribution, plus a sensor statistics table that shows why harmonization matters. |
| 🏨 **Tourism exposure** | For each tourism site: detections within a chosen radius over a chosen look-back window, nearest detection distance, MODIS/VIIRS split, and an alert level. A "focus on a site" map shows the surrounding detections. |
| ℹ️ **Data & methods** | Dataset overview, data notes, the data contract and a MODIS vs VIIRS comparison. |

**Sidebar filters** apply across the whole app: date range, sensor, region, harmonized confidence, day/night, minimum FRP, tourism site type, an option to collapse cross-sensor matches, and a CSV download of the filtered data.

### Tourism alert levels

Based on the number of detections within the selected radius during the look-back window:

| Level | Detections |
|---|---|
| Clear | 0 |
| Watch | 1–5 |
| Elevated | 6–25 |
| High | more than 25 |

---

## Quick start

**Requirements:** Python 3.10 or newer.

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Run the dashboard
python -m streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

### Project structure

```
tourismfirewatch/
├── app.py                         # Streamlit dashboard
├── requirements.txt
├── README.md
└── data/
    ├── processed_fires.csv        # harmonized MODIS + VIIRS detections
    └── tourism_locations.csv      # optional: tourism locations
```

If `data/processed_fires.csv` is missing, the app runs on **synthetic demo data** (a banner says so) so the interface can be tested. If `data/tourism_locations.csv` is missing, a built-in sample list of well-known destinations is used.

---

## Data

Fire detections come from **NASA FIRMS** (Fire Information for Resource Management System): MODIS (Terra and Aqua) and VIIRS (Suomi NPP, NOAA-20, NOAA-21) active-fire products. The processed file in this repository uses the standard-processing (SP) products.

### MODIS vs VIIRS

| | MODIS | VIIRS |
|---|---|---|
| Pixel size | ≈ 1 km | ≈ 375 m |
| Record starts | 2000 | 2012 |
| Small-fire detection | Weaker | Better |
| Confidence field | Numeric 0–100 | Categorical `l` / `n` / `h` |
| Typical FRP per detection | Higher (larger pixels) | Lower |

Sensor-specific characteristics are **preserved**, not hidden: every record keeps its sensor label, satellite, original confidence value and pixel size, and the dashboard shows the differences side by side.

### Harmonization

- **Common schema:** MODIS and VIIRS records are merged into one table (see below).
- **Confidence classes:** MODIS < 30 → `low`, 30–79 → `nominal`, ≥ 80 → `high`; VIIRS `l` → `low`, `n` → `nominal`, `h` → `high`. The original value is kept in `confidence_raw`.
- **Cross-sensor matching:** `cross_sensor_match` flags detections that overlap a detection from the other sensor on the same day (approximate spatial overlap). The sidebar option *Collapse cross-sensor matches* hides MODIS detections that VIIRS already saw, keeping the finer 375 m record. *(Matching distance threshold: see the data-processing notes of the data lead.)*

### Data contract: `data/processed_fires.csv`

One row per detection.

| Column | Type | Required | Notes |
|---|---|---|---|
| `latitude`, `longitude` | float | yes | Detection centre |
| `acq_date` | `YYYY-MM-DD` | yes | Acquisition date (UTC) |
| `acq_time` | int `HHMM` | optional | Acquisition time (UTC) |
| `sensor` | `MODIS` \| `VIIRS` | yes | Preserved sensor label |
| `frp` | float (MW) | yes | Fire radiative power |
| `confidence_raw` | str | optional | Original value (MODIS 0–100, VIIRS l/n/h) |
| `confidence_class` | `low` \| `nominal` \| `high` | yes | Harmonized class |
| `daynight` | `D` \| `N` | optional | Day or night overpass |
| `resolution_m` | int | optional | 1000 (MODIS) / 375 (VIIRS) |
| `satellite` | str | optional | Terra / Aqua / N / N20 / N21 (kept for reference) |
| `region` | str | optional | Region label for the filter; computed from coordinates if missing |
| `cross_sensor_match` | bool | optional | Overlap with the other sensor on the same day |

The loader tolerates common export quirks: title lines above the header, blank lines, comma / tab / semicolon delimiters, and Excel encodings.

### Tourism file: `data/tourism_locations.csv`

Columns: `name`, `type`, `latitude`, `longitude`, optional `country`. Suggested `type` values: `Park`, `Resort area`, `Hotel`, `Heritage site`, `Attraction`.

---

## Technology stack

- **Python** with **pandas** and **NumPy** for data handling and the distance (haversine) calculations
- **Streamlit** for the dashboard
- **Plotly** for the maps, calendar heatmap and charts

---

## Development workflow

NASA data collection → data harmonization → interactive fire map → burning activity calendar → tourism integration → dashboard → testing → submission.

---

## Limitations

- The processed dataset provided for this submission is a **sample** (200 records for Australia and Pakistan). In 133 of these records, the acquisition date was not readable in the source file. These records are shown on the map and in tourism counts, but left out of the calendar and trend charts. No dates were estimated or filled in.
- **Region labels** are approximate (bounding-box based), so a few records near borders may be labelled with a neighbouring country.
- The **tourism list** is a curated sample of well-known destinations, not a complete hotel and attraction database.
- Standard-processing (SP) fire products are released with a delay, so the data is **not real-time**.
- Satellite active-fire detections can include non-wildfire heat sources (e.g. agricultural or industrial burning), and small or short-lived fires can be missed, especially by the coarser MODIS pixels.
- Cross-sensor matching is approximate.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit` not recognized | Use `python -m streamlit run app.py` |
| `pip` not recognized | Use `python -m pip install -r requirements.txt` |
| Port already in use | `python -m streamlit run app.py --server.port 8502` |
| Old data still showing after replacing the CSV | Stop the app (`Ctrl + C`) and start it again; the app caches loaded data |
| "missing required columns" | Make sure the CSV's header row contains the required columns listed above |
| Many dates show `########` in the spreadsheet | The column is too narrow. Widen it before exporting, or export directly from Python with dates as `YYYY-MM-DD` |

---

## Team

| Member | Role |
|---|---|
| Aqsa Kanwal | Team Lead & Project Coordinator |
| Asad Ullah Khan | Python Developer & Data Harmonization |
| Rubab Shahzadi | NASA Data Research & Documentation |
| Engr Ali | GIS & Interactive Map Development |
| Muhammad Ashar Ansari | Dashboard & Data Visualization |
| Ayesha Andleeb | Tourism Research & Location Data |

---

## Acknowledgements

Fire data: NASA FIRMS, using MODIS and VIIRS active-fire observations. Map tiles: © OpenStreetMap contributors. Built for the NASA Space Apps Challenge 2026.

**Demo / presentation links:** _add here_
