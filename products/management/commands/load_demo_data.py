"""
Carga datos de ejemplo para probar el sistema.
Uso: python manage.py load_demo_data [--business-name "Mi Pizzeria"]
Idempotente: se puede ejecutar multiples veces sin duplicar datos.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import BusinessType, Tenant, User
from products.models import Category, Product, ProductVariant
from sales.models import PaymentMethod
from inventory.models import Supplier, Ingredient, RecipeItem
from employees.models import Employee
from accounting.models import ExpenseCategory


class Command(BaseCommand):
    help = 'Carga datos de ejemplo (productos, ingredientes, recetas, empleados, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--business-name',
            default='Pizzeria Demo',
            help='Nombre del negocio de ejemplo (default: Pizzeria Demo)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Cargar datos aunque ya existan productos en el sistema',
        )

    def handle(self, *args, **options):
        # Safety check: don't run if data already exists
        if not options['force']:
            if Product.objects.exists():
                self.stdout.write('')
                self.stdout.write(self.style.WARNING(
                    '  Ya hay productos cargados en el sistema.'
                ))
                self.stdout.write(self.style.WARNING(
                    '  Los datos de ejemplo no se cargaron para no interferir.'
                ))
                self.stdout.write('')
                self.stdout.write(
                    '  Si realmente queres cargarlos, usa: '
                    'python manage.py load_demo_data --force'
                )
                self.stdout.write('')
                return

        business_name = options['business_name']
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=== Cargando datos de ejemplo ==='))

        # 1. BusinessType
        bt, _ = BusinessType.objects.get_or_create(
            code='pizzeria',
            defaults={
                'name': 'Pizzeria',
                'description': 'Pizzeria y empanadas',
                'default_categories': [
                    {'name': 'Pizzas', 'icon': 'pizza', 'color': '#EF4444'},
                    {'name': 'Empanadas', 'icon': 'empanada', 'color': '#F59E0B'},
                    {'name': 'Bebidas', 'icon': 'drink', 'color': '#3B82F6'},
                    {'name': 'Postres', 'icon': 'dessert', 'color': '#EC4899'},
                ],
            }
        )

        # 2. Tenant - use existing or create
        tenant = Tenant.objects.filter(is_active=True).first()
        if tenant:
            self.stdout.write(f'  Usando negocio existente: {tenant.name}')
        else:
            tenant, _ = Tenant.objects.get_or_create(
                slug='demo',
                defaults={
                    'name': business_name,
                    'business_type': bt,
                    'owner_name': 'Admin',
                    'phone': '11-1234-5678',
                    'address': 'Av. Corrientes 1234',
                    'tax_rate': Decimal('21.00'),
                }
            )
            self.stdout.write(f'  Negocio creado: {tenant.name}')

        # Assign tenant to users that don't have one
        User.objects.filter(tenant__isnull=True, is_superuser=True).update(
            tenant=tenant, role='owner'
        )

        # 3. Categories
        categories_data = [
            {'name': 'Pizzas', 'icon': 'pizza', 'color': '#EF4444', 'sort_order': 1},
            {'name': 'Empanadas', 'icon': 'empanada', 'color': '#F59E0B', 'sort_order': 2},
            {'name': 'Bebidas', 'icon': 'bebida', 'color': '#3B82F6', 'sort_order': 3},
            {'name': 'Postres', 'icon': 'postre', 'color': '#EC4899', 'sort_order': 4},
        ]
        cats = {}
        for cd in categories_data:
            cat, _ = Category.objects.get_or_create(
                tenant=tenant, name=cd['name'], defaults=cd
            )
            cats[cd['name']] = cat
        self.stdout.write(f'  Categorias: {len(cats)}')

        # 4. Products
        products_data = [
            # Pizzas (con variantes)
            {'name': 'Muzzarella', 'cat': 'Pizzas', 'price': '8500', 'variants': True, 'prep': True},
            {'name': 'Napolitana', 'cat': 'Pizzas', 'price': '9000', 'variants': True, 'prep': True},
            {'name': 'Fugazzeta', 'cat': 'Pizzas', 'price': '9500', 'variants': True, 'prep': True},
            {'name': 'Calabresa', 'cat': 'Pizzas', 'price': '9500', 'variants': True, 'prep': True},
            {'name': 'Especial', 'cat': 'Pizzas', 'price': '10500', 'variants': True, 'prep': True},
            {'name': 'Roquefort', 'cat': 'Pizzas', 'price': '10000', 'variants': True, 'prep': True},
            {'name': 'Jamon y Morron', 'cat': 'Pizzas', 'price': '10000', 'variants': True, 'prep': True},
            {'name': 'Cuatro Quesos', 'cat': 'Pizzas', 'price': '11000', 'variants': True, 'prep': True},
            # Empanadas
            {'name': 'Empanada Carne', 'cat': 'Empanadas', 'price': '1200', 'prep': True},
            {'name': 'Empanada J&Q', 'cat': 'Empanadas', 'price': '1200', 'prep': True},
            {'name': 'Empanada Pollo', 'cat': 'Empanadas', 'price': '1200', 'prep': True},
            {'name': 'Empanada Humita', 'cat': 'Empanadas', 'price': '1200', 'prep': True},
            {'name': 'Empanada Verdura', 'cat': 'Empanadas', 'price': '1100', 'prep': True},
            # Bebidas
            {'name': 'Coca Cola 500ml', 'cat': 'Bebidas', 'price': '2000'},
            {'name': 'Coca Cola 1.5L', 'cat': 'Bebidas', 'price': '3500'},
            {'name': 'Sprite 500ml', 'cat': 'Bebidas', 'price': '2000'},
            {'name': 'Agua mineral 500ml', 'cat': 'Bebidas', 'price': '1200'},
            {'name': 'Cerveza Quilmes 1L', 'cat': 'Bebidas', 'price': '3000'},
            # Postres
            {'name': 'Flan casero', 'cat': 'Postres', 'price': '3500', 'prep': True},
            {'name': 'Vigilante', 'cat': 'Postres', 'price': '4000'},
        ]

        prods = {}
        for pd in products_data:
            prod, _ = Product.objects.get_or_create(
                tenant=tenant, name=pd['name'],
                defaults={
                    'category': cats[pd['cat']],
                    'base_price': Decimal(pd['price']),
                    'has_variants': pd.get('variants', False),
                    'requires_preparation': pd.get('prep', False),
                }
            )
            prods[pd['name']] = prod
        self.stdout.write(f'  Productos: {len(prods)}')

        # 5. Variants for pizzas (sizes + toppings)
        variant_count = 0
        pizza_names = [p['name'] for p in products_data if p['cat'] == 'Pizzas']

        size_variants = [
            {'name': 'Grande', 'price_modifier': Decimal('0'), 'is_default': True, 'sort_order': 1},
            {'name': 'Chica', 'price_modifier': Decimal('-2000'), 'sort_order': 2},
        ]
        topping_variants = [
            {'name': 'Extra muzzarella', 'price_modifier': Decimal('1500'), 'sort_order': 1},
            {'name': 'Jamon', 'price_modifier': Decimal('2000'), 'sort_order': 2},
            {'name': 'Huevo frito', 'price_modifier': Decimal('1000'), 'sort_order': 3},
        ]

        for pname in pizza_names:
            prod = prods[pname]
            for sv in size_variants:
                _, created = ProductVariant.objects.get_or_create(
                    product=prod, variant_type='size', name=sv['name'],
                    defaults=sv,
                )
                if created:
                    variant_count += 1
            for tv in topping_variants:
                _, created = ProductVariant.objects.get_or_create(
                    product=prod, variant_type='topping', name=tv['name'],
                    defaults=tv,
                )
                if created:
                    variant_count += 1
        self.stdout.write(f'  Variantes: {variant_count}')

        # 6. Payment Methods
        pm_data = [
            {'name': 'Efectivo', 'is_cash': True, 'sort_order': 1},
            {'name': 'Debito', 'requires_reference': True, 'sort_order': 2},
            {'name': 'Credito', 'requires_reference': True, 'sort_order': 3},
            {'name': 'Transferencia', 'requires_reference': True, 'sort_order': 4},
            {'name': 'MercadoPago', 'requires_reference': True, 'sort_order': 5},
        ]
        for pmd in pm_data:
            PaymentMethod.objects.get_or_create(
                tenant=tenant, name=pmd['name'], defaults=pmd
            )
        self.stdout.write(f'  Metodos de pago: {len(pm_data)}')

        # 7. Suppliers
        suppliers_data = [
            {'name': 'Distribuidora Norte', 'contact_name': 'Carlos', 'phone': '11-5555-0001'},
            {'name': 'Lacteos del Sur', 'contact_name': 'Ana', 'phone': '11-5555-0002'},
            {'name': 'Bebidas Express', 'contact_name': 'Pedro', 'phone': '11-5555-0003'},
        ]
        sups = {}
        for sd in suppliers_data:
            sup, _ = Supplier.objects.get_or_create(
                tenant=tenant, name=sd['name'], defaults=sd
            )
            sups[sd['name']] = sup
        self.stdout.write(f'  Proveedores: {len(sups)}')

        # 8. Ingredients
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
            {'name': 'Calabresa', 'unit': 'kg', 'stock': '5', 'min': '2', 'cost': '6000', 'sup': 'Distribuidora Norte'},
            {'name': 'Queso pategras', 'unit': 'kg', 'stock': '4', 'min': '2', 'cost': '7500', 'sup': 'Lacteos del Sur'},
            {'name': 'Queso provolone', 'unit': 'kg', 'stock': '3', 'min': '1', 'cost': '8000', 'sup': 'Lacteos del Sur'},
            {'name': 'Coca Cola 500ml', 'unit': 'u', 'stock': '48', 'min': '12', 'cost': '1000', 'sup': 'Bebidas Express'},
            {'name': 'Coca Cola 1.5L', 'unit': 'u', 'stock': '24', 'min': '6', 'cost': '1800', 'sup': 'Bebidas Express'},
            {'name': 'Sprite 500ml', 'unit': 'u', 'stock': '24', 'min': '12', 'cost': '1000', 'sup': 'Bebidas Express'},
            {'name': 'Agua mineral 500ml', 'unit': 'u', 'stock': '48', 'min': '12', 'cost': '500', 'sup': 'Bebidas Express'},
            {'name': 'Cerveza Quilmes 1L', 'unit': 'u', 'stock': '24', 'min': '6', 'cost': '1500', 'sup': 'Bebidas Express'},
            {'name': 'Dulce de leche', 'unit': 'kg', 'stock': '3', 'min': '1', 'cost': '4000', 'sup': 'Distribuidora Norte'},
            {'name': 'Dulce de batata', 'unit': 'kg', 'stock': '2', 'min': '1', 'cost': '3500', 'sup': 'Distribuidora Norte'},
            {'name': 'Queso crema', 'unit': 'kg', 'stock': '2', 'min': '1', 'cost': '5000', 'sup': 'Lacteos del Sur'},
        ]
        ings = {}
        for igd in ingredients_data:
            ing, _ = Ingredient.objects.get_or_create(
                tenant=tenant, name=igd['name'],
                defaults={
                    'unit': igd['unit'],
                    'current_stock': Decimal(igd['stock']),
                    'min_stock': Decimal(igd['min']),
                    'cost_per_unit': Decimal(igd['cost']),
                    'supplier': sups.get(igd['sup']),
                }
            )
            ings[igd['name']] = ing
        self.stdout.write(f'  Ingredientes: {len(ings)}')

        # 9. RecipeItems (recetas: que ingredientes lleva cada producto)
        recipes = {
            'Muzzarella': [
                ('Harina 000', '0.400'), ('Muzzarella', '0.300'),
                ('Salsa de tomate', '0.150'), ('Levadura', '0.020'), ('Aceite', '0.030'),
            ],
            'Napolitana': [
                ('Harina 000', '0.400'), ('Muzzarella', '0.250'),
                ('Salsa de tomate', '0.200'), ('Levadura', '0.020'), ('Aceite', '0.030'),
            ],
            'Fugazzeta': [
                ('Harina 000', '0.400'), ('Muzzarella', '0.350'),
                ('Cebolla', '0.300'), ('Levadura', '0.020'), ('Aceite', '0.030'),
            ],
            'Calabresa': [
                ('Harina 000', '0.400'), ('Muzzarella', '0.250'),
                ('Calabresa', '0.200'), ('Salsa de tomate', '0.150'),
                ('Levadura', '0.020'), ('Aceite', '0.030'),
            ],
            'Especial': [
                ('Harina 000', '0.400'), ('Muzzarella', '0.250'),
                ('Jamon cocido', '0.150'), ('Morron', '0.100'),
                ('Salsa de tomate', '0.150'), ('Levadura', '0.020'), ('Aceite', '0.030'),
            ],
            'Roquefort': [
                ('Harina 000', '0.400'), ('Muzzarella', '0.200'),
                ('Roquefort', '0.150'), ('Salsa de tomate', '0.150'),
                ('Levadura', '0.020'), ('Aceite', '0.030'),
            ],
            'Jamon y Morron': [
                ('Harina 000', '0.400'), ('Muzzarella', '0.250'),
                ('Jamon cocido', '0.200'), ('Morron', '0.150'),
                ('Salsa de tomate', '0.150'), ('Levadura', '0.020'), ('Aceite', '0.030'),
            ],
            'Cuatro Quesos': [
                ('Harina 000', '0.400'), ('Muzzarella', '0.200'),
                ('Roquefort', '0.100'), ('Queso pategras', '0.100'),
                ('Queso provolone', '0.100'), ('Salsa de tomate', '0.100'),
                ('Levadura', '0.020'), ('Aceite', '0.030'),
            ],
            # Empanadas (cada unidad)
            'Empanada Carne': [
                ('Harina 000', '0.080'), ('Aceite', '0.010'),
            ],
            'Empanada J&Q': [
                ('Harina 000', '0.080'), ('Jamon cocido', '0.040'),
                ('Muzzarella', '0.040'), ('Aceite', '0.010'),
            ],
            'Empanada Pollo': [
                ('Harina 000', '0.080'), ('Aceite', '0.010'),
            ],
            'Empanada Humita': [
                ('Harina 000', '0.080'), ('Aceite', '0.010'),
            ],
            'Empanada Verdura': [
                ('Harina 000', '0.080'), ('Aceite', '0.010'),
            ],
            # Bebidas (1 unidad de stock = 1 producto vendido)
            'Coca Cola 500ml': [('Coca Cola 500ml', '1')],
            'Coca Cola 1.5L': [('Coca Cola 1.5L', '1')],
            'Sprite 500ml': [('Sprite 500ml', '1')],
            'Agua mineral 500ml': [('Agua mineral 500ml', '1')],
            'Cerveza Quilmes 1L': [('Cerveza Quilmes 1L', '1')],
            # Postres
            'Flan casero': [
                ('Huevos', '0.500'), ('Dulce de leche', '0.100'),
            ],
            'Vigilante': [
                ('Dulce de batata', '0.150'), ('Queso crema', '0.100'),
            ],
        }

        recipe_count = 0
        for prod_name, recipe_items in recipes.items():
            if prod_name not in prods:
                continue
            prod = prods[prod_name]
            for ing_name, qty in recipe_items:
                if ing_name not in ings:
                    continue
                _, created = RecipeItem.objects.get_or_create(
                    product=prod, ingredient=ings[ing_name],
                    defaults={'quantity_needed': Decimal(qty)}
                )
                if created:
                    recipe_count += 1
        self.stdout.write(f'  Recetas: {recipe_count} ingredientes vinculados')

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
                tenant=tenant, first_name=ed['first_name'], last_name=ed['last_name'],
                defaults={
                    'position': ed['position'],
                    'phone': ed['phone'],
                    'monthly_salary': Decimal(ed['salary']),
                }
            )
        self.stdout.write(f'  Empleados: {len(employees_data)}')

        # 11. Expense Categories
        expense_cats = ['Insumos', 'Servicios', 'Alquiler', 'Sueldos', 'Impuestos', 'Mantenimiento', 'Otros']
        for ec in expense_cats:
            ExpenseCategory.objects.get_or_create(tenant=tenant, name=ec)
        self.stdout.write(f'  Categorias de gasto: {len(expense_cats)}')

        # Done
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Datos de ejemplo cargados ==='))
        self.stdout.write(f'  Negocio: {tenant.name}')
        self.stdout.write(f'  {len(prods)} productos, {len(ings)} ingredientes, {recipe_count} recetas')
        self.stdout.write(f'  Todo listo para probar el POS')
        self.stdout.write('')
