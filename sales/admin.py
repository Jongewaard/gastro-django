from django.contrib import admin
from .models import PaymentMethod, Sale, SaleItem, DailySummary


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'is_cash', 'requires_reference', 'is_active', 'sort_order']
    list_filter = ['tenant', 'is_cash', 'requires_reference', 'is_active']
    search_fields = ['name', 'tenant__name']
    list_editable = ['sort_order', 'is_active']
    ordering = ['tenant', 'sort_order', 'name']


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    fields = ['product', 'quantity', 'unit_price', 'selected_variants', 'notes']
    readonly_fields = ['unit_price']  # Se puede calcular automáticamente


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'tenant', 'customer_name', 'order_type', 'status', 'total_amount', 'payment_method', 'is_paid', 'created_at']
    list_filter = ['tenant', 'status', 'order_type', 'payment_method', 'is_paid', 'created_at']
    search_fields = ['sale_number', 'customer_name', 'payment_reference']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    inlines = [SaleItemInline]
    
    fieldsets = (
        ('Información de la Venta', {
            'fields': ('tenant', 'sale_number', 'customer_name', 'order_type', 'status', 'created_by')
        }),
        ('Totales', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Pago', {
            'fields': ('payment_method', 'payment_reference', 'is_paid')
        }),
        ('Delivery', {
            'fields': ('delivery_address', 'delivery_phone', 'delivery_fee'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tenant', 'payment_method', 'created_by')


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'unit_price', 'get_total_price']
    list_filter = ['sale__tenant', 'product__category']
    search_fields = ['sale__sale_number', 'product__name']
    
    def get_total_price(self, obj):
        return f"${obj.get_total_price()}"
    get_total_price.short_description = "Precio Total"


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'date', 'total_sales', 'total_revenue', 'is_closed']
    list_filter = ['tenant', 'is_closed', 'date']
    search_fields = ['tenant__name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at', 'closed_at']
    
    fieldsets = (
        ('Información', {
            'fields': ('tenant', 'date', 'is_closed', 'closed_by')
        }),
        ('Métricas de Ventas', {
            'fields': ('total_sales', 'total_revenue', 'cash_sales', 'card_sales')
        }),
        ('Productos Populares', {
            'fields': ('top_products',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'closed_at'),
            'classes': ('collapse',)
        }),
    )