from django.contrib import admin
from .models import Supplier, Ingredient, StockMovement, RecipeItem


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_name', 'phone', 'tenant', 'is_active']
    list_filter = ['tenant', 'is_active']
    search_fields = ['name', 'contact_name']


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'current_stock', 'unit', 'min_stock', 'cost_per_unit', 'is_low_stock', 'tenant']
    list_filter = ['tenant', 'unit', 'is_active', 'supplier']
    search_fields = ['name']

    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = "Stock bajo"


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['ingredient', 'movement_type', 'quantity', 'total_cost', 'created_by', 'created_at']
    list_filter = ['movement_type', 'ingredient__tenant', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(RecipeItem)
class RecipeItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'ingredient', 'quantity_needed']
    list_filter = ['product__tenant']
