#!/usr/bin/env python
"""
Script para poblar la base de datos con datos iniciales.
Ejecutar: python manage.py shell < populate_initial_data.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_saas.settings')
django.setup()

from accounts.models import BusinessType
from products.models import BUSINESS_TYPE_TEMPLATES
from sales.models import BUSINESS_PAYMENT_METHODS

def populate_business_types():
    """Crear tipos de negocio con sus configuraciones"""
    
    business_types_data = [
        {
            'code': 'pizzeria',
            'name': 'Pizzería',
            'description': 'Negocio especializado en pizzas, empanadas y comida rápida',
            'default_categories': [
                {'name': 'Pizzas', 'icon': '🍕', 'color': '#EF4444'},
                {'name': 'Empanadas', 'icon': '🥟', 'color': '#F59E0B'},
                {'name': 'Bebidas', 'icon': '🥤', 'color': '#3B82F6'},
                {'name': 'Postres', 'icon': '🍰', 'color': '#EC4899'},
            ],
            'default_products': [
                {'name': 'Pizza Muzzarella', 'category': 'Pizzas', 'price': 8500, 'has_variants': True},
                {'name': 'Pizza Napolitana', 'category': 'Pizzas', 'price': 9000, 'has_variants': True},
                {'name': 'Empanada Carne', 'category': 'Empanadas', 'price': 800},
                {'name': 'Coca Cola 500ml', 'category': 'Bebidas', 'price': 1500},
            ],
            'default_roles': ['owner', 'admin', 'cashier', 'cook', 'delivery']
        },
        {
            'code': 'heladeria',
            'name': 'Heladería',
            'description': 'Negocio de helados artesanales, batidos y postres fríos',
            'default_categories': [
                {'name': 'Helados', 'icon': '🍦', 'color': '#EC4899'},
                {'name': 'Batidos', 'icon': '🥤', 'color': '#8B5CF6'},
                {'name': 'Tortas Heladas', 'icon': '🎂', 'color': '#EF4444'},
                {'name': 'Café', 'icon': '☕', 'color': '#A3A3A3'},
            ],
            'default_products': [
                {'name': 'Helado Dulce de Leche', 'category': 'Helados', 'price': 2500, 'has_variants': True},
                {'name': 'Helado Chocolate', 'category': 'Helados', 'price': 2500, 'has_variants': True},
                {'name': 'Batido Frutilla', 'category': 'Batidos', 'price': 3500},
                {'name': 'Torta Rogel', 'category': 'Tortas Heladas', 'price': 15000},
            ],
            'default_roles': ['owner', 'admin', 'cashier', 'server']
        },
        {
            'code': 'restaurante',
            'name': 'Restaurante',
            'description': 'Restaurante con servicio de mesa y variedad gastronómica',
            'default_categories': [
                {'name': 'Entradas', 'icon': '🥗', 'color': '#10B981'},
                {'name': 'Platos Principales', 'icon': '🍽️', 'color': '#EF4444'},
                {'name': 'Postres', 'icon': '🍰', 'color': '#EC4899'},
                {'name': 'Bebidas', 'icon': '🥤', 'color': '#3B82F6'},
            ],
            'default_products': [
                {'name': 'Ensalada César', 'category': 'Entradas', 'price': 4500},
                {'name': 'Bife de Chorizo', 'category': 'Platos Principales', 'price': 12000, 'has_variants': True},
                {'name': 'Tiramisu', 'category': 'Postres', 'price': 3500},
            ],
            'default_roles': ['owner', 'admin', 'waiter', 'cook', 'cashier']
        },
        {
            'code': 'cafeteria',
            'name': 'Cafetería',
            'description': 'Café, desayunos, meriendas y snacks',
            'default_categories': [
                {'name': 'Cafés', 'icon': '☕', 'color': '#A3A3A3'},
                {'name': 'Desayunos', 'icon': '🥐', 'color': '#F59E0B'},
                {'name': 'Sandwiches', 'icon': '🥪', 'color': '#10B981'},
                {'name': 'Pasteles', 'icon': '🧁', 'color': '#EC4899'},
            ],
            'default_products': [
                {'name': 'Café Americano', 'category': 'Cafés', 'price': 2200, 'has_variants': True},
                {'name': 'Tostadas con Mermelada', 'category': 'Desayunos', 'price': 2800},
                {'name': 'Sandwich Jamón y Queso', 'category': 'Sandwiches', 'price': 3500},
            ],
            'default_roles': ['owner', 'admin', 'barista', 'cashier']
        }
    ]
    
    created_count = 0
    for data in business_types_data:
        business_type, created = BusinessType.objects.get_or_create(
            code=data['code'],
            defaults={
                'name': data['name'],
                'description': data['description'],
                'default_categories': data['default_categories'],
                'default_products': data['default_products'],
                'default_roles': data['default_roles']
            }
        )
        if created:
            created_count += 1
            print(f"✅ Creado: {business_type.name}")
        else:
            print(f"ℹ️ Ya existe: {business_type.name}")
    
    print(f"\n🎉 {created_count} tipos de negocio creados/actualizados")
    return BusinessType.objects.all().count()

if __name__ == '__main__':
    print("🚀 Poblando datos iniciales del sistema...")
    total_types = populate_business_types()
    print(f"\n✅ Setup completo. {total_types} tipos de negocio disponibles.")
    print("\n📝 Próximos pasos:")
    print("1. Crear superuser: python manage.py createsuperuser")
    print("2. Ejecutar servidor: python manage.py runserver")
    print("3. Acceder a /admin para configurar el primer tenant")