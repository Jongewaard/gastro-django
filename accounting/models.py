from django.db import models
from django.utils import timezone
from decimal import Decimal


class ExpenseCategory(models.Model):
    """Categoria de gastos"""
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoria de Gasto"
        verbose_name_plural = "Categorias de Gastos"
        unique_together = ['tenant', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name


class CashRegister(models.Model):
    """Caja registradora / cierre de caja"""
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    STATUS_CHOICES = [
        ('open', 'Abierta'),
        ('closed', 'Cerrada'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opened_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='registers_opened')
    closed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='registers_closed')

    opening_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    initial_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    expected_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    closing_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    difference = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Caja Registradora"
        verbose_name_plural = "Cajas Registradoras"
        ordering = ['-date', '-opened_at']

    def __str__(self):
        return f"Caja {self.date} - {self.get_status_display()}"

    def calculate_expected(self):
        """Calcula el monto esperado basado en ventas en efectivo"""
        from sales.models import Sale
        cash_sales = Sale.objects.filter(
            tenant=self.tenant,
            created_at__gte=self.opened_at,
            payment_method__is_cash=True,
            is_paid=True
        ).aggregate(total=models.Sum('total_amount'))
        self.expected_amount = self.initial_amount + (cash_sales['total'] or Decimal('0.00'))
        return self.expected_amount


class CashMovement(models.Model):
    """Movimiento de caja (ingreso/egreso manual)"""
    register = models.ForeignKey(CashRegister, on_delete=models.CASCADE, related_name='movements')

    MOVEMENT_TYPES = [
        ('in', 'Ingreso'),
        ('out', 'Egreso'),
    ]
    movement_type = models.CharField(max_length=5, choices=MOVEMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Caja"
        verbose_name_plural = "Movimientos de Caja"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} ${self.amount} - {self.description}"


class Expense(models.Model):
    """Gasto del negocio"""
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)

    paid_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ['-date']

    def __str__(self):
        return f"{self.description} - ${self.amount} ({self.date})"