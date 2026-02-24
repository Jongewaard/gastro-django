from django.db import models
from django.utils import timezone
from decimal import Decimal


class Employee(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    user = models.OneToOneField('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    POSITION_CHOICES = [
        ('encargado', 'Encargado'),
        ('cajero', 'Cajero'),
        ('cocinero', 'Cocinero'),
        ('pizzero', 'Pizzero'),
        ('delivery', 'Delivery'),
        ('mozo', 'Mozo'),
        ('limpieza', 'Limpieza'),
        ('ayudante', 'Ayudante de cocina'),
    ]
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='ayudante')

    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    dni = models.CharField(max_length=20, blank=True, verbose_name="DNI")

    hire_date = models.DateField(default=timezone.now)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.get_position_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class WorkSchedule(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    shift_start = models.TimeField()
    shift_end = models.TimeField()
    break_minutes = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Horario de Trabajo"
        verbose_name_plural = "Horarios de Trabajo"
        unique_together = ['employee', 'date']
        ordering = ['date', 'shift_start']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.shift_start}-{self.shift_end})"

    @property
    def scheduled_hours(self):
        from datetime import datetime, timedelta
        start = datetime.combine(self.date, self.shift_start)
        end = datetime.combine(self.date, self.shift_end)
        if end < start:
            end += timedelta(days=1)
        diff = end - start
        hours = diff.total_seconds() / 3600
        hours -= self.break_minutes / 60
        return round(max(hours, 0), 1)


class WorkLog(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='work_logs')
    date = models.DateField()
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    break_minutes = models.PositiveIntegerField(default=0)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    STATUS_CHOICES = [
        ('working', 'Trabajando'),
        ('completed', 'Completado'),
        ('absent', 'Ausente'),
        ('late', 'Tarde'),
        ('half_day', 'Medio dia'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='working')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.get_status_display()})"

    def calculate_hours(self):
        if self.clock_in and self.clock_out:
            from datetime import datetime, timedelta
            start = datetime.combine(self.date, self.clock_in)
            end = datetime.combine(self.date, self.clock_out)
            if end < start:
                end += timedelta(days=1)
            diff = end - start
            hours = diff.total_seconds() / 3600
            hours -= self.break_minutes / 60
            self.total_hours = Decimal(str(round(max(hours, 0), 2)))
        return self.total_hours
