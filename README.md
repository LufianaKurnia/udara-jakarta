# 🌫️ Dashboard ISPU DKI Jakarta — Federasi PostgreSQL + MySQL

Dashboard web interaktif (Python + Streamlit + Plotly) yang menggabungkan data dari dua database berbeda (MYSQL dan Postgresql)

NAMA: Lufiana Kurnia
KELAS: IF-7B
NIM: 230660121149

## 1. DATA SUMBER

Satu Data DKI Jakarta
https://satudata.jakarta.go.id/open-data/detail?kategori=dataset&page_url=data-indeks-standar-pencemar-udara-ispu-di-provinsi-dki-jakarta&data_no=1

via API endpoint
https://ws.jakarta.go.id/gateway/DataPortalSatuDataJakarta/1.0/satudata?kategori=dataset&tipe=detail&url=data-indeks-standar-pencemar-udara-ispu-di-provinsi-dki-jakarta

## 2. Arsitektur

DBMS 1 – Fakta | PostgreSQL (Postgres.app) | `ispu_harian` | Volume data tumbuh, query analitik, `UPSERT` (`ON CONFLICT`) |

DBMS 2 – Master | MySQL/MariaDB (XAMPP) | `stasiun`, `kategori_ispu`, `parameter_pencemar` | Data referensi kecil & stabil |

flowchart LR

- API[API Satu Data Jakarta] -->|requests| ETL[db/seed_data.py lean_api_records]
- ETL -->|fakta| PG[(PostgreSQL ispu_harian)]
- ETL -->|seed master| MY[(MySQL stasiun, kategori_ispu, parameter_pencemar)]
- PG -->|SQLAlchemy + psycopg2| APP[app.py - Pandas merge]
- MY -->|SQLAlchemy + mysql-connector| APP
- APP --> UI[Streamlit + Plotly]

- PostgreSQL.ispu_harian.kode_stasiun -> MySQL.stasiun.kode_stasiun
- PostgreSQL.ispu_harian.kategori -> MySQL.kategori_ispu.kategori
- PostgreSQL.ispu_harian.parameter_kritis -> MySQL.parameter_pencemar.kode_parameter

## 3. Fitur interaktif

- Filter rentang tanggal, stasiun, kategori ISPU
- Pilih metrik tren (ISPU maks / PM10 / PM2.5 / SO₂ / CO / O₃ / NO₂) + rata-rata bergerak 7 hari
- Peta stasiun (ukuran & warna = rata-rata ISPU, hover detail)
- Tren harian dengan pita kategori, bar/pie distribusi kategori, heatmap & boxplot polutan
- Unduh CSV hasil filter, panel status koneksi kedua database

## 5. Referensi

Referensi kode

- Streamlit – koneksi database: https://docs.streamlit.io/develop/tutorials/databases
- Plotly Express (peta, heatmap, bar): https://plotly.com/python/
- SQLAlchemy 2.0 – engine & `URL.create`: https://docs.sqlalchemy.org/en/20/core/engines.html
- Pandas `merge`: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html
