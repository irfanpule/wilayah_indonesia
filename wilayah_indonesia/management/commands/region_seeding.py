import os
import csv
import sys
import importlib.resources as resources

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from wilayah_indonesia import apps
from wilayah_indonesia.models import Provinsi, Kabupaten, Kecamatan, Desa


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

    def add_arguments(self, parser):
        parser.add_argument('--provinsi', action='store_true', help='hanya menambahkan data provinsi')
        parser.add_argument('--kabupaten', action='store_true', help='hanya menambahkan data kabupaten')
        parser.add_argument('--kecamatan', action='store_true', help='hanya menambahkan data kecamatan')
        parser.add_argument('--desa', action='store_true', help='hanya menambahkan data desa')
        parser.add_argument('--delete', action='store_true', help='hapus semua data wilayah')

    def handle(self, *args, **options):
        if options['delete']:
            self.delete_all_data_batch()
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
        with resources.open_text("wilayah_indonesia.csv", f"{region.lower()}.csv") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")
            row_count = len(list(reader))
            counter = 0
            csv_file.seek(0)
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

    def delete_all_data_batch(self, batch_size=500):
        """
        Menghapus semua data wilayah secara batch untuk menghindari SQLite variable limit
        """
        # Hapus Desa dalam batch
        self.stdout.write('Menghapus data Desa...')
        desa_count = 0
        while True:
            batch = list(Desa.objects.all()[:batch_size])
            if not batch:
                break
            Desa.objects.filter(id__in=[obj.id for obj in batch]).delete()
            desa_count += len(batch)
            progress(desa_count, desa_count + batch_size, suffix=f"Desa ({desa_count})")
        
        # Hapus Kecamatan dalam batch
        self.stdout.write('\nMenghapus data Kecamatan...')
        kecamatan_count = 0
        while True:
            batch = list(Kecamatan.objects.all()[:batch_size])
            if not batch:
                break
            Kecamatan.objects.filter(id__in=[obj.id for obj in batch]).delete()
            kecamatan_count += len(batch)
            progress(kecamatan_count, kecamatan_count + batch_size, suffix=f"Kecamatan ({kecamatan_count})")
        
        # Hapus Kabupaten dalam batch
        self.stdout.write('\nMenghapus data Kabupaten...')
        kabupaten_count = 0
        while True:
            batch = list(Kabupaten.objects.all()[:batch_size])
            if not batch:
                break
            Kabupaten.objects.filter(id__in=[obj.id for obj in batch]).delete()
            kabupaten_count += len(batch)
            progress(kabupaten_count, kabupaten_count + batch_size, suffix=f"Kabupaten ({kabupaten_count})")
        
        # Hapus Provinsi dalam batch
        self.stdout.write('\nMenghapus data Provinsi...')
        provinsi_count = 0
        while True:
            batch = list(Provinsi.objects.all()[:batch_size])
            if not batch:
                break
            Provinsi.objects.filter(id__in=[obj.id for obj in batch]).delete()
            provinsi_count += len(batch)
            progress(provinsi_count, provinsi_count + batch_size, suffix=f"Provinsi ({provinsi_count})")
        
        print()  # New line setelah progress bar
        self.stdout.write(self.style.SUCCESS("Sukses hapus semua data wilayah"))
