from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path

from .models import BackupConfig, BackupRecord
from .utils import restore_backup


@admin.register(BackupConfig)
class BackupConfigAdmin(admin.ModelAdmin):
    list_display = ['is_enabled', 'frequency', 'backup_time', 'retention_days', 'last_backup_at']


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ['filename', 'status', 'trigger', 'file_size_display', 'created_at']
    list_filter = ['status', 'trigger']
    readonly_fields = [
        'filename', 'file_path', 'file_size', 'status', 'trigger',
        'error_message', 'created_at', 'created_by', 'duration_seconds',
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:record_id>/restore/',
                self.admin_site.admin_view(self.restore_view),
                name='backups_backuprecord_restore',
            ),
        ]
        return custom + urls

    def restore_view(self, request, record_id):
        record = BackupRecord.objects.filter(id=record_id, status='success').first()
        if not record:
            messages.error(request, 'Backup no encontrado o no exitoso.')
            return redirect('..')

        if request.method == 'POST' and request.POST.get('confirm') == 'RESTAURAR':
            success, msg = restore_backup(record_id)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)
            return redirect('../../')

        context = {
            **self.admin_site.each_context(request),
            'record': record,
            'title': f'Restaurar backup: {record.filename}',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/backups/restore_confirm.html', context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        record = BackupRecord.objects.filter(id=object_id, status='success').first()
        if record:
            extra_context['show_restore_button'] = True
            extra_context['restore_url'] = f'{object_id}/restore/'
        return super().change_view(request, object_id, form_url, extra_context)
