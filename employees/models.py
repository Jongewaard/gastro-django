from django.db import models
from decimal import Decimal


class Employee(models.Model):
    """Empleado del negocio"""
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    user = models.OneToOneField('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dni = models.CharField(max_length=20, blank=True, verbose_name="DNI")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    POSITION_CHOICES = [
        ('cook', 'Cocinero'),
        ('cashier', 'Cajero'),
        ('delivery', 'Delivery'),
        ('waiter', 'Mozo'),
        ('manager', 'Encargado'),
        ('cleaner', 'Limpieza'),
        ('barista', 'Barista'),
        ('helper', 'Ayudante'),
        ('other', 'Otro'),
    ]
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='other')
    role = models.CharField(max_length=20, choices=POSITION_CHOICES, default='other')

    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    hire_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

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
    """Horario/turno de trabajo programado"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    shift_start = models.TimeField()
    shift_end = models.TimeField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_present = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Horario de Trabajo"
        verbose_name_plural = "Horarios de Trabajo"
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
        return round(diff.total_seconds() / 3600, 1)


class WorkLog(models.Model):
    """Registro real de asistencia (reloj biometrico o manual)"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='work_logs')
    date = models.DateField()
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)

    STATUS_CHOICES = [
        ('present', 'Presente'),
        ('absent', 'Ausente'),
        ('late', 'Tarde'),
        ('half_day', 'Medio dia'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)

    # Futuro: datos del reloj biometrico
    biometric_device_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.get_status_display()})"

    @property
    def total_hours(self):
        if self.clock_in and self.clock_out:
            diff = self.clock_out - self.clock_in
            return round(diff.total_seconds() / 3600, 1)
        return 0