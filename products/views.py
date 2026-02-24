from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation

from .models import Product, Category


@login_required
def product_list(request):
    """List all products grouped by category."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    categories = Category.objects.filter(
        tenant=tenant
    ).prefetch_related('product_set').order_by('sort_order', 'name')

    # Also get uncategorized products (shouldn't happen, but safety)
    products = Product.objects.filter(
        tenant=tenant
    ).select_related('category').order_by('category__sort_order', 'sort_order', 'name')

    context = {
        'categories': categories,
        'products': products,
        'active_page': 'products',
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_create(request):
    """Create a new product. GET shows form, POST creates product."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            base_price = request.POST.get('base_price', '0')
            has_variants = request.POST.get('has_variants') == 'on'
            requires_preparation = request.POST.get('requires_preparation') == 'on'
            is_active = request.POST.get('is_active') == 'on'

            if not name:
                messages.error(request, 'El nombre del producto es obligatorio.')
                raise ValueError('Missing name')

            if not category_id:
                messages.error(request, 'Debe seleccionar una categoría.')
                raise ValueError('Missing category')

            category = get_object_or_404(Category, id=category_id, tenant=tenant)

            try:
                base_price = Decimal(base_price)
                if base_price <= 0:
                    raise ValueError()
            except (InvalidOperation, ValueError):
                messages.error(request, 'El precio debe ser un número mayor a 0.')
                raise ValueError('Invalid price')

            product = Product.objects.create(
                tenant=tenant,
                category=category,
                name=name,
                description=description,
                base_price=base_price,
                has_variants=has_variants,
                requires_preparation=requires_preparation,
                is_active=is_active,
            )
            if request.FILES.get('image'):
                product.image = request.FILES['image']
                product.save(update_fields=['image'])

            messages.success(request, f'Producto "{product.name}" creado exitosamente.')
            return redirect('products')

        except ValueError:
            # Re-render form with existing data
            pass

    categories = Category.objects.filter(tenant=tenant, is_active=True).order_by('sort_order', 'name')
    context = {
        'categories': categories,
        'editing': False,
        'active_page': 'products',
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_edit(request, product_id):
    """Edit a product. GET shows form with data, POST updates."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    product = get_object_or_404(Product, id=product_id, tenant=tenant)

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            base_price = request.POST.get('base_price', '0')
            has_variants = request.POST.get('has_variants') == 'on'
            requires_preparation = request.POST.get('requires_preparation') == 'on'
            is_active = request.POST.get('is_active') == 'on'

            if not name:
                messages.error(request, 'El nombre del producto es obligatorio.')
                raise ValueError('Missing name')

            if not category_id:
                messages.error(request, 'Debe seleccionar una categoría.')
                raise ValueError('Missing category')

            category = get_object_or_404(Category, id=category_id, tenant=tenant)

            try:
                base_price = Decimal(base_price)
                if base_price <= 0:
                    raise ValueError()
            except (InvalidOperation, ValueError):
                messages.error(request, 'El precio debe ser un número mayor a 0.')
                raise ValueError('Invalid price')

            product.category = category
            product.name = name
            product.description = description
            product.base_price = base_price
            product.has_variants = has_variants
            product.requires_preparation = requires_preparation
            product.is_active = is_active

            if request.POST.get('remove_image'):
                product.image = ''
            elif request.FILES.get('image'):
                product.image = request.FILES['image']

            product.save()

            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            return redirect('products')

        except ValueError:
            pass

    categories = Category.objects.filter(tenant=tenant, is_active=True).order_by('sort_order', 'name')
    context = {
        'product': product,
        'categories': categories,
        'editing': True,
        'active_page': 'products',
    }
    return render(request, 'products/product_form.html', context)


@login_required
@require_POST
def product_delete(request, product_id):
    """Delete a product. POST only."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    product = get_object_or_404(Product, id=product_id, tenant=tenant)

    # Check if product has sales history - soft delete instead
    if product.saleitem_set.exists():
        product.is_active = False
        product.save(update_fields=['is_active'])
        messages.warning(request, f'Producto "{product.name}" desactivado (tiene historial de ventas).')
    else:
        product_name = product.name
        product.delete()
        messages.success(request, f'Producto "{product_name}" eliminado.')

    return redirect('products')


@login_required
@require_POST
def product_toggle(request, product_id):
    """Toggle product is_active status. POST only."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    product = get_object_or_404(Product, id=product_id, tenant=tenant)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])

    status = 'activado' if product.is_active else 'desactivado'
    messages.success(request, f'Producto "{product.name}" {status}.')
    return redirect('products')


# --- Category views ---

@login_required
def category_list(request):
    """List all categories for the tenant."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    categories = Category.objects.filter(
        tenant=tenant
    ).annotate(
        product_count=models.Count('product')
    ).order_by('sort_order', 'name')

    context = {
        'categories': categories,
        'active_page': 'categories',
    }
    return render(request, 'products/category_list.html', context)


@login_required
def category_create(request):
    """Create a new category. GET shows form, POST creates."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '').strip()
        color = request.POST.get('color', '#3B82F6').strip()
        sort_order = request.POST.get('sort_order', '0')

        if not name:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
        else:
            try:
                sort_order = int(sort_order)
            except (ValueError, TypeError):
                sort_order = 0

            # Check for duplicate name
            if Category.objects.filter(tenant=tenant, name=name).exists():
                messages.error(request, f'Ya existe una categoría con el nombre "{name}".')
            else:
                category = Category.objects.create(
                    tenant=tenant,
                    name=name,
                    description=description,
                    icon=icon,
                    color=color,
                    sort_order=sort_order,
                )
                messages.success(request, f'Categoría "{category.name}" creada exitosamente.')
                return redirect('categories')

    context = {
        'editing': False,
        'active_page': 'categories',
    }
    return render(request, 'products/category_form.html', context)


@login_required
def category_edit(request, category_id):
    """Edit a category. GET shows form with data, POST updates."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    category = get_object_or_404(Category, id=category_id, tenant=tenant)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '').strip()
        color = request.POST.get('color', '#3B82F6').strip()
        sort_order = request.POST.get('sort_order', '0')

        if not name:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
        else:
            try:
                sort_order = int(sort_order)
            except (ValueError, TypeError):
                sort_order = 0

            # Check for duplicate name (exclude current)
            if Category.objects.filter(tenant=tenant, name=name).exclude(id=category.id).exists():
                messages.error(request, f'Ya existe una categoría con el nombre "{name}".')
            else:
                category.name = name
                category.description = description
                category.icon = icon
                category.color = color
                category.sort_order = sort_order
                category.save()

                messages.success(request, f'Categoría "{category.name}" actualizada exitosamente.')
                return redirect('categories')

    context = {
        'category': category,
        'editing': True,
        'active_page': 'categories',
    }
    return render(request, 'products/category_form.html', context)


@login_required
@require_POST
def category_delete(request, category_id):
    """Delete a category. POST only."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    category = get_object_or_404(Category, id=category_id, tenant=tenant)

    # Check if category has products
    if category.product_set.exists():
        messages.error(
            request,
            f'No se puede eliminar la categoría "{category.name}" porque tiene productos asociados.'
        )
        return redirect('categories')

    category_name = category.name
    category.delete()

    messages.success(request, f'Categoría "{category_name}" eliminada.')
    return redirect('categories')
