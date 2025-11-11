# Solusi: Migrasi Data dengan on_delete=SET_NULL

## ⚠️ Problem

Model dengan `on_delete=models.SET_NULL` akan kehilangan referensi ketika data wilayah dihapus:

```python
class Profile(models.Model):
    provinsi = models.ForeignKey(Provinsi, on_delete=models.SET_NULL, null=True)
```

Ketika data Provinsi lama dihapus, `provinsi_id` di Profile akan menjadi `NULL`.

## ✅ Solusi 1: Import Tanpa Hapus Data Lama (RECOMMENDED)

Gunakan `update_or_create` tanpa parameter `--clear`:

```bash
# JANGAN gunakan --clear
python manage.py import_base_csv

# Lalu migrasi relasi
python manage.py migrate_wilayah_relations --auto-discover
```

### Cara Kerja:

1. **Data lama tetap ada** (tidak dihapus)
2. **Data dengan ID sama** → diupdate namanya
3. **Data dengan ID baru** → diinsert
4. Relasi di Profile masih menunjuk ke ID lama yang valid
5. Command migrasi akan update ke ID baru

### Keuntungan:
✅ Aman - tidak ada data yang hilang  
✅ Tidak break foreign key  
✅ Bisa rollback jika ada masalah  

### Kelemahan:
⚠️ Database akan punya data duplikat sementara (lama + baru)  
⚠️ Perlu cleanup manual setelah migrasi selesai  

---

## ✅ Solusi 2: Temporary Disable Foreign Key (Advanced)

Untuk PostgreSQL/MySQL, kita bisa disable foreign key constraint sementara.

### Step 1: Backup Database

```bash
# PostgreSQL
pg_dump -U username dbname > backup.sql

# MySQL
mysqldump -u username -p dbname > backup.sql
```

### Step 2: Disable Foreign Key Check

**PostgreSQL:**
```sql
-- Disable FK temporarily
SET session_replication_role = 'replica';

-- Import data baru
-- ...

-- Enable FK again
SET session_replication_role = 'origin';
```

**MySQL:**
```sql
SET FOREIGN_KEY_CHECKS=0;

-- Import data baru
-- ...

SET FOREIGN_KEY_CHECKS=1;
```

### Step 3: Jalankan Migrasi

```bash
# Import dengan clear
python manage.py import_base_csv --clear

# Migrasi relasi (akan update ke ID baru)
python manage.py migrate_wilayah_relations --auto-discover
```

### Step 4: Re-enable Foreign Key

Jalankan SQL enable di Step 2.

---

## ✅ Solusi 3: Command Khusus Migrasi dengan Disable FK

Saya bisa buatkan command yang otomatis handle disable/enable FK:

```bash
python manage.py migrate_wilayah_with_fk_disable --auto-discover
```

Command ini akan:
1. Disable FK checks
2. Import data baru (clear lama)
3. Migrasi relasi
4. Enable FK checks

---

## 📊 Perbandingan Solusi

| Solusi | Keamanan | Kompleksitas | Database Support | Recommended |
|--------|----------|--------------|------------------|-------------|
| **#1: Tanpa Clear** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Semua DB | ✅ Ya |
| **#2: Manual FK Disable** | ⭐⭐⭐ | ⭐⭐ | PostgreSQL, MySQL | - |
| **#3: Command Auto FK** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | PostgreSQL, MySQL | Opsional |

---

## 🎯 Recommended Workflow (Solusi #1)

```bash
# 1. Import data baru TANPA clear
python manage.py import_base_csv

# 2. Test migrasi dengan dry-run
python manage.py migrate_wilayah_relations --auto-discover --dry-run

# 3. Migrasi relasi sebenarnya
python manage.py migrate_wilayah_relations --auto-discover

# 4. Cleanup data lama yang tidak terpakai
python manage.py cleanup_old_wilayah
```

---

## 🛠️ Command: cleanup_old_wilayah

Command untuk menghapus data wilayah lama yang sudah tidak direferensi:

```bash
# Lihat data yang akan dihapus
python manage.py cleanup_old_wilayah --dry-run

# Hapus data yang tidak direferensi
python manage.py cleanup_old_wilayah

# Paksa hapus semua kecuali yang direferensi
python manage.py cleanup_old_wilayah --force
```

Command ini akan:
- Cari wilayah yang tidak direferensi oleh model lain
- Tampilkan list data yang akan dihapus
- Hapus dengan aman (atomic transaction)

---

## 💡 Alternatif: Ubah on_delete

Jika memungkinkan, ubah model menjadi:

```python
class Profile(models.Model):
    # Option 1: CASCADE (hapus profile jika provinsi dihapus)
    provinsi = models.ForeignKey(Provinsi, on_delete=models.CASCADE)
    
    # Option 2: PROTECT (prevent hapus provinsi jika masih ada profile)
    provinsi = models.ForeignKey(Provinsi, on_delete=models.PROTECT)
    
    # Option 3: DO_NOTHING (dangerous, bisa orphaned FK)
    provinsi = models.ForeignKey(Provinsi, on_delete=models.DO_NOTHING)
```

Tapi ini memerlukan migration dan bisa impact existing logic.

---

## ❓ FAQ

### Q: Apakah data akan duplikat permanent?
A: Tidak, setelah migrasi selesai, jalankan `cleanup_old_wilayah` untuk hapus data lama.

### Q: Bagaimana tahu mana data lama dan baru?
A: Data lama = ID yang ada di CSV lama  
Data baru = ID yang ada di CSV baru tetapi tidak ada di CSV lama

### Q: Apakah aman untuk production?
A: Ya, solusi #1 (tanpa clear) sangat aman. Selalu backup database dulu!
