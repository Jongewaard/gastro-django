from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class BusinessType(models.Model):
    """Tipos de negocio gastronómico soportados"""
    BUSINESS_TYPES = [
        ('pizzeria', 'Pizzería'),
        ('heladeria', 'Heladería'),
        ('restaurante', 'Restaurante'),
        ('cafeteria', 'Cafetería'),
        ('panaderia', 'Panadería'),
        ('bar', 'Bar/Pub'),
        ('comida_rapida', 'Comida Rápida'),
    ]
    
    code = models.CharField(max_length=20, choices=BUSINESS_TYPES, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    # Template configuration for initial setup
    default_categories = models.JSONField(default=dict, help_text="Categorías por defecto para este tipo de negocio")
    default_products = models.JSONField(default=list, help_text="Productos ejemplo para setup inicial")
    default_roles = models.JSONField(default=list, help_text="Roles de empleados típicos")
    
    class Meta:
        verbose_name = "Tipo de Negocio"
        verbose_name_plural = "Tipos de Negocio"
    
    def __str__(self):
        return self.name


class Tenant(models.Model):
    """Tenant - representa cada negocio gastronómico individual"""
    name = models.CharField(max_length=100, help_text="Nombre del negocio")
    slug = models.SlugField(unique=True, help_text="Identificador único (URL)")
    business_type = models.ForeignKey(BusinessType, on_delete=models.CASCADE)
    
    # Business info
    owner_name = models.CharField(max_length=100, help_text="Nombre del propietario")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    # Configuration
    config = models.JSONField(default=dict, help_text="Configuraciones específicas del negocio")
    timezone = models.CharField(max_length=50, default='America/Argentina/Buenos_Aires')
    currency = models.CharField(max_length=10, default='ARS')
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Negocio (Tenant)"
        verbose_name_plural = "Negocios (Tenants)"
    
    def __str__(self):
        return f"{self.name} ({self.get_business_type_display()})"


class User(AbstractUser):
    """Usuario extendido con soporte multi-tenant"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Role within the tenant
    ROLE_CHOICES = [
        ('owner', 'Propietario'),
        ('admin', 'Administrador'),
        ('manager', 'Encargado'),
        ('employee', 'Empleado'),
        ('cashier', 'Cajero'),
        ('cook', 'Cocinero'),
        ('delivery', 'Delivery'),
        ('counter', 'Contador'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "Sin negocio"
        return f"{self.get_full_name() or self.username} - {tenant_name}"


class TenantMiddleware:
    """Middleware para manejar multi-tenancy básico"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Por ahora usamos tenant via session/user
        # Futuro: subdomain o path-based routing
        if hasattr(request.user, 'tenant') and request.user.tenant:
            request.tenant = request.user.tenant
        else:
            request.tenant = None
            
        response = self.get_response(request)
        return response