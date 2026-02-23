from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import BusinessType, Tenant, User


@admin.register(BusinessType)
class BusinessTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'description']
    list_filter = ['code']
    search_fields = ['name', 'description']
    readonly_fields = ['default_categories', 'default_products', 'default_roles']


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'business_type', 'owner_name', 'is_active', 'created_at']
    list_filter = ['business_type', 'is_active', 'created_at']
    search_fields = ['name', 'owner_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información del Negocio', {
            'fields': ('name', 'slug', 'business_type', 'is_active')
        }),
        ('Datos del Propietario', {
            'fields': ('owner_name', 'email', 'phone', 'address')
        }),
        ('Configuración', {
            'fields': ('config', 'timezone', 'currency'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'tenant', 'role', 'is_active', 'date_joined']
    list_filter = ['tenant', 'role', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información del Negocio', {
            'fields': ('tenant', 'role', 'phone')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información del Negocio', {
            'fields': ('tenant', 'role', 'phone')
        }),
    )