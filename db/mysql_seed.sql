-- Seed data master untuk MySQL (idempotent: aman dijalankan berulang).
-- CATATAN: koordinat stasiun adalah PERKIRAAN (area sekitar lokasi stasiun),
-- verifikasi ulang dengan sumber resmi DLH DKI Jakarta bila diperlukan.

INSERT INTO stasiun (kode_stasiun, nama_stasiun, wilayah, alamat, latitude, longitude) VALUES
('DKI1', 'Bundaran Hotel Indonesia (HI)', 'Jakarta Pusat',  'Bundaran HI, Jl. M.H. Thamrin',  -6.195000, 106.823000),
('DKI2', 'Kelapa Gading',                  'Jakarta Utara',  'Kelapa Gading',                  -6.157000, 106.908500),
('DKI3', 'Jagakarsa',                      'Jakarta Selatan','Jagakarsa',                      -6.335000, 106.819000),
('DKI4', 'Lubang Buaya',                   'Jakarta Timur',  'Lubang Buaya, Cipayung',         -6.295000, 106.905000),
('DKI5', 'Kebon Jeruk',                    'Jakarta Barat',  'Kebon Jeruk',                    -6.195000, 106.770000)
ON DUPLICATE KEY UPDATE
    nama_stasiun = VALUES(nama_stasiun), wilayah = VALUES(wilayah), alamat = VALUES(alamat),
    latitude = VALUES(latitude), longitude = VALUES(longitude);

INSERT INTO kategori_ispu (kategori, urutan, rentang_min, rentang_max, warna_hex, deskripsi) VALUES
('TIDAK ADA DATA',      0, NULL, NULL, '#9E9E9E', 'Data pengukuran tidak tersedia pada hari tersebut'),
('BAIK',                1,    0,   50, '#2E7D32', 'Kualitas udara baik, tidak berdampak pada kesehatan'),
('SEDANG',              2,   51,  100, '#1976D2', 'Dapat diterima, namun berdampak pada kelompok sensitif'),
('TIDAK SEHAT',         3,  101,  200, '#F9A825', 'Merugikan manusia, hewan, dan tumbuhan'),
('SANGAT TIDAK SEHAT',  4,  201,  300, '#D32F2F', 'Meningkatkan risiko kesehatan pada banyak orang'),
('BERBAHAYA',           5,  301,  500, '#212121', 'Berbahaya bagi seluruh populasi')
ON DUPLICATE KEY UPDATE
    urutan = VALUES(urutan), rentang_min = VALUES(rentang_min), rentang_max = VALUES(rentang_max),
    warna_hex = VALUES(warna_hex), deskripsi = VALUES(deskripsi);

INSERT INTO parameter_pencemar (kode_parameter, nama_parameter, kolom_data, satuan, dampak_kesehatan) VALUES
('PM10', 'Partikulat PM10',        'pm10', 'ug/m3', 'Partikel kasar yang dapat masuk ke saluran pernapasan atas, memicu iritasi dan memperburuk asma'),
('PM25', 'Partikulat PM2.5',       'pm25', 'ug/m3', 'Partikel halus yang dapat masuk jauh ke paru-paru dan aliran darah, terkait penyakit pernapasan dan jantung'),
('SO2',  'Sulfur Dioksida (SO2)',  'so2',  'ug/m3', 'Mengiritasi saluran pernapasan, memperburuk asma dan bronkitis'),
('CO',   'Karbon Monoksida (CO)',  'co',   'ug/m3', 'Mengurangi kemampuan darah mengangkut oksigen, berbahaya bagi penderita penyakit jantung'),
('O3',   'Ozon (O3)',              'o3',   'ug/m3', 'Mengiritasi paru-paru, memicu batuk dan sesak napas'),
('NO2',  'Nitrogen Dioksida (NO2)','no2',  'ug/m3', 'Mengiritasi saluran pernapasan dan meningkatkan kerentanan terhadap infeksi paru')
ON DUPLICATE KEY UPDATE
    nama_parameter = VALUES(nama_parameter), kolom_data = VALUES(kolom_data),
    satuan = VALUES(satuan), dampak_kesehatan = VALUES(dampak_kesehatan);
