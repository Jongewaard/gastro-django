from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from django.views.decorators.http import require_POST

from .models import Ingredient, StockMovement, Supplier


@login_required
def ingredient_list(request):
    """List all ingredients with stock status indicators."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    ingredients = Ingredient.objects.filter(
        tenant=tenant
    ).select_related('supplier').order_by('name')

    # Add stock status annotations
    low_stock = ingredients.filter(current_stock__lte=F('min_stock'))

    # Calculate total stock value
    total_value = sum(i.stock_value for i in ingredients)

    context = {
        'ingredients': ingredients,
        'low_stock_count': low_stock.count(),
        'total_count': ingredients.count(),
        'total_value': total_value,
        'active_page': 'inventory',
    }
    return render(request, 'inventory/ingredient_list.html', context)


@login_required
def ingredient_create(request):
    """Create a new ingredient. GET shows form, POST creates."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        unit = request.POST.get('unit', 'u')
        current_stock = request.POST.get('current_stock', '0')
        min_stock = request.POST.get('min_stock', '0')
        cost_per_unit = request.POST.get('cost_per_unit', '0')
        supplier_id = request.POST.get('supplier', '')

        if not name:
            messages.error(request, 'El nombre del ingrediente es obligatorio.')
        else:
            try:
                current_stock = Decimal(current_stock) if current_stock else Decimal('0.00')
                min_stock = Decimal(min_stock) if min_stock else Decimal('0.00')
                cost_per_unit = Decimal(cost_per_unit) if cost_per_unit else Decimal('0.00')
            except (InvalidOperation, ValueError):
                messages.error(request, 'Los valores numéricos son inválidos.')
                current_stock = Decimal('0.00')
                min_stock = Decimal('0.00')
                cost_per_unit = Decimal('0.00')

            supplier = None
            if supplier_id:
                try:
                    supplier = Supplier.objects.get(id=supplier_id, tenant=tenant)
                except Supplier.DoesNotExist:
                    pass

            # Check for duplicate name
            if Ingredient.objects.filter(tenant=tenant, name=name).exists():
                messages.error(request, f'Ya existe un ingrediente con el nombre "{name}".')
            else:
                ingredient = Ingredient.objects.create(
                    tenant=tenant,
                    name=name,
                    unit=unit,
                    current_stock=current_stock,
                    min_stock=min_stock,
                    cost_per_unit=cost_per_unit,
                    supplier=supplier,
                )
                messages.success(request, f'Ingrediente "{ingredient.name}" creado exitosamente.')
                return redirect('inventory')

    suppliers = Supplier.objects.filter(tenant=tenant, is_active=True).order_by('name')
    context = {
        'suppliers': suppliers,
        'unit_choices': Ingredient.UNIT_CHOICES,
        'editing': False,
        'active_page': 'inventory',
    }
    return render(request, 'inventory/ingredient_form.html', context)


@login_required
def ingredient_edit(request, ingredient_id):
    """Edit an ingredient. GET shows form with data, POST updates."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    ingredient = get_object_or_404(Ingredient, id=ingredient_id, tenant=tenant)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        unit = request.POST.get('unit', 'u')
        current_stock = request.POST.get('current_stock', '0')
        min_stock = request.POST.get('min_stock', '0')
        cost_per_unit = request.POST.get('cost_per_unit', '0')
        supplier_id = request.POST.get('supplier', '')

        if not name:
            messages.error(request, 'El nombre del ingrediente es obligatorio.')
        else:
            try:
                current_stock = Decimal(current_stock) if current_stock else Decimal('0.00')
                min_stock = Decimal(min_stock) if min_stock else Decimal('0.00')
                cost_per_unit = Decimal(cost_per_unit) if cost_per_unit else Decimal('0.00')
            except (InvalidOperation, ValueError):
                messages.error(request, 'Los valores numéricos son inválidos.')
                return redirect('ingredient_edit', ingredient_id=ingredient.id)

            supplier = None
            if supplier_id:
                try:
                    supplier = Supplier.objects.get(id=supplier_id, tenant=tenant)
                except Supplier.DoesNotExist:
                    pass

            # Check for duplicate name (exclude current)
            if Ingredient.objects.filter(tenant=tenant, name=name).exclude(id=ingredient.id).exists():
                messages.error(request, f'Ya existe un ingrediente con el nombre "{name}".')
            else:
                ingredient.name = name
                ingredient.unit = unit
                ingredient.current_stock = current_stock
                ingredient.min_stock = min_stock
                ingredient.cost_per_unit = cost_per_unit
                ingredient.supplier = supplier
                ingredient.save()

                messages.success(request, f'Ingrediente "{ingredient.name}" actualizado exitosamente.')
                return redirect('inventory')

    suppliers = Supplier.objects.filter(tenant=tenant, is_active=True).order_by('name')
    context = {
        'ingredient': ingredient,
        'suppliers': suppliers,
        'unit_choices': Ingredient.UNIT_CHOICES,
        'editing': True,
        'active_page': 'inventory',
    }
    return render(request, 'inventory/ingredient_form.html', context)


@login_required
@require_POST
def ingredient_delete(request, ingredient_id):
    """Delete an ingredient. POST only."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    ingredient = get_object_or_404(Ingredient, id=ingredient_id, tenant=tenant)
    ingredient_name = ingredient.name
    ingredient.delete()

    messages.success(request, f'Ingrediente "{ingredient_name}" eliminado.')
    return redirect('inventory')


@login_required
def stock_movements(request):
    """
    List recent stock movements.
    Optional `ingredient_id` GET param to filter by ingredient.
    """
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    movements = StockMovement.objects.filter(
        ingredient__tenant=tenant
    ).select_related('ingredient', 'created_by').order_by('-created_at')

    # Optional ingredient filter
    ingredient_id = request.GET.get('ingredient_id')
    ingredient_filter = None
    if ingredient_id:
        try:
            ingredient_filter = Ingredient.objects.get(id=ingredient_id, tenant=tenant)
            movements = movements.filter(ingredient=ingredient_filter)
        except Ingredient.DoesNotExist:
            pass

    # Limit to last 100 movements
    movements = movements[:100]

    ingredients = Ingredient.objects.filter(tenant=tenant).order_by('name')

    context = {
        'movements': movements,
        'ingredients': ingredients,
        'ingredient_filter': ingredient_filter,
        'selected_ingredient': ingredient_filter,
        'active_page': 'stock_movements',
    }
    return render(request, 'inventory/stock_movements.html', context)


@login_required
@require_POST
def stock_movement_add(request):
    """
    Create a StockMovement and apply it to stock.
    POST fields: ingredient_id, movement_type, quantity, unit_cost, notes
    """
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    ingredient_id = request.POST.get('ingredient_id')
    movement_type = request.POST.get('movement_type', '')
    quantity = request.POST.get('quantity', '0')
    unit_cost = request.POST.get('unit_cost', '')
    notes = request.POST.get('notes', '').strip()

    if not ingredient_id or not movement_type or not quantity:
        messages.error(request, 'Ingrediente, tipo de movimiento y cantidad son obligatorios.')
        return redirect('stock_movements')

    ingredient = get_object_or_404(Ingredient, id=ingredient_id, tenant=tenant)

    # Validate movement type
    valid_types = [t[0] for t in StockMovement.MOVEMENT_TYPES]
    if movement_type not in valid_types:
        messages.error(request, 'Tipo de movimiento inválido.')
        return redirect('stock_movements')

    try:
        quantity = Decimal(quantity)
        if quantity <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        messages.error(request, 'La cantidad debe ser un número mayor a 0.')
        return redirect('stock_movements')

    unit_cost_decimal = None
    if unit_cost:
        try:
            unit_cost_decimal = Decimal(unit_cost)
        except (InvalidOperation, ValueError):
            unit_cost_decimal = None

    movement = StockMovement.objects.create(
        ingredient=ingredient,
        movement_type=movement_type,
        quantity=quantity,
        unit_cost=unit_cost_decimal,
        notes=notes,
        created_by=request.user,
    )

    # Apply the movement to stock
    movement.apply_to_stock()

    messages.success(
        request,
        f'Movimiento de stock registrado: {movement.get_movement_type_display()} '
        f'de {quantity} {ingredient.unit} de {ingredient.name}.'
    )
    return redirect('stock_movements')


# --- Supplier views ---

@login_required
def supplier_list(request):
    """List all suppliers for the tenant."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    suppliers = Supplier.objects.filter(tenant=tenant).order_by('name')

    context = {
        'suppliers': suppliers,
        'active_page': 'suppliers',
    }
    return render(request, 'inventory/supplier_list.html', context)


@login_required
def supplier_create(request):
    """Create a new supplier. GET shows form, POST creates."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        contact_name = request.POST.get('contact_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not name:
            messages.error(request, 'El nombre del proveedor es obligatorio.')
        else:
            supplier = Supplier.objects.create(
                tenant=tenant,
                name=name,
                contact_name=contact_name,
                phone=phone,
                email=email,
                address=address,
                notes=notes,
            )
            messages.success(request, f'Proveedor "{supplier.name}" creado exitosamente.')
            return redirect('suppliers')

    context = {
        'editing': False,
        'active_page': 'suppliers',
    }
    return render(request, 'inventory/supplier_form.html', context)


@login_required
def supplier_edit(request, supplier_id):
    """Edit a supplier. GET shows form with data, POST updates."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    supplier = get_object_or_404(Supplier, id=supplier_id, tenant=tenant)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        contact_name = request.POST.get('contact_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not name:
            messages.error(request, 'El nombre del proveedor es obligatorio.')
        else:
            supplier.name = name
            supplier.contact_name = contact_name
            supplier.phone = phone
            supplier.email = email
            supplier.address = address
            supplier.notes = notes
            supplier.save()

            messages.success(request, f'Proveedor "{supplier.name}" actualizado exitosamente.')
            return redirect('suppliers')

    context = {
        'supplier': supplier,
        'editing': True,
        'active_page': 'suppliers',
    }
    return render(request, 'inventory/supplier_form.html', context)
