from django.urls import path
from . import views

app_name = 'wilayah_indonesia'


urlpatterns = [
    path('provinsi/', views.ProvinsiListView.as_view(), name='provinsi-list'),
    path('provinsi/detail/<int:pk>/', views.ProvinsiDetailView.as_view(), name='provinsi-detail'),
    path('kabupaten/<int:provinsi_id>/', views.KabupatenListView.as_view(), name='kabupaten-list'),
    path('kabupaten/detail/<int:pk>/', views.KabupatenDetailView.as_view(), name='kabupaten-detail'),
    path('kecamatan/<int:kabupaten_id>/', views.KecamatanListView.as_view(), name='kecamatan-list'),
    path('kecamatan/detail/<int:pk>/', views.KecamatanDetailView.as_view(), name='kecamatan-detail'),
    path('desa/<int:kecamatan_id>/', views.DesaListView.as_view(), name='desa-list'),
    path('desa/detail/<int:pk>/', views.DesaDetailView.as_view(), name='desa-detail'),
]
