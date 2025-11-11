from django.db import models


class WilayahIDMapping(models.Model):
    """
    Model untuk menyimpan mapping wilayah lama ke wilayah baru.
    Matching berdasarkan NAMA wilayah karena ID bisa berubah total.
    
    Workflow:
    1. Sebelum import data baru, simpan dulu mapping dari data lama
    2. Import data baru dengan ID baru
    3. Update relasi di model lain dengan matching berdasarkan nama
    """
    TIPE_CHOICES = [
        ('provinsi', 'Provinsi'),
        ('kabupaten', 'Kabupaten'),
        ('kecamatan', 'Kecamatan'),
        ('desa', 'Desa'),
    ]
    
    tipe = models.CharField(max_length=20, choices=TIPE_CHOICES, db_index=True)
    id_lama = models.CharField(max_length=50, db_index=True, help_text="ID dari sistem lama")
    id_baru = models.CharField(max_length=50, db_index=True, null=True, blank=True, help_text="ID dari sistem baru")
    nama = models.CharField(max_length=200, db_index=True, help_text="Nama wilayah untuk matching")
    nama_parent = models.CharField(max_length=200, blank=True, help_text="Nama parent untuk disambiguasi")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Wilayah ID Mapping"
        unique_together = [['tipe', 'id_lama']]
        indexes = [
            models.Index(fields=['tipe', 'id_lama']),
            models.Index(fields=['tipe', 'nama']),
            models.Index(fields=['tipe', 'id_baru']),
        ]
    
    def __str__(self):
        if self.id_baru:
            return f"{self.tipe}: {self.nama} ({self.id_lama} → {self.id_baru})"
        return f"{self.tipe}: {self.nama} (ID lama: {self.id_lama})"


class Provinsi(models.Model):
    nama = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = "Provinsi"

        
    def __str__(self):
        return self.nama


class Kabupaten(models.Model):
    nama = models.CharField(max_length=200)
    provinsi = models.ForeignKey("Provinsi", on_delete=models.CASCADE, related_name="provinsis")

    class Meta:
        verbose_name_plural = "Kabupaten"
        
    def __str__(self):
        return self.nama


class Kecamatan(models.Model):
    nama = models.CharField(max_length=200)
    kabupaten = models.ForeignKey("Kabupaten", on_delete=models.CASCADE, related_name="kabupatens")

    class Meta:
        verbose_name_plural = "Kecamatan"
        
    def __str__(self):
        return self.nama


class Desa(models.Model):
    nama = models.CharField(max_length=200)
    kecamatan = models.ForeignKey("Kecamatan", on_delete=models.CASCADE, related_name="kecamatans")

    class Meta:
        verbose_name_plural = "Desa"
        
    def __str__(self):
        return self.nama


class WilayahDisplayMixin:
    def get_provinsi_display(self):
        return self.provinsi.nama if getattr(self, "provinsi", None) else ""

    def get_kabupaten_display(self):
        return self.kabupaten.nama if getattr(self, "kabupaten", None) else ""

    def get_kecamatan_display(self):
        return self.kecamatan.nama if getattr(self, "kecamatan", None) else ""

    def get_desa_display(self):
        return self.desa.nama if getattr(self, "desa", None) else ""
