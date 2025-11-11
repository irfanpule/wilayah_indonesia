import csv
import sys
import importlib.resources as resources

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from wilayah_indonesia.models import Provinsi, Kabupaten, Kecamatan, Desa


def progress(count, total, suffix=''):
    """
    Progress bar untuk menampilkan proses import
    """
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()


class Command(BaseCommand):
    help = 'Import data wilayah Indonesia dari file base.csv dengan format ID dan Nama'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='base.csv',
            help='Nama file CSV yang akan diimport (default: base.csv)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Hapus semua data wilayah sebelum import'
        )

    def handle(self, *args, **options):
        filename = options['file']
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Menghapus semua data wilayah...'))
            self.clear_data_batch()
            self.stdout.write(self.style.SUCCESS('Semua data wilayah berhasil dihapus'))

        self.stdout.write(self.style.SUCCESS(f'Memulai import dari {filename}...'))
        
        try:
            with resources.open_text("wilayah_indonesia.csv", filename) as csv_file:
                self.process_csv(csv_file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File {filename} tidak ditemukan'))
            raise CommandError(f'File {filename} tidak ditemukan di wilayah_indonesia/csv/')

    def process_csv(self, csv_file):
        """
        Memproses file CSV dan mengkategorikan data berdasarkan panjang ID
        Import dilakukan dalam 2 pass:
        - Pass 1: Provinsi, Kabupaten, Kecamatan
        - Pass 2: Desa (setelah semua Kecamatan tersedia)
        """
        reader = csv.reader(csv_file, delimiter=",")
        
        # Hitung total baris
        rows = list(reader)
        total_rows = len(rows)
        
        # Counter untuk setiap jenis wilayah
        stats = {
            'provinsi': 0,
            'kabupaten': 0,
            'kecamatan': 0,
            'desa': 0,
            'error': 0
        }
        
        # Temporary storage untuk batch insert
        provinsi_cache = {}
        kabupaten_cache = {}
        kecamatan_cache = {}
        
        # Simpan data desa untuk diproses di pass kedua
        desa_data = []
        
        self.stdout.write(self.style.SUCCESS('\n=== PASS 1: Import Provinsi, Kabupaten, Kecamatan ==='))
        
        with transaction.atomic():
            for idx, row in enumerate(rows, 1):
                try:
                    if len(row) < 2:
                        continue
                    
                    raw_id = row[0].strip()
                    nama = row[1].strip()
                    
                    # Hapus titik dari ID untuk menghitung digit
                    clean_id = raw_id.replace('.', '')
                    digit_count = len(clean_id)
                    
                    # Kategori berdasarkan jumlah digit
                    if digit_count == 2:
                        # Provinsi
                        provinsi, created = Provinsi.objects.update_or_create(
                            id=clean_id,
                            defaults={'nama': nama}
                        )
                        provinsi_cache[clean_id] = provinsi
                        stats['provinsi'] += 1
                        progress(idx, total_rows, suffix='Provinsi')
                        
                    elif digit_count == 4:
                        # Kabupaten
                        provinsi_id = clean_id[:2]
                        
                        if provinsi_id not in provinsi_cache:
                            try:
                                provinsi_cache[provinsi_id] = Provinsi.objects.get(id=provinsi_id)
                            except Provinsi.DoesNotExist:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f'\nProvinsi dengan ID {provinsi_id} tidak ditemukan untuk Kabupaten {nama}'
                                    )
                                )
                                stats['error'] += 1
                                continue
                        
                        kabupaten, created = Kabupaten.objects.update_or_create(
                            id=clean_id,
                            defaults={
                                'nama': nama,
                                'provinsi': provinsi_cache[provinsi_id]
                            }
                        )
                        kabupaten_cache[clean_id] = kabupaten
                        stats['kabupaten'] += 1
                        progress(idx, total_rows, suffix='Kabupaten')
                        
                    elif digit_count == 6:
                        # Kecamatan
                        kabupaten_id = clean_id[:4]
                        
                        if kabupaten_id not in kabupaten_cache:
                            try:
                                kabupaten_cache[kabupaten_id] = Kabupaten.objects.get(id=kabupaten_id)
                            except Kabupaten.DoesNotExist:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f'\nKabupaten dengan ID {kabupaten_id} tidak ditemukan untuk Kecamatan {nama}'
                                    )
                                )
                                stats['error'] += 1
                                continue
                        
                        kecamatan, created = Kecamatan.objects.update_or_create(
                            id=clean_id,
                            defaults={
                                'nama': nama,
                                'kabupaten': kabupaten_cache[kabupaten_id]
                            }
                        )
                        kecamatan_cache[clean_id] = kecamatan
                        stats['kecamatan'] += 1
                        progress(idx, total_rows, suffix='Kecamatan')
                        
                    elif digit_count >= 10:
                        # Simpan data desa untuk diproses nanti
                        desa_data.append({
                            'id': clean_id,
                            'nama': nama,
                            'kecamatan_id': clean_id[:6],
                            'raw_id': raw_id  # Simpan raw_id untuk mapping
                        })
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'\nID {raw_id} dengan {digit_count} digit tidak dikenali'
                            )
                        )
                        stats['error'] += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'\nError pada baris {idx}: {str(e)}')
                    )
                    stats['error'] += 1
                    continue
        
        # Pass 2: Import Desa setelah semua Kecamatan sudah tersedia
        print()  # New line setelah progress bar
        self.stdout.write(self.style.SUCCESS('\n=== PASS 2: Import Desa ==='))
        
        total_desa = len(desa_data)
        with transaction.atomic():
            for idx, desa in enumerate(desa_data, 1):
                try:
                    kecamatan_id = desa['kecamatan_id']
                    
                    # Load kecamatan dari cache atau database
                    if kecamatan_id not in kecamatan_cache:
                        try:
                            kecamatan_cache[kecamatan_id] = Kecamatan.objects.get(id=kecamatan_id)
                        except Kecamatan.DoesNotExist:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'\nKecamatan dengan ID {kecamatan_id} tidak ditemukan untuk Desa {desa["nama"]}'
                                )
                            )
                            stats['error'] += 1
                            continue
                    
                    Desa.objects.update_or_create(
                        id=desa['id'],
                        defaults={
                            'nama': desa['nama'],
                            'kecamatan': kecamatan_cache[kecamatan_id]
                        }
                    )
                    stats['desa'] += 1
                    progress(idx, total_desa, suffix='Desa')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'\nError pada desa {desa["nama"]}: {str(e)}')
                    )
                    stats['error'] += 1
                    continue
        
        # Print hasil
        print()  # New line setelah progress bar
        self.stdout.write(self.style.SUCCESS('\n=== HASIL IMPORT ==='))
        self.stdout.write(self.style.SUCCESS(f"✓ Provinsi  : {stats['provinsi']} data"))
        self.stdout.write(self.style.SUCCESS(f"✓ Kabupaten : {stats['kabupaten']} data"))
        self.stdout.write(self.style.SUCCESS(f"✓ Kecamatan : {stats['kecamatan']} data"))
        self.stdout.write(self.style.SUCCESS(f"✓ Desa      : {stats['desa']} data"))
        if stats['error'] > 0:
            self.stdout.write(self.style.WARNING(f"⚠ Error     : {stats['error']} data"))
        self.stdout.write(self.style.SUCCESS(f"\nTotal berhasil diimport: {sum([stats['provinsi'], stats['kabupaten'], stats['kecamatan'], stats['desa']])} data"))

    def clear_data_batch(self, batch_size=500):
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
