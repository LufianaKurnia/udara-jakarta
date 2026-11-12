"""Pembersihan data API (ETL) dan federasi data PostgreSQL + MySQL di Pandas."""
import re

import pandas as pd

POLLUTANTS = ["pm10", "pm25", "so2", "co", "o3", "no2"]
FACT_COLUMNS = ["kode_stasiun", "tanggal", *POLLUTANTS, "ispu_max", "parameter_kritis", "kategori"]

RAW_TO_DB = {
    "pm_sepuluh": "pm10",
    "pm_duakomalima": "pm25",
    "sulfur_dioksida": "so2",
    "karbon_monoksida": "co",
    "ozon": "o3",
    "nitrogen_dioksida": "no2",
    "max": "ispu_max",
}
NA_TOKENS = ["N/A", "NA", "null", "NULL", "None", "-", ""]
VALID_PARAMS = {"PM10", "PM25", "SO2", "CO", "O3", "NO2"}


def extract_station_code(name):
    """'DKI3  Jagakarsa' / 'DKI1  Bundaran Hotel Indonesia (HI)' -> 'DKI3' / 'DKI1'."""
    match = re.search(r"DKI\s*(\d+)", str(name).upper())
    return f"DKI{match.group(1)}" if match else None


def clean_api_records(records):
    """Ubah JSON mentah API menjadi DataFrame bersih siap masuk PostgreSQL."""
    raw = pd.DataFrame(records)
    if raw.empty:
        return pd.DataFrame(columns=FACT_COLUMNS)

    raw = raw.astype("string").apply(lambda col: col.str.strip())
    raw = raw.mask(raw.isin(NA_TOKENS))

    df = pd.DataFrame()
    df["kode_stasiun"] = raw["stasiun"].map(extract_station_code)

    periode = raw["periode_data"].astype("string")
    df["tanggal"] = pd.to_datetime(
        {
            "year": pd.to_numeric(periode.str[:4], errors="coerce"),
            "month": pd.to_numeric(periode.str[4:6], errors="coerce"),
            "day": pd.to_numeric(raw["tanggal"], errors="coerce"),
        },
        errors="coerce",
    )

    for raw_col, db_col in RAW_TO_DB.items():
        df[db_col] = pd.to_numeric(raw[raw_col], errors="coerce").astype("Int64")

    param = raw["parameter_pencemar_kritis"].astype("string").str.upper().str.replace(".", "", regex=False)
    df["parameter_kritis"] = param.where(param.isin(VALID_PARAMS))
    df["kategori"] = raw["kategori"].astype("string").str.upper().fillna("TIDAK ADA DATA")

    df = df.dropna(subset=["kode_stasiun", "tanggal"])
    df = df.drop_duplicates(subset=["kode_stasiun", "tanggal"], keep="last")
    df["tanggal"] = df["tanggal"].dt.date
    return df[FACT_COLUMNS].sort_values(["tanggal", "kode_stasiun"]).reset_index(drop=True)


def federate(ispu, stasiun, kategori, parameter):
    """Gabungkan fakta (PostgreSQL) dengan master (MySQL) di level aplikasi."""
    df = ispu.merge(stasiun, on="kode_stasiun", how="left", validate="m:1")
    df = df.merge(
        kategori[["kategori", "urutan", "warna_hex"]], on="kategori", how="left", validate="m:1"
    )
    df = df.merge(
        parameter[["kode_parameter", "nama_parameter"]].rename(
            columns={"kode_parameter": "parameter_kritis", "nama_parameter": "nama_parameter_kritis"}
        ),
        on="parameter_kritis",
        how="left",
    )
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    df["tahun_bulan"] = df["tanggal"].dt.to_period("M").astype(str)
    df["tidak_sehat"] = df["urutan"].fillna(0) >= 3
    return df
