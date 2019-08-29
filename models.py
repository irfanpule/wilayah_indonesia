from django.db import models


class Provinsi(models.Model):
    nama = models.CharField(max_length=200)

    def __str__(self):
        return self.nama


class Kabupaten(models.Model):
    nama = models.CharField(max_length=200)
    provinsi = models.ForeignKey("Provinsi", on_delete=models.CASCADE, related_name="provinsis")

    def __str__(self):
        return self.nama


class Kecamatan(models.Model):
    nama = models.CharField(max_length=200)
    kabupaten = models.ForeignKey("Kabupaten", on_delete=models.CASCADE, related_name="kabupatens")

    def __str__(self):
        return self.nama


class Desa(models.Model):
    nama = models.CharField(max_length=200)
    kecamatan = models.ForeignKey("Kecamatan", on_delete=models.CASCADE, related_name="kecamatans")

    def __str__(self):
        return self.nama
