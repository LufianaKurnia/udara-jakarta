"""Konfigurasi koneksi database.

Urutan pencarian setiap setting:
  1. Environment variable / file .env  (lokal)
  2. st.secrets                        (Streamlit Community Cloud)
Tidak ada password yang ditulis langsung di kode.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def get_setting(name, default=None):
    value = os.getenv(name)
    if value not in (None, ""):
        return value
    try:  # st.secrets hanya ada saat dijalankan lewat Streamlit
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default


def postgres_url():
    full = get_setting("POSTGRES_URL")
    if full:
        return make_url(full)
    query = {}
    if get_setting("PG_SSLMODE"):
        query["sslmode"] = get_setting("PG_SSLMODE")
    return URL.create(
        "postgresql+psycopg2",
        username=get_setting("PG_USER"),
        password=get_setting("PG_PASSWORD"),
        host=get_setting("PG_HOST", "localhost"),
        port=int(get_setting("PG_PORT", "5432")),
        database=get_setting("PG_DATABASE", "ispu_jakarta"),
        query=query,
    )


def mysql_url():
    full = get_setting("MYSQL_URL")
    if full:
        return make_url(full)
    driver = get_setting("MYSQL_DRIVER", "mysqlconnector")
    return URL.create(
        f"mysql+{driver}",
        username=get_setting("MYSQL_USER", "root"),
        password=get_setting("MYSQL_PASSWORD"),
        host=get_setting("MYSQL_HOST", "127.0.0.1"),
        port=int(get_setting("MYSQL_PORT", "3306")),
        database=get_setting("MYSQL_DATABASE", "ispu_master"),
    )


def mysql_connect_args():
    """Opsi SSL untuk MySQL cloud (mis. TiDB Cloud). Kosong untuk XAMPP lokal."""
    ca = get_setting("MYSQL_SSL_CA")
    if not ca:
        return {}
    if get_setting("MYSQL_DRIVER", "mysqlconnector") == "pymysql":
        return {"ssl": {"ca": ca}}
    return {"ssl_ca": ca, "ssl_verify_cert": True}
