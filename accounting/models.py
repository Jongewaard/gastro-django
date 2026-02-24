from django.db import models
from django.utils import timezone
from decimal import Decimal


class ExpenseCategory(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoria de Gasto"
        verbose_name_plural = "Categorias de Gasto"
        unique_together = ['tenant', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name


class CashRegister(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    opened_by = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='opened_registers'
    )
    closed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='closed_registers'
    )
    opening_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    closing_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    difference = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    STATUS_CHOICES = [
        ('open', 'Abierta'),
        ('closed', 'Cerrada'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ['-date']

    def __str__(self):
        return f"Caja {self.date} - {self.get_status_display()}"

    def calculate_expected(self):
        movements = self.movements.all()
        total_in = sum(m.amount for m in movements if m.amount > 0)
        total_out = sum(abs(m.amount) for m in movements if m.amount < 0)
        self.expected_amount = self.opening_amount + total_in - total_out
        return self.expected_amount

    def close(self, closing_amount, closed_by):
        self.calculate_expected()
        self.closing_amount = closing_amount
        self.difference = closing_amount - (self.expected_amount or self.opening_amount)
        self.closed_by = closed_by
        self.closed_at = timezone.now()
        self.status = 'closed'
        self.save()


class CashMovement(models.Model):
    register = models.ForeignKey(CashRegister, on_delete=models.CASCADE, related_name='movements')

    MOVEMENT_TYPES = [
        ('sale', 'Venta'),
        ('expense', 'Gasto'),
        ('withdrawal', 'Retiro'),
        ('deposit', 'Deposito'),
        ('adjustment', 'Ajuste'),
        ('tip', 'Propina'),
    ]
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Caja"
        verbose_name_plural = "Movimientos de Caja"
        ordering = ['-created_at']

    def __str__(self):
        sign = "+" if self.amount > 0 else ""
        return f"{self.get_movement_type_display()}: {sign}${self.amount}"


class Expense(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    paid_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} - ${self.amount}"
