from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductCombo


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'icon', 'color', 'is_active', 'sort_order']
    list_filter = ['tenant', 'is_active']
    search_fields = ['name', 'tenant__name']
    list_editable = ['sort_order', 'is_active']
    ordering = ['tenant', 'sort_order', 'name']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['variant_type', 'name', 'price_modifier', 'is_default', 'is_active', 'sort_order']


class ProductComboInline(admin.TabularInline):
    model = ProductCombo
    fk_name = 'combo_product'
    extra = 0
    fields = ['component_product', 'quantity', 'is_optional']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'tenant', 'base_price', 'has_variants', 'is_active', 'track_inventory']
    list_filter = ['tenant', 'category', 'has_variants', 'is_active', 'track_inventory']
    search_fields = ['name', 'description', 'category__name']
    list_editable = ['base_price', 'is_active']
    ordering = ['tenant', 'category', 'sort_order', 'name']
    
    inlines = [ProductVariantInline, ProductComboInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('tenant', 'category', 'name', 'description', 'image')
        }),
        ('Precio y Configuración', {
            'fields': ('base_price', 'has_variants', 'is_combo', 'requires_preparation')
        }),
        ('Estado y Orden', {
            'fields': ('is_active', 'is_featured', 'sort_order')
        }),
        ('Inventario', {
            'fields': ('track_inventory', 'current_stock', 'min_stock'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tenant', 'category')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'variant_type', 'name', 'price_modifier', 'is_default', 'is_active']
    list_filter = ['product__tenant', 'variant_type', 'is_active']
    search_fields = ['name', 'product__name']
    ordering = ['product', 'variant_type', 'sort_order']


@admin.register(ProductCombo)
class ProductComboAdmin(admin.ModelAdmin):
    list_display = ['combo_product', 'component_product', 'quantity', 'is_optional']
    list_filter = ['combo_product__tenant', 'is_optional']
    search_fields = ['combo_product__name', 'component_product__name']