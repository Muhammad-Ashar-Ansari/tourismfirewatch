"""
TourismFireWatch - Dashboard & Data Visualization module (Streamlit)
NASA Space Apps Challenge 2026

Run:   streamlit run app.py

PLUG IN REAL DATA (no code changes needed):
  data/processed_fires.csv      <- Asad's harmonized MODIS + VIIRS file
  data/tourism_locations.csv    <- Ayesha's tourism dataset
If those files are missing, the app runs on realistic DEMO data so the whole
team can develop against the same data contract (see the "Data & methods" tab).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="TourismFireWatch", page_icon="🔥", layout="wide")

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
FIRE_FILE = DATA_DIR / "processed_fires.csv"
TOURISM_FILE = DATA_DIR / "tourism_locations.csv"

FIRE_REQUIRED = ["latitude", "longitude", "acq_date", "sensor", "frp", "confidence_class"]
TOURISM_REQUIRED = ["name", "type", "latitude", "longitude"]

SENSOR_COLORS = {"MODIS": "#E4572E", "VIIRS": "#2A7FBA"}
SENSOR_RES_M = {"MODIS": 1000, "VIIRS": 375}
CONF_ORDER = ["low", "nominal", "high"]
LEVEL_ORDER = ["Clear", "Watch", "Elevated", "High"]
LEVEL_COLORS = {"Clear": "#6BAA75", "Watch": "#F2C14E", "Elevated": "#F78154", "High": "#B33F40"}

# Region presets: bbox = (lat_min, lat_max, lon_min, lon_max). Used for the region
# filter (works on real data too) and to generate the demo hotspots.
REGIONS = {
    "California, USA": dict(
        bbox=(32, 42.5, -124.7, -114), center=(37.2, -119.5), zoom=5, peak=250, kappa=3.0, n=2600, spread=0.25,
        hotspots=[(37.9, -119.8), (36.5, -118.7), (39.1, -120.2), (34.2, -118.5), (38.5, -122.4)]),
    "Southeast Australia": dict(
        bbox=(-39.5, -32, 140, 154), center=(-36.5, 147), zoom=5, peak=15, kappa=3.0, n=2400, spread=0.25,
        hotspots=[(-33.7, 150.2), (-36.4, 148.3), (-38.0, 143.5), (-38.9, 146.3)]),
    "Amazon, Brazil": dict(
        bbox=(-18, 2, -70, -48), center=(-8, -60), zoom=3.5, peak=250, kappa=3.5, n=3200, spread=0.4,
        hotspots=[(-3.0, -60.0), (-2.6, -55.5), (-8.0, -62.0), (-15.4, -55.8), (-10.0, -55.0)]),
    "Mediterranean Europe": dict(
        bbox=(35, 43, -10, 27), center=(39, 10), zoom=3.2, peak=205, kappa=3.0, n=1800, spread=0.25,
        hotspots=[(39.7, 21.6), (38.4, 22.5), (37.6, 21.6), (38.8, -9.4), (40.0, -8.0)]),
    "Punjab & Sindh, Pakistan": dict(
        bbox=(23.5, 32.5, 66, 75), center=(28, 70.5), zoom=5, peak=305, kappa=2.5, n=2200, spread=0.35,
        hotspots=[(31.4, 74.2), (30.5, 71.8), (28.7, 71.3), (27.3, 68.2), (24.8, 67.9)]),
    "Indonesia": dict(
        bbox=(-9, 3, 100, 120), center=(-2.5, 110), zoom=4, peak=260, kappa=3.5, n=2800, spread=0.3,
        hotspots=[(-2.7, 111.9), (-1.8, 103.5), (-3.2, 104.2), (-8.5, 115.2), (-7.9, 113.0)]),
}

# Demo tourism list (real, well-known places; replace with Ayesha's dataset)
DEMO_SITES = [
    ("Yosemite National Park", "Park", "USA", 37.8651, -119.5383),
    ("Sequoia National Park", "Park", "USA", 36.4864, -118.5658),
    ("Lake Tahoe", "Resort area", "USA", 39.0968, -120.0324),
    ("Napa Valley", "Attraction", "USA", 38.5025, -122.2654),
    ("Griffith Observatory", "Attraction", "USA", 34.1184, -118.3004),
    ("Blue Mountains National Park", "Park", "Australia", -33.72, 150.31),
    ("Kosciuszko National Park", "Park", "Australia", -36.456, 148.263),
    ("Great Ocean Road", "Attraction", "Australia", -38.68, 143.39),
    ("Wilsons Promontory National Park", "Park", "Australia", -39.03, 146.32),
    ("Kakadu National Park", "Park", "Australia", -12.80, 132.90),
    ("Mataranka Thermal Pools", "Attraction", "Australia", -14.92, 133.07),
    ("Purnululu National Park (Bungle Bungles)", "Park", "Australia", -17.50, 128.40),
    ("Mitchell Falls", "Attraction", "Australia", -14.82, 125.70),
    ("Lakefield National Park (Cape York)", "Park", "Australia", -14.90, 144.20),
    ("Litchfield National Park", "Park", "Australia", -13.10, 130.80),
    ("Nitmiluk (Katherine Gorge)", "Park", "Australia", -14.30, 132.40),
    ("Teatro Amazonas, Manaus", "Attraction", "Brazil", -3.1303, -60.0233),
    ("Anavilhanas National Park", "Park", "Brazil", -2.7, -60.8),
    ("Alter do Chão", "Resort area", "Brazil", -2.5, -55.0),
    ("Chapada dos Guimarães NP", "Park", "Brazil", -15.43, -55.75),
    ("Meteora", "Heritage site", "Greece", 39.7217, 21.6306),
    ("Delphi", "Heritage site", "Greece", 38.4824, 22.5010),
    ("Ancient Olympia", "Heritage site", "Greece", 37.6383, 21.6300),
    ("Sintra", "Heritage site", "Portugal", 38.7979, -9.3881),
    ("Serra da Estrela Natural Park", "Park", "Portugal", 40.32, -7.61),
    ("Lahore Fort", "Heritage site", "Pakistan", 31.5888, 74.3142),
    ("Derawar Fort", "Heritage site", "Pakistan", 28.7747, 71.3342),
    ("Mohenjo-daro", "Heritage site", "Pakistan", 27.3292, 68.1389),
    ("Makli Necropolis, Thatta", "Heritage site", "Pakistan", 24.7667, 67.8833),
    ("Mohatta Palace, Karachi", "Attraction", "Pakistan", 24.8138, 67.0307),
    ("Nankana Sahib", "Heritage site", "Pakistan", 31.4505, 73.7047),
    ("Harappa", "Heritage site", "Pakistan", 30.6306, 72.8639),
    ("Tomb of Shah Rukn-e-Alam, Multan", "Heritage site", "Pakistan", 30.1978, 71.4783),
    ("Uch Sharif", "Heritage site", "Pakistan", 29.2333, 71.0667),
    ("Noor Mahal, Bahawalpur", "Attraction", "Pakistan", 29.3956, 71.6836),
    ("Katas Raj Temples", "Heritage site", "Pakistan", 32.7167, 72.9500),
    ("Tanjung Puting National Park", "Park", "Indonesia", -2.75, 111.85),
    ("Ubud, Bali", "Resort area", "Indonesia", -8.5069, 115.2625),
    ("Mount Bromo", "Attraction", "Indonesia", -7.9425, 112.953),
    ("Kerinci Seblat National Park", "Park", "Indonesia", -2.0, 101.5),
]


def show(fig: go.Figure, key: str | None = None, container=None) -> None:
    """Render a plotly figure full-width (works on old and new Streamlit versions)."""
    target = container if container is not None else st
    try:
        target.plotly_chart(fig, width="stretch", key=key)
    except TypeError:  # older Streamlit without width="stretch"
        target.plotly_chart(fig, use_container_width=True, key=key)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def assign_region(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    region = np.full(len(lat), "Other", dtype=object)
    for name, r in REGIONS.items():
        la0, la1, lo0, lo1 = r["bbox"]
        region[(lat >= la0) & (lat <= la1) & (lon >= lo0) & (lon <= lo1)] = name
    return region


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


def make_demo_fires(seed: int = 42) -> pd.DataFrame:
    """Synthetic MODIS/VIIRS detections that follow the real data contract."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-11-15", "2026-11-12")
    doy = dates.dayofyear.values
    frames = []
    for name, r in REGIONS.items():
        n = r["n"]
        w = np.exp(r["kappa"] * np.cos(2 * np.pi * (doy - r["peak"]) / 365.25))
        w /= w.sum()
        d = rng.choice(dates.values, size=n, p=w)
        hs = np.array(r["hotspots"])
        k = rng.integers(0, len(hs), n)
        lat = hs[k, 0] + rng.normal(0, r["spread"], n)
        lon = hs[k, 1] + rng.normal(0, r["spread"], n)

        is_viirs = rng.random(n) < 0.70
        v = pd.DataFrame({"latitude": lat[is_viirs], "longitude": lon[is_viirs], "acq_date": d[is_viirs], "sensor": "VIIRS"})
        m_own = pd.DataFrame({"latitude": lat[~is_viirs], "longitude": lon[~is_viirs], "acq_date": d[~is_viirs], "sensor": "MODIS"})
        # ~30% of VIIRS detections also seen by MODIS the same day (cross-sensor matches)
        twin = v.sample(frac=0.30, random_state=seed).copy()
        twin["latitude"] += rng.normal(0, 0.004, len(twin))
        twin["longitude"] += rng.normal(0, 0.004, len(twin))
        twin["sensor"] = "MODIS"
        twin["cross_sensor_match"] = True
        for df in (v, m_own):
            df["cross_sensor_match"] = False
        part = pd.concat([v, m_own, twin], ignore_index=True)
        part["region_hint"] = name
        frames.append(part)

    f = pd.concat(frames, ignore_index=True)
    n = len(f)
    is_v = (f["sensor"] == "VIIRS").values

    # FRP: MODIS pixels are larger -> higher per-pixel FRP
    f["frp"] = np.where(is_v, rng.lognormal(0.8, 1.0, n), rng.lognormal(1.9, 1.0, n)).round(1)

    # Overpass time: local solar time -> UTC
    local_h = np.where(is_v, rng.choice([1.5, 13.5], n), rng.choice([10.5, 13.5, 22.5, 1.5], n))
    local_h = local_h + rng.uniform(-0.6, 0.6, n)
    utc_h = (local_h - f["longitude"].values / 15.0) % 24
    f["acq_time"] = (np.floor(utc_h) * 100 + np.floor((utc_h % 1) * 60)).astype(int)
    f["daynight"] = np.where((local_h % 24 >= 6) & (local_h % 24 < 18), "D", "N")

    # Confidence: VIIRS = l/n/h, MODIS = 0-100 -> harmonized class
    viirs_raw = rng.choice(["l", "n", "h"], n, p=[0.15, 0.65, 0.20])
    modis_raw = np.clip(rng.beta(2.2, 1.4, n) * 100, 0, 100).astype(int)
    f["confidence_raw"] = np.where(is_v, viirs_raw, modis_raw.astype(str))
    modis_cls = np.where(modis_raw < 30, "low", np.where(modis_raw < 80, "nominal", "high"))
    viirs_cls = pd.Series(viirs_raw).map({"l": "low", "n": "nominal", "h": "high"}).values
    f["confidence_class"] = np.where(is_v, viirs_cls, modis_cls)
    f["resolution_m"] = f["sensor"].map(SENSOR_RES_M)
    f["acq_date"] = pd.to_datetime(f["acq_date"])
    return f.drop(columns=["region_hint"]).sort_values("acq_date", ignore_index=True)


def read_flexible_csv(path: Path) -> pd.DataFrame:
    """Read a CSV/TSV even if it has a title line, blank lines, a different delimiter
    (comma / tab / semicolon), a BOM, or UTF-16 encoding (common with Excel exports)."""
    from io import StringIO

    text = ""
    for enc in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            text = Path(path).read_text(encoding=enc)
        except (UnicodeError, UnicodeDecodeError):
            continue
        if "latitude" in text.lower():
            break
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if "latitude" in ln.lower() and "longitude" in ln.lower()), 0)
    header = lines[start] if lines else ""
    sep = max([",", "\t", ";"], key=header.count)
    df = pd.read_csv(StringIO("\n".join(lines[start:])), sep=sep, skip_blank_lines=True)
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.loc[:, ~(df.columns.str.startswith("unnamed") & df.isna().all())]
    return df.dropna(how="all")


def normalize_fires(df: pd.DataFrame) -> pd.DataFrame:
    """Validate + fill optional columns so the rest of the app can rely on them."""
    missing = [c for c in FIRE_REQUIRED if c not in df.columns]
    if missing:
        st.error(f"`processed_fires.csv` is missing required columns: {missing}")
        st.caption(f"Columns found in the file: {list(df.columns)[:15]}")
        st.stop()
    df = df.copy()
    for c in ("latitude", "longitude"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[df["latitude"].notna() & df["longitude"].notna()].copy()

    raw_dates = df["acq_date"]
    try:
        parsed = pd.to_datetime(raw_dates, errors="coerce", format="mixed")
    except (TypeError, ValueError):  # older pandas
        parsed = pd.to_datetime(raw_dates, errors="coerce")
    df["date_known"] = parsed.notna()
    df["acq_date"] = parsed

    df["sensor"] = df["sensor"].astype(str).str.upper()
    df["confidence_class"] = df["confidence_class"].astype(str).str.lower()
    df["frp"] = pd.to_numeric(df["frp"], errors="coerce").fillna(0.0)
    if "acq_time" not in df:
        df["acq_time"] = 0
    df["acq_time"] = pd.to_numeric(df["acq_time"], errors="coerce").fillna(0).astype(int)
    if "daynight" not in df:
        df["daynight"] = "?"
    if "confidence_raw" not in df:
        df["confidence_raw"] = ""
    if "resolution_m" not in df:
        df["resolution_m"] = df["sensor"].map(SENSOR_RES_M)
    if "cross_sensor_match" not in df:
        df["cross_sensor_match"] = False
    df["cross_sensor_match"] = df["cross_sensor_match"].fillna(False).astype(str).str.lower().isin(["true", "1", "yes"])
    return df


@st.cache_data(show_spinner="Loading data...")
def load_data():
    using_demo_fires = not FIRE_FILE.exists()
    using_demo_sites = not TOURISM_FILE.exists()
    fires = make_demo_fires() if using_demo_fires else read_flexible_csv(FIRE_FILE)
    fires = normalize_fires(fires)
    if "region" in fires.columns and fires["region"].notna().any():
        fires["region"] = fires["region"].fillna("Other").astype(str)
    else:
        fires["region"] = assign_region(fires["latitude"].to_numpy(dtype=float), fires["longitude"].to_numpy(dtype=float))
    fires["hour"] = (fires["acq_time"].astype(int) // 100).clip(0, 23)

    if using_demo_sites:
        sites = pd.DataFrame(DEMO_SITES, columns=["name", "type", "country", "latitude", "longitude"])
    else:
        sites = read_flexible_csv(TOURISM_FILE)
        miss = [c for c in TOURISM_REQUIRED if c not in sites.columns]
        if miss:
            st.error(f"`tourism_locations.csv` is missing required columns: {miss}")
            st.stop()
        for c in ("latitude", "longitude"):
            sites[c] = pd.to_numeric(sites[c], errors="coerce")
        sites = sites.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
        if "country" not in sites:
            sites["country"] = ""
    return fires, sites, using_demo_fires, using_demo_sites


# ----------------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------------
_HAS_NEW_MAP = hasattr(go, "Scattermap")
_Scatter = go.Scattermap if _HAS_NEW_MAP else go.Scattermapbox
_MAPKEY = "map" if _HAS_NEW_MAP else "mapbox"


def fire_map(fires, sites=None, center=(20, 10), zoom=1.3, height=560, max_points=15000):
    """Placeholder map: swap this function for Engr Ali's folium/GIS map when ready."""
    fig = go.Figure()
    for sensor in ["MODIS", "VIIRS"]:
        g = fires[fires["sensor"] == sensor]
        if g.empty:
            continue
        if len(g) > max_points:
            g = g.sample(max_points, random_state=0)
        cd = np.column_stack([g["acq_date"].dt.strftime("%Y-%m-%d").fillna("date unknown"), g["frp"].round(1), g["confidence_class"], g["acq_time"].astype(int)])
        fig.add_trace(_Scatter(
            lat=g["latitude"], lon=g["longitude"], mode="markers", name=f"{sensor} ({SENSOR_RES_M[sensor]} m)",
            marker=dict(size=7 if sensor == "MODIS" else 4, color=SENSOR_COLORS[sensor], opacity=0.65),
            customdata=cd,
            hovertemplate=f"<b>{sensor}</b><br>%{{customdata[0]}} · %{{customdata[3]}} UTC<br>FRP: %{{customdata[1]}} MW<br>Confidence: %{{customdata[2]}}<extra></extra>",
        ))
    if sites is not None and len(sites):
        fig.add_trace(_Scatter(
            lat=sites["latitude"], lon=sites["longitude"], mode="markers", name="Tourism site",
            marker=dict(size=11, color="#1B998B"),
            customdata=np.column_stack([sites["name"], sites["type"]]),
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
        ))
    fig.update_layout(
        **{_MAPKEY: dict(style="open-street-map", center=dict(lat=center[0], lon=center[1]), zoom=zoom)},
        margin=dict(l=0, r=0, t=0, b=0), height=height,
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.8)", font=dict(color="#222")),
    )
    return fig


def calendar_heatmap(daily: pd.Series, label: str) -> go.Figure:
    """GitHub-style calendar: columns = weeks, rows = weekdays."""
    idx = pd.date_range(daily.index.min(), daily.index.max())
    s = daily.reindex(idx, fill_value=0)
    start = idx[0] - pd.Timedelta(days=idx[0].weekday())
    n_weeks = (idx[-1] - start).days // 7 + 1
    z = np.full((7, n_weeks), np.nan)
    text = np.full((7, n_weeks), "", dtype=object)
    for d, v in s.items():
        w, wd = (d - start).days // 7, d.weekday()
        z[wd, w] = v
        text[wd, w] = d.strftime("%a %d %b %Y")
    x = [start + pd.Timedelta(weeks=i) for i in range(n_weeks)]
    fig = go.Figure(go.Heatmap(
        z=z, x=x, y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], customdata=text,
        hovertemplate="%{customdata}<br>" + label + ": %{z:,.0f}<extra></extra>",
        colorscale="YlOrRd", zmin=0, xgap=3, ygap=3, hoverongaps=False, colorbar=dict(title=label, thickness=12),
    ))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(dtick="M1", tickformat="%b %Y", showgrid=False)
    fig.update_layout(height=270, margin=dict(l=10, r=10, t=10, b=10))
    return fig


def tourism_exposure(fires: pd.DataFrame, sites: pd.DataFrame, radius_km: float) -> pd.DataFrame:
    out = sites.copy().reset_index(drop=True)
    if fires.empty:
        out["fires_in_radius"] = 0
        out["modis"] = 0
        out["viirs"] = 0
        out["nearest_km"] = np.nan
        out["max_frp_mw"] = 0.0
    else:
        slat = out["latitude"].to_numpy(dtype=float)
        slon = out["longitude"].to_numpy(dtype=float)
        flat = fires["latitude"].to_numpy(dtype=float)
        flon = fires["longitude"].to_numpy(dtype=float)
        fsensor = fires["sensor"].astype(str).to_numpy()
        ffrp = fires["frp"].to_numpy(dtype=float)
        d = haversine_km(slat[:, None], slon[:, None], flat[None, :], flon[None, :])
        inside = d <= radius_km
        is_modis = (fsensor == "MODIS")[None, :]
        out["fires_in_radius"] = inside.sum(1)
        out["modis"] = (inside & is_modis).sum(1)
        out["viirs"] = (inside & ~is_modis).sum(1)
        out["nearest_km"] = d.min(1).round(1)
        out["max_frp_mw"] = np.where(inside, ffrp[None, :], 0).max(1).round(1)
    out["level"] = pd.cut(out["fires_in_radius"], bins=[-1, 0, 5, 25, np.inf], labels=LEVEL_ORDER).astype(str)
    return out


# ----------------------------------------------------------------------------
# Load + sidebar filters
# ----------------------------------------------------------------------------
fires_all, sites_all, demo_fires, demo_sites = load_data()

st.title("🔥 TourismFireWatch")
st.caption("Global fire activity monitoring & smart tourism awareness · NASA MODIS + VIIRS active-fire detections · NASA Space Apps Challenge 2026")
if demo_fires:
    st.info("Running on **DEMO data** (synthetic fire detections). Put `data/processed_fires.csv` next to `app.py` to switch to real data.", icon="🧪")

sb = st.sidebar
sb.header("Filters")
_dated = fires_all[fires_all["date_known"]]
if _dated.empty:
    st.error("None of the records has a readable `acq_date`, so the dashboard cannot build date filters. Use YYYY-MM-DD dates.")
    st.stop()
dmin, dmax = _dated["acq_date"].min().date(), _dated["acq_date"].max().date()
dr = sb.date_input("Date range", value=(dmin, dmax), min_value=dmin, max_value=dmax)
d0, d1 = (dr[0], dr[1]) if isinstance(dr, (tuple, list)) and len(dr) == 2 else (dmin, dmax)
sensors = sb.multiselect("Sensor", ["MODIS", "VIIRS"], default=["MODIS", "VIIRS"])
region_choice = sb.selectbox("Region", ["Global"] + sorted(fires_all["region"].unique()))
conf = sb.multiselect("Confidence (harmonized)", CONF_ORDER, default=CONF_ORDER)
dn = sb.multiselect("Day / night", ["D", "N"], default=["D", "N"], format_func=lambda x: {"D": "Day", "N": "Night"}[x])
frp_max = float(np.ceil(fires_all["frp"].quantile(0.999)))
min_frp = sb.slider("Minimum FRP (MW)", 0.0, frp_max, 0.0, step=0.5)
collapse = sb.checkbox("Collapse cross-sensor matches", value=False,
                       help="Hide MODIS detections that VIIRS already saw at the same place and day (keeps the finer 375 m record).")
n_unknown = int((~fires_all["date_known"]).sum())
include_unknown = False
if n_unknown:
    include_unknown = sb.checkbox(f"Include {n_unknown:,} records with unknown date", value=True,
                                  help="Their dates were lost in the source file. Shown on the map and in tourism counts only.")
site_types = sorted(sites_all["type"].dropna().unique())
types = sb.multiselect("Tourism site types", site_types, default=site_types)

_in_range = (fires_all["acq_date"] >= pd.Timestamp(d0)) & (fires_all["acq_date"] < pd.Timestamp(d1) + pd.Timedelta(days=1))
_date_ok = _in_range | ((~fires_all["date_known"]) & include_unknown)
mask = (
    _date_ok
    & fires_all["sensor"].isin(sensors) & fires_all["confidence_class"].isin(conf)
    & fires_all["daynight"].isin(dn + ["?"]) & (fires_all["frp"] >= min_frp)
)
if region_choice != "Global":
    mask &= fires_all["region"] == region_choice
if collapse:
    mask &= ~((fires_all["sensor"] == "MODIS") & fires_all["cross_sensor_match"])
f = fires_all[mask]
fd = f[f["date_known"]]  # records with a usable date (calendar / trends)
sites = sites_all[sites_all["type"].isin(types)]

def region_view(df: pd.DataFrame):
    """Auto centre/zoom the map on the filtered detections."""
    lat, lon = df["latitude"], df["longitude"]
    span = max(lat.quantile(0.98) - lat.quantile(0.02), lon.quantile(0.98) - lon.quantile(0.02), 2)
    return (float(lat.median()), float(lon.median())), float(np.clip(np.log2(360 / span) - 0.3, 1.3, 8))


if region_choice != "Global":
    view_center, view_zoom = region_view(f)
else:
    view_center, view_zoom = (20, 10), 1.3

sb.divider()
sb.caption(f"{len(f):,} of {len(fires_all):,} detections match")
sb.caption(("Source: DEMO data" if demo_fires else f"Source: data/{FIRE_FILE.name} ({len(fires_all):,} rows loaded)"))
sb.download_button("⬇️ Download filtered CSV", f.drop(columns=["hour"]).to_csv(index=False).encode(), "tourismfirewatch_filtered.csv", "text/csv")

if f.empty:
    st.warning("No detections match the current filters. Widen the date range or relax a filter.")
    st.stop()

# ----------------------------------------------------------------------------
# KPI row
# ----------------------------------------------------------------------------
k = st.columns(5)
k[0].metric("Detections", f"{len(f):,}")
k[1].metric("MODIS (1 km)", f"{(f['sensor'] == 'MODIS').sum():,}")
k[2].metric("VIIRS (375 m)", f"{(f['sensor'] == 'VIIRS').sum():,}")
k[3].metric("Total FRP", f"{f['frp'].sum():,.0f} MW")
if len(fd):
    daily_all = fd.groupby(fd["acq_date"].dt.normalize()).size()
    busiest = daily_all.idxmax()
    k[4].metric("Busiest day", busiest.strftime("%d %b %Y"), f"{daily_all.max():,} detections", delta_color="off")
else:
    k[4].metric("Busiest day", "-")

tab_map, tab_cal, tab_trend, tab_tour, tab_info = st.tabs(
    ["🗺️ Fire map", "📅 Burning calendar", "📈 Trends & sensors", "🏨 Tourism exposure", "ℹ️ Data & methods"])

# ----------------------------------------------------------------------------
# Tab 1 - Map
# ----------------------------------------------------------------------------
with tab_map:
    c1, c2 = st.columns([1, 1])
    show_sites = c1.toggle("Show tourism sites", value=True)
    max_pts = c2.select_slider("Max points per sensor (speed)", [2000, 5000, 15000, 30000], value=15000)
    show(fire_map(f, sites if show_sites else None, view_center, view_zoom, max_points=max_pts), key="main_map")
    st.caption("Marker size reflects pixel size: MODIS ≈ 1 km (larger), VIIRS ≈ 375 m (smaller). Hover for date, overpass time, FRP and confidence.")

# ----------------------------------------------------------------------------
# Tab 2 - Calendar
# ----------------------------------------------------------------------------
with tab_cal:
    cc = st.columns([1, 1])
    cal_sensor = cc[0].radio("Calendar for", ["Combined", "MODIS", "VIIRS"], horizontal=True)
    cal_metric = cc[1].radio("Metric", ["Detections", "Total FRP (MW)"], horizontal=True)
    cf = fd if cal_sensor == "Combined" else fd[fd["sensor"] == cal_sensor]
    if cf.empty:
        st.warning("No detections for this sensor under the current filters.")
    else:
        grp = cf.groupby(cf["acq_date"].dt.normalize())
        daily = grp.size() if cal_metric == "Detections" else grp["frp"].sum().round(0)
        show(calendar_heatmap(daily, cal_metric), key="calendar")

        st.subheader("Inspect a day")
        best = daily.idxmax().date()
        day = st.date_input("Pick a date (defaults to the busiest day)", value=best,
                            min_value=cf["acq_date"].min().date(), max_value=cf["acq_date"].max().date())
        dd = cf[cf["acq_date"].dt.date == day]
        m = st.columns(4)
        m[0].metric("Detections", f"{len(dd):,}")
        m[1].metric("MODIS", f"{(dd['sensor'] == 'MODIS').sum():,}")
        m[2].metric("VIIRS", f"{(dd['sensor'] == 'VIIRS').sum():,}")
        m[3].metric("Max FRP", f"{dd['frp'].max():,.0f} MW" if len(dd) else "-")
        if dd.empty:
            st.info("No detections on this day.")
        else:
            left, right = st.columns([3, 2])
            with left:
                show(fire_map(dd, sites if show_sites else None, view_center, view_zoom, height=420), key="day_map")
            with right:
                st.dataframe(
                    dd.sort_values("frp", ascending=False).head(15)[["sensor", "region", "frp", "confidence_class", "acq_time", "daynight"]],
                    hide_index=True)

# ----------------------------------------------------------------------------
# Tab 3 - Trends
# ----------------------------------------------------------------------------
with tab_trend:
    if fd.empty:
        st.info("No records with a readable date match the filters, so the date-based charts are hidden.")
    else:
        smooth = st.checkbox("7-day smoothing", value=True)
        full_idx = pd.date_range(fd["acq_date"].min().normalize(), fd["acq_date"].max().normalize())
        daily_s = (fd.groupby([fd["acq_date"].dt.normalize(), "sensor"]).size().unstack(fill_value=0).reindex(full_idx, fill_value=0))
        if smooth:
            daily_s = daily_s.rolling(7, min_periods=1).mean()
        fig = px.line(daily_s, color_discrete_map=SENSOR_COLORS, labels={"index": "Date", "value": "Detections / day", "sensor": "Sensor"})
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=30, b=10), title="Daily detections by sensor")
        show(fig, key="daily")

        a, b = st.columns(2)
        monthly = fd.groupby([fd["acq_date"].dt.to_period("M").dt.to_timestamp(), "sensor"]).size().reset_index(name="detections")
        fig = px.bar(monthly, x="acq_date", y="detections", color="sensor", barmode="group", color_discrete_map=SENSOR_COLORS,
                     labels={"acq_date": "Month"}, title="Monthly detections")
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
        show(fig, key="monthly", container=a)

        reg = f.groupby(["region", "sensor"]).size().reset_index(name="detections")
        fig = px.bar(reg, y="region", x="detections", color="sensor", orientation="h", barmode="stack",
                     color_discrete_map=SENSOR_COLORS, title="Detections by region")
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10), yaxis=dict(categoryorder="total ascending"))
        show(fig, key="region", container=b)

    st.subheader("Sensor comparison (why harmonization matters)")
    c1, c2, c3 = st.columns(3)
    fig = px.histogram(f, x="hour", color="sensor", nbins=24, barmode="group", color_discrete_map=SENSOR_COLORS,
                       labels={"hour": "Hour of day (UTC)"}, title="Overpass times")
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
    show(fig, key="hours", container=c1)

    ct = (pd.crosstab(f["sensor"], f["confidence_class"], normalize="index") * 100).reindex(columns=CONF_ORDER, fill_value=0).reset_index().melt("sensor", var_name="confidence", value_name="share")
    fig = px.bar(ct, x="sensor", y="share", color="confidence", category_orders={"confidence": CONF_ORDER},
                 color_discrete_sequence=["#F2C14E", "#F78154", "#B33F40"], labels={"share": "% of detections"}, title="Confidence mix")
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
    show(fig, key="conf", container=c2)

    fig = px.box(f[f["frp"] > 0], x="sensor", y="frp", color="sensor", log_y=True, color_discrete_map=SENSOR_COLORS,
                 labels={"frp": "FRP (MW, log)"}, title="Fire radiative power")
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
    show(fig, key="frp", container=c3)

    stats = f.groupby("sensor").agg(
        detections=("frp", "size"), mean_frp_mw=("frp", "mean"), median_frp_mw=("frp", "median"),
        high_confidence_pct=("confidence_class", lambda s: (s == "high").mean() * 100),
        cross_sensor_matches=("cross_sensor_match", "sum")).round(1).reset_index()
    stats.insert(1, "pixel_size_m", stats["sensor"].map(SENSOR_RES_M))
    st.dataframe(stats, hide_index=True)

# ----------------------------------------------------------------------------
# Tab 4 - Tourism exposure
# ----------------------------------------------------------------------------
with tab_tour:
    st.markdown("How close are tourist sites to **recent satellite-detected fire activity**? "
                "Counts are within a radius of each site, over a look-back window ending at the end of the selected date range.")
    t1, t2 = st.columns(2)
    radius = t1.slider("Radius (km)", 5, 150, 50, step=5)
    look = t2.slider("Look-back window (days)", 1, 365, 60)
    w_start = pd.Timestamp(d1) - pd.Timedelta(days=look - 1)
    recent = f[(f["acq_date"] >= w_start) | (~f["date_known"])]
    if n_unknown and include_unknown:
        st.caption(f"Counts also include {int((~f['date_known']).sum()):,} records with unknown date (they cannot be placed in the look-back window).")
    exp = tourism_exposure(recent, sites, radius)

    lv = exp["level"].value_counts().reindex(LEVEL_ORDER, fill_value=0)
    cols = st.columns(4)
    for col, name in zip(cols, LEVEL_ORDER):
        col.metric(name, int(lv[name]))

    top = exp.sort_values("fires_in_radius", ascending=False).head(12)
    fig = px.bar(top, y="name", x="fires_in_radius", color="level", orientation="h", color_discrete_map=LEVEL_COLORS,
                 category_orders={"level": LEVEL_ORDER}, labels={"fires_in_radius": f"Detections within {radius} km", "name": ""},
                 title="Sites with the most nearby detections")
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=40, b=10), yaxis=dict(categoryorder="total ascending"))
    show(fig, key="tour_bar")

    st.dataframe(
        exp.sort_values("fires_in_radius", ascending=False)[["name", "type", "country", "level", "fires_in_radius", "modis", "viirs", "nearest_km", "max_frp_mw"]],
        hide_index=True)

    if len(exp):
        st.subheader("Focus on a site")
        pick = st.selectbox("Site", exp.sort_values("fires_in_radius", ascending=False)["name"])
        s = exp[exp["name"] == pick].iloc[0]
        dist = haversine_km(float(s["latitude"]), float(s["longitude"]), recent["latitude"].to_numpy(dtype=float), recent["longitude"].to_numpy(dtype=float)) if len(recent) else np.array([])
        near = recent[dist <= radius] if len(recent) else recent
        zoom = float(np.clip(10 - np.log2(radius / 5), 4, 10))
        st.markdown(f"**{pick}** · {s['type']} · alert level **{s['level']}** · {int(s['fires_in_radius'])} detections within {radius} km "
                    f"(nearest: {s['nearest_km']} km)")
        show(fire_map(near, exp[exp["name"] == pick], (s["latitude"], s["longitude"]), zoom, height=420), key="site_map")
    st.caption("⚠️ This shows satellite detections near a location, not a safety advisory. Always check official local fire and tourism authorities.")

# ----------------------------------------------------------------------------
# Tab 5 - Data & methods
# ----------------------------------------------------------------------------
with tab_info:
    st.subheader("Dataset overview")
    o = st.columns(4)
    o[0].metric("Records loaded", f"{len(fires_all):,}")
    o[1].metric("With readable date", f"{int(fires_all['date_known'].sum()):,}")
    o[2].metric("Date coverage", f"{dmin:%d %b} – {dmax:%d %b %Y}")
    o[3].metric("Tourism sites", f"{len(sites_all):,}")
    oa, ob = st.columns(2)
    oa.markdown("**Records by region and sensor**")
    oa.dataframe(pd.crosstab(fires_all["region"], fires_all["sensor"]).reset_index())
    if "satellite" in fires_all.columns:
        ob.markdown("**Records by satellite**")
        ob.dataframe(fires_all["satellite"].astype(str).value_counts().rename_axis("satellite").reset_index(name="records"), hide_index=True)
    notes = []
    if n_unknown:
        notes.append(f"{n_unknown:,} of {len(fires_all):,} records have no readable acquisition date in the source file. "
                     "They are shown on the map and in the tourism counts, but left out of the calendar and trend charts.")
    if demo_sites:
        notes.append("Tourism sites are a curated sample of well-known destinations; replace them with `data/tourism_locations.csv` for a full dataset.")
    if notes:
        st.markdown("**Data notes**")
        for n_ in notes:
            st.caption("• " + n_)

    st.subheader("Data contract (what the dashboard expects)")
    st.markdown("**`data/processed_fires.csv`** - one row per detection, from the harmonization step.")
    st.dataframe(pd.DataFrame([
        ("latitude, longitude", "float", "yes", "Detection centre"),
        ("acq_date", "YYYY-MM-DD", "yes", "Acquisition date (UTC)"),
        ("acq_time", "int HHMM", "optional", "Acquisition time (UTC)"),
        ("sensor", "MODIS | VIIRS", "yes", "Preserved sensor label"),
        ("frp", "float (MW)", "yes", "Fire radiative power"),
        ("confidence_raw", "str", "optional", "Original value (MODIS 0-100, VIIRS l/n/h)"),
        ("confidence_class", "low | nominal | high", "yes", "Harmonized class (MODIS <30 low, 30-79 nominal, >=80 high; VIIRS l/n/h)"),
        ("daynight", "D | N", "optional", "Day or night overpass"),
        ("resolution_m", "int", "optional", "1000 (MODIS) / 375 (VIIRS)"),
        ("satellite", "str", "optional", "Terra / Aqua / N / N20 / N21 (ignored by the app, kept for reference)"),
        ("region", "str", "optional", "Region label for the filter; computed from lat/lon if missing"),
        ("cross_sensor_match", "bool", "optional", "True if MODIS detection overlaps a VIIRS one (same day, nearby)"),
    ], columns=["column", "type", "required", "notes"]), hide_index=True)
    st.markdown("**`data/tourism_locations.csv`** - columns `name, type, latitude, longitude` (+ optional `country`).")

    st.subheader("MODIS vs VIIRS at a glance")
    st.dataframe(pd.DataFrame([
        ("Pixel size", "≈ 1 km", "≈ 375 m"),
        ("Record starts", "2000", "2012"),
        ("Small-fire detection", "Weaker", "Better"),
        ("Confidence field", "Numeric 0-100", "Categorical l / n / h"),
        ("Typical FRP per detection", "Higher (bigger pixels)", "Lower"),
    ], columns=["", "MODIS", "VIIRS"]), hide_index=True)
    st.caption("Sensor-specific differences are preserved in the data and surfaced in the charts rather than hidden. "
               "Confidence classes are a coarse harmonization; compare raw values before drawing scientific conclusions.")
