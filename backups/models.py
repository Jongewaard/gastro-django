from datetime import time as dt_time
from pathlib import Path

from django.conf import settings
from django.db import models


class BackupConfig(models.Model):
    """
    Singleton configuration for database backups.
    Only one row should ever exist (enforced via save() override).
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Diario'),
        ('every_12h', 'Cada 12 horas'),
        ('every_6h', 'Cada 6 horas'),
        ('weekly', 'Semanal'),
    ]

    is_enabled = models.BooleanField(default=False, verbose_name='Backups activados')
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='daily',
        verbose_name='Frecuencia',
    )
    backup_time = models.TimeField(
        default=dt_time(3, 0),
        verbose_name='Hora del backup',
    )
    backup_dir = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='Carpeta de backups',
    )
    retention_days = models.PositiveIntegerField(
        default=30,
        verbose_name='Dias de retencion',
    )
    max_backups = models.PositiveIntegerField(
        default=50,
        verbose_name='Maximo de backups',
    )
    compress = models.BooleanField(
        default=True,
        verbose_name='Comprimir backups',
    )
    last_backup_at = models.DateTimeField(null=True, blank=True, verbose_name='Ultimo backup')
    last_backup_status = models.CharField(max_length=20, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )

    class Meta:
        verbose_name = 'Configuracion de Backups'
        verbose_name_plural = 'Configuracion de Backups'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def get_backup_dir(self):
        if self.backup_dir:
            return Path(self.backup_dir)
        return Path(settings.BASE_DIR) / 'backups'

    def __str__(self):
        return f'Backup Config ({self.get_frequency_display()})'


class BackupRecord(models.Model):
    """Log of each backup attempt."""
    STATUS_CHOICES = [
        ('success', 'Exitoso'),
        ('failed', 'Fallido'),
        ('in_progress', 'En progreso'),
    ]
    TRIGGER_CHOICES = [
        ('manual', 'Manual'),
        ('scheduled', 'Programado'),
    ]

    filename = models.CharField(max_length=255, verbose_name='Archivo')
    file_path = models.CharField(max_length=500, verbose_name='Ruta completa')
    file_size = models.BigIntegerField(default=0, verbose_name='Tamano (bytes)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default='manual')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Creado por',
    )
    duration_seconds = models.FloatField(default=0, verbose_name='Duracion (seg)')

    class Meta:
        verbose_name = 'Registro de Backup'
        verbose_name_plural = 'Registros de Backup'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.filename} - {self.get_status_display()}'

    def file_size_display(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} TB'

    def file_exists(self):
        return Path(self.file_path).exists() if self.file_path else False
