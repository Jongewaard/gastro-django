import datetime
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import CashRegister, CashMovement, Expense, ExpenseCategory
from sales.models import Sale, SaleItem


@login_required
def cash_register_view(request):
    """
    Shows current cash register status.
    If no open register, shows "open" button.
    If open, shows movements and running total.
    """
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    open_register = CashRegister.objects.filter(
        tenant=tenant,
        status='open'
    ).first()

    movements = []
    running_total = Decimal('0.00')

    if open_register:
        movements = CashMovement.objects.filter(
            register=open_register
        ).select_related('created_by').order_by('-created_at')

        open_register.calculate_expected()
        running_total = open_register.expected_amount or open_register.opening_amount

    # Recent closed registers
    recent_registers = CashRegister.objects.filter(
        tenant=tenant,
        status='closed'
    ).select_related('opened_by', 'closed_by').order_by('-date')[:10]

    context = {
        'open_register': open_register,
        'movements': movements,
        'running_total': running_total,
        'recent_registers': recent_registers,
    }
    return render(request, 'accounting/cash_register.html', context)


@login_required
@require_POST
def cash_open(request):
    """Open a new cash register with an opening amount."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    # Check if there's already an open register
    existing_open = CashRegister.objects.filter(tenant=tenant, status='open').exists()
    if existing_open:
        messages.error(request, 'Ya hay una caja abierta. Debe cerrarla antes de abrir una nueva.')
        return redirect('cash_register_view')

    opening_amount = request.POST.get('opening_amount', '0')
    try:
        opening_amount = Decimal(opening_amount)
        if opening_amount < 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        messages.error(request, 'El monto de apertura debe ser un número válido.')
        return redirect('cash_register_view')

    register = CashRegister.objects.create(
        tenant=tenant,
        date=timezone.now().date(),
        opened_by=request.user,
        opening_amount=opening_amount,
        status='open',
    )

    messages.success(request, f'Caja abierta con ${opening_amount} de fondo.')
    return redirect('cash_register_view')


@login_required
@require_POST
def cash_close(request):
    """Close the open register with a closing amount. Calculates difference."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    open_register = CashRegister.objects.filter(tenant=tenant, status='open').first()
    if not open_register:
        messages.error(request, 'No hay ninguna caja abierta para cerrar.')
        return redirect('cash_register_view')

    closing_amount = request.POST.get('closing_amount', '0')
    notes = request.POST.get('notes', '').strip()

    try:
        closing_amount = Decimal(closing_amount)
        if closing_amount < 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        messages.error(request, 'El monto de cierre debe ser un número válido.')
        return redirect('cash_register_view')

    # Use the model's close method which calculates expected and difference
    open_register.close(closing_amount=closing_amount, closed_by=request.user)
    if notes:
        open_register.notes = notes
        open_register.save(update_fields=['notes'])

    difference = open_register.difference
    if difference and difference != Decimal('0.00'):
        diff_str = f'+${difference}' if difference > 0 else f'-${abs(difference)}'
        messages.warning(request, f'Caja cerrada. Diferencia detectada: {diff_str}.')
    else:
        messages.success(request, 'Caja cerrada correctamente. Sin diferencias.')

    return redirect('cash_register_view')


@login_required
@require_POST
def cash_movement_add(request):
    """Add a movement to the open cash register."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    open_register = CashRegister.objects.filter(tenant=tenant, status='open').first()
    if not open_register:
        messages.error(request, 'No hay ninguna caja abierta. Abra una caja primero.')
        return redirect('cash_register_view')

    movement_type = request.POST.get('movement_type', '')
    amount = request.POST.get('amount', '0')
    description = request.POST.get('description', '').strip()

    # Validate movement type
    valid_types = [t[0] for t in CashMovement.MOVEMENT_TYPES]
    if movement_type not in valid_types:
        messages.error(request, 'Tipo de movimiento inválido.')
        return redirect('cash_register_view')

    try:
        amount = Decimal(amount)
        if amount == 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        messages.error(request, 'El monto debe ser un número distinto de cero.')
        return redirect('cash_register_view')

    if not description:
        messages.error(request, 'La descripción es obligatoria.')
        return redirect('cash_register_view')

    # For withdrawals and expenses, ensure amount is negative
    if movement_type in ('withdrawal', 'expense') and amount > 0:
        amount = -amount

    # For deposits and sales, ensure amount is positive
    if movement_type in ('deposit', 'sale', 'tip') and amount < 0:
        amount = abs(amount)

    CashMovement.objects.create(
        register=open_register,
        movement_type=movement_type,
        amount=amount,
        description=description,
        created_by=request.user,
    )

    messages.success(request, f'Movimiento de caja registrado: {description}.')
    return redirect('cash_register_view')


@login_required
def expense_list(request):
    """
    List expenses with date filters.
    Optional GET params: date_from, date_to
    """
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    expenses = Expense.objects.filter(
        tenant=tenant
    ).select_related('category', 'paid_by').order_by('-date', '-created_at')

    # Date filters
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    date_from = None
    date_to = None

    if date_from_str:
        try:
            date_from = datetime.date.fromisoformat(date_from_str)
            expenses = expenses.filter(date__gte=date_from)
        except ValueError:
            pass

    if date_to_str:
        try:
            date_to = datetime.date.fromisoformat(date_to_str)
            expenses = expenses.filter(date__lte=date_to)
        except ValueError:
            pass

    # Calculate total
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    context = {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'accounting/expense_list.html', context)


@login_required
def expense_create(request):
    """Create a new expense. GET shows form, POST creates."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    if request.method == 'POST':
        category_id = request.POST.get('category', '')
        description = request.POST.get('description', '').strip()
        amount = request.POST.get('amount', '0')
        date_str = request.POST.get('date', '')
        receipt_number = request.POST.get('receipt_number', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not description:
            messages.error(request, 'La descripción es obligatoria.')
        elif not amount:
            messages.error(request, 'El monto es obligatorio.')
        else:
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    raise ValueError()
            except (InvalidOperation, ValueError):
                messages.error(request, 'El monto debe ser un número mayor a 0.')
                amount = None

            if amount:
                category = None
                if category_id:
                    try:
                        category = ExpenseCategory.objects.get(id=category_id, tenant=tenant)
                    except ExpenseCategory.DoesNotExist:
                        pass

                try:
                    expense_date = datetime.date.fromisoformat(date_str) if date_str else timezone.now().date()
                except ValueError:
                    expense_date = timezone.now().date()

                expense = Expense.objects.create(
                    tenant=tenant,
                    category=category,
                    description=description,
                    amount=amount,
                    date=expense_date,
                    paid_by=request.user,
                    receipt_number=receipt_number,
                    notes=notes,
                )

                # Also register as a cash movement if there's an open register
                open_register = CashRegister.objects.filter(
                    tenant=tenant,
                    status='open'
                ).first()
                if open_register:
                    CashMovement.objects.create(
                        register=open_register,
                        movement_type='expense',
                        amount=-amount,
                        description=f'Gasto: {description}',
                        reference=receipt_number,
                        created_by=request.user,
                    )

                messages.success(request, f'Gasto "{description}" registrado por ${amount}.')
                return redirect('expense_list')

    categories = ExpenseCategory.objects.filter(tenant=tenant, is_active=True).order_by('name')
    context = {
        'expense_categories': categories,
        'editing': False,
    }
    return render(request, 'accounting/expense_form.html', context)


@login_required
def reports_view(request):
    """
    Sales summary for the week.
    Shows daily totals, total revenue, top products, cash vs card breakdown.
    """
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    # Calculate the current week (Monday to Sunday)
    today = timezone.now().date()
    week_start = today - datetime.timedelta(days=today.weekday())  # Monday
    week_end = week_start + datetime.timedelta(days=6)  # Sunday

    # Daily totals for the week
    daily_totals = []
    total_revenue = Decimal('0.00')
    total_tickets = 0
    total_cash = Decimal('0.00')
    total_card = Decimal('0.00')

    current_date = week_start
    while current_date <= week_end:
        day_sales = Sale.objects.filter(
            tenant=tenant,
            created_at__date=current_date
        ).exclude(status='cancelled')

        day_aggregate = day_sales.aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )

        day_total = day_aggregate['total'] or Decimal('0.00')
        day_count = day_aggregate['count'] or 0

        # Cash vs card for this day
        day_cash = day_sales.filter(
            payment_method__is_cash=True
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

        day_card = day_total - day_cash

        daily_totals.append({
            'date': current_date,
            'total': day_total,
            'count': day_count,
            'cash': day_cash,
            'card': day_card,
        })

        total_revenue += day_total
        total_tickets += day_count
        total_cash += day_cash
        total_card += day_card

        current_date += datetime.timedelta(days=1)

    # Top products for the week
    top_products = SaleItem.objects.filter(
        sale__tenant=tenant,
        sale__created_at__date__gte=week_start,
        sale__created_at__date__lte=week_end,
    ).exclude(
        sale__status='cancelled'
    ).values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(models.F('quantity') * models.F('unit_price'))
    ).order_by('-total_quantity')[:10]

    context = {
        'week_start': week_start,
        'week_end': week_end,
        'daily_totals': daily_totals,
        'total_revenue': total_revenue,
        'total_tickets': total_tickets,
        'total_cash': total_cash,
        'total_card': total_card,
        'top_products': top_products,
        'today': today,
    }
    return render(request, 'accounting/reports.html', context)
