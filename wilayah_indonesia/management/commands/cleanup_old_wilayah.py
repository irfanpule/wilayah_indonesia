import sys
from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps
from django.db.models import Count, Q

from wilayah_indonesia.models import Provinsi, Kabupaten, Kecamatan, Desa


def progress(count, total, suffix=''):
    """Progress bar untuk menampilkan proses"""
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()


class Command(BaseCommand):
    help = 'Hapus data wilayah lama yang sudah tidak direferensi oleh model lain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Tampilkan data yang akan dihapus tanpa benar-benar menghapus'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Paksa hapus tanpa konfirmasi'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode DRY-RUN: Tidak ada data yang akan dihapus\n'))
        
        self.stdout.write(self.style.SUCCESS('=== MENCARI DATA WILAYAH YANG TIDAK DIREFERENSI ===\n'))
        
        # Cari semua model yang berelasi dengan wilayah
        wilayah_references = self.find_wilayah_references()
        
        # Cari data yang tidak direferensi
        orphaned_data = self.find_orphaned_data(wilayah_references)
        
        # Tampilkan hasil
        total_orphaned = sum(len(data) for data in orphaned_data.values())
        
        if total_orphaned == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ Tidak ada data wilayah yang perlu dihapus!'))
            return
        
        self.stdout.write(self.style.WARNING(f'\n=== DITEMUKAN {total_orphaned} DATA TIDAK DIREFERENSI ===\n'))
        
        for tipe, data_list in orphaned_data.items():
            if data_list:
                self.stdout.write(f"\n{tipe.upper()} ({len(data_list)} data):")
                # Tampilkan 10 pertama
                for item in data_list[:10]:
                    self.stdout.write(f"  - ID {item['id']}: {item['nama']}")
                if len(data_list) > 10:
                    self.stdout.write(f"  ... dan {len(data_list) - 10} lainnya")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN] Data tidak akan dihapus'))
            return
        
        # Konfirmasi
        if not force:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Anda akan menghapus {total_orphaned} data wilayah!'))
            confirm = input('Ketik "yes" untuk konfirmasi: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Dibatalkan'))
                return
        
        # Hapus data
        self.delete_orphaned_data(orphaned_data)
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Berhasil menghapus {total_orphaned} data wilayah'))
    
    def find_wilayah_references(self):
        """
        Cari semua model yang punya foreign key ke Provinsi, Kabupaten, Kecamatan, Desa
        dan kumpulkan ID yang direferensi
        """
        references = {
            'provinsi': set(),
            'kabupaten': set(),
            'kecamatan': set(),
            'desa': set()
        }
        
        wilayah_models = {
            'provinsi': Provinsi,
            'kabupaten': Kabupaten,
            'kecamatan': Kecamatan,
            'desa': Desa
        }
        
        self.stdout.write('Scanning model yang berelasi dengan wilayah...\n')
        
        for app_config in apps.get_app_configs():
            # Skip app wilayah_indonesia sendiri
            if app_config.label == 'wilayah_indonesia':
                continue
            
            for model in app_config.get_models():
                # Cek setiap field
                for field in model._meta.get_fields():
                    if hasattr(field, 'related_model') and field.related_model:
                        for tipe, wilayah_model in wilayah_models.items():
                            if field.related_model == wilayah_model:
                                # Ambil semua ID yang direferensi
                                field_name = f"{field.name}_id"
                                ids = model.objects.filter(
                                    **{f"{field.name}__isnull": False}
                                ).values_list(field_name, flat=True).distinct()
                                
                                references[tipe].update(ids)
                                
                                if ids:
                                    self.stdout.write(
                                        f"  ✓ {app_config.label}.{model.__name__}.{field.name} "
                                        f"→ {len(ids)} {tipe} direferensi"
                                    )
        
        # Tambahkan referensi internal (parent-child relationship)
        # Kabupaten → Provinsi
        prov_ids = Kabupaten.objects.values_list('provinsi_id', flat=True).distinct()
        references['provinsi'].update(prov_ids)
        
        # Kecamatan → Kabupaten
        kab_ids = Kecamatan.objects.values_list('kabupaten_id', flat=True).distinct()
        references['kabupaten'].update(kab_ids)
        
        # Desa → Kecamatan
        kec_ids = Desa.objects.values_list('kecamatan_id', flat=True).distinct()
        references['kecamatan'].update(kec_ids)
        
        self.stdout.write(f"\n  Internal: Provinsi={len(prov_ids)}, Kabupaten={len(kab_ids)}, Kecamatan={len(kec_ids)}")
        
        return references
    
    def find_orphaned_data(self, references):
        """Cari data yang tidak direferensi"""
        orphaned = {
            'provinsi': [],
            'kabupaten': [],
            'kecamatan': [],
            'desa': []
        }
        
        # Provinsi yang tidak direferensi
        provinsi_list = Provinsi.objects.exclude(id__in=references['provinsi'])
        orphaned['provinsi'] = [
            {'id': p.id, 'nama': p.nama} for p in provinsi_list
        ]
        
        # Kabupaten yang tidak direferensi
        kabupaten_list = Kabupaten.objects.exclude(id__in=references['kabupaten'])
        orphaned['kabupaten'] = [
            {'id': k.id, 'nama': k.nama} for k in kabupaten_list
        ]
        
        # Kecamatan yang tidak direferensi
        kecamatan_list = Kecamatan.objects.exclude(id__in=references['kecamatan'])
        orphaned['kecamatan'] = [
            {'id': k.id, 'nama': k.nama} for k in kecamatan_list
        ]
        
        # Desa yang tidak direferensi
        desa_list = Desa.objects.exclude(id__in=references['desa'])
        orphaned['desa'] = [
            {'id': d.id, 'nama': d.nama} for d in desa_list
        ]
        
        return orphaned
    
    def delete_orphaned_data(self, orphaned_data):
        """Hapus data yang tidak direferensi menggunakan batch untuk menghindari SQL variable limit"""
        stats = {
            'provinsi': 0,
            'kabupaten': 0,
            'kecamatan': 0,
            'desa': 0
        }
        
        # SQLite limit: 999 variables, gunakan batch 500 untuk safety
        BATCH_SIZE = 500
        
        with transaction.atomic():
            # Hapus dari bawah ke atas (Desa → Kecamatan → Kabupaten → Provinsi)
            
            # Hapus Desa
            if orphaned_data['desa']:
                ids = [d['id'] for d in orphaned_data['desa']]
                total = len(ids)
                deleted_count = 0
                
                self.stdout.write(f'\n  Menghapus {total} Desa...')
                for i in range(0, total, BATCH_SIZE):
                    batch_ids = ids[i:i + BATCH_SIZE]
                    deleted = Desa.objects.filter(id__in=batch_ids).delete()
                    deleted_count += deleted[0]
                    progress(i + len(batch_ids), total, suffix='Desa')
                
                stats['desa'] = deleted_count
                print()  # New line after progress
                self.stdout.write(f'  ✓ Desa: {stats["desa"]} data dihapus')
            
            # Hapus Kecamatan
            if orphaned_data['kecamatan']:
                ids = [k['id'] for k in orphaned_data['kecamatan']]
                total = len(ids)
                deleted_count = 0
                
                self.stdout.write(f'  Menghapus {total} Kecamatan...')
                for i in range(0, total, BATCH_SIZE):
                    batch_ids = ids[i:i + BATCH_SIZE]
                    deleted = Kecamatan.objects.filter(id__in=batch_ids).delete()
                    deleted_count += deleted[0]
                    progress(i + len(batch_ids), total, suffix='Kecamatan')
                
                stats['kecamatan'] = deleted_count
                print()
                self.stdout.write(f'  ✓ Kecamatan: {stats["kecamatan"]} data dihapus')
            
            # Hapus Kabupaten
            if orphaned_data['kabupaten']:
                ids = [k['id'] for k in orphaned_data['kabupaten']]
                total = len(ids)
                deleted_count = 0
                
                self.stdout.write(f'  Menghapus {total} Kabupaten...')
                for i in range(0, total, BATCH_SIZE):
                    batch_ids = ids[i:i + BATCH_SIZE]
                    deleted = Kabupaten.objects.filter(id__in=batch_ids).delete()
                    deleted_count += deleted[0]
                    progress(i + len(batch_ids), total, suffix='Kabupaten')
                
                stats['kabupaten'] = deleted_count
                print()
                self.stdout.write(f'  ✓ Kabupaten: {stats["kabupaten"]} data dihapus')
            
            # Hapus Provinsi
            if orphaned_data['provinsi']:
                ids = [p['id'] for p in orphaned_data['provinsi']]
                total = len(ids)
                deleted_count = 0
                
                self.stdout.write(f'  Menghapus {total} Provinsi...')
                for i in range(0, total, BATCH_SIZE):
                    batch_ids = ids[i:i + BATCH_SIZE]
                    deleted = Provinsi.objects.filter(id__in=batch_ids).delete()
                    deleted_count += deleted[0]
                    progress(i + len(batch_ids), total, suffix='Provinsi')
                
                stats['provinsi'] = deleted_count
                print()
                self.stdout.write(f'  ✓ Provinsi: {stats["provinsi"]} data dihapus')
