from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class PaymentMethod(models.Model):
    """Métodos de pago configurables por tenant"""
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_cash = models.BooleanField(default=False)
    requires_reference = models.BooleanField(default=False, help_text="¿Requiere número de referencia?")
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        unique_together = ['tenant', 'name']
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class Sale(models.Model):
    """Venta/Ticket individual"""
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    
    # Sale info
    sale_number = models.CharField(max_length=20, help_text="Número de ticket/factura")
    customer_name = models.CharField(max_length=100, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('preparing', 'En Preparación'),
        ('ready', 'Listo'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Payment info
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    payment_reference = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Staff
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    
    # Delivery info (optional)
    delivery_address = models.TextField(blank=True)
    delivery_phone = models.CharField(max_length=20, blank=True)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"#{self.sale_number} - ${self.total_amount} ({self.get_status_display()})"
    
    def calculate_totals(self):
        """Recalcula los totales basado en los items"""
        items = self.items.all()
        self.subtotal = sum(item.get_total_price() for item in items)
        # TODO: calcular impuestos según configuración del tenant
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount + self.delivery_fee
        self.save()


class SaleItem(models.Model):
    """Items/productos de una venta"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Variantes seleccionadas (JSON para flexibilidad)
    selected_variants = models.JSONField(default=list, help_text="Lista de variantes seleccionadas")
    
    # Notas especiales
    notes = models.TextField(blank=True, help_text="Notas especiales para cocina")
    
    class Meta:
        verbose_name = "Item de Venta"
        verbose_name_plural = "Items de Venta"
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} (${self.unit_price})"
    
    def get_total_price(self):
        """Precio total del item (cantidad × precio unitario)"""
        return self.quantity * self.unit_price


class DailySummary(models.Model):
    """Resumen diario de ventas por tenant"""
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    date = models.DateField()
    
    # Sales metrics
    total_sales = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    card_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Popular products (JSON)
    top_products = models.JSONField(default=list)
    
    # Status
    is_closed = models.BooleanField(default=False)
    closed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Resumen Diario"
        verbose_name_plural = "Resúmenes Diarios"
        unique_together = ['tenant', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.date} (${self.total_revenue})"


# Default payment methods per business type
BUSINESS_PAYMENT_METHODS = {
    'pizzeria': [
        {'name': 'Efectivo', 'is_cash': True},
        {'name': 'Tarjeta Débito', 'requires_reference': True},
        {'name': 'Tarjeta Crédito', 'requires_reference': True},
        {'name': 'Transferencia', 'requires_reference': True},
        {'name': 'MercadoPago', 'requires_reference': True},
    ],
    'heladeria': [
        {'name': 'Efectivo', 'is_cash': True},
        {'name': 'Tarjeta', 'requires_reference': True},
        {'name': 'QR/Digital', 'requires_reference': True},
    ]
}