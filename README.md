# Wilayah Indonesia

Aplikasi ini menyediakan data wilayah administratif Indonesia (provinsi, kabupaten/kota, kecamatan, dan desa) yang dapat digunakan untuk kebutuhan input pada Admin site, form custom, REST API.

![admin-site](https://raw.githubusercontent.com/irfanpule/wilayah_indonesia/refs/heads/master/wilayah_indonesia/screenshoots/animation-chaining.gif)

## Fitur

- Menyediakan data wilayah Indonesia secara lengkap
- Mendukung proses seeding ke database
- Tersedia form chained untuk diimplementasikan pada form Admin site atau form custom
- Tersedia endpoint REST API

## Instalasi
Via PIP
```
pip install django-wilayah-indonesia
```

Manual
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

Setelah berhasil lakukan
1. **Registrasi App**
    ```
    INSTALLED_APPS = [
        ....
        
        'wilayah_indonesia'

        ....
    ]
    ```
2. **Migrate**
    ```bash
    ./manage.py migrate
    ```

3. **Register URL**
    Registrasikan url django-select2 dan wilayah_indonesia
    ```python
    path('wilayah-indonesia/', include('wilayah_indonesia.urls')),
    path('select2/', include('django_select2.urls'))
    ```

## ⚠️ PENTING: Upgrade ke Versi Baru

Jika Anda melakukan **upgrade dari versi lama** dan data wilayah sudah ada di database, harap ikuti panduan migrasi untuk menghindari kehilangan data!

**Panduan Lengkap:** Lihat [MIGRASI_QUICKSTART.md](MIGRASI_QUICKSTART.md) atau [MIGRASI_DATA.md](MIGRASI_DATA.md)

### Quick Guide Migrasi:

**Jika model Anda menggunakan `on_delete=SET_NULL`:**
```bash
# 1. Import data baru TANPA --clear (data lama tetap ada)
python manage.py import_base_csv

# 2. Migrasi relasi (matching dari CSV lama ke database baru)
python manage.py migrate_wilayah_relations --auto-discover

# 3. Cleanup data lama (opsional)
python manage.py cleanup_old_wilayah
```

**Catatan:** Pastikan file CSV lama (`provinces.csv`, `regencies.csv`, `districts.csv`, `villages.csv`) tersedia di `wilayah_indonesia/csv/` untuk proses migrasi.

---

## Seeding Data Wilayah
### Import dari File Tunggal (base.csv)

Alternatif, Anda dapat menggunakan command `import_base_csv` untuk import data dari satu file CSV dengan format: `ID,Nama`

```bash
# Import data baru
python manage.py import_base_csv

# Atau import dengan menghapus data lama (hati-hati jika ada on_delete=SET_NULL)
python manage.py import_base_csv --clear
```

**Format CSV:**
```csv
11,ACEH
1101,KAB. ACEH SELATAN
110101,Bakongan
1101012001,Keude Bakongan
```

Kategori berdasarkan panjang ID:
- **2 digit** → Provinsi
- **4 digit** → Kabupaten
- **6 digit** → Kecamatan  
- **10+ digit** → Desa

## Model
Contoh kode:
```python
from wilayah_indonesia.models import WilayahDisplayMixin

class Profile(WilayahDisplayMixin, models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nik = models.CharField(max_length=16, unique=True)
    # field lainnya....
    provinsi = models.ForeignKey("wilayah_indonesia.Provinsi", on_delete=models.SET_NULL, null=True, blank=True)
    kabupaten = models.ForeignKey("wilayah_indonesia.Kabupaten", on_delete=models.SET_NULL, null=True, blank=True)
    kecamatan = models.ForeignKey("wilayah_indonesia.Kecamatan", on_delete=models.SET_NULL, null=True, blank=True)
    desa = models.ForeignKey("wilayah_indonesia.Desa", on_delete=models.SET_NULL, null=True, blank=True)
    # field lainnya ....

    def __str__(self):
        return self.nik
```
Disediakan class mixin untuk mempermudah akses nama dari masing-masing wilayah. Cukup gunakan `WilayahDisplayMixin` kamu dapat dengan mudah akses nama wilayah seperti ini: `get_provinsi_display()`, `get_kabupaten_display()`, `get_kecamatan_display`, `get_desa_display()`.

*NB: Disarakan nama field tetap menggunakan `provinsi, kabupaten, kecamatan, desa` agar fungsi mixin bekerja*


## Form
Sudah tersedia tersedia class mixin untuk form select2 chained dapat dilihat pada `wilayah_indonesia/forms.py`
- Gunakan fungsi chiined yang sudah disediakan untuk membuat select chained pada form. Contoh
```python    
# Form -------
# Implementasi fungsi chained pada form
from wilayah_indonesia.forms import WilayahChainedFormMixin

class ProfileAdminForm(WilayahChainedFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'


# Admin site -------
# Implementasi form pada admin site
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nik', 'no_ponsel', 'jenis_kelamin')
    # atribute lainnya ....
    form = ProfileAdminForm  # tambahkan form disini
```

## Endpoint
- Untuk mendapatkan data provinsi 
```
{{base_url}}/wilayah-indonesia/provinsi/
```
- Untuk mendapatkan data kabupaten harus menambahkan id provinsi pada url
```
{{base_url}}/wilayah-indonesia/kabupaten/18/
```
- Untuk mendapatkan data kecamatan harus menambahkan id kabupaten pada url
```
{{base_url}}/wilayah-indonesia/kecamatan/1809/
```
- Untuk mendapatkan data desa harus menambahkan id kecamatan pada url
```
{{base_url}}/wilayah-indonesia/desa/1809050/
```
- Untuk melakukan filter atau search data cukup menambahkan query param pada url `{{uri}}/?search=way`. Berlaku untuk semua endpoint


## Lisensi

MIT License.