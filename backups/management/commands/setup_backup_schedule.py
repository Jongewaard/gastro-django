from django.core.management.base import BaseCommand

from backups.models import BackupConfig
from backups.utils import setup_schedule, remove_schedule, get_scheduler_status


class Command(BaseCommand):
    help = 'Setup or update OS scheduled task for automatic backups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove the scheduled task',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current scheduler status',
        )

    def handle(self, *args, **options):
        if options['status']:
            status = get_scheduler_status()
            if status['is_scheduled']:
                self.stdout.write(self.style.SUCCESS('Backup programado ACTIVO'))
                if status['details']:
                    self.stdout.write(status['details'])
            else:
                self.stdout.write(self.style.WARNING('No hay backup programado'))
            return

        if options['remove']:
            remove_schedule()
            self.stdout.write(self.style.SUCCESS('Tarea programada eliminada.'))
            return

        config = BackupConfig.get_config()
        if not config.is_enabled:
            self.stdout.write(self.style.WARNING(
                'Los backups estan desactivados. Activalos primero desde la configuracion.'
            ))
            return

        success, message = setup_schedule(config.frequency, config.backup_time)
        if success:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stderr.write(self.style.ERROR(message))
