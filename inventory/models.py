from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Supplier(models.Model):
    """Proveedor de ingredientes/insumos"""
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
    """Ingrediente/insumo del negocio"""
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    UNIT_CHOICES = [
        ('kg', 'Kilogramos'),
        ('g', 'Gramos'),
        ('lt', 'Litros'),
        ('ml', 'Mililitros'),
        ('un', 'Unidades'),
    ]
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES, default='kg')

    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

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


class StockMovement(models.Model):
    """Movimiento de stock (entrada/salida)"""
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='movements')

    MOVEMENT_TYPES = [
        ('in', 'Entrada'),
        ('out', 'Salida'),
        ('adjustment', 'Ajuste'),
        ('waste', 'Merma'),
    ]
    movement_type = models.CharField(max_length=15, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} {self.ingredient.unit} de {self.ingredient.name}"


class RecipeItem(models.Model):
    """Ingrediente necesario para un producto (receta)"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='recipe_items')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='used_in_recipes')
    quantity_needed = models.DecimalField(max_digits=10, decimal_places=3, help_text="Cantidad necesaria por unidad de producto")

    class Meta:
        verbose_name = "Item de Receta"
        verbose_name_plural = "Items de Receta"
        unique_together = ['product', 'ingredient']

    def __str__(self):
        return f"{self.product.name}: {self.quantity_needed} {self.ingredient.unit} de {self.ingredient.name}"