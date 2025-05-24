from django.shortcuts import render
from wilayah_indonesia.models import Provinsi, Kabupaten, Kecamatan, Desa
from django.http import JsonResponse
from django.views import View
from django.views.generic.detail import DetailView


class ProvinsiListView(View):
    model = Provinsi
    
    def get(self, request):
        queryset = self.get_queryset(request)
        data = self.get_response_data(queryset)
        return JsonResponse({'data': data})

    def get_queryset(self, request, **filters):
        if filters:
            queryset = self.model.objects.filter(**filters)
        else:
            queryset = self.model.objects.all()
        search_query = request.GET.get('search')
        if search_query:
            queryset = queryset.filter(nama__icontains=search_query)
        return queryset
    
    def get_response_data(self, queryset):
        return [{'value': value.pk, 'name': value.nama} for value in queryset]


class KabupatenListView(ProvinsiListView):
    model = Kabupaten
    
    def get(self, request, provinsi_id):
        queryset = self.get_queryset(request, provinsi_id=provinsi_id)
        data = self.get_response_data(queryset)
        return JsonResponse({'data': data})
    

class KecamatanListView(ProvinsiListView):
    model = Kecamatan
    
    def get(self, request, kabupaten_id):
        queryset = self.get_queryset(request, kabupaten_id=kabupaten_id)
        data = self.get_response_data(queryset)
        return JsonResponse({'data': data})


class DesaListView(ProvinsiListView):
    model = Desa
    
    def get(self, request, kecamatan_id):
        queryset = self.get_queryset(request, kecamatan_id=kecamatan_id)
        data = self.get_response_data(queryset)
        return JsonResponse({'data': data})
    

class ProvinsiDetailView(DetailView):
    model = Provinsi

    def get(self, request, *args, **kwargs):
        try:
            data = self.get_response_data()
            return JsonResponse(data)
        except self.model.DoesNotExist:
            return JsonResponse({'error': 'Data not found'}, status=404)
    
    def get_response_data(self):
        obj = self.get_object()
        return {'id': obj.pk, 'name': obj.nama}


class KabupatenDetailView(ProvinsiDetailView):
    model = Kabupaten


class KecamatanDetailView(ProvinsiDetailView):
    model = Kecamatan
    

class DesaDetailView(ProvinsiDetailView):
    model = Desa
