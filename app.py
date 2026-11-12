"""
Dashboard ISPU DKI Jakarta — redesigned admin dashboard.
Federasi data:
- PostgreSQL: fakta pengukuran harian (ispu_harian)
- MySQL: master stasiun, kategori ISPU, parameter pencemar
Data digabung di level aplikasi dengan Pandas, lalu divisualisasikan dengan Plotly.

Ikon menggunakan inline SVG bergaya Lucide (open source), tanpa emoji.
Jalankan: streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.db import db_status, load_ispu_postgres, load_master_mysql
from src.pipeline import POLLUTANTS, federate


# ---------------------------------------------------------------------
# Page setup & theme
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="ISPU DKI Jakarta | Air Quality Dashboard",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

PINK = "#E84B91"
PURPLE = "#8056B8"
CYAN = "#42B8D5"
YELLOW = "#F5B52E"
INK = "#20283A"
MUTED = "#8791A3"
BORDER = "#E9EDF3"
BG = "#F5F7FB"

ICON_PATHS = {
    "layout-dashboard": '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "map-pin": '<path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
    "chart-column": '<path d="M3 3v18h18"/><rect x="7" y="12" width="3" height="6" rx="1"/><rect x="13" y="8" width="3" height="10" rx="1"/><rect x="19" y="4" width="2" height="14" rx="1"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5"/><path d="M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>',
    "wind": '<path d="M3 8h12a3 3 0 1 0-3-3"/><path d="M2 12h17a3 3 0 1 1-3 3"/><path d="M4 16h6a3 3 0 1 1-3 3"/>',
    "cloud": '<path d="M20 16.2A4.8 4.8 0 0 0 18 7h-1.2A7 7 0 1 0 4 16.3"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
    "filter": '<path d="M4 7h16M7 12h10m-7 5h4"/><circle cx="8" cy="7" r="1.5"/><circle cx="15" cy="12" r="1.5"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.7a8 8 0 0 1-1.7 1l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.7-1l-1.7.7-1.4-2.4 1.4-1.1a7 7 0 0 1 0-2l-1.4-1.1 1.4-2.4 1.7.7a8 8 0 0 1 1.7-1l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.7 1l1.7-.7 1.4 2.4-1.4 1.1a7 7 0 0 1 0 2Z"/>',
    "arrow-up-right": '<path d="M7 17 17 7M7 7h10v10"/>',
    "check-circle": '<path d="M22 11.1V12a10 10 0 1 1-5.9-9.1"/><path d="m9 11 3 3L22 4"/>',
    "alert-circle": '<circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/>',
    "list": '<path d="M9 6h12M9 12h12M9 18h12"/><path d="M4 6h.01M4 12h.01M4 18h.01"/>',
}


def icon(name, size=18, color="currentColor"):
    path = ICON_PATHS.get(name, ICON_PATHS["activity"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{path}</svg>'
    )


st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
    :root {{ --pink:{PINK}; --purple:{PURPLE}; --cyan:{CYAN}; --yellow:{YELLOW}; }}
    html, body, [class*="css"] {{ font-family:'DM Sans',sans-serif; }}
    .stApp {{ background:{BG}; color:{INK}; }}
    [data-testid="stHeader"] {{ background:transparent; }}
    [data-testid="stToolbar"] {{ right:1rem; }}
    [data-testid="stSidebar"] {{ background:#fff; border-right:1px solid {BORDER}; }}
    [data-testid="stSidebar"] > div:first-child {{ padding-top:1.1rem; }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color:#647084; }}
    .block-container {{ padding:1.35rem 2rem 2.5rem; max-width:1600px; }}
    h1,h2,h3 {{ color:{INK}; letter-spacing:-.035em; }}
    h1 {{ font-size:1.65rem !important; font-weight:800 !important; }}
    h2 {{ font-size:1.1rem !important; font-weight:700 !important; }}
    .brand {{ display:flex; align-items:center; gap:10px; padding:8px 8px 26px; }}
    .brand-mark {{ width:34px;height:34px;border-radius:11px;display:grid;place-items:center;
      background:linear-gradient(135deg,{PINK},{PURPLE});color:#fff;font-size:18px;font-weight:800; }}
    .brand-name {{ font-size:19px;font-weight:800;letter-spacing:-.7px;color:{INK}; }}
    .nav-label {{ font-size:10px;text-transform:uppercase;letter-spacing:1.4px;color:#A0A8B6;
      font-weight:700;margin:18px 10px 8px; }}
    .nav-item {{ display:flex;align-items:center;gap:12px;padding:10px 12px;margin:4px 0;
      border-radius:10px;color:#697487;font-size:13px;font-weight:600; }}
    .nav-item.active {{ background:#FFF0F6;color:{PINK};box-shadow:inset 3px 0 {PINK}; }}
    /* Clickable sidebar navigation buttons styled to match the reference. */
    [data-testid="stSidebar"] [data-testid="stButton"] > button {{
      min-height:54px;width:100%;justify-content:flex-start;text-align:left;
      border:0;border-radius:16px;padding:0 15px;margin:3px 0;
      background:transparent;color:#697487;font-size:14px;font-weight:700;
      box-shadow:none;transition:all .15s ease;
    }}
    [data-testid="stSidebar"] [data-testid="stButton"] > button:hover {{
      background:#F8F8FB;color:{PINK};border:0;
    }}
    [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {{
      background:#FFF0F6;color:{PINK};box-shadow:inset 5px 0 {PINK};
    }}
    [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"]:hover {{
      background:#FCE8F1;color:{PINK};
    }}
    [data-testid="stSidebar"] [data-testid="stButton"] > button p {{
      font-size:14px;font-weight:700;margin:0;
    }}
    [data-testid="stSidebar"] [data-testid="stButton"] button div[data-testid="stMarkdownContainer"] {{
      display:flex;align-items:center;
    }}
    .side-note {{ margin:25px 4px 0;padding:14px;border-radius:12px;background:#F7F8FC;
      color:#7D8798;font-size:11px;line-height:1.6; }}
    .topbar {{ display:flex;justify-content:space-between;align-items:center;margin:0 0 18px; }}
    .eyebrow {{ color:#929BAD;font-size:11px;font-weight:600;letter-spacing:.4px; }}
    .top-actions {{ display:flex;align-items:center;gap:17px;color:#7D8798; }}
    .avatar {{ width:34px;height:34px;border-radius:50%;background:#252D3D;color:white;
      display:grid;place-items:center;font-size:11px;font-weight:700; }}
    .panel {{ background:#fff;border:1px solid #EDF0F5;border-radius:15px;padding:19px 20px;
      box-shadow:0 5px 20px rgba(29,43,71,.035); }}
    .panel-head {{ display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px; }}
    .panel-title {{ font-size:14px;font-weight:700;color:{INK}; }}
    .panel-sub {{ color:#9AA3B1;font-size:11px;margin-top:3px; }}
    .kpi-label {{ color:#9099A9;font-size:11px;font-weight:600;margin-bottom:7px; }}
    .kpi-value {{ font-size:25px;line-height:1.1;font-weight:800;color:{INK};letter-spacing:-1px; }}
    .kpi-foot {{ color:#9AA3B1;font-size:10px;margin-top:6px; }}
    .kpi-icon {{ width:37px;height:37px;border-radius:12px;display:grid;place-items:center;color:white; }}
    .gradient-card {{ color:white;border-radius:14px;padding:17px 18px;min-height:116px;
      position:relative;overflow:hidden; }}
    .gradient-card:after {{ content:'';position:absolute;width:130px;height:130px;border-radius:50%;
      right:-32px;bottom:-82px;background:rgba(255,255,255,.15); }}
    .gradient-label {{ font-size:11px;font-weight:600;opacity:.88; }}
    .gradient-value {{ font-size:24px;font-weight:800;margin-top:9px;letter-spacing:-.6px; }}
    .gradient-foot {{ font-size:10px;opacity:.8;margin-top:2px; }}
    .status-pill {{ display:inline-block;padding:5px 9px;border-radius:7px;font-size:10px;font-weight:700; }}
    .section-gap {{ height:12px; }}
    div[data-testid="stMetric"] {{ background:#fff;border:1px solid #EDF0F5;padding:15px 17px;
      border-radius:14px;box-shadow:0 5px 20px rgba(29,43,71,.025); }}
    div[data-testid="stMetricLabel"] {{ color:#929BAD;font-size:11px;font-weight:600; }}
    div[data-testid="stMetricValue"] {{ color:{INK};font-size:25px;font-weight:800; }}
    div[data-testid="stMetricDelta"] {{ font-size:10px; }}
    .stTabs [data-baseweb="tab-list"] {{ gap:8px;border-bottom:1px solid {BORDER}; }}
    .stTabs [data-baseweb="tab"] {{ border-radius:8px 8px 0 0;padding:10px 14px;color:#758094;font-size:12px; }}
    .stTabs [aria-selected="true"] {{ color:{PINK} !important;border-bottom-color:{PINK} !important; }}
    .stButton>button {{ border-radius:9px;border:1px solid {BORDER};font-weight:600;font-size:12px; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{ background:#fff;border:1px solid #EDF0F5;border-radius:15px;box-shadow:0 5px 20px rgba(29,43,71,.035); }}
    [data-testid="stVerticalBlockBorderWrapper"] > div {{ border:0 !important; }}
    [data-testid="stDataFrame"] {{ border:1px solid {BORDER};border-radius:10px;overflow:hidden; }}
    hr {{ border-color:{BORDER}; }}
    @media(max-width:900px) {{ .block-container{{padding:1rem;}} }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------
API_SOURCE = (
    "https://ws.jakarta.go.id/gateway/DataPortalSatuDataJakarta/1.0/satudata"
    "?kategori=dataset&tipe=detail&url=data-indeks-standar-pencemar-udara-ispu-di-provinsi-dki-jakarta"
)


@st.cache_data(ttl=600, show_spinner="Mengambil data dari PostgreSQL dan MySQL…")
def load_all():
    ispu = load_ispu_postgres()
    stasiun, kategori, parameter = load_master_mysql()
    return ispu, stasiun, kategori, parameter, federate(ispu, stasiun, kategori, parameter)


@st.cache_data(ttl=60)
def load_status():
    return db_status()


try:
    ispu, stasiun, kategori, parameter, df = load_all()
except Exception as exc:
    st.error(
        "Koneksi database gagal. Pastikan PostgreSQL dan MySQL aktif, file .env benar, "
        "serta db/seed_data.py sudah dijalankan."
    )
    with st.expander("Detail error"):
        st.exception(exc)
    st.stop()

if df.empty:
    st.warning("Belum ada data. Jalankan python db/seed_data.py terlebih dahulu.")
    st.stop()

df = df.copy()
df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")
df = df.dropna(subset=["tanggal"])
color_map = dict(zip(kategori["kategori"], kategori["warna_hex"]))
cat_order = kategori.sort_values("urutan")["kategori"].tolist()
param_names = dict(zip(parameter["kolom_data"], parameter["nama_parameter"]))
metric_labels = {
    "ispu_max": "ISPU maksimum",
    **{k: v for k, v in param_names.items() if k in POLLUTANTS},
}
if not metric_labels:
    metric_labels = {"ispu_max": "ISPU maksimum"}


# ---------------------------------------------------------------------
# Sidebar — filters and navigation
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f'<div class="brand"><div class="brand-mark">L</div><div class="brand-name">Air<span style="color:{PINK}">lytics.</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
    page_options = [
        ("Dashboard", ":material/dashboard:"),
        ("Peta Stasiun", ":material/location_on:"),
        ("Tren Kualitas Udara", ":material/show_chart:"),
        ("Kategori ISPU", ":material/bar_chart:"),
        ("Data & Arsitektur", ":material/database:"),
    ]
    if "main_navigation" not in st.session_state:
        st.session_state["main_navigation"] = "Dashboard"

    # Tombol sungguhan: klik akan mengubah halaman aktif lalu Streamlit rerun.
    for page_name, page_icon in page_options:
        is_active = st.session_state["main_navigation"] == page_name
        if st.button(
            page_name,
            key=f"nav_{page_name}",
            icon=page_icon,
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state["main_navigation"] = page_name
            st.rerun()

    selected_page = st.session_state["main_navigation"]

    st.markdown('<div class="nav-label">Filter data</div>', unsafe_allow_html=True)
    min_d, max_d = df["tanggal"].min().date(), df["tanggal"].max().date()
    picked = st.date_input(
        "Rentang tanggal",
        (min_d, max_d),
        min_value=min_d,
        max_value=max_d,
    )
    if isinstance(picked, (tuple, list)) and len(picked) == 2:
        start, end = picked
    elif isinstance(picked, (tuple, list)) and len(picked) == 1:
        start = end = picked[0]
    else:
        start, end = min_d, max_d

    station_options = stasiun.sort_values("kode_stasiun")["nama_stasiun"].tolist()
    chosen_stations = st.multiselect(
        "Stasiun pemantauan", station_options, default=station_options
    )
    cat_options = [c for c in cat_order if c in set(df["kategori"].dropna())]
    chosen_cats = st.multiselect("Kategori ISPU", cat_options, default=cat_options)
    metric = st.selectbox(
        "Metrik tren",
        list(metric_labels),
        format_func=metric_labels.get,
    )
    smooth = st.toggle("Rata-rata bergerak 7 hari", value=False)

    st.markdown('<div class="nav-label">System</div>', unsafe_allow_html=True)
    with st.expander("Status koneksi database"):
        try:
            status = load_status()
            st.caption("PostgreSQL · data pengukuran")
            st.code(status["pg_version"].split(",")[0])
            st.write(f"ispu_harian: {status['pg_rows']:,} baris")
            st.caption("MySQL · data master")
            st.code(status["mysql_version"])
            for table, count in status["mysql_rows"].items():
                st.write(f"{table}: {count:,} baris")
        except Exception as exc:
            st.warning(f"Status database tidak tersedia: {exc}")

    st.markdown(
        '<div class="side-note">Air quality monitoring dashboard<br/>Data source: Satu Data Jakarta<br/>Refresh data: setiap 10 menit</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------
f = df[
    (df["tanggal"].dt.date >= start)
    & (df["tanggal"].dt.date <= end)
    & (df["nama_stasiun"].isin(chosen_stations))
    & (df["kategori"].isin(chosen_cats))
].copy()

if f.empty:
    st.warning("Tidak ada data untuk kombinasi filter yang dipilih.")
    st.stop()

valid = f.dropna(subset=["ispu_max"])
mean_by_station = valid.groupby("nama_stasiun")["ispu_max"].mean()
n_bad = int(f["tidak_sehat"].fillna(0).sum())
avg_ispu = valid["ispu_max"].mean() if len(valid) else 0
worst_station = mean_by_station.idxmax() if len(mean_by_station) else "—"
worst_value = mean_by_station.max() if len(mean_by_station) else 0
obs_count = len(f)


if selected_page == "Dashboard":
    # ---------------------------------------------------------------------
    # Header
    # ---------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="topbar">
          <div>
            <div class="eyebrow">OVERVIEW / AIR QUALITY</div>
            <h1 style="margin:5px 0 0">Dashboard Kualitas Udara</h1>
            <div class="panel-sub">Indeks Standar Pencemar Udara · Provinsi DKI Jakarta</div>
          </div>
          <div class="top-actions">
            <span title="Notifikasi">{icon("bell",19)}</span>
            <span title="Pengaturan">{icon("settings",19)}</span>
            <div class="avatar">AQ</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    # ---------------------------------------------------------------------
    # KPI cards
    # ---------------------------------------------------------------------
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Jumlah observasi", f"{obs_count:,}", help="Jumlah baris pengukuran sesuai filter.")
    k2.metric("Rata-rata ISPU maksimum", f"{avg_ispu:.1f}", help="Rata-rata nilai ISPU maksimum.")
    k3.metric("Hari tidak sehat", f"{n_bad:,}", f"{n_bad / obs_count:.1%} dari observasi" if obs_count else "—", delta_color="off")
    k4.metric("Stasiun dengan rata-rata tertinggi", worst_station, f"Rata-rata {worst_value:.1f}")


    # ---------------------------------------------------------------------
    # Main visual row — trend + category donut
    # ---------------------------------------------------------------------
    left, right = st.columns([2.15, 1], gap="medium")
    with left:
        with st.container(border=True):
            st.markdown(
                '<div class="panel-head"><div><div class="panel-title">Tren kualitas udara</div>'
                '<div class="panel-sub">Pergerakan indeks berdasarkan tanggal dan stasiun</div></div>'
                '<div class="eyebrow">FILTERED PERIOD</div></div>',
                unsafe_allow_html=True,
            )
            t = f.sort_values(["nama_stasiun", "tanggal"]).copy()
            if smooth:
                t[metric] = t.groupby("nama_stasiun")[metric].transform(
                    lambda s: s.rolling(7, min_periods=1).mean()
                )
            trend = px.line(
                t,
                x="tanggal",
                y=metric,
                color="nama_stasiun",
                markers=not smooth,
                labels={
                    "tanggal": "Tanggal",
                    metric: metric_labels[metric],
                    "nama_stasiun": "Stasiun",
                },
                color_discrete_sequence=[PINK, PURPLE, CYAN, YELLOW, "#56B98A", "#E87952"],
            )
            trend.update_layout(
                height=300,
                margin=dict(l=5, r=5, t=10, b=5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Sans", color="#7E899B", size=10),
                legend=dict(orientation="h", y=1.12, x=0, title=""),
                hovermode="x unified",
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=True, gridcolor="#EEF1F5", zeroline=False),
            )
            if metric == "ispu_max":
                for _, r in kategori[kategori["urutan"].between(1, 4)].iterrows():
                    trend.add_hrect(
                        y0=r["rentang_min"],
                        y1=r["rentang_max"],
                        fillcolor=r["warna_hex"],
                        opacity=0.08,
                        line_width=0,
                        layer="below",
                    )
            st.plotly_chart(trend, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                '<div class="panel-sub">Pita warna menunjukkan rentang kategori ISPU dari data master MySQL.</div>',
                unsafe_allow_html=True,
            )

    with right:
        with st.container(border=True):
            st.markdown(
                '<div class="panel-head"><div><div class="panel-title">Komposisi kategori</div>'
                '<div class="panel-sub">Proporsi kategori pada data terpilih</div></div></div>',
                unsafe_allow_html=True,
            )
            share = f["kategori"].value_counts().reindex(cat_order).dropna().reset_index()
            share.columns = ["kategori", "jumlah"]
            donut = px.pie(
                share,
                names="kategori",
                values="jumlah",
                hole=0.70,
                color="kategori",
                color_discrete_map=color_map,
            )
            donut.update_traces(
                textinfo="none",
                hovertemplate="%{label}<br>%{value:,} observasi (%{percent})<extra></extra>",
                marker=dict(line=dict(color="white", width=3)),
            )
            donut.update_layout(
                height=235,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                annotations=[
                    dict(
                        text=f"<b>{len(f):,}</b><br><span style='font-size:10px;color:#9AA3B1'>OBSERVASI</span>",
                        x=0.5,
                        y=0.5,
                        showarrow=False,
                        font=dict(size=21, color=INK),
                    )
                ],
            )
            st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False})
            for _, row in share.iterrows():
                color = color_map.get(row["kategori"], MUTED)
                pct = row["jumlah"] / max(len(f), 1) * 100
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin:7px 2px;font-size:11px">'
                    f'<span style="color:#778296"><span style="color:{color};font-size:15px">●</span> &nbsp;{row["kategori"]}</span>'
                    f'<b style="color:{INK}">{pct:.1f}%</b></div>',
                    unsafe_allow_html=True,
                )


    # ---------------------------------------------------------------------
    # Color summary cards, replacing template's sales cards with ISPU insights
    # ---------------------------------------------------------------------
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    cards = [
        (c1, "Rata-rata ISPU", f"{avg_ispu:.1f}", "Nilai rata-rata periode terpilih", f"linear-gradient(120deg,{PINK},{PURPLE})"),
        (c2, "Stasiun terpantau", f"{f['nama_stasiun'].nunique():,}", "Jumlah stasiun dalam filter", f"linear-gradient(120deg,{PURPLE},#6850B8)"),
        (c3, "Hari tidak sehat", f"{n_bad:,}", "Observasi dengan status tidak sehat", f"linear-gradient(120deg,{CYAN},#5796D7)"),
        (c4, "Nilai ISPU tertinggi", f"{valid['ispu_max'].max():.0f}" if len(valid) else "—", "Puncak ISPU pada periode ini", f"linear-gradient(120deg,{YELLOW},#F07B52)"),
    ]
    for col, label, value, foot, bg in cards:
        with col:
            st.markdown(
                f'<div class="gradient-card" style="background:{bg}">'
                f'<div class="gradient-label">{label}</div>'
                f'<div class="gradient-value">{value}</div>'
                f'<div class="gradient-foot">{foot}</div></div>',
                unsafe_allow_html=True,
            )


    # ---------------------------------------------------------------------
    # Lower row — latest readings and quick insights
    # ---------------------------------------------------------------------
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    lower_left, lower_right = st.columns([0.95, 2.05], gap="medium")

    with lower_left:
        with st.container(border=True):
            st.markdown(
                '<div class="panel-title">Ringkasan kondisi</div>'
                '<div class="panel-sub">Insight otomatis dari data terfilter</div>',
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            if len(valid):
                latest = f.sort_values("tanggal").iloc[-1]
                latest_cat = latest.get("kategori", "—")
                st.markdown(
                    f'<div style="display:flex;gap:10px;align-items:center;margin-bottom:17px">'
                    f'<div class="kpi-icon" style="background:#EAF8F1;color:#3CA879">{icon("check-circle",18,"#3CA879")}</div>'
                    f'<div><div style="font-size:11px;color:#929BAD">Kategori terbaru</div>'
                    f'<div style="font-size:14px;font-weight:700;color:{INK}">{latest_cat}</div></div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="display:flex;gap:10px;align-items:center;margin-bottom:17px">'
                    f'<div class="kpi-icon" style="background:#FFF1F6;color:{PINK}">{icon("map-pin",18,PINK)}</div>'
                    f'<div><div style="font-size:11px;color:#929BAD">Stasiun dengan rerata tertinggi</div>'
                    f'<div style="font-size:14px;font-weight:700;color:{INK}">{worst_station}</div></div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="display:flex;gap:10px;align-items:center">'
                    f'<div class="kpi-icon" style="background:#FFF7E7;color:#D89A18">{icon("calendar",18,"#D89A18")}</div>'
                    f'<div><div style="font-size:11px;color:#929BAD">Periode data</div>'
                    f'<div style="font-size:13px;font-weight:700;color:{INK}">{start:%d %b %Y} – {end:%d %b %Y}</div></div></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("Belum ada nilai ISPU valid pada filter ini.")
            st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
            st.markdown(
                '<div style="background:#F7F8FC;border-radius:10px;padding:12px;color:#8A94A5;font-size:10px;line-height:1.6">'
                'Catatan: ringkasan mengikuti rentang tanggal, stasiun, dan kategori yang dipilih pada panel filter.</div>',
                unsafe_allow_html=True,
            )

    with lower_right:
        with st.container(border=True):
            st.markdown(
                '<div class="panel-head"><div><div class="panel-title">Pengukuran terbaru</div>'
                '<div class="panel-sub">Daftar observasi terakhir berdasarkan filter</div></div></div>',
                unsafe_allow_html=True,
            )
            columns_to_show = [
                c for c in [
                    "tanggal", "nama_stasiun", "wilayah", "ispu_max",
                    "parameter_kritis", "kategori"
                ] if c in f.columns
            ]
            latest_rows = f.sort_values("tanggal", ascending=False)[columns_to_show].head(8).copy()
            if "tanggal" in latest_rows:
                latest_rows["tanggal"] = latest_rows["tanggal"].dt.strftime("%d %b %Y")
            st.dataframe(
                latest_rows,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "tanggal": st.column_config.TextColumn("Tanggal"),
                    "nama_stasiun": st.column_config.TextColumn("Stasiun"),
                    "wilayah": st.column_config.TextColumn("Wilayah"),
                    "ispu_max": st.column_config.NumberColumn("ISPU", format="%.0f"),
                    "parameter_kritis": st.column_config.TextColumn("Parameter kritis"),
                    "kategori": st.column_config.TextColumn("Kategori"),
                },
            )


# ---------------------------------------------------------------------
# Clickable page navigation
# ---------------------------------------------------------------------
if selected_page != "Dashboard":
    page_titles = {
        "Peta Stasiun": "Peta persebaran stasiun pemantauan",
        "Tren Kualitas Udara": "Tren kualitas udara",
        "Kategori ISPU": "Analisis kategori ISPU",
        "Data & Arsitektur": "Data dan arsitektur sistem",
    }
    st.markdown(f'<div class="eyebrow">WORKSPACE / {selected_page.upper()}</div>', unsafe_allow_html=True)
    st.title(page_titles[selected_page])
    st.caption(f"Data ditampilkan berdasarkan filter yang dipilih · {start:%d %b %Y} – {end:%d %b %Y}")

if selected_page == "Peta Stasiun":
        agg = (
            f.groupby(
                ["kode_stasiun", "nama_stasiun", "wilayah", "latitude", "longitude"],
                as_index=False,
            )
            .agg(
                rata_ispu=("ispu_max", "mean"),
                ispu_tertinggi=("ispu_max", "max"),
                hari_tidak_sehat=("tidak_sehat", "sum"),
                observasi=("tanggal", "count"),
            )
        )
        agg["ukuran"] = agg["rata_ispu"].fillna(0) + 10
        map_common = dict(
            lat="latitude",
            lon="longitude",
            size="ukuran",
            color="rata_ispu",
            hover_name="nama_stasiun",
            size_max=38,
            zoom=9.6,
            height=520,
            center=dict(lat=-6.23, lon=106.84),
            color_continuous_scale="YlOrRd",
            hover_data={
                "wilayah": True,
                "rata_ispu": ":.1f",
                "ispu_tertinggi": True,
                "hari_tidak_sehat": True,
                "latitude": False,
                "longitude": False,
                "ukuran": False,
            },
        )
        if hasattr(px, "scatter_map"):
            map_fig = px.scatter_map(agg, **map_common)
            map_fig.update_layout(map_style="open-street-map")
        else:
            map_fig = px.scatter_mapbox(agg, **map_common)
            map_fig.update_layout(mapbox_style="open-street-map")
        map_fig.update_layout(margin=dict(l=0, r=0, t=5, b=0), coloraxis_colorbar_title="Rata-rata ISPU")
        st.plotly_chart(map_fig, use_container_width=True)
        st.caption("Koordinat stasiun berasal dari tabel stasiun di MySQL (perkiraan).")


if selected_page == "Tren Kualitas Udara":
        detailed = f.sort_values(["nama_stasiun", "tanggal"]).copy()
        if smooth:
            detailed[metric] = detailed.groupby("nama_stasiun")[metric].transform(
                lambda s: s.rolling(7, min_periods=1).mean()
            )
        fig = px.line(
            detailed,
            x="tanggal",
            y=metric,
            color="nama_stasiun",
            markers=not smooth,
            labels={"tanggal": "Tanggal", metric: metric_labels[metric], "nama_stasiun": "Stasiun"},
        )
        fig.update_layout(height=460, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)


if selected_page == "Kategori ISPU":
        left, right = st.columns(2)
        by_station = f.groupby(["nama_stasiun", "kategori"]).size().reset_index(name="jumlah_hari")
        fig = px.bar(
            by_station,
            x="nama_stasiun",
            y="jumlah_hari",
            color="kategori",
            color_discrete_map=color_map,
            category_orders={"kategori": cat_order},
            labels={"nama_stasiun": "Stasiun", "jumlah_hari": "Jumlah hari", "kategori": "Kategori"},
            title="Distribusi kategori per stasiun",
        )
        left.plotly_chart(fig, use_container_width=True)
        by_month = f.groupby(["tahun_bulan", "kategori"]).size().reset_index(name="jumlah_hari")
        fig = px.bar(
            by_month,
            x="tahun_bulan",
            y="jumlah_hari",
            color="kategori",
            color_discrete_map=color_map,
            category_orders={"kategori": cat_order},
            labels={"tahun_bulan": "Bulan", "jumlah_hari": "Jumlah hari", "kategori": "Kategori"},
            title="Distribusi kategori per bulan",
        )
        fig.update_xaxes(type="category")
        right.plotly_chart(fig, use_container_width=True)

        st.markdown("### Analisis polutan")
        left, right = st.columns(2)
        heat = f.groupby("nama_stasiun")[POLLUTANTS].mean().rename(columns=param_names)
        fig = px.imshow(
            heat.round(1),
            text_auto=".0f",
            aspect="auto",
            color_continuous_scale="YlOrRd",
            labels=dict(x="Polutan", y="Stasiun", color="Rata-rata"),
            title="Rata-rata sub-indeks polutan per stasiun",
        )
        left.plotly_chart(fig, use_container_width=True)
        fig = px.box(
            f,
            x="nama_stasiun",
            y=metric,
            color="nama_stasiun",
            points="outliers",
            labels={"nama_stasiun": "Stasiun", metric: metric_labels[metric]},
            title=f"Sebaran {metric_labels[metric]}",
        )
        fig.update_layout(showlegend=False)
        right.plotly_chart(fig, use_container_width=True)

        crit = (
            f.dropna(subset=["parameter_kritis"])
            .assign(nama=lambda d: d["nama_parameter_kritis"].fillna(d["parameter_kritis"]))
            .groupby("nama")
            .size()
            .sort_values()
            .reset_index(name="jumlah_hari")
        )
        if len(crit):
            fig = px.bar(
                crit,
                x="jumlah_hari",
                y="nama",
                orientation="h",
                labels={"jumlah_hari": "Jumlah hari", "nama": "Parameter kritis"},
                title="Polutan yang paling sering menjadi parameter kritis",
            )
            st.plotly_chart(fig, use_container_width=True)
        with st.expander("Dampak kesehatan tiap polutan"):
            st.dataframe(
                parameter[["nama_parameter", "satuan", "dampak_kesehatan"]],
                hide_index=True,
                use_container_width=True,
            )


    # Analisis polutan menjadi bagian lanjutan halaman kategori.
if selected_page == "Data & Arsitektur":
        st.markdown("### Alur data")
        st.markdown(
            """
            1. **Extract** — `db/seed_data.py` mengambil JSON dari API Satu Data Jakarta.
            2. **Clean** — `src/pipeline.py::clean_api_records` menormalisasi nama stasiun,
               menangani nilai kosong, menggabungkan tanggal, dan membuang duplikat.
            3. **Load** — data fakta masuk ke **PostgreSQL** (`ispu_harian`), sedangkan data
               master masuk ke **MySQL** (`stasiun`, `kategori_ispu`, `parameter_pencemar`).
            4. **Federate** — aplikasi membaca kedua DBMS dan menggabungkan data dengan
               `DataFrame.merge()` di Pandas.
            5. **Visualize** — hasilnya ditampilkan melalui Streamlit dan Plotly.
            """
        )
        shown_cols = [
            "tanggal", "kode_stasiun", "nama_stasiun", "wilayah",
            *[p for p in POLLUTANTS if p in f.columns],
            "ispu_max", "parameter_kritis", "kategori",
        ]
        shown = f[[c for c in shown_cols if c in f.columns]].copy()
        st.dataframe(shown, use_container_width=True, hide_index=True)
        st.download_button(
            "Unduh CSV sesuai filter",
            shown.to_csv(index=False).encode("utf-8"),
            file_name="ispu_jakarta_filtered.csv",
            mime="text/csv",
        )


st.divider()
st.caption(
    f"Sumber data: [API Satu Data Jakarta – ISPU DKI Jakarta]({API_SOURCE}). "
    "Dataset dikelola Pemerintah Provinsi DKI Jakarta."
)
