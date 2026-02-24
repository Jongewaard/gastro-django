from django.core.management.base import BaseCommand

from backups.utils import perform_backup, cleanup_old_backups


class Command(BaseCommand):
    help = 'Create a database backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scheduled',
            action='store_true',
            help='Mark this backup as triggered by the scheduler',
        )
        parser.add_argument(
            '--no-compress',
            action='store_true',
            help='Do not compress the backup file',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Also run cleanup of old backups after creating new one',
        )

    def handle(self, *args, **options):
        trigger = 'scheduled' if options['scheduled'] else 'manual'
        compress = not options['no_compress']

        self.stdout.write(f'Creando backup de base de datos (trigger={trigger})...')
        record = perform_backup(compress=compress, trigger=trigger)

        if record.status == 'success':
            self.stdout.write(self.style.SUCCESS(
                f'Backup creado: {record.filename} '
                f'({record.file_size_display()}) en {record.duration_seconds}s'
            ))
        else:
            self.stderr.write(self.style.ERROR(
                f'Backup fallido: {record.error_message}'
            ))

        if options['cleanup']:
            deleted, freed = cleanup_old_backups()
            if deleted:
                self.stdout.write(f'Limpieza: {deleted} backups antiguos eliminados')
