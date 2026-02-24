import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Sale, SaleItem, PaymentMethod
from products.models import Product
from accounting.models import CashRegister, CashMovement


@login_required
@require_POST
def sale_create(request):
    """
    Create a new sale with items.
    Expects JSON body:
    {
        "items": [{"product_id": int, "quantity": int, "unit_price": str/float}, ...],
        "customer_name": str (optional),
        "payment_method_id": int
    }
    Returns JSON: {"success": bool, "sale_id": int, "sale_number": str}
    """
    tenant = request.user.tenant
    if not tenant:
        return JsonResponse({'success': False, 'error': 'Usuario sin negocio asignado.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)

    items_data = data.get('items', [])
    customer_name = data.get('customer_name', '')
    payment_method_id = data.get('payment_method_id')

    if not items_data:
        return JsonResponse({'success': False, 'error': 'La venta debe tener al menos un producto.'}, status=400)

    if not payment_method_id:
        return JsonResponse({'success': False, 'error': 'Debe seleccionar un método de pago.'}, status=400)

    try:
        payment_method = PaymentMethod.objects.get(id=payment_method_id, tenant=tenant, is_active=True)
    except PaymentMethod.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Método de pago no válido.'}, status=400)

    try:
        # Generate sale number: tenant_id-YYYYMMDD-sequential
        today = timezone.now().date()
        today_str = today.strftime('%Y%m%d')
        today_count = Sale.objects.filter(
            tenant=tenant,
            created_at__date=today
        ).count() + 1
        sale_number = f"{tenant.id}-{today_str}-{today_count:04d}"

        # Create the sale
        sale = Sale.objects.create(
            tenant=tenant,
            sale_number=sale_number,
            customer_name=customer_name,
            status='pending',
            payment_method=payment_method,
            is_paid=True,
            created_by=request.user,
        )

        # Create sale items
        subtotal = Decimal('0.00')
        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity', 1)
            unit_price = item_data.get('unit_price')

            if not product_id or not unit_price:
                continue

            try:
                product = Product.objects.get(id=product_id, tenant=tenant)
            except Product.DoesNotExist:
                continue

            try:
                unit_price = Decimal(str(unit_price))
                quantity = int(quantity)
                if quantity < 1:
                    quantity = 1
            except (InvalidOperation, ValueError, TypeError):
                continue

            sale_item = SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
            )
            subtotal += sale_item.get_total_price()

        # Verify at least one item was created
        if sale.items.count() == 0:
            sale.delete()
            return JsonResponse({'success': False, 'error': 'Ningún producto válido en la venta.'}, status=400)

        # Calculate totals
        sale.subtotal = subtotal
        tax_rate = tenant.tax_rate or Decimal('0.00')
        sale.tax_amount = subtotal * tax_rate / Decimal('100')
        sale.total_amount = sale.subtotal + sale.tax_amount - sale.discount_amount + sale.delivery_fee
        sale.save()

        # If payment is cash, create a CashMovement in the open register
        if payment_method.is_cash:
            open_register = CashRegister.objects.filter(
                tenant=tenant,
                status='open'
            ).first()
            if open_register:
                CashMovement.objects.create(
                    register=open_register,
                    movement_type='sale',
                    amount=sale.total_amount,
                    description=f'Venta #{sale.sale_number}',
                    reference=sale.sale_number,
                    created_by=request.user,
                )

        return JsonResponse({
            'success': True,
            'sale_id': sale.id,
            'sale_number': sale.sale_number,
            'total_amount': str(sale.total_amount),
        })

    except Exception:
        return JsonResponse({'success': False, 'error': 'Error interno al crear la venta.'}, status=500)


@login_required
@require_POST
def sale_update_status(request, sale_id):
    """
    Update sale status.
    Expects JSON body: {"status": "pending"|"preparing"|"ready"|"delivered"}
    Returns JSON: {"success": bool}
    """
    tenant = request.user.tenant
    if not tenant:
        return JsonResponse({'success': False, 'error': 'Usuario sin negocio asignado.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)

    new_status = data.get('status')
    valid_statuses = ['pending', 'preparing', 'ready', 'delivered']
    if new_status not in valid_statuses:
        return JsonResponse({
            'success': False,
            'error': f'Estado inválido. Opciones: {", ".join(valid_statuses)}'
        }, status=400)

    try:
        sale = Sale.objects.get(id=sale_id, tenant=tenant)
    except Sale.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Venta no encontrada.'}, status=404)

    if sale.status == 'cancelled':
        return JsonResponse({'success': False, 'error': 'No se puede modificar una venta cancelada.'}, status=400)

    sale.status = new_status
    if new_status == 'delivered':
        sale.completed_at = timezone.now()
    sale.save()

    return JsonResponse({
        'success': True,
        'sale_id': sale.id,
        'sale_number': sale.sale_number,
        'new_status': new_status,
        'status_display': sale.get_status_display(),
    })


@login_required
@require_POST
def sale_cancel(request, sale_id):
    """
    Cancel a sale.
    Returns JSON: {"success": bool}
    """
    tenant = request.user.tenant
    if not tenant:
        return JsonResponse({'success': False, 'error': 'Usuario sin negocio asignado.'}, status=403)

    try:
        sale = Sale.objects.get(id=sale_id, tenant=tenant)
    except Sale.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Venta no encontrada.'}, status=404)

    if sale.status == 'cancelled':
        return JsonResponse({'success': False, 'error': 'La venta ya está cancelada.'}, status=400)

    sale.status = 'cancelled'
    sale.save()

    # If the sale was paid in cash, reverse the cash movement in the open register
    if sale.payment_method.is_cash:
        open_register = CashRegister.objects.filter(
            tenant=tenant,
            status='open'
        ).first()
        if open_register:
            CashMovement.objects.create(
                register=open_register,
                movement_type='adjustment',
                amount=-sale.total_amount,
                description=f'Cancelación venta #{sale.sale_number}',
                reference=sale.sale_number,
                created_by=request.user,
            )

    return JsonResponse({
        'success': True,
        'sale_id': sale.id,
        'sale_number': sale.sale_number,
        'status': 'cancelled',
    })
