#!/usr/bin/env python3
"""Inisialisasi kedua database lalu isi datanya.

Langkah:
  1. Buat database (jika belum ada) di PostgreSQL & MySQL
  2. Jalankan DDL (postgres_schema.sql, mysql_schema.sql)
  3. Isi data master ke MySQL (mysql_seed.sql)
  4. Ambil data ISPU dari API Satu Data Jakarta -> bersihkan -> upsert ke PostgreSQL
  5. Cek integritas lintas-DBMS (kode stasiun di PostgreSQL harus ada di MySQL)

Pemakaian:
  python db/seed_data.py                      # ambil dari API (snapshot disimpan ke data/raw/)
  python db/seed_data.py --source file        # pakai snapshot lokal data/raw/ispu_raw.json
"""
import argparse
import json
import sys
from pathlib import Path

import requests
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import mysql_connect_args, mysql_url, postgres_url  # noqa: E402
from src.pipeline import clean_api_records  # noqa: E402

API_URL = (
    "https://ws.jakarta.go.id/gateway/DataPortalSatuDataJakarta/1.0/satudata"
    "?kategori=dataset&tipe=detail&url=data-indeks-standar-pencemar-udara-ispu-di-provinsi-dki-jakarta"
)
RAW_FILE = ROOT / "data" / "raw" / "ispu_raw.json"
DB_DIR = ROOT / "db"


# ----------------------------------------------------------------- extract
def fetch_from_api():
    print(f"[extract] GET {API_URL}")
    resp = requests.get(API_URL, timeout=90, headers={"User-Agent": "Mozilla/5.0 (tugas-kuliah)"})
    resp.raise_for_status()
    # API mengirim BOM di awal -> pakai utf-8-sig
    payload = json.loads(resp.content.decode("utf-8-sig"))
    records = payload["data"]
    RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
    RAW_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"[extract] {len(records)} baris, snapshot disimpan di {RAW_FILE.relative_to(ROOT)}")
    return records


def load_from_file():
    payload = json.loads(RAW_FILE.read_text(encoding="utf-8-sig"))
    records = payload["data"]
    print(f"[extract] {len(records)} baris dibaca dari {RAW_FILE.relative_to(ROOT)}")
    return records


# --------------------------------------------------------------- DB helpers
def split_sql(sql):
    lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def run_sql_file(engine, path):
    with engine.begin() as conn:
        for stmt in split_sql(path.read_text(encoding="utf-8")):
            conn.exec_driver_sql(stmt)
    print(f"[ddl] {path.name} OK")


def ensure_postgres_db():
    url = postgres_url()
    name = url.database
    try:
        admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        with admin.connect() as conn:
            exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": name}).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{name}"'))
                print(f"[db] PostgreSQL database '{name}' dibuat")
    except Exception as exc:  # database cloud biasanya sudah ada & user tidak boleh CREATE DATABASE
        print(f"[db] lewati pembuatan database PostgreSQL ({exc.__class__.__name__}); diasumsikan sudah ada")


def ensure_mysql_db():
    url = mysql_url()
    name = url.database
    try:
        # sambung ke database sistem "mysql" (selalu ada), bukan database=None
        admin = create_engine(url.set(database="mysql"), connect_args=mysql_connect_args())
        with admin.connect() as conn:
            conn.exec_driver_sql(f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4")
            conn.commit()
        print(f"[db] MySQL database '{name}' siap")
    except Exception as exc:
        print(f"[db] GAGAL membuat database MySQL: {exc}")
        raise

# --------------------------------------------------------------------- load
UPSERT_PG = text(
    """
    INSERT INTO ispu_harian
        (kode_stasiun, tanggal, pm10, pm25, so2, co, o3, no2, ispu_max, parameter_kritis, kategori)
    VALUES
        (:kode_stasiun, :tanggal, :pm10, :pm25, :so2, :co, :o3, :no2, :ispu_max, :parameter_kritis, :kategori)
    ON CONFLICT (kode_stasiun, tanggal) DO UPDATE SET
        pm10 = EXCLUDED.pm10, pm25 = EXCLUDED.pm25, so2 = EXCLUDED.so2, co = EXCLUDED.co,
        o3 = EXCLUDED.o3, no2 = EXCLUDED.no2, ispu_max = EXCLUDED.ispu_max,
        parameter_kritis = EXCLUDED.parameter_kritis, kategori = EXCLUDED.kategori
    """
)


def to_records(df):
    """DataFrame -> list dict berisi tipe Python murni (NA -> None)."""
    records = []
    for row in df.to_dict("records"):
        records.append(
            {k: (None if v is None or str(v) in ("<NA>", "nan", "NaT") else (v.item() if hasattr(v, "item") else v))
             for k, v in row.items()}
        )
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", choices=["api", "file"], default="api")
    args = parser.parse_args()

    print("== 1. Siapkan database ==")
    ensure_postgres_db()
    ensure_mysql_db()
    pg = create_engine(postgres_url())
    my = create_engine(mysql_url(), connect_args=mysql_connect_args())

    print("== 2. DDL ==")
    run_sql_file(pg, DB_DIR / "postgres_schema.sql")
    run_sql_file(my, DB_DIR / "mysql_schema.sql")

    print("== 3. Seed data master -> MySQL ==")
    run_sql_file(my, DB_DIR / "mysql_seed.sql")

    print("== 4. Extract -> Clean -> Load PostgreSQL ==")
    if args.source == "api":
        try:
            records = fetch_from_api()
        except Exception as exc:
            if RAW_FILE.exists():
                print(f"[extract] API gagal ({exc}); memakai snapshot lokal")
                records = load_from_file()
            else:
                raise
    else:
        records = load_from_file()

    df = clean_api_records(records)
    print(f"[clean] {len(records)} baris mentah -> {len(df)} baris bersih")
    print(df["kode_stasiun"].value_counts().sort_index().to_string())
    with pg.begin() as conn:
        conn.execute(UPSERT_PG, to_records(df))
    print(f"[load] {len(df)} baris di-upsert ke PostgreSQL.ispu_harian")

    print("== 5. Cek integritas lintas DBMS ==")
    with my.connect() as conn:
        master_codes = {r[0] for r in conn.execute(text("SELECT kode_stasiun FROM stasiun"))}
    with pg.connect() as conn:
        fact_codes = {r[0] for r in conn.execute(text("SELECT DISTINCT kode_stasiun FROM ispu_harian"))}
    orphan = fact_codes - master_codes
    if orphan:
        print(f"[WARN] kode stasiun di PostgreSQL tanpa master di MySQL: {sorted(orphan)}")
    else:
        print("[OK] semua kode_stasiun di PostgreSQL punya master di MySQL")
    print("\nSelesai. Jalankan:  streamlit run app.py")


if __name__ == "__main__":
    main()
