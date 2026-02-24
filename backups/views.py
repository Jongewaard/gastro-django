import os
import signal
import sys
from datetime import time as dt_time
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .export_xlsx import generate_export_bytes
from .models import BackupConfig, BackupRecord
from .utils import (
    cleanup_old_backups,
    get_scheduler_status,
    perform_backup,
    remove_schedule,
    setup_schedule,
)


def backup_role_required(view_func):
    """Only owner/admin roles can access backup features."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ('owner', 'admin') and not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para acceder a la configuracion de backups.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def _format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f'{size_bytes:.1f} {unit}'
        size_bytes /= 1024
    return f'{size_bytes:.1f} TB'


@login_required
@backup_role_required
def backup_dashboard(request):
    config = BackupConfig.get_config()
    records = BackupRecord.objects.all()[:50]
    scheduler_status = get_scheduler_status()

    # Sync: si config y scheduler están desincronizados, corregir
    if config.is_enabled and not scheduler_status['is_scheduled']:
        setup_schedule(config.frequency, config.backup_time)
        scheduler_status = get_scheduler_status()
    elif not config.is_enabled and scheduler_status['is_scheduled']:
        remove_schedule()
        scheduler_status = get_scheduler_status()

    total_backups = BackupRecord.objects.filter(status='success').count()
    total_size = sum(
        r.file_size for r in BackupRecord.objects.filter(status='success')
    )

    context = {
        'config': config,
        'records': records,
        'scheduler_status': scheduler_status,
        'total_backups': total_backups,
        'total_size_display': _format_size(total_size),
        'backup_dir': str(config.get_backup_dir()),
        'active_page': 'backups',
    }
    return render(request, 'backups/backup_dashboard.html', context)


@login_required
@backup_role_required
@require_POST
def backup_save_config(request):
    config = BackupConfig.get_config()

    config.is_enabled = request.POST.get('is_enabled') == 'on'
    config.frequency = request.POST.get('frequency', 'daily')

    time_str = request.POST.get('backup_time', '03:00')
    try:
        parts = time_str.split(':')
        config.backup_time = dt_time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        pass

    try:
        config.retention_days = max(1, int(request.POST.get('retention_days', 30)))
    except (ValueError, TypeError):
        config.retention_days = 30

    try:
        config.max_backups = max(1, int(request.POST.get('max_backups', 50)))
    except (ValueError, TypeError):
        config.max_backups = 50

    config.compress = request.POST.get('compress') == 'on'
    config.backup_dir = request.POST.get('backup_dir', '').strip()
    config.updated_by = request.user
    config.save()

    if config.is_enabled:
        success, msg = setup_schedule(config.frequency, config.backup_time)
        if success:
            messages.success(request, 'Configuracion guardada y backup programado activado.')
        else:
            messages.warning(request, f'Configuracion guardada, pero error al programar: {msg}')
    else:
        remove_schedule()
        messages.success(request, 'Configuracion guardada. Backups programados desactivados.')

    return redirect('backup_dashboard')


@login_required
@backup_role_required
@require_POST
def backup_create_now(request):
    record = perform_backup(trigger='manual', user=request.user)
    if record.status == 'success':
        messages.success(
            request,
            f'Backup creado: {record.filename} ({record.file_size_display()})',
        )
    else:
        messages.error(request, f'Error al crear backup: {record.error_message}')

    cleanup_old_backups()
    return redirect('backup_dashboard')


@login_required
@backup_role_required
def backup_download(request, record_id):
    record = BackupRecord.objects.filter(id=record_id, status='success').first()
    if not record:
        raise Http404('Backup no encontrado.')

    file_path = Path(record.file_path)
    if not file_path.exists():
        messages.error(request, 'El archivo de backup ya no existe en el disco.')
        return redirect('backup_dashboard')

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=record.filename,
    )


@login_required
@backup_role_required
@require_POST
def backup_delete(request, record_id):
    record = BackupRecord.objects.filter(id=record_id).first()
    if not record:
        raise Http404('Backup no encontrado.')

    file_path = Path(record.file_path)
    filename = record.filename
    if file_path.exists():
        file_path.unlink()

    record.delete()
    messages.success(request, f'Backup "{filename}" eliminado.')
    return redirect('backup_dashboard')


@login_required
@backup_role_required
@require_POST
def backup_cleanup(request):
    deleted, freed = cleanup_old_backups()
    if deleted:
        freed_mb = freed / (1024 * 1024)
        messages.success(request, f'{deleted} backups eliminados, {freed_mb:.1f} MB liberados.')
    else:
        messages.info(request, 'No hay backups antiguos para limpiar.')
    return redirect('backup_dashboard')


@login_required
@backup_role_required
def export_excel(request):
    """Export all business data to an Excel file."""
    tenant = request.user.tenant
    if not tenant:
        messages.error(request, 'No hay un negocio asociado a tu cuenta.')
        return redirect('backup_dashboard')

    days_param = request.GET.get('days')
    days = int(days_param) if days_param and days_param.isdigit() else None

    try:
        xlsx_bytes = generate_export_bytes(tenant, days=days)
    except Exception as e:
        messages.error(request, f'Error al generar el Excel: {e}')
        return redirect('backup_dashboard')

    from django.utils import timezone as tz
    today = tz.localdate().strftime('%Y-%m-%d')
    filename = f'{tenant.slug}_datos_{today}.xlsx'

    from django.http import HttpResponse
    response = HttpResponse(
        xlsx_bytes,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@backup_role_required
@require_POST
def server_restart(request):
    """
    Restart the server. Works when running under run_server.pyw wrapper:
    the wrapper detects the exit and restarts the process automatically.
    Returns a JSON response before killing the process.
    """
    # Send response first, then schedule the exit
    import threading

    def delayed_exit():
        import time
        time.sleep(1)
        os._exit(0)  # Hard exit; run_server.pyw loop will restart us

    threading.Thread(target=delayed_exit, daemon=True).start()
    return JsonResponse({'status': 'restarting', 'message': 'Reiniciando servidor...'})
