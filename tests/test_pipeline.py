import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import clean_api_records, extract_station_code, federate  # noqa: E402

SAMPLE = [
    {"periode_data": "202401", "bulan": "01", "tanggal": "21", "stasiun": "DKI3  Jagakarsa",
     "pm_sepuluh": "51", "pm_duakomalima": "65", "sulfur_dioksida": "45", "karbon_monoksida": "9",
     "ozon": "8", "nitrogen_dioksida": "79", "max": "79", "parameter_pencemar_kritis": "null", "kategori": "SEDANG"},
    {"periode_data": "202404", "bulan": "4", "tanggal": "1", "stasiun": "DKI1  Bunderan HI",
     "pm_sepuluh": "N/A", "pm_duakomalima": "96", "sulfur_dioksida": "11", "karbon_monoksida": "26",
     "ozon": "27", "nitrogen_dioksida": "52", "max": "96", "parameter_pencemar_kritis": "PM25", "kategori": "SEDANG"},
    {"periode_data": "202403", "bulan": "3", "tanggal": "22", "stasiun": "DKI4 Lubang Buaya",
     "pm_sepuluh": "N/A", "pm_duakomalima": "N/A", "sulfur_dioksida": "N/A", "karbon_monoksida": "N/A",
     "ozon": "N/A", "nitrogen_dioksida": "N/A", "max": "N/A", "parameter_pencemar_kritis": "N/A",
     "kategori": "TIDAK ADA DATA"},
    # duplikat (stasiun+tanggal sama, nama ditulis beda) -> harus tinggal satu
    {"periode_data": "202404", "bulan": "4", "tanggal": "1", "stasiun": "DKI1  Bundaran Hotel Indonesia (HI)",
     "pm_sepuluh": "63", "pm_duakomalima": "96", "sulfur_dioksida": "11", "karbon_monoksida": "26",
     "ozon": "27", "nitrogen_dioksida": "52", "max": "96", "parameter_pencemar_kritis": "PM25", "kategori": "SEDANG"},
]


def test_station_code_variants():
    assert extract_station_code("DKI1  Bunderan HI") == "DKI1"
    assert extract_station_code("DKI1  Bundaran Hotel Indonesia (HI)") == "DKI1"
    assert extract_station_code("DKI5  Kebon Jeruk  Jakarta Barat") == "DKI5"
    assert extract_station_code("Stasiun lain") is None


def test_clean_records():
    df = clean_api_records(SAMPLE)
    assert len(df) == 3  # duplikat DKI1 2024-04-01 dibuang
    jaga = df[df.kode_stasiun == "DKI3"].iloc[0]
    assert str(jaga.tanggal) == "2024-01-21" and jaga.ispu_max == 79
    assert pd.isna(jaga.parameter_kritis)  # "null" -> NA
    hi = df[df.kode_stasiun == "DKI1"].iloc[0]
    assert hi.pm10 == 63  # baris terakhir yang dipertahankan
    kosong = df[df.kode_stasiun == "DKI4"].iloc[0]
    assert pd.isna(kosong.ispu_max) and kosong.kategori == "TIDAK ADA DATA"


def test_federate():
    fact = clean_api_records(SAMPLE)
    stasiun = pd.DataFrame({"kode_stasiun": ["DKI1", "DKI3", "DKI4"], "nama_stasiun": ["HI", "Jagakarsa", "LB"],
                            "wilayah": ["a", "b", "c"], "alamat": ["", "", ""],
                            "latitude": [-6.1, -6.3, -6.2], "longitude": [106.8, 106.8, 106.9]})
    kategori = pd.DataFrame({"kategori": ["TIDAK ADA DATA", "SEDANG"], "urutan": [0, 2], "warna_hex": ["#999", "#00f"]})
    parameter = pd.DataFrame({"kode_parameter": ["PM25"], "nama_parameter": ["Partikulat PM2.5"]})
    out = federate(fact, stasiun, kategori, parameter)
    assert len(out) == len(fact)
    assert out["nama_stasiun"].notna().all()
    assert not out["tidak_sehat"].any()
