#!/usr/bin/env python
"""
Script para poblar datos iniciales de la pizzeria.
Ejecutar: venv/Scripts/python manage.py shell < populate_initial_data.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_saas.settings')
django.setup()

from decimal import Decimal
from django.utils import timezone
from accounts.models import BusinessType, Tenant, User
from products.models import Category, Product
from sales.models import PaymentMethod
from inventory.models import Supplier, Ingredient
from employees.models import Employee
from accounting.models import ExpenseCategory

print("=== Creando datos iniciales ===")

# 1. Business Type
bt, _ = BusinessType.objects.get_or_create(
    code='pizzeria',
    defaults={
        'name': 'Pizzeria',
        'description': 'Pizzeria y empanadas',
        'default_categories': {
            'categories': ['Pizzas', 'Empanadas', 'Bebidas', 'Postres']
        },
    }
)
print(f"  BusinessType: {bt}")

# 2. Tenant
tenant, _ = Tenant.objects.get_or_create(
    slug='la-esquina',
    defaults={
        'name': 'Pizzeria La Esquina',
        'business_type': bt,
        'owner_name': 'Admin',
        'phone': '11-1234-5678',
        'address': 'Av. Corrientes 1234, CABA',
        'tax_rate': Decimal('21.00'),
    }
)
print(f"  Tenant: {tenant}")

# 3. Superuser
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_superuser(
        username='admin',
        password='admin123',
        email='admin@gastro.local',
        first_name='Admin',
        last_name='Sistema',
        tenant=tenant,
        role='owner',
    )
    print(f"  Superuser: admin / admin123")
else:
    admin_user = User.objects.get(username='admin')
    print(f"  Superuser ya existe: {admin_user}")

# 4. Staff user (cajero)
if not User.objects.filter(username='cajero').exists():
    cajero = User.objects.create_user(
        username='cajero',
        password='cajero123',
        first_name='Maria',
        last_name='Gonzalez',
        tenant=tenant,
        role='cashier',
        is_staff=False,
    )
    print(f"  Cajero: cajero / cajero123")

# 5. Categories
categories_data = [
    {'name': 'Pizzas', 'icon': 'pizza', 'color': '#EF4444', 'sort_order': 1},
    {'name': 'Empanadas', 'icon': 'empanada', 'color': '#F59E0B', 'sort_order': 2},
    {'name': 'Bebidas', 'icon': 'bebida', 'color': '#3B82F6', 'sort_order': 3},
    {'name': 'Postres', 'icon': 'postre', 'color': '#EC4899', 'sort_order': 4},
]
cats = {}
for cd in categories_data:
    cat, _ = Category.objects.get_or_create(
        tenant=tenant, name=cd['name'],
        defaults=cd
    )
    cats[cd['name']] = cat
print(f"  Categorias: {len(cats)}")

# 6. Products
products_data = [
    {'name': 'Muzzarella', 'category': 'Pizzas', 'price': '8500.00'},
    {'name': 'Napolitana', 'category': 'Pizzas', 'price': '9000.00'},
    {'name': 'Fugazzeta', 'category': 'Pizzas', 'price': '9500.00'},
    {'name': 'Calabresa', 'category': 'Pizzas', 'price': '9500.00'},
    {'name': 'Especial', 'category': 'Pizzas', 'price': '10500.00'},
    {'name': 'Roquefort', 'category': 'Pizzas', 'price': '10000.00'},
    {'name': 'Jamon y Morron', 'category': 'Pizzas', 'price': '10000.00'},
    {'name': 'Cuatro Quesos', 'category': 'Pizzas', 'price': '11000.00'},
    {'name': 'Empanada Carne', 'category': 'Empanadas', 'price': '1200.00'},
    {'name': 'Empanada J&Q', 'category': 'Empanadas', 'price': '1200.00'},
    {'name': 'Empanada Pollo', 'category': 'Empanadas', 'price': '1200.00'},
    {'name': 'Empanada Humita', 'category': 'Empanadas', 'price': '1200.00'},
    {'name': 'Empanada Verdura', 'category': 'Empanadas', 'price': '1100.00'},
    {'name': 'Coca Cola 500ml', 'category': 'Bebidas', 'price': '2000.00'},
    {'name': 'Coca Cola 1.5L', 'category': 'Bebidas', 'price': '3500.00'},
    {'name': 'Sprite 500ml', 'category': 'Bebidas', 'price': '2000.00'},
    {'name': 'Agua mineral 500ml', 'category': 'Bebidas', 'price': '1200.00'},
    {'name': 'Cerveza Quilmes 1L', 'category': 'Bebidas', 'price': '3000.00'},
    {'name': 'Flan casero', 'category': 'Postres', 'price': '3500.00'},
    {'name': 'Vigilante', 'category': 'Postres', 'price': '4000.00'},
]
for pd in products_data:
    Product.objects.get_or_create(
        tenant=tenant, name=pd['name'],
        defaults={
            'category': cats[pd['category']],
            'base_price': Decimal(pd['price']),
            'requires_preparation': pd['category'] in ('Pizzas', 'Empanadas', 'Postres'),
        }
    )
print(f"  Productos: {len(products_data)}")

# 7. Payment Methods
pm_data = [
    {'name': 'Efectivo', 'is_cash': True, 'sort_order': 1},
    {'name': 'Debito', 'requires_reference': True, 'sort_order': 2},
    {'name': 'Credito', 'requires_reference': True, 'sort_order': 3},
    {'name': 'Transferencia', 'requires_reference': True, 'sort_order': 4},
    {'name': 'MercadoPago', 'requires_reference': True, 'sort_order': 5},
]
for pmd in pm_data:
    PaymentMethod.objects.get_or_create(
        tenant=tenant, name=pmd['name'],
        defaults=pmd
    )
print(f"  Metodos de pago: {len(pm_data)}")

# 8. Suppliers
suppliers_data = [
    {'name': 'Distribuidora Norte', 'contact_name': 'Carlos', 'phone': '11-5555-0001'},
    {'name': 'Lacteos del Sur', 'contact_name': 'Ana', 'phone': '11-5555-0002'},
    {'name': 'Bebidas Express', 'contact_name': 'Pedro', 'phone': '11-5555-0003'},
]
sups = {}
for sd in suppliers_data:
    sup, _ = Supplier.objects.get_or_create(
        tenant=tenant, name=sd['name'],
        defaults=sd
    )
    sups[sd['name']] = sup
print(f"  Proveedores: {len(sups)}")

# 9. Ingredients
ingredients_data = [
    {'name': 'Harina 000', 'unit': 'kg', 'stock': '50', 'min': '10', 'cost': '800', 'sup': 'Distribuidora Norte'},
    {'name': 'Muzzarella', 'unit': 'kg', 'stock': '20', 'min': '5', 'cost': '5500', 'sup': 'Lacteos del Sur'},
    {'name': 'Salsa de tomate', 'unit': 'l', 'stock': '15', 'min': '5', 'cost': '1200', 'sup': 'Distribuidora Norte'},
    {'name': 'Jamon cocido', 'unit': 'kg', 'stock': '8', 'min': '3', 'cost': '7000', 'sup': 'Distribuidora Norte'},
    {'name': 'Morron', 'unit': 'kg', 'stock': '5', 'min': '2', 'cost': '3000', 'sup': 'Distribuidora Norte'},
    {'name': 'Cebolla', 'unit': 'kg', 'stock': '10', 'min': '3', 'cost': '1500', 'sup': 'Distribuidora Norte'},
    {'name': 'Roquefort', 'unit': 'kg', 'stock': '3', 'min': '1', 'cost': '9000', 'sup': 'Lacteos del Sur'},
    {'name': 'Huevos', 'unit': 'doc', 'stock': '5', 'min': '2', 'cost': '4000', 'sup': 'Distribuidora Norte'},
    {'name': 'Levadura', 'unit': 'kg', 'stock': '3', 'min': '1', 'cost': '2500', 'sup': 'Distribuidora Norte'},
    {'name': 'Aceite', 'unit': 'l', 'stock': '10', 'min': '3', 'cost': '2000', 'sup': 'Distribuidora Norte'},
    {'name': 'Coca Cola 500ml', 'unit': 'u', 'stock': '48', 'min': '12', 'cost': '1000', 'sup': 'Bebidas Express'},
    {'name': 'Coca Cola 1.5L', 'unit': 'u', 'stock': '24', 'min': '6', 'cost': '1800', 'sup': 'Bebidas Express'},
]
for igd in ingredients_data:
    Ingredient.objects.get_or_create(
        tenant=tenant, name=igd['name'],
        defaults={
            'unit': igd['unit'],
            'current_stock': Decimal(igd['stock']),
            'min_stock': Decimal(igd['min']),
            'cost_per_unit': Decimal(igd['cost']),
            'supplier': sups.get(igd['sup']),
        }
    )
print(f"  Ingredientes: {len(ingredients_data)}")

# 10. Employees
employees_data = [
    {'first_name': 'Carlos', 'last_name': 'Rodriguez', 'position': 'pizzero', 'phone': '11-4444-0001', 'salary': '350000'},
    {'first_name': 'Laura', 'last_name': 'Martinez', 'position': 'cajero', 'phone': '11-4444-0002', 'salary': '280000'},
    {'first_name': 'Diego', 'last_name': 'Fernandez', 'position': 'delivery', 'phone': '11-4444-0003', 'salary': '250000'},
    {'first_name': 'Sofia', 'last_name': 'Lopez', 'position': 'ayudante', 'phone': '11-4444-0004', 'salary': '220000'},
    {'first_name': 'Martin', 'last_name': 'Garcia', 'position': 'cocinero', 'phone': '11-4444-0005', 'salary': '320000'},
]
for ed in employees_data:
    Employee.objects.get_or_create(
        tenant=tenant,
        first_name=ed['first_name'],
        last_name=ed['last_name'],
        defaults={
            'position': ed['position'],
            'phone': ed['phone'],
            'monthly_salary': Decimal(ed['salary']),
        }
    )
print(f"  Empleados: {len(employees_data)}")

# 11. Expense Categories
expense_cats = ['Insumos', 'Servicios', 'Alquiler', 'Sueldos', 'Impuestos', 'Mantenimiento', 'Otros']
for ec in expense_cats:
    ExpenseCategory.objects.get_or_create(tenant=tenant, name=ec)
print(f"  Categorias de gasto: {len(expense_cats)}")

print("\n=== DATOS INICIALES CREADOS ===")
print(f"  Negocio: {tenant.name}")
print(f"  Login: admin / admin123")
print(f"  Login cajero: cajero / cajero123")
print(f"  URL: http://127.0.0.1:8000/")
