from django.core.management.base import BaseCommand

from backups.models import BackupRecord
from backups.utils import restore_backup


class Command(BaseCommand):
    help = 'Restore the database from a backup'

    def add_arguments(self, parser):
        parser.add_argument(
            'record_id',
            type=int,
            help='ID del registro de backup a restaurar',
        )

    def handle(self, *args, **options):
        record_id = options['record_id']
        record = BackupRecord.objects.filter(id=record_id).first()

        if not record:
            self.stderr.write(self.style.ERROR(f'No existe un backup con ID {record_id}'))
            return

        self.stdout.write(f'Restaurando desde: {record.filename} ({record.created_at})')
        self.stdout.write(self.style.WARNING(
            'ATENCION: Esto reemplazara la base de datos actual.'
        ))

        confirm = input('Escribi "RESTAURAR" para confirmar: ')
        if confirm != 'RESTAURAR':
            self.stdout.write('Operacion cancelada.')
            return

        success, message = restore_backup(record_id)
        if success:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stderr.write(self.style.ERROR(message))
