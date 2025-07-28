import os
import csv
import sys

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from wilayah_indonesia.wilayah_indonesia import apps
from wilayah_indonesia.wilayah_indonesia.models import Provinsi, Kabupaten, Kecamatan, Desa


def progress(count, total, suffix=''):
    """
    get example from https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
    """
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()

class Command(BaseCommand):
    help = 'Menambahkan semua data wilayah yang ada di Indonesia'

    CSV_DIR = os.path.join(apps.WilayahIndonesiaConfig.name, 'csv')

    def add_arguments(self, parser):
        parser.add_argument('--provinsi', action='store_true', help='hanya menambahkan data provinsi')
        parser.add_argument('--kabupaten', action='store_true', help='hanya menambahkan data kabupaten')
        parser.add_argument('--kecamatan', action='store_true', help='hanya menambahkan data kecamatan')
        parser.add_argument('--desa', action='store_true', help='hanya menambahkan data desa')
        parser.add_argument('--delete', action='store_true', help='hapus semua data wilayah')

    def handle(self, *args, **options):
        if options['delete']:
            Provinsi.objects.all().delete()
            progress(1, 3, suffix="Hapus data")
            Kabupaten.objects.all().delete()
            progress(2, 3, suffix="Hapus data")
            Kecamatan.objects.all().delete()
            progress(3, 3, suffix="Hapus data")
            self.stdout.write(self.style.SUCCESS("Sukses hapus semua data wilayah"))
            return

        if options['provinsi']:
            self.seeding('provinces')
            return
        elif options['kabupaten']:
            self.seeding('regencies')
            return
        elif options['kecamatan']:
            self.seeding('districts')
            return
        elif options['desa']:
            self.seeding('villages')
            return
        else:
            self.seeding('provinces')
            self.seeding('regencies')
            self.seeding('districts')
            self.seeding('villages')
            return

    def seeding(self, region):
        file = open(self.CSV_DIR + f'/{region.lower()}.csv', 'r')
        reader = csv.reader(file, delimiter=",")
        row_count = len(list(reader))
        counter = 0
        file.seek(0)
        for row in reader:
            progress(counter, row_count, suffix=region.title())
            counter = counter + 1
            self.query(row, region)
        self.stdout.write(self.style.SUCCESS(f"Sukses menambahkan {counter} data"))

    def query(self, row, region):
        message = "Data {0} kosong, kamu harus menambahkan data {0} terlebih dahulu"
        if region == 'provinces':
            Provinsi.objects.update_or_create(id=row[0], defaults={"nama": row[1]})
        elif region == 'regencies':
            try:
                Kabupaten.objects.update_or_create(id=row[0], provinsi_id=row[1], defaults={"nama": row[2]})
            except IntegrityError:
                raise CommandError(message.format('provinsi'))
        elif region == 'districts':
            try:
                Kecamatan.objects.update_or_create(id=row[0], kabupaten_id=row[1], defaults={"nama": row[2]})
            except IntegrityError:
                raise CommandError(message.format('kabupaten'))
        elif region == 'villages':
            try:
                Desa.objects.update_or_create(id=row[0], kecamatan_id=row[1], defaults={"nama": row[2]})
            except IntegrityError:
                raise CommandError(message.format('desa'))
