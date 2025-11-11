# Migrasi Data Wilayah Indonesia

Panduan lengkap untuk migrasi data wilayah Indonesia dan update relasi di model-model lain.

## 🎯 Problem yang Diselesaikan

Ketika data wilayah Indonesia di-update dengan **ID yang berbeda**, semua relasi di model lain (Profile, Address, dll) akan broken karena menunjuk ke ID lama yang sudah tidak ada.

**Contoh:**
- Data lama: Provinsi "ACEH" dengan ID `11`
- Data baru: Provinsi "ACEH" dengan ID `14` (ID berubah!)
- Model Profile yang punya `provinsi_id=11` akan error karena ID 11 tidak ada lagi

**Solusi:** Matching berdasarkan **NAMA wilayah** dari CSV lama, bukan ID!

## Fitur Utama

1. **Import data wilayah baru** dengan ID baru
2. **Siapkan file CSV lama** (provinces.csv, regencies.csv, dll)
3. **Matching otomatis berdasarkan nama** dari CSV lama ke database baru
4. **Update semua relasi** di model-model lain secara otomatis

## Cara Kerja

```
1. Data lama di CSV: provinces.csv
   11,ACEH

2. Model Profile di database:
   provinsi_id = 11

3. Import data baru:
   14,ACEH (ID berubah dari 11 ke 14)

4. Command migrate_wilayah_relations:
   - Ambil provinsi_id=11 dari Profile
   - Cek di provinces.csv: ID 11 = "ACEH"
   - Query database baru: Provinsi nama="ACEH" → dapat ID 14
   - Update Profile: provinsi_id = 14
```

## Struktur Data CSV

Format CSV yang didukung:
```csv
ID,Nama
11,ACEH
11.01,KAB. ACEH SELATAN
11.01.01,Bakongan
11.01.01.2001,Keude Bakongan
```

Kategori berdasarkan panjang ID (titik tidak dihitung):
- **2 digit** → Provinsi (contoh: `11`)
- **4 digit** → Kabupaten (contoh: `11.01` → `1101`)
- **6 digit** → Kecamatan (contoh: `11.01.01` → `110101`)
- **10+ digit** → Desa (contoh: `11.01.01.2001` → `1101012001`)

## 📋 Cara Penggunaan (Step by Step)

### ⚠️ PENTING: Jika Model Menggunakan on_delete=SET_NULL

Jika model Anda menggunakan `on_delete=models.SET_NULL`, **JANGAN** gunakan `--clear`!

```python
class Profile(models.Model):
    provinsi = models.ForeignKey(Provinsi, on_delete=models.SET_NULL, null=True)
```

**Gunakan workflow Metode A** (tanpa clear).

Lihat [SOLUSI_SET_NULL.md](SOLUSI_SET_NULL.md) untuk penjelasan lengkap.

---

### Metode A: Import Tanpa Hapus (RECOMMENDED untuk SET_NULL)

Metode ini aman untuk `on_delete=SET_NULL` karena data lama tidak dihapus.

#### Step 1: Simpan File CSV Lama

Pastikan file CSV lama tersedia di `wilayah_indonesia/csv/`:
- `provinces.csv`
- `regencies.csv` 
- `districts.csv`
- `villages.csv`

#### Step 2: Import Data Baru TANPA Clear

```bash
# TANPA --clear, data lama tetap ada
python manage.py import_base_csv
```

Ini akan:
- Data dengan ID sama → diupdate
- Data dengan ID baru → diinsert
- **Data lama tidak dihapus** → relasi tetap valid

#### Step 3: Migrasi Relasi

```bash
# Test dulu
python manage.py migrate_wilayah_relations --auto-discover --dry-run

# Migrasi sebenarnya
python manage.py migrate_wilayah_relations --auto-discover
```

#### Step 4: Cleanup Data Lama (Opsional)

Setelah migrasi berhasil, hapus data lama yang tidak terpakai:

```bash
# Lihat data yang akan dihapus
python manage.py cleanup_old_wilayah --dry-run

# Hapus data yang tidak direferensi
python manage.py cleanup_old_wilayah
```

---

### Metode B: Import Dengan Clear (Untuk on_delete=CASCADE/PROTECT)

Hanya gunakan jika model **TIDAK** menggunakan `SET_NULL`.

#### Step 1: Simpan File CSV Lama

Sama seperti Metode A.

#### Step 2: Import Data Baru Dengan Clear

```bash
python manage.py import_base_csv --clear
```

**⚠️ WARNING:** Data lama akan dihapus! Jika ada `on_delete=SET_NULL`, referensi akan jadi NULL.

#### Step 3: Migrasi Relasi

```bash
python manage.py migrate_wilayah_relations --auto-discover
```

**Output contoh:**
```
=== MENCARI MODEL DENGAN RELASI WILAYAH ===

  ✓ accounts.Profile
    - provinsi → Provinsi
    - kabupaten → Kabupaten
  ✓ shops.Store
    - kecamatan → Kecamatan
    - desa → Desa

=== DITEMUKAN 2 MODEL ===

--- Migrasi accounts.Profile ---
[============================================================] 100.0% ...Profile
  ✓ Selesai: 1250 updated, 0 skipped, 0 errors

--- Migrasi shops.Store ---
[============================================================] 100.0% ...Store
  ✓ Selesai: 89 updated, 0 skipped, 0 errors
```

**Test dulu dengan dry-run:**
```bash
python manage.py migrate_wilayah_relations --auto-discover --dry-run
```

**Migrasi model tertentu saja:**
```bash
python manage.py migrate_wilayah_relations --app=accounts --model=Profile
```

## 💡 Contoh Kasus Penggunaan

### Contoh 1: Migrasi Data Wilayah dengan ID Berubah Total

**Situasi:**
- Data lama: Provinsi "ACEH" = ID `11`
- Data baru: Provinsi "ACEH" = ID `14` (ID berubah!)
- Ada 1250 Profile yang punya `provinsi_id=11`

**Solusi:**

```python
# accounts/models.py
from django.db import models
from wilayah_indonesia.models import Provinsi, Kabupaten

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=200)
    provinsi = models.ForeignKey(Provinsi, on_delete=models.SET_NULL, null=True)
    kabupaten = models.ForeignKey(Kabupaten, on_delete=models.SET_NULL, null=True)
```

**Langkah migrasi:**

```bash
# 1. Buat migration untuk model WilayahIDMapping
python manage.py makemigrations wilayah_indonesia
python manage.py migrate

# 2. Simpan mapping data LAMA (sebelum import!)
python manage.py save_old_mapping

# 3. Import data BARU
python manage.py import_base_csv --clear

# 4. Matching berdasarkan nama, isi id_baru di mapping
python manage.py update_mapping_with_new_ids

# 5. Update semua relasi di Profile
python manage.py migrate_wilayah_relations --auto-discover
```

**Hasil:**
- Semua Profile yang punya `provinsi_id=11` akan diupdate jadi `provinsi_id=14`
- Matching berdasarkan nama "ACEH", bukan ID!

### Contoh 2: Multiple Models dengan Relasi Wilayah

```python
# models.py
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provinsi = models.ForeignKey(Provinsi, on_delete=models.CASCADE)
    kabupaten = models.ForeignKey(Kabupaten, on_delete=models.CASCADE)
    alamat_lengkap = models.TextField()

class Store(models.Model):
    nama = models.CharField(max_length=200)
    kecamatan = models.ForeignKey(Kecamatan, on_delete=models.CASCADE)
    desa = models.ForeignKey(Desa, on_delete=models.SET_NULL, null=True)
```

**Migrasi semua model sekaligus:**

```bash
# Setelah step 1-4 di atas selesai, jalankan:
python manage.py migrate_wilayah_relations --auto-discover
```

**Output:**

```
=== MENCARI MODEL DENGAN RELASI WILAYAH ===

  ✓ accounts.Profile
    - provinsi → Provinsi
    - kabupaten → Kabupaten
  ✓ accounts.Address
    - provinsi → Provinsi
    - kabupaten → Kabupaten
  ✓ shops.Store
    - kecamatan → Kecamatan
    - desa → Desa

=== DITEMUKAN 3 MODEL ===

--- Migrasi accounts.Profile ---
[============================================================] 100.0% ...Profile
  ✓ Selesai: 1250 updated, 0 skipped, 0 errors

--- Migrasi accounts.Address ---
[============================================================] 100.0% ...Address
  ✓ Selesai: 532 updated, 0 skipped, 0 errors

--- Migrasi shops.Store ---
[============================================================] 100.0% ...Store
  ✓ Selesai: 89 updated, 0 skipped, 0 errors
```

### Contoh 3: Test Dulu dengan Dry Run

```bash
# Lihat apa yang akan berubah tanpa mengubah data
python manage.py migrate_wilayah_relations --auto-discover --dry-run
```

**Output:**
```
--- Migrasi accounts.Profile ---
  [DRY-RUN] provinsi_id: 11 → 14
  [DRY-RUN] kabupaten_id: 1101 → 1401
  ...
  ✓ Selesai: 1250 updated, 0 skipped, 0 errors
```

Jika hasilnya OK, jalankan tanpa `--dry-run`.

## Cara Kerja Mapping

### Tabel WilayahIDMapping

Model ini menyimpan relasi ID lama → ID baru:

| tipe | id_lama | id_baru | nama |
|------|---------|---------|------|
| provinsi | 11 | 11 | ACEH |
| kabupaten | 11.01 | 1101 | KAB. ACEH SELATAN |
| kecamatan | 11.01.01 | 110101 | Bakongan |
| desa | 11.01.01.2001 | 1101012001 | Keude Bakongan |

### Proses Migrasi

1. Load semua mapping ke memory untuk performa
2. Untuk setiap record di model target (misal Profile):
   - Ambil ID lama dari field ForeignKey (`provinsi_id`, `kabupaten_id`, dll)
   - Cari ID baru di mapping table
   - Update field dengan ID baru
3. Save hanya field yang berubah (efisien)

## Tips dan Troubleshooting

### Error: "Tidak ada data mapping ditemukan"

Pastikan Anda sudah menjalankan import dengan parameter `--save-mapping`:

```bash
python manage.py import_base_csv --save-mapping
```

### Cek Mapping yang Tersimpan

Anda bisa cek data mapping di Django admin atau shell:

```python
from wilayah_indonesia.models import WilayahIDMapping

# Lihat jumlah mapping
print(f"Provinsi: {WilayahIDMapping.objects.filter(tipe='provinsi').count()}")
print(f"Kabupaten: {WilayahIDMapping.objects.filter(tipe='kabupaten').count()}")
print(f"Kecamatan: {WilayahIDMapping.objects.filter(tipe='kecamatan').count()}")
print(f"Desa: {WilayahIDMapping.objects.filter(tipe='desa').count()}")

# Lihat contoh mapping
for m in WilayahIDMapping.objects.filter(tipe='provinsi')[:5]:
    print(f"{m.id_lama} → {m.id_baru}: {m.nama}")
```

### Backup Database

Selalu backup database sebelum menjalankan migrasi:

```bash
# PostgreSQL
pg_dump -U username dbname > backup.sql

# MySQL
mysqldump -u username -p dbname > backup.sql

# SQLite
cp db.sqlite3 db.sqlite3.backup
```

### Rollback Jika Terjadi Error

Jika terjadi error saat migrasi, transaksi akan di-rollback otomatis. Database akan tetap dalam keadaan sebelum migrasi dimulai.

## 📚 Command Reference

### import_base_csv

Import data wilayah dari file CSV.

```bash
python manage.py import_base_csv [options]
```

**Options:**
- `--file=FILENAME`: Nama file CSV (default: base.csv)
- `--clear`: Hapus semua data wilayah sebelum import

**Contoh:**
```bash
# Import dengan hapus data lama
python manage.py import_base_csv --clear

# Import dari file lain
python manage.py import_base_csv --file=wilayah_2024.csv --clear
```

### migrate_wilayah_relations

Migrasi relasi wilayah di model-model lain dengan matching dari CSV lama ke database baru.

```bash
python manage.py migrate_wilayah_relations [options]
```

**Options:**
- `--auto-discover`: Otomatis cari semua model dengan relasi wilayah
- `--app=APP_LABEL`: Nama app untuk migrasi model tertentu
- `--model=MODEL_NAME`: Nama model untuk migrasi model tertentu
- `--dry-run`: Test mode tanpa menyimpan perubahan
- `--csv-dir=DIR`: Direktori CSV lama (default: wilayah_indonesia.csv)

**Contoh:**
```bash
# Auto-discover dan migrasi semua model
python manage.py migrate_wilayah_relations --auto-discover

# Test dulu dengan dry-run
python manage.py migrate_wilayah_relations --auto-discover --dry-run

# Migrasi model tertentu
python manage.py migrate_wilayah_relations --app=accounts --model=Profile

# Gunakan CSV dari direktori lain
python manage.py migrate_wilayah_relations --auto-discover --csv-dir=backup.csv
```

## Frequently Asked Questions (FAQ)

### Q: Apakah data wilayah lama akan terhapus?

A: Ya, jika Anda menggunakan parameter `--clear`. Tanpa parameter ini, data akan di-update (update_or_create).

### Q: Apakah relasi di model lain akan otomatis update?

A: Tidak otomatis. Anda harus menjalankan command `migrate_wilayah_relations` setelah import.

### Q: Bagaimana jika ada data yang tidak ada mappingnya?

A: Data akan di-skip dan ditampilkan di log error. Pastikan semua data wilayah sudah di-import dengan benar.

### Q: Apakah bisa import data wilayah tanpa menyimpan mapping?

A: Ya, cukup jalankan tanpa parameter `--save-mapping`. Berguna jika Anda tidak perlu migrasi relasi.

### Q: Berapa lama proses migrasi?

A: Tergantung jumlah data. Untuk 90.000+ data wilayah biasanya 2-5 menit. Migrasi relasi tergantung jumlah records di model target.

## Support

Jika ada pertanyaan atau issue, silakan buat issue di repository ini.
