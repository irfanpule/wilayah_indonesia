# Wilayah Indonesia

Aplikasi ini menyediakan data wilayah administratif Indonesia (provinsi, kabupaten/kota, kecamatan, dan desa) yang dapat digunakan untuk kebutuhan input pada Admin site, form custom, REST API.

![admin-site](https://raw.githubusercontent.com/irfanpule/wilayah_indonesia/refs/heads/master/screenshoots/select-chained-admin-site.png)

## Fitur

- Menyediakan data wilayah Indonesia secara lengkap
- Mendukung proses seeding ke database
- Tersedia form chained untuk diimplementasikan pada form Admin site atau form custome
- Tersedia endpoint REST API

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

4. **Register URL**
    ```python
    path('wilayah-indonesia/', include('wilayah_indonesia.urls')),
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
- Daftarkan path django-select2 pada url root project kamu
```
path('select2/', include('django_select2.urls'))
```
- Gunakan fungsi chiined yang sudah disediakan untuk membuat select chained pada form. Contoh
```python

# Model -------
# Implementasi field wilayah_indonesia pada model
class Profile(models.Model):
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
    
# Form -------
# Implementasi fungsi chained pada form
from wilayah_indonesia.forms import provinsiChained, kabupatenChained, kecamatanChained, desaChained

class ProfileAdminForm(forms.ModelForm):
    provinsi = provinsiChained()    
    kabupaten = kabupatenChained()
    kecamatan = kecamatanChained()
    desa = desaChained()
    
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
## Endpoint REST API
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