from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

from sales.models import Sale, DailySummary
from products.models import Product
from accounts.models import Tenant


@login_required
def dashboard_view(request):
    """Vista principal del dashboard"""
    user = request.user
    
    # Solo usuarios con tenant pueden acceder
    if not user.tenant:
        messages.error(request, 'Tu usuario no está asignado a ningún negocio. Contacta al administrador.')
        return redirect('/admin/')
    
    # Obtener estadísticas del día
    today = timezone.now().date()
    
    # Ventas del día
    today_sales = Sale.objects.filter(
        tenant=user.tenant,
        created_at__date=today
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    # Productos con stock bajo
    low_stock_products = Product.objects.filter(
        tenant=user.tenant,
        track_inventory=True,
        current_stock__lte=F('min_stock')
    ).count()
    
    # Total de productos
    total_products = Product.objects.filter(tenant=user.tenant).count()
    
    # Ventas recientes (últimas 10)
    recent_sales = Sale.objects.filter(
        tenant=user.tenant
    ).select_related('payment_method').prefetch_related('items').order_by('-created_at')[:10]
    
    stats = {
        'today_sales': today_sales['total'] or 0,
        'today_tickets': today_sales['count'] or 0,
        'low_stock': low_stock_products,
        'total_products': total_products,
    }
    
    context = {
        'stats': stats,
        'recent_sales': recent_sales,
    }
    
    return render(request, 'dashboard.html', context)


def simple_login_view(request):
    """Vista simple de login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'login.html')


def logout_view(request):
    """Vista de logout"""
    logout(request)
    return redirect('login')


@login_required 
def pos_view(request):
    """Vista del punto de venta (POS)"""
    if not request.user.tenant:
        return redirect('dashboard')
    
    # Obtener productos por categoría
    from products.models import Category
    categories = Category.objects.filter(
        tenant=request.user.tenant,
        is_active=True
    ).prefetch_related('product_set').order_by('sort_order', 'name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'pos.html', context)


@login_required
def products_view(request):
    """Vista de gestión de productos"""
    if not request.user.tenant:
        return redirect('dashboard')
    
    products = Product.objects.filter(
        tenant=request.user.tenant
    ).select_related('category').order_by('category', 'sort_order', 'name')
    
    context = {
        'products': products,
    }
    
    return render(request, 'products.html', context)


@login_required
def reports_view(request):
    """Vista de reportes básicos"""
    if not request.user.tenant:
        return redirect('dashboard')
    
    # Ventas de los últimos 7 días
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=6)
    
    daily_sales = []
    current_date = start_date
    while current_date <= end_date:
        sales = Sale.objects.filter(
            tenant=request.user.tenant,
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