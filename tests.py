from django.test import TestCase
from django.db import connection

from .models import Provinsi


class TestQuery(TestCase):

    def test_query(self):
        Provinsi.objects.all()
        self.assertEqual(len(connection.queries), 1)
