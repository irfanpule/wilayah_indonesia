from django import forms

from .models import Kabupaten, Kecamatan, Desa, Provinsi
from django_select2.forms import ModelSelect2Widget


def provinsiChained():
    return forms.ModelChoiceField(
        queryset=Provinsi.objects.all(),
        widget=ModelSelect2Widget(
            model=Provinsi,
            search_fields=['nama__icontains'],
        )
    )


def kabupatenChained():
    return forms.ModelChoiceField(
        queryset=Kabupaten.objects.all(),
        widget=ModelSelect2Widget(
            model=Kabupaten,
            search_fields=['nama__icontains'],
            dependent_fields={'provinsi': 'provinsi'},
        )
    )


def kecamatanChained():
    return forms.ModelChoiceField(
        queryset=Kecamatan.objects.all(),
        widget=ModelSelect2Widget(
            model=Kecamatan,
            search_fields=['nama__icontains'],
            dependent_fields={'kabupaten': 'kabupaten'},
        )
    )


def desaChained():
    return forms.ModelChoiceField(
        queryset=Desa.objects.all(),
        widget=ModelSelect2Widget(
            model=Desa,
            search_fields=['nama__icontains'],
            dependent_fields={'kecamatan': 'kecamatan'},
        )
    )
