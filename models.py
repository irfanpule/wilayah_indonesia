from django.db import models


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
