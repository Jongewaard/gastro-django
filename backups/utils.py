import gzip
import platform
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone


TASK_NAME = 'GastroSaaS_DatabaseBackup'


def get_db_path():
    return Path(settings.DATABASES['default']['NAME'])


def perform_backup(backup_dir=None, compress=True, trigger='manual', user=None):
    """
    Create a database backup using sqlite3's backup() API.
    Returns the BackupRecord instance.
    """
    from .models import BackupConfig, BackupRecord

    config = BackupConfig.get_config()
    if backup_dir is None:
        backup_dir = config.get_backup_dir()
    else:
        backup_dir = Path(backup_dir)

    if compress is None:
        compress = config.compress

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = timezone.localtime().strftime('%Y-%m-%d_%H%M%S')
    base_filename = f'backup_{timestamp}.sqlite3'
    filename = base_filename + '.gz' if compress else base_filename
    file_path = backup_dir / filename

    record = BackupRecord.objects.create(
        filename=filename,
        file_path=str(file_path),
        status='in_progress',
        trigger=trigger,
        created_by=user,
    )

    start_time = time.time()

    try:
        db_path = get_db_path()
        temp_path = backup_dir / f'_temp_{base_filename}'

        source = sqlite3.connect(str(db_path))
        dest = sqlite3.connect(str(temp_path))
        source.backup(dest)
        dest.close()
        source.close()

        if compress:
            with open(temp_path, 'rb') as f_in:
                with gzip.open(file_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            temp_path.unlink()
        else:
            temp_path.rename(file_path)

        elapsed = time.time() - start_time
        record.status = 'success'
        record.file_size = file_path.stat().st_size
        record.duration_seconds = round(elapsed, 2)
        record.save()

        config.last_backup_at = timezone.now()
        config.last_backup_status = 'success'
        config.save(update_fields=['last_backup_at', 'last_backup_status'])

        return record

    except Exception as e:
        elapsed = time.time() - start_time
        record.status = 'failed'
        record.error_message = str(e)
        record.duration_seconds = round(elapsed, 2)
        record.save()

        config.last_backup_status = 'failed'
        config.save(update_fields=['last_backup_status'])

        return record


def restore_backup(record_id):
    """
    Restore a database from a backup file.
    1. Creates a safety backup of the current DB
    2. Uses sqlite3.backup() to overwrite the live DB from the backup file
    Returns (success: bool, message: str).
    """
    from .models import BackupRecord

    record = BackupRecord.objects.filter(id=record_id, status='success').first()
    if not record:
        return False, 'Backup no encontrado o no exitoso.'

    backup_path = Path(record.file_path)
    if not backup_path.exists():
        return False, 'El archivo de backup ya no existe en el disco.'

    # 1. Safety backup before restoring
    safety = perform_backup(trigger='manual')
    if safety.status != 'success':
        return False, f'No se pudo crear backup de seguridad previo: {safety.error_message}'

    # 2. Decompress if needed, then restore
    try:
        db_path = get_db_path()
        temp_path = db_path.parent / '_temp_restore.sqlite3'

        if record.filename.endswith('.gz'):
            with gzip.open(backup_path, 'rb') as f_in:
                with open(temp_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(backup_path, temp_path)

        # Use sqlite3 backup API: copy from restored file TO live database
        source = sqlite3.connect(str(temp_path))
        dest = sqlite3.connect(str(db_path))
        source.backup(dest)
        dest.close()
        source.close()

        temp_path.unlink()
        return True, f'Base de datos restaurada desde {record.filename}. Se creo un backup de seguridad previo ({safety.filename}).'

    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return False, f'Error al restaurar: {str(e)}'


def cleanup_old_backups():
    """
    Remove backups older than retention_days and enforce max_backups.
    Returns (deleted_count, freed_bytes).
    """
    from .models import BackupConfig, BackupRecord

    config = BackupConfig.get_config()
    cutoff_date = timezone.now() - timedelta(days=config.retention_days)

    deleted_count = 0
    freed_bytes = 0

    # Delete by age
    old_records = BackupRecord.objects.filter(
        created_at__lt=cutoff_date,
        status='success',
    )
    for record in old_records:
        path = Path(record.file_path)
        if path.exists():
            freed_bytes += path.stat().st_size
            path.unlink()
        deleted_count += 1
    old_records.delete()

    # Enforce max count
    success_count = BackupRecord.objects.filter(status='success').count()
    excess = success_count - config.max_backups
    if excess > 0:
        oldest = list(
            BackupRecord.objects.filter(status='success')
            .order_by('created_at')[:excess]
        )
        for record in oldest:
            path = Path(record.file_path)
            if path.exists():
                freed_bytes += path.stat().st_size
                path.unlink()
            deleted_count += 1
            record.delete()

    return deleted_count, freed_bytes


# ============================================================
# Cross-Platform Scheduler Integration
# ============================================================

def _get_python_path():
    return sys.executable


def _get_manage_py_path():
    return str(Path(settings.BASE_DIR) / 'manage.py')


def get_scheduler_status():
    """Check if a scheduled backup task exists in the OS scheduler."""
    system = platform.system()

    if system == 'Windows':
        try:
            result = subprocess.run(
                ['schtasks', '/Query', '/TN', TASK_NAME, '/FO', 'LIST', '/V'],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return {'is_scheduled': True, 'details': result.stdout}
            return {'is_scheduled': False, 'details': ''}
        except Exception:
            return {'is_scheduled': False, 'details': 'Error al verificar el programador'}

    elif system == 'Linux':
        try:
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True, text=True, timeout=10,
            )
            if TASK_NAME in result.stdout:
                return {'is_scheduled': True, 'details': result.stdout}
            return {'is_scheduled': False, 'details': ''}
        except Exception:
            return {'is_scheduled': False, 'details': 'Error al verificar crontab'}

    return {'is_scheduled': False, 'details': f'Plataforma no soportada: {system}'}


def setup_schedule(frequency, backup_time):
    """
    Create or update the OS scheduled task.
    Returns (success: bool, message: str).
    """
    system = platform.system()
    python_path = _get_python_path()
    manage_path = _get_manage_py_path()
    command = f'"{python_path}" "{manage_path}" backup_db --scheduled --cleanup'

    remove_schedule()

    time_str = backup_time.strftime('%H:%M')

    if system == 'Windows':
        return _setup_windows_schedule(command, frequency, time_str)
    elif system == 'Linux':
        return _setup_linux_schedule(command, frequency, time_str)
    else:
        return False, f'Plataforma no soportada: {system}'


def _setup_windows_schedule(command, frequency, time_str):
    try:
        args = ['schtasks', '/Create', '/TN', TASK_NAME, '/F']

        if frequency == 'daily':
            args += ['/SC', 'DAILY', '/ST', time_str]
        elif frequency == 'every_12h':
            args += ['/SC', 'DAILY', '/ST', time_str, '/RI', '720', '/DU', '24:00']
        elif frequency == 'every_6h':
            args += ['/SC', 'DAILY', '/ST', time_str, '/RI', '360', '/DU', '24:00']
        elif frequency == 'weekly':
            args += ['/SC', 'WEEKLY', '/D', 'DOM', '/ST', time_str]

        args += ['/TR', command]

        result = subprocess.run(args, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return True, 'Tarea programada creada exitosamente.'
        return False, f'Error al crear la tarea: {result.stderr}'

    except Exception as e:
        return False, f'Error: {str(e)}'


def _setup_linux_schedule(command, frequency, time_str):
    try:
        hour, minute = time_str.split(':')

        if frequency == 'daily':
            cron_schedule = f'{minute} {hour} * * *'
        elif frequency == 'every_12h':
            cron_schedule = f'{minute} {hour},{(int(hour) + 12) % 24} * * *'
        elif frequency == 'every_6h':
            cron_schedule = f'{minute} */6 * * *'
        elif frequency == 'weekly':
            cron_schedule = f'{minute} {hour} * * 0'

        cron_line = f'{cron_schedule} {command} # {TASK_NAME}'

        result = subprocess.run(
            ['crontab', '-l'],
            capture_output=True, text=True, timeout=10,
        )
        existing = result.stdout if result.returncode == 0 else ''
        lines = [l for l in existing.strip().split('\n') if TASK_NAME not in l and l.strip()]
        lines.append(cron_line)
        new_crontab = '\n'.join(lines) + '\n'

        proc = subprocess.Popen(
            ['crontab', '-'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        )
        _, stderr = proc.communicate(input=new_crontab, timeout=10)
        if proc.returncode == 0:
            return True, 'Cron job creado exitosamente.'
        return False, f'Error al crear cron job: {stderr}'

    except Exception as e:
        return False, f'Error: {str(e)}'


def remove_schedule():
    """Remove the scheduled backup task from the OS."""
    system = platform.system()

    if system == 'Windows':
        try:
            subprocess.run(
                ['schtasks', '/Delete', '/TN', TASK_NAME, '/F'],
                capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pass
    elif system == 'Linux':
        try:
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                lines = [l for l in result.stdout.split('\n')
                         if TASK_NAME not in l and l.strip()]
                new_crontab = '\n'.join(lines) + '\n' if lines else ''
                proc = subprocess.Popen(
                    ['crontab', '-'],
                    stdin=subprocess.PIPE, text=True,
                )
                proc.communicate(input=new_crontab, timeout=10)
        except Exception:
            pass
