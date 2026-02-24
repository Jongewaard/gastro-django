"""
Exporta todos los datos del negocio a un archivo Excel.
Uso: python manage.py export_xlsx [--days 30] [--output ruta.xlsx]
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Tenant
from backups.export_xlsx import generate_export


class Command(BaseCommand):
    help = 'Exporta datos del negocio a un archivo Excel (.xlsx)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Solo exportar datos de los ultimos N dias (default: todo)',
        )
        parser.add_argument(
            '--output', '-o',
            type=str,
            default=None,
            help='Ruta del archivo de salida (default: backups/export_FECHA.xlsx)',
        )

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(is_active=True).first()
        if not tenant:
            self.stderr.write(self.style.ERROR('No hay ningun negocio activo.'))
            return

        days = options['days']
        output_path = options['output']

        self.stdout.write(f'Exportando datos de "{tenant.name}"...')
        if days:
            self.stdout.write(f'  Periodo: ultimos {days} dias')

        wb = generate_export(tenant, days=days)

        if not output_path:
            backup_dir = Path(settings.BASE_DIR) / 'backups'
            backup_dir.mkdir(exist_ok=True)
            today = timezone.localdate().strftime('%Y-%m-%d')
            output_path = str(backup_dir / f'export_{today}.xlsx')

        wb.save(output_path)
        self.stdout.write(self.style.SUCCESS(f'Excel exportado: {output_path}'))
