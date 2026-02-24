from django.db import models
from decimal import Decimal


class Supplier(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    contact_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        unique_together = ['tenant', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    UNIT_CHOICES = [
        ('kg', 'Kilogramos'),
        ('g', 'Gramos'),
        ('l', 'Litros'),
        ('ml', 'Mililitros'),
        ('u', 'Unidades'),
        ('doc', 'Docenas'),
        ('paq', 'Paquetes'),
    ]
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES, default='u')
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ingrediente"
        verbose_name_plural = "Ingredientes"
        unique_together = ['tenant', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.min_stock

    @property
    def stock_value(self):
        return self.current_stock * self.cost_per_unit


class StockMovement(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='movements')

    MOVEMENT_TYPES = [
        ('purchase', 'Compra'),
        ('usage', 'Uso/Consumo'),
        ('adjustment', 'Ajuste'),
        ('waste', 'Desperdicio'),
        ('return', 'Devolucion'),
    ]
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()}: {self.quantity} {self.ingredient.unit} de {self.ingredient.name}"

    def save(self, *args, **kwargs):
        if self.unit_cost and self.quantity:
            self.total_cost = abs(self.quantity) * self.unit_cost
        super().save(*args, **kwargs)

    def apply_to_stock(self):
        ingredient = self.ingredient
        if self.movement_type in ('purchase', 'return'):
            ingredient.current_stock += abs(self.quantity)
        elif self.movement_type in ('usage', 'waste'):
            ingredient.current_stock -= abs(self.quantity)
        elif self.movement_type == 'adjustment':
            ingredient.current_stock = abs(self.quantity)
        ingredient.save()


class RecipeItem(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='recipe_items')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='used_in_recipes')
    quantity_needed = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        verbose_name = "Item de Receta"
        verbose_name_plural = "Items de Receta"
        unique_together = ['product', 'ingredient']

    def __str__(self):
        return f"{self.product.name}: {self.quantity_needed} {self.ingredient.unit} de {self.ingredient.name}"
