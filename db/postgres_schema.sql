-- =====================================================================
-- DBMS 1: PostgreSQL  -> TABEL FAKTA (data transaksi/pengukuran harian)
-- Database: ispu_jakarta
-- Sumber  : API Satu Data Jakarta - Indeks Standar Pencemar Udara (ISPU)
-- =====================================================================
-- Catatan: kode_stasiun merujuk ke tabel `stasiun` di MySQL. Karena beda
-- DBMS, relasi ini TIDAK bisa berupa FOREIGN KEY; integritasnya dijaga
-- di level aplikasi (lihat seed_data.py dan src/pipeline.py).

CREATE TABLE IF NOT EXISTS ispu_harian (
    id                BIGSERIAL PRIMARY KEY,
    kode_stasiun      VARCHAR(10) NOT NULL,
    tanggal           DATE        NOT NULL,
    pm10              SMALLINT,
    pm25              SMALLINT,
    so2               SMALLINT,
    co                SMALLINT,
    o3                SMALLINT,
    no2               SMALLINT,
    ispu_max          SMALLINT,
    parameter_kritis  VARCHAR(10),
    kategori          VARCHAR(20) NOT NULL,
    created_at        TIMESTAMP   NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ispu_stasiun_tanggal UNIQUE (kode_stasiun, tanggal)
);

CREATE INDEX IF NOT EXISTS idx_ispu_tanggal  ON ispu_harian (tanggal);
CREATE INDEX IF NOT EXISTS idx_ispu_kategori ON ispu_harian (kategori);
