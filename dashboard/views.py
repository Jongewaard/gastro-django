from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from datetime import timedelta

import json
from sales.models import Sale, PaymentMethod
from products.models import Product, Category, ProductVariant
from inventory.models import Ingredient
from employees.models import Employee, WorkSchedule
from accounting.models import CashRegister


def simple_login_view(request):
    """Login view with POST authentication."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next', request.GET.get('next', ''))
            if not next_url or not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')


@require_POST
def logout_view(request):
    """Logout and redirect to login. POST only for CSRF protection."""
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    """Main dashboard with stats overview."""
    user = request.user
    tenant = user.tenant

    if not tenant:
        messages.error(
            request,
            'Tu usuario no está asignado a ningún negocio. Contacta al administrador.'
        )
        return redirect('/admin/')

    today = timezone.now().date()

    # Today's sales stats
    today_sales = Sale.objects.filter(
        tenant=tenant,
        created_at__date=today
    ).exclude(status='cancelled').aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )

    # Low stock ingredients
    low_stock_ingredients = Ingredient.objects.filter(
        tenant=tenant,
        is_active=True,
        current_stock__lte=F('min_stock')
    )
    low_stock_count = low_stock_ingredients.count()

    # Employees working today (scheduled for today)
    employees_today = WorkSchedule.objects.filter(
        employee__tenant=tenant,
        employee__is_active=True,
        date=today
    ).select_related('employee')

    # Open cash register info
    open_register = CashRegister.objects.filter(
        tenant=tenant,
        status='open'
    ).first()

    register_balance = None
    if open_register:
        open_register.calculate_expected()
        register_balance = open_register.expected_amount

    # Recent sales (last 10)
    recent_sales = Sale.objects.filter(
        tenant=tenant
    ).select_related('payment_method').prefetch_related('items').order_by('-created_at')[:10]

    stats = {
        'today_sales': today_sales['total'] or 0,
        'today_tickets': today_sales['count'] or 0,
        'low_stock': low_stock_count,
        'employees_today': employees_today.count(),
    }

    context = {
        'stats': stats,
        'recent_sales': recent_sales,
        'low_stock_ingredients': low_stock_ingredients[:5],
        'employees_today_list': employees_today,
        'open_register': open_register,
        'register_balance': register_balance,
        'active_page': 'dashboard',
    }

    return render(request, 'dashboard.html', context)


@login_required
def pos_view(request):
    """Point of Sale page - loads categories and products for the tenant."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    categories = Category.objects.filter(
        tenant=tenant,
        is_active=True
    ).prefetch_related(
        'product_set'
    ).order_by('sort_order', 'name')

    # Filter products to only active ones
    products = Product.objects.filter(
        tenant=tenant,
        is_active=True
    ).select_related('category').prefetch_related('variants').order_by('category__sort_order', 'sort_order', 'name')

    # Build variant data for JS
    products_with_variants = {}
    for p in products:
        if p.has_variants:
            variants_by_type = {}
            for v in p.variants.filter(is_active=True).order_by('variant_type', 'sort_order', 'name'):
                vtype = v.get_variant_type_display()
                if vtype not in variants_by_type:
                    variants_by_type[vtype] = []
                variants_by_type[vtype].append({
                    'id': v.id,
                    'name': v.name,
                    'price_modifier': float(v.price_modifier),
                    'is_default': v.is_default,
                    'type_key': v.variant_type,
                })
            if variants_by_type:
                products_with_variants[p.id] = variants_by_type

    # Payment methods for the POS
    payment_methods = PaymentMethod.objects.filter(
        tenant=tenant,
        is_active=True
    ).order_by('sort_order', 'name')

    context = {
        'categories': categories,
        'products': products,
        'payment_methods': payment_methods,
        'products_variants_json': json.dumps(products_with_variants),
        'active_page': 'pos',
    }

    return render(request, 'pos.html', context)


@login_required
def orders_view(request):
    """Shows orders grouped by status for today."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    today = timezone.now().date()

    # Get today's orders grouped by status
    base_qs = Sale.objects.filter(
        tenant=tenant,
        created_at__date=today
    ).select_related('payment_method', 'created_by').prefetch_related('items__product')

    pending_orders = base_qs.filter(status='pending').order_by('-created_at')
    preparing_orders = base_qs.filter(status='preparing').order_by('-created_at')
    ready_orders = base_qs.filter(status='ready').order_by('-created_at')
    delivered_orders = base_qs.filter(status='delivered').order_by('-created_at')

    context = {
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'delivered_orders': delivered_orders,
        'today': today,
        'active_page': 'orders',
    }

    return render(request, 'orders.html', context)
