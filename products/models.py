from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """Categorías de productos configurables por tipo de negocio"""
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icono CSS/emoji")
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Color hex")
    
    # Display settings
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        unique_together = ['tenant', 'name']
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class Product(models.Model):
    """Producto base - adaptable a cualquier tipo de negocio gastronómico"""
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True)
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Precio base del producto"
    )
    
    # Product configuration
    has_variants = models.BooleanField(default=False, help_text="¿Tiene variantes? (tamaños, sabores, etc.)")
    is_combo = models.BooleanField(default=False, help_text="¿Es un combo de productos?")
    requires_preparation = models.BooleanField(default=True, help_text="¿Requiere preparación en cocina?")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    # Inventory tracking
    track_inventory = models.BooleanField(default=False)
    current_stock = models.IntegerField(default=0)
    min_stock = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        unique_together = ['tenant', 'name']
        ordering = ['category', 'sort_order', 'name']
    
    def __str__(self):
        return f"{self.name} - ${self.base_price}"
    
    def get_current_price(self):
        """Obtiene el precio actual (puede incluir lógica de horarios/promociones)"""
        return self.base_price


class ProductVariant(models.Model):
    """Variantes de producto: tamaños, sabores, extras, etc."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    VARIANT_TYPES = [
        ('size', 'Tamaño'),
        ('flavor', 'Sabor'),
        ('topping', 'Extra/Topping'),
        ('preparation', 'Preparación'),
        ('custom', 'Personalizado'),
    ]
    
    variant_type = models.CharField(max_length=20, choices=VARIANT_TYPES)
    name = models.CharField(max_length=100)
    price_modifier = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Modificador de precio (+/- respecto al precio base)"
    )
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Variante de Producto"
        verbose_name_plural = "Variantes de Producto"
        unique_together = ['product', 'variant_type', 'name']
        ordering = ['variant_type', 'sort_order', 'name']
    
    def __str__(self):
        modifier = f"(+${self.price_modifier})" if self.price_modifier > 0 else f"(${self.price_modifier})" if self.price_modifier < 0 else ""
        return f"{self.product.name} - {self.name} {modifier}"


class ProductCombo(models.Model):
    """Componentes de combos/promociones"""
    combo_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='combo_items')
    component_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='used_in_combos')
    quantity = models.PositiveIntegerField(default=1)
    is_optional = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Componente de Combo"
        verbose_name_plural = "Componentes de Combo"
        unique_together = ['combo_product', 'component_product']
    
    def __str__(self):
        return f"{self.combo_product.name} + {self.quantity}x {self.component_product.name}"


# Business type templates para setup inicial
BUSINESS_TYPE_TEMPLATES = {
    'pizzeria': {
        'categories': [
            {'name': 'Pizzas', 'icon': '🍕', 'color': '#EF4444'},
            {'name': 'Empanadas', 'icon': '🥟', 'color': '#F59E0B'},
            {'name': 'Bebidas', 'icon': '🥤', 'color': '#3B82F6'},
            {'name': 'Postres', 'icon': '🍰', 'color': '#EC4899'},
        ],
        'sample_products': [
            {'name': 'Pizza Muzzarella', 'category': 'Pizzas', 'price': 8500, 'has_variants': True},
            {'name': 'Pizza Napolitana', 'category': 'Pizzas', 'price': 9000, 'has_variants': True},
            {'name': 'Empanada Carne', 'category': 'Empanadas', 'price': 800},
            {'name': 'Coca Cola 500ml', 'category': 'Bebidas', 'price': 1500},
        ]
    },
    'heladeria': {
        'categories': [
            {'name': 'Helados', 'icon': '🍦', 'color': '#EC4899'},
            {'name': 'Batidos', 'icon': '🥤', 'color': '#8B5CF6'},
            {'name': 'Tortas', 'icon': '🎂', 'color': '#EF4444'},
            {'name': 'Café', 'icon': '☕', 'color': '#A3A3A3'},
        ],
        'sample_products': [
            {'name': 'Helado Dulce de Leche', 'category': 'Helados', 'price': 2500, 'has_variants': True},
            {'name': 'Helado Chocolate', 'category': 'Helados', 'price': 2500, 'has_variants': True},
            {'name': 'Batido Frutilla', 'category': 'Batidos', 'price': 3500},
            {'name': 'Torta Chocolate', 'category': 'Tortas', 'price': 15000},
        ]
    }
}