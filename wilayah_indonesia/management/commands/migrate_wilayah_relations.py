import sys
import csv
import importlib.resources as resources
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.apps import apps
from django.db.models import ForeignKey, Q

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
    help = 'Migrasi relasi wilayah di model-model lain dengan matching dari CSV lama ke database baru'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Nama app yang akan dimigrasi (contoh: accounts, profiles)'
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Nama model yang akan dimigrasi (contoh: Profile, UserAddress)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Jalankan tanpa menyimpan perubahan (untuk testing)'
        )
        parser.add_argument(
            '--auto-discover',
            action='store_true',
            help='Otomatis cari semua model yang punya relasi ke wilayah'
        )
        parser.add_argument(
            '--csv-dir',
            type=str,
            default='wilayah_indonesia.csv',
            help='Direktori CSV lama (default: wilayah_indonesia.csv dalam package)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        csv_dir = options['csv_dir']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode DRY-RUN: Tidak ada data yang akan diubah\n'))
        
        # Load mapping dari CSV lama
        self.stdout.write(self.style.SUCCESS('=== LOADING CSV LAMA ==='))
        try:
            self.old_data = self.load_old_csv_data(csv_dir)
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Provinsi  : {len(self.old_data['provinsi'])} data\n"
                    f"✓ Kabupaten : {len(self.old_data['kabupaten'])} data\n"
                    f"✓ Kecamatan : {len(self.old_data['kecamatan'])} data\n"
                    f"✓ Desa      : {len(self.old_data['desa'])} data\n"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error loading CSV: {str(e)}\n'
                    'Pastikan file CSV lama tersedia di wilayah_indonesia/csv/'
                )
            )
            return
        
        # Build mapping cache: old_id -> new_id
        self.stdout.write(self.style.SUCCESS('=== BUILDING MAPPING (old_id → new_id) ==='))
        self.id_mapping = self.build_id_mapping()
        
        total_mapped = sum(len(m) for m in self.id_mapping.values())
        self.stdout.write(self.style.SUCCESS(f'✓ Total {total_mapped} mapping berhasil dibuat\n'))
        
        if options['auto_discover']:
            self.auto_discover_and_migrate(dry_run)
        elif options['app'] and options['model']:
            self.migrate_specific_model(options['app'], options['model'], dry_run)
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Gunakan --auto-discover untuk otomatis cari model, atau '
                    'spesifikasi --app dan --model untuk model tertentu'
                )
            )

    def load_old_csv_data(self, csv_dir):
        """Load data dari CSV lama ke memory"""
        old_data = {
            'provinsi': {},  # old_id -> nama
            'kabupaten': {},  # old_id -> (nama, provinsi_id)
            'kecamatan': {},  # old_id -> (nama, kabupaten_id)
            'desa': {}  # old_id -> (nama, kecamatan_id)
        }
        
        # Load provinces.csv
        with resources.open_text(csv_dir, "provinces.csv") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    old_data['provinsi'][row[0]] = row[1]
        
        # Load regencies.csv
        with resources.open_text(csv_dir, "regencies.csv") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    old_data['kabupaten'][row[0]] = (row[2], row[1])  # (nama, provinsi_id)
        
        # Load districts.csv
        with resources.open_text(csv_dir, "districts.csv") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    old_data['kecamatan'][row[0]] = (row[2], row[1])  # (nama, kabupaten_id)
        
        # Load villages.csv
        with resources.open_text(csv_dir, "villages.csv") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    old_data['desa'][row[0]] = (row[2], row[1])  # (nama, kecamatan_id)
        
        return old_data
    
    def build_id_mapping(self):
        """
        Build mapping dari old_id ke new_id berdasarkan nama
        Matching: old CSV -> query database baru by nama
        """
        mapping = {
            'provinsi': {},
            'kabupaten': {},
            'kecamatan': {},
            'desa': {}
        }
        
        stats = {
            'provinsi': {'matched': 0, 'unmatched': 0},
            'kabupaten': {'matched': 0, 'unmatched': 0},
            'kecamatan': {'matched': 0, 'unmatched': 0},
            'desa': {'matched': 0, 'unmatched': 0}
        }
        
        # Mapping Provinsi
        for old_id, nama in self.old_data['provinsi'].items():
            try:
                provinsi = Provinsi.objects.get(nama__iexact=nama)
                mapping['provinsi'][old_id] = str(provinsi.id)
                stats['provinsi']['matched'] += 1
            except Provinsi.DoesNotExist:
                stats['provinsi']['unmatched'] += 1
            except Provinsi.MultipleObjectsReturned:
                # Ambil yang pertama
                provinsi = Provinsi.objects.filter(nama__iexact=nama).first()
                mapping['provinsi'][old_id] = str(provinsi.id)
                stats['provinsi']['matched'] += 1
        
        # Mapping Kabupaten
        for old_id, (nama, old_prov_id) in self.old_data['kabupaten'].items():
            try:
                # Normalize nama kabupaten untuk matching yang lebih baik
                nama_normalized = nama.replace('KABUPATEN ', '').replace('KAB. ', '').replace('KOTA ', '').strip()
                
                query = Q(nama__icontains=nama_normalized)
                
                # Jika provinsi parent bisa dimapping, gunakan untuk filter lebih spesifik
                if old_prov_id in mapping['provinsi']:
                    query &= Q(provinsi_id=mapping['provinsi'][old_prov_id])
                
                kabupaten = Kabupaten.objects.filter(query).first()
                if kabupaten:
                    mapping['kabupaten'][old_id] = str(kabupaten.id)
                    stats['kabupaten']['matched'] += 1
                else:
                    # Try exact match
                    kabupaten = Kabupaten.objects.filter(nama__iexact=nama).first()
                    if kabupaten:
                        mapping['kabupaten'][old_id] = str(kabupaten.id)
                        stats['kabupaten']['matched'] += 1
                    else:
                        stats['kabupaten']['unmatched'] += 1
            except Exception:
                stats['kabupaten']['unmatched'] += 1
        
        # Mapping Kecamatan
        for old_id, (nama, old_kab_id) in self.old_data['kecamatan'].items():
            try:
                query = Q(nama__iexact=nama)
                
                # Gunakan parent kabupaten untuk filter
                if old_kab_id in mapping['kabupaten']:
                    query &= Q(kabupaten_id=mapping['kabupaten'][old_kab_id])
                
                kecamatan = Kecamatan.objects.filter(query).first()
                if kecamatan:
                    mapping['kecamatan'][old_id] = str(kecamatan.id)
                    stats['kecamatan']['matched'] += 1
                else:
                    # Try without parent
                    kecamatan = Kecamatan.objects.filter(nama__iexact=nama).first()
                    if kecamatan:
                        mapping['kecamatan'][old_id] = str(kecamatan.id)
                        stats['kecamatan']['matched'] += 1
                    else:
                        stats['kecamatan']['unmatched'] += 1
            except Exception:
                stats['kecamatan']['unmatched'] += 1
        
        # Mapping Desa
        for old_id, (nama, old_kec_id) in self.old_data['desa'].items():
            try:
                query = Q(nama__iexact=nama)
                
                # Gunakan parent kecamatan untuk filter
                if old_kec_id in mapping['kecamatan']:
                    query &= Q(kecamatan_id=mapping['kecamatan'][old_kec_id])
                
                desa = Desa.objects.filter(query).first()
                if desa:
                    mapping['desa'][old_id] = str(desa.id)
                    stats['desa']['matched'] += 1
                else:
                    # Try without parent
                    desa = Desa.objects.filter(nama__iexact=nama).first()
                    if desa:
                        mapping['desa'][old_id] = str(desa.id)
                        stats['desa']['matched'] += 1
                    else:
                        stats['desa']['unmatched'] += 1
            except Exception:
                stats['desa']['unmatched'] += 1
        
        # Print statistics
        for tipe, stat in stats.items():
            matched = stat['matched']
            unmatched = stat['unmatched']
            total = matched + unmatched
            if total > 0:
                pct = (matched / total * 100) if total > 0 else 0
                status = '✓' if unmatched == 0 else '⚠️'
                self.stdout.write(
                    f"  {status} {tipe.capitalize():12} : {matched}/{total} matched ({pct:.1f}%)"
                )
        
        return mapping
    
    def auto_discover_and_migrate(self, dry_run):
        """Otomatis cari dan migrasi semua model yang punya relasi ke wilayah"""
        self.stdout.write(self.style.SUCCESS('\n=== MENCARI MODEL DENGAN RELASI WILAYAH ===\n'))
        
        wilayah_models = [Provinsi, Kabupaten, Kecamatan, Desa]
        models_to_migrate = []
        
        for app_config in apps.get_app_configs():
            # Skip app wilayah_indonesia sendiri
            if app_config.label == 'wilayah_indonesia':
                continue
                
            for model in app_config.get_models():
                # Cek apakah model punya foreign key ke model wilayah
                has_wilayah_relation = False
                fields_info = []
                
                for field in model._meta.get_fields():
                    if isinstance(field, ForeignKey):
                        if field.related_model in wilayah_models:
                            has_wilayah_relation = True
                            fields_info.append({
                                'field_name': field.name,
                                'model': field.related_model.__name__
                            })
                
                if has_wilayah_relation:
                    models_to_migrate.append({
                        'app': app_config.label,
                        'model': model.__name__,
                        'model_class': model,
                        'fields': fields_info
                    })
                    
                    self.stdout.write(
                        f"  ✓ {app_config.label}.{model.__name__}"
                    )
                    for field_info in fields_info:
                        self.stdout.write(
                            f"    - {field_info['field_name']} → {field_info['model']}"
                        )
        
        if not models_to_migrate:
            self.stdout.write(self.style.WARNING('\nTidak ada model dengan relasi wilayah ditemukan'))
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'\n=== DITEMUKAN {len(models_to_migrate)} MODEL ===\n')
        )
        
        # Migrasi setiap model
        for model_info in models_to_migrate:
            self.migrate_model(model_info, dry_run)

    def migrate_specific_model(self, app_label, model_name, dry_run):
        """Migrasi model tertentu"""
        try:
            model_class = apps.get_model(app_label, model_name)
        except LookupError:
            raise CommandError(f'Model {app_label}.{model_name} tidak ditemukan')
        
        # Analisa field yang ada
        fields_info = []
        wilayah_models = [Provinsi, Kabupaten, Kecamatan, Desa]
        
        for field in model_class._meta.get_fields():
            if isinstance(field, ForeignKey):
                if field.related_model in wilayah_models:
                    fields_info.append({
                        'field_name': field.name,
                        'model': field.related_model.__name__
                    })
        
        if not fields_info:
            self.stdout.write(
                self.style.WARNING(
                    f'Model {app_label}.{model_name} tidak memiliki relasi ke wilayah'
                )
            )
            return
        
        model_info = {
            'app': app_label,
            'model': model_name,
            'model_class': model_class,
            'fields': fields_info
        }
        
        self.migrate_model(model_info, dry_run)

    def migrate_model(self, model_info, dry_run):
        """Migrasi relasi wilayah untuk satu model"""
        model_class = model_info['model_class']
        model_name = f"{model_info['app']}.{model_info['model']}"
        
        self.stdout.write(
            self.style.SUCCESS(f'\n--- Migrasi {model_name} ---')
        )
        
        # Hitung total records
        total_records = model_class.objects.count()
        if total_records == 0:
            self.stdout.write(self.style.WARNING('  Tidak ada data untuk dimigrasi'))
            return
        
        stats = {
            'total': total_records,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Gunakan mapping yang sudah dibuild dari CSV
        mappings = self.id_mapping
        
        # DEBUG: Print mapping untuk kabupaten
        self.stdout.write(self.style.WARNING('\n  DEBUG: Sample mapping kabupaten:'))
        sample_count = 0
        for old_id, new_id in mappings['kabupaten'].items():
            if sample_count < 10:
                self.stdout.write(f'    {old_id} → {new_id}')
                sample_count += 1
        
        # Proses setiap record
        queryset = model_class.objects.select_related(
            *[f['field_name'] for f in model_info['fields']]
        ).all()
        
        with transaction.atomic():
            for idx, obj in enumerate(queryset, 1):
                try:
                    updated = False
                    updates = []
                    
                    for field_info in model_info['fields']:
                        field_name = field_info['field_name']
                        tipe = field_info['model'].lower()
                        
                        # Dapatkan nilai field saat ini (old_id)
                        old_id = getattr(obj, f"{field_name}_id")
                        
                        if old_id is None:
                            continue
                        
                        old_id_str = str(old_id)
                        
                        # DEBUG: Print current values
                        if field_name == 'kabupaten':
                            self.stdout.write(
                                f'    DEBUG: Record {obj.pk} - {field_name}_id = {old_id_str}'
                            )
                        
                        # Cari new_id di mapping (old_id -> new_id)
                        if old_id_str in mappings[tipe]:
                            new_id = mappings[tipe][old_id_str]
                            
                            if old_id_str != new_id:
                                if not dry_run:
                                    setattr(obj, f"{field_name}_id", new_id)
                                    updated = True
                                    updates.append(f"{field_name}: {old_id_str}→{new_id}")
                                else:
                                    self.stdout.write(
                                        f'  [DRY-RUN] Record {obj.pk}: {field_name}: {old_id_str} → {new_id}'
                                    )
                                    updated = True
                                    updates.append(f"{field_name}: {old_id_str}→{new_id}")
                            else:
                                if field_name == 'kabupaten':
                                    self.stdout.write(
                                        f'    DEBUG: No change needed - {old_id_str} maps to same ID'
                                    )
                        else:
                            if field_name == 'kabupaten':
                                self.stdout.write(
                                    f'    DEBUG: No mapping found for {field_name} ID {old_id_str}'
                                )
                    
                    if updated:
                        if not dry_run:
                            obj.save(update_fields=[f"{f['field_name']}_id" for f in model_info['fields']])
                        stats['updated'] += 1
                    else:
                        stats['skipped'] += 1
                    
                    progress(idx, total_records, suffix=model_info['model'])
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'\n  Error pada record ID {obj.pk}: {str(e)}')
                    )
                    stats['errors'] += 1
                    
                    if not dry_run:
                        transaction.set_rollback(True)
                        raise
        
        # Print hasil
        print()  # New line setelah progress bar
        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Selesai: {stats['updated']} updated, "
                f"{stats['skipped']} skipped, {stats['errors']} errors"
            )
        )
