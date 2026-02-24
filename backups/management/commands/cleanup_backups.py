from django.core.management.base import BaseCommand

from backups.utils import cleanup_old_backups


class Command(BaseCommand):
    help = 'Remove old backups based on retention policy'

    def handle(self, *args, **options):
        deleted, freed = cleanup_old_backups()
        if deleted:
            freed_mb = freed / (1024 * 1024)
            self.stdout.write(self.style.SUCCESS(
                f'{deleted} backups eliminados, {freed_mb:.1f} MB liberados'
            ))
        else:
            self.stdout.write('No hay backups para limpiar.')
