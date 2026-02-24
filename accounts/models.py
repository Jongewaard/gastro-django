from django.db import models
from django.contrib.auth.models import AbstractUser


class BusinessType(models.Model):
    BUSINESS_TYPES = [
        ('pizzeria', 'Pizzeria'),
        ('heladeria', 'Heladeria'),
        ('restaurante', 'Restaurante'),
        ('cafeteria', 'Cafeteria'),
        ('panaderia', 'Panaderia'),
        ('bar', 'Bar/Pub'),
        ('comida_rapida', 'Comida Rapida'),
    ]

    code = models.CharField(max_length=20, choices=BUSINESS_TYPES, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    default_categories = models.JSONField(default=dict)
    default_products = models.JSONField(default=list)
    default_roles = models.JSONField(default=list)

    class Meta:
        verbose_name = "Tipo de Negocio"
        verbose_name_plural = "Tipos de Negocio"

    def __str__(self):
        return self.name


class Tenant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    business_type = models.ForeignKey(BusinessType, on_delete=models.CASCADE)
    owner_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    config = models.JSONField(default=dict)
    timezone = models.CharField(max_length=50, default='America/Argentina/Buenos_Aires')
    currency = models.CharField(max_length=10, default='ARS')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Negocio (Tenant)"
        verbose_name_plural = "Negocios (Tenants)"

    def __str__(self):
        return f"{self.name} ({self.business_type.name})"


class User(AbstractUser):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    ROLE_CHOICES = [
        ('owner', 'Propietario'),
        ('admin', 'Administrador'),
        ('manager', 'Encargado'),
        ('employee', 'Empleado'),
        ('cashier', 'Cajero'),
        ('cook', 'Cocinero'),
        ('delivery', 'Delivery'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        name = self.get_full_name() or self.username
        tenant_name = self.tenant.name if self.tenant else "Sin negocio"
        return f"{name} - {tenant_name}"

    def is_manager_or_above(self):
        return self.role in ('owner', 'admin', 'manager') or self.is_superuser
