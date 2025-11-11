# Cara Migrasi Data Wilayah (Quick Start)

## Problem
Data wilayah baru punya **ID yang berbeda**. Semua relasi di model lain (Profile, Address, dll) akan broken!

## ⚠️ Model Menggunakan on_delete=SET_NULL?

Jika model Anda punya:
```python
provinsi = models.ForeignKey(Provinsi, on_delete=models.SET_NULL, null=True)
```

**GUNAKAN METODE A** (tanpa --clear)

---

## Metode A: Import Tanpa Clear (SAFE untuk SET_NULL)

### 1️⃣ Import Data Baru TANPA Clear
```bash
python manage.py import_base_csv
```

### 2️⃣ Migrasi Relasi
```bash
python manage.py migrate_wilayah_relations --auto-discover
```

### 3️⃣ Cleanup Data Lama (Opsional)
```bash
python manage.py cleanup_old_wilayah --dry-run
python manage.py cleanup_old_wilayah
```

**DONE!** ✨

---

## Metode B: Import Dengan Clear (Hanya untuk CASCADE/PROTECT)

### 1️⃣ Import Data Baru Dengan Clear
```bash
python manage.py import_base_csv --clear
```

### 2️⃣ Migrasi Relasi
```bash
python manage.py migrate_wilayah_relations --auto-discover
```

**DONE!** ✨

## Cara Kerja

**Matching berdasarkan NAMA dari CSV lama**, bukan ID!

```
CSV Lama (provinces.csv):
  11,ACEH
  
Database Lama (Profile):
  provinsi_id = 11

↓ Import Data Baru
  
Database Baru:
  14,ACEH (ID berubah!)

↓ migrate_wilayah_relations

1. Ambil provinsi_id=11 dari Profile
2. Cek CSV lama: ID 11 → "ACEH"
3. Query DB baru: nama="ACEH" → ID 14
4. Update Profile: provinsi_id=14
```

## Requirement

- File CSV lama harus ada di `wilayah_indonesia/csv/`:
  - `provinces.csv`
  - `regencies.csv`
  - `districts.csv`
  - `villages.csv`

## Dokumentasi Lengkap

Lihat [MIGRASI_DATA.md](MIGRASI_DATA.md) untuk dokumentasi detail dan troubleshooting.
