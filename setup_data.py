#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_saas.settings')
django.setup()

from accounts.models import BusinessType

# Crear tipos de negocio básicos
pizzeria, created = BusinessType.objects.get_or_create(
    code='pizzeria',
    defaults={
        'name': 'Pizzería',
        'description': 'Negocio especializado en pizzas, empanadas y comida rapida',
        'default_categories': [
            {'name': 'Pizzas', 'icon': 'pizza', 'color': '#EF4444'},
            {'name': 'Empanadas', 'icon': 'empanada', 'color': '#F59E0B'},
            {'name': 'Bebidas', 'icon': 'drink', 'color': '#3B82F6'},
            {'name': 'Postres', 'icon': 'dessert', 'color': '#EC4899'},
        ],
        'default_products': [],
        'default_roles': ['owner', 'admin', 'cashier', 'cook', 'delivery']
    }
)

heladeria, created = BusinessType.objects.get_or_create(
    code='heladeria',
    defaults={
        'name': 'Heladería',
        'description': 'Negocio de helados artesanales, batidos y postres frios',
        'default_categories': [
            {'name': 'Helados', 'icon': 'ice-cream', 'color': '#EC4899'},
            {'name': 'Batidos', 'icon': 'smoothie', 'color': '#8B5CF6'},
            {'name': 'Tortas', 'icon': 'cake', 'color': '#EF4444'},
            {'name': 'Cafe', 'icon': 'coffee', 'color': '#A3A3A3'},
        ],
        'default_products': [],
        'default_roles': ['owner', 'admin', 'cashier', 'server']
    }
)

print("Business types creados exitosamente!")
print(f"Total: {BusinessType.objects.count()}")