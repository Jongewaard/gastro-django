from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta

from sales.models import Sale, PaymentMethod
from products.models import Product, Category
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
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')


def logout_view(request):
    """Logout and redirect to login."""
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
        'low_stock_count': low_stock_count,
        'employees_today_count': employees_today.count(),
    }

    context = {
        'stats': stats,
        'recent_sales': recent_sales,
        'low_stock_ingredients': low_stock_ingredients[:5],
        'employees_today': employees_today,
        'open_register': open_register,
        'register_balance': register_balance,
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
    ).select_related('category').order_by('category__sort_order', 'sort_order', 'name')

    # Payment methods for the POS
    payment_methods = PaymentMethod.objects.filter(
        tenant=tenant,
        is_active=True
    ).order_by('sort_order', 'name')

    context = {
        'categories': categories,
        'products': products,
        'payment_methods': payment_methods,
    }

    return render(request, 'pos.html', context)


@login_required
def products_view(request):
    """Vista de gestion de productos."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    products = Product.objects.filter(
        tenant=tenant
    ).select_related('category').order_by('category', 'sort_order', 'name')

    context = {
        'products': products,
    }

    return render(request, 'products.html', context)


@login_required
def reports_view(request):
    """Vista de reportes basicos."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=6)

    daily_sales = []
    current_date = start_date
    while current_date <= end_date:
        sales = Sale.objects.filter(
            tenant=tenant,
            created_at__date=current_date
        ).aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        daily_sales.append({
            'date': current_date,
            'total': sales['total'] or 0,
            'count': sales['count'] or 0,
        })
        current_date += timedelta(days=1)

    context = {
        'daily_sales': daily_sales,
    }

    return render(request, 'reports.html', context)


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
    }

    return render(request, 'orders.html', context)
