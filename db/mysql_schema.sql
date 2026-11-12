-- =====================================================================
-- DBMS 2: MySQL (XAMPP)  -> DATA MASTER / REFERENSI
-- Database: ispu_master
-- =====================================================================

CREATE TABLE IF NOT EXISTS stasiun (
    kode_stasiun  VARCHAR(10)  NOT NULL,
    nama_stasiun  VARCHAR(100) NOT NULL,
    wilayah       VARCHAR(50)  NOT NULL,
    alamat        VARCHAR(255),
    latitude      DECIMAL(9,6) NOT NULL,
    longitude     DECIMAL(9,6) NOT NULL,
    PRIMARY KEY (kode_stasiun)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS kategori_ispu (
    kategori     VARCHAR(20) NOT NULL,
    urutan       TINYINT     NOT NULL,
    rentang_min  SMALLINT,
    rentang_max  SMALLINT,
    warna_hex    CHAR(7)     NOT NULL,
    deskripsi    VARCHAR(255),
    PRIMARY KEY (kategori)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS parameter_pencemar (
    kode_parameter    VARCHAR(10)  NOT NULL,
    nama_parameter    VARCHAR(100) NOT NULL,
    kolom_data        VARCHAR(10)  NOT NULL,
    satuan            VARCHAR(20)  NOT NULL,
    dampak_kesehatan  VARCHAR(500),
    PRIMARY KEY (kode_parameter)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
