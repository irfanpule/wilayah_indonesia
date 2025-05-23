# Wilayah Indonesia

Aplikasi ini menyediakan data wilayah administratif Indonesia (provinsi, kabupaten/kota, kecamatan, dan desa) yang dapat digunakan untuk kebutuhan aplikasi backend.

## Fitur

- Menyediakan data wilayah Indonesia secara lengkap
- Mendukung proses seeding ke database

## Instalasi

1. **Clone repository**
    - Unduh zip dan extrak dalam direktori proyek
    - Atau masuk dalam direktori proyek kamu lalu clone repositori ini
    ```bash
    git clone https://github.com/irfanpule/data-wilayah-indonesia.
    ```
    

2. **Install dependencies**
    ```bash
    pip install django-select2
    ```

3. **Migrate**
    ```bash
    ./manage.py migrate
    ```

## Seeding Data Wilayah

Jalankan perintah berikut untuk melakukan seeding data wilayah ke database:

```bash
./manage.py region_seeding
```
Atau jika hanya ingin menjalankan seeder wilayah:
```bash
./manage.py region_seeding --provinsi
```
```bash
./manage.py region_seeding --kabupaten
```
```bash
./manage.py region_seeding --kecamatan
```
```bash
./manage.py region_seeding --desa
```

Untuk menghapus data gunakan command ini

```bash
./manage.py region_seeding --delete
```

## Form
Sudah tersedia konfigurasi bawaan sederhana untuk form select2 dapat dilihat pada `wilayah_indonesia/forms.py`

## Lisensi

MIT License.