"""Koneksi & query ke dua DBMS: PostgreSQL (fakta) dan MySQL (master)."""
from functools import lru_cache

import pandas as pd
from sqlalchemy import create_engine, text

from .config import mysql_connect_args, mysql_url, postgres_url
from .pipeline import POLLUTANTS


@lru_cache(maxsize=1)
def pg_engine():
    return create_engine(postgres_url(), pool_pre_ping=True)


@lru_cache(maxsize=1)
def mysql_engine():
    return create_engine(mysql_url(), connect_args=mysql_connect_args(), pool_pre_ping=True)


def load_ispu_postgres():
    """DBMS 1 - PostgreSQL: tabel fakta pengukuran harian."""
    query = """
        SELECT kode_stasiun, tanggal, pm10, pm25, so2, co, o3, no2,
               ispu_max, parameter_kritis, kategori
        FROM ispu_harian
        ORDER BY tanggal, kode_stasiun
    """
    with pg_engine().connect() as conn:
        df = pd.read_sql(text(query), conn)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    for col in [*POLLUTANTS, "ispu_max"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_master_mysql():
    """DBMS 2 - MySQL: data master (stasiun, kategori, parameter)."""
    with mysql_engine().connect() as conn:
        stasiun = pd.read_sql(text("SELECT * FROM stasiun"), conn)
        kategori = pd.read_sql(text("SELECT * FROM kategori_ispu ORDER BY urutan"), conn)
        parameter = pd.read_sql(text("SELECT * FROM parameter_pencemar"), conn)
    stasiun[["latitude", "longitude"]] = stasiun[["latitude", "longitude"]].astype(float)
    return stasiun, kategori, parameter


def db_status():
    """Info versi & jumlah baris kedua DBMS (untuk panel status di dashboard)."""
    info = {}
    with pg_engine().connect() as conn:
        info["pg_version"] = conn.execute(text("SELECT version()")).scalar()
        info["pg_rows"] = conn.execute(text("SELECT COUNT(*) FROM ispu_harian")).scalar()
    with mysql_engine().connect() as conn:
        info["mysql_version"] = conn.execute(text("SELECT VERSION()")).scalar()
        info["mysql_rows"] = {
            t: conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            for t in ("stasiun", "kategori_ispu", "parameter_pencemar")
        }
    return info
