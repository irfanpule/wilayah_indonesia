from django.contrib import admin
from .models import Provinsi, Kabupaten, Kecamatan, Desa


class ProvinsiAdmin(admin.ModelAdmin):
    search_fields = ('nama',)
    list_display = ('id', 'nama')


class KabupatenAdmin(admin.ModelAdmin):
    search_fields = ('nama', 'provinsi__nama')
    list_display = ('id', 'nama', 'nama_provinsi')

    def nama_provinsi(self, obj):
        return obj.provinsi.nama
    nama_provinsi.short_description = 'provinsi'
    nama_provinsi.admin_order_field = 'provinsi__nama'


class KecamatanAdmin(admin.ModelAdmin):
    search_fields = ('nama', 'kabupaten__nama')
    list_display = ('id', 'nama', 'nama_kabupaten')

    def nama_kabupaten(self, obj):
        return obj.kabupaten.nama
    nama_kabupaten.short_description = 'kabupaten'
    nama_kabupaten.admin_order_field = 'kabupaten__nama'


class DesaAdmin(admin.ModelAdmin):
    search_fields = ('nama', 'kecamatan__nama')
    list_display = ('id', 'nama', 'nama_kecamatan')

    def nama_kecamatan(self, obj):
        return obj.kecamatan.nama
    nama_kecamatan.short_description = 'kecamatan'
    nama_kecamatan.admin_order_field = 'kecamatan__nama'


admin.site.register(Provinsi, ProvinsiAdmin)
admin.site.register(Kabupaten, KabupatenAdmin)
admin.site.register(Kecamatan, KecamatanAdmin)
admin.site.register(Desa, DesaAdmin)
