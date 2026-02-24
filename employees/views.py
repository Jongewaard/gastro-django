import datetime
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Employee, WorkSchedule, WorkLog


@login_required
def employee_list(request):
    """List all employees for the tenant."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    employees = Employee.objects.filter(tenant=tenant).order_by('last_name', 'first_name')

    context = {
        'employees': employees,
    }
    return render(request, 'employees/employee_list.html', context)


@login_required
def employee_create(request):
    """Create a new employee. GET shows form, POST creates."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        position = request.POST.get('position', '')
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        dni = request.POST.get('dni', '').strip()
        hire_date = request.POST.get('hire_date', '')
        hourly_rate = request.POST.get('hourly_rate', '0')
        monthly_salary = request.POST.get('monthly_salary', '0')

        if not first_name or not last_name:
            messages.error(request, 'Nombre y apellido son obligatorios.')
        elif not position:
            messages.error(request, 'Debe seleccionar un puesto.')
        else:
            try:
                hourly_rate = Decimal(hourly_rate) if hourly_rate else Decimal('0.00')
                monthly_salary = Decimal(monthly_salary) if monthly_salary else Decimal('0.00')
            except (InvalidOperation, ValueError):
                hourly_rate = Decimal('0.00')
                monthly_salary = Decimal('0.00')

            try:
                hire_date = datetime.date.fromisoformat(hire_date) if hire_date else timezone.now().date()
            except ValueError:
                hire_date = timezone.now().date()

            employee = Employee.objects.create(
                tenant=tenant,
                first_name=first_name,
                last_name=last_name,
                position=position,
                phone=phone,
                email=email,
                dni=dni,
                hire_date=hire_date,
                hourly_rate=hourly_rate,
                monthly_salary=monthly_salary,
            )
            messages.success(request, f'Empleado "{employee.full_name}" creado exitosamente.')
            return redirect('employee_list')

    context = {
        'position_choices': Employee.POSITION_CHOICES,
        'editing': False,
    }
    return render(request, 'employees/employee_form.html', context)


@login_required
def employee_edit(request, employee_id):
    """Edit an employee. GET shows form with data, POST updates."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    employee = get_object_or_404(Employee, id=employee_id, tenant=tenant)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        position = request.POST.get('position', '')
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        dni = request.POST.get('dni', '').strip()
        hire_date = request.POST.get('hire_date', '')
        hourly_rate = request.POST.get('hourly_rate', '0')
        monthly_salary = request.POST.get('monthly_salary', '0')

        if not first_name or not last_name:
            messages.error(request, 'Nombre y apellido son obligatorios.')
        elif not position:
            messages.error(request, 'Debe seleccionar un puesto.')
        else:
            try:
                hourly_rate = Decimal(hourly_rate) if hourly_rate else Decimal('0.00')
                monthly_salary = Decimal(monthly_salary) if monthly_salary else Decimal('0.00')
            except (InvalidOperation, ValueError):
                hourly_rate = Decimal('0.00')
                monthly_salary = Decimal('0.00')

            try:
                hire_date = datetime.date.fromisoformat(hire_date) if hire_date else employee.hire_date
            except ValueError:
                hire_date = employee.hire_date

            employee.first_name = first_name
            employee.last_name = last_name
            employee.position = position
            employee.phone = phone
            employee.email = email
            employee.dni = dni
            employee.hire_date = hire_date
            employee.hourly_rate = hourly_rate
            employee.monthly_salary = monthly_salary
            employee.save()

            messages.success(request, f'Empleado "{employee.full_name}" actualizado exitosamente.')
            return redirect('employee_list')

    context = {
        'employee': employee,
        'position_choices': Employee.POSITION_CHOICES,
        'editing': True,
    }
    return render(request, 'employees/employee_form.html', context)


@login_required
@require_POST
def employee_delete(request, employee_id):
    """Delete an employee. POST only."""
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    employee = get_object_or_404(Employee, id=employee_id, tenant=tenant)
    employee_name = employee.full_name
    employee.delete()

    messages.success(request, f'Empleado "{employee_name}" eliminado.')
    return redirect('employee_list')


@login_required
def schedule_view(request):
    """
    Shows weekly schedule grid.
    Takes `week_start` GET param (ISO date, defaults to this Monday).
    Shows all employees and their scheduled shifts for the week.
    """
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    # Determine week start (Monday)
    week_start_str = request.GET.get('week_start', '')
    try:
        week_start = datetime.date.fromisoformat(week_start_str)
    except (ValueError, TypeError):
        today = timezone.now().date()
        week_start = today - datetime.timedelta(days=today.weekday())  # Monday

    week_end = week_start + datetime.timedelta(days=6)  # Sunday
    week_days = [week_start + datetime.timedelta(days=i) for i in range(7)]

    # Previous/next week navigation
    prev_week = (week_start - datetime.timedelta(days=7)).isoformat()
    next_week = (week_start + datetime.timedelta(days=7)).isoformat()

    # Get all active employees
    employees = Employee.objects.filter(tenant=tenant, is_active=True).order_by('last_name', 'first_name')

    # Get all schedules for the week
    schedules = WorkSchedule.objects.filter(
        employee__tenant=tenant,
        employee__is_active=True,
        date__gte=week_start,
        date__lte=week_end,
    ).select_related('employee')

    # Build a lookup: {(employee_id, date): schedule}
    schedule_map = {}
    for schedule in schedules:
        schedule_map[(schedule.employee_id, schedule.date)] = schedule

    # Build schedule grid: list of {employee, days: [schedule_or_none for each day]}
    schedule_grid = []
    for emp in employees:
        days = []
        for day in week_days:
            days.append(schedule_map.get((emp.id, day)))
        schedule_grid.append({
            'employee': emp,
            'days': days,
        })

    context = {
        'week_start': week_start,
        'week_end': week_end,
        'week_days': week_days,
        'prev_week': prev_week,
        'next_week': next_week,
        'schedule_grid': schedule_grid,
        'employees': employees,
    }
    return render(request, 'employees/schedule.html', context)


@login_required
@require_POST
def schedule_save(request):
    """
    Create or update a WorkSchedule.
    POST fields: employee_id, date, shift_start, shift_end, break_minutes
    """
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    employee_id = request.POST.get('employee_id')
    date_str = request.POST.get('date', '')
    shift_start_str = request.POST.get('shift_start', '')
    shift_end_str = request.POST.get('shift_end', '')
    break_minutes = request.POST.get('break_minutes', '0')

    if not employee_id or not date_str or not shift_start_str or not shift_end_str:
        messages.error(request, 'Todos los campos son obligatorios.')
        return redirect('schedule_view')

    employee = get_object_or_404(Employee, id=employee_id, tenant=tenant)

    try:
        schedule_date = datetime.date.fromisoformat(date_str)
    except ValueError:
        messages.error(request, 'Fecha inválida.')
        return redirect('schedule_view')

    try:
        shift_start = datetime.time.fromisoformat(shift_start_str)
        shift_end = datetime.time.fromisoformat(shift_end_str)
    except ValueError:
        messages.error(request, 'Hora de inicio o fin inválida.')
        return redirect('schedule_view')

    try:
        break_minutes = int(break_minutes)
        if break_minutes < 0:
            break_minutes = 0
    except (ValueError, TypeError):
        break_minutes = 0

    # Create or update
    schedule, created = WorkSchedule.objects.update_or_create(
        employee=employee,
        date=schedule_date,
        defaults={
            'shift_start': shift_start,
            'shift_end': shift_end,
            'break_minutes': break_minutes,
        }
    )

    action = 'creado' if created else 'actualizado'
    messages.success(request, f'Horario de {employee.full_name} para {schedule_date} {action}.')

    # Redirect back to the same week view
    week_start = schedule_date - datetime.timedelta(days=schedule_date.weekday())
    return redirect(f'/employees/schedule/?week_start={week_start.isoformat()}')


@login_required
def attendance_view(request):
    """
    Shows today's attendance.
    Lists all active employees with their clock_in/clock_out status.
    """
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    today = timezone.now().date()

    employees = Employee.objects.filter(tenant=tenant, is_active=True).order_by('last_name', 'first_name')

    # Get today's work logs
    work_logs = WorkLog.objects.filter(
        employee__tenant=tenant,
        date=today,
    ).select_related('employee')

    # Build lookup: {employee_id: work_log}
    log_map = {log.employee_id: log for log in work_logs}

    # Build attendance list
    attendance = []
    for emp in employees:
        log = log_map.get(emp.id)
        attendance.append({
            'employee': emp,
            'work_log': log,
            'clock_in': log.clock_in if log else None,
            'clock_out': log.clock_out if log else None,
            'status': log.status if log else 'absent',
            'total_hours': log.total_hours if log else Decimal('0.00'),
        })

    context = {
        'attendance': attendance,
        'today': today,
        'status_choices': WorkLog.STATUS_CHOICES,
    }
    return render(request, 'employees/attendance.html', context)


@login_required
@require_POST
def attendance_save(request):
    """
    Create or update a WorkLog entry.
    POST fields: employee_id, date, clock_in, clock_out, break_minutes, status, notes
    Auto-calculates total_hours.
    """
    tenant = request.user.tenant
    if not tenant:
        return redirect('dashboard')

    employee_id = request.POST.get('employee_id')
    date_str = request.POST.get('date', '')
    clock_in_str = request.POST.get('clock_in', '')
    clock_out_str = request.POST.get('clock_out', '')
    break_minutes = request.POST.get('break_minutes', '0')
    status = request.POST.get('status', 'working')
    notes = request.POST.get('notes', '').strip()

    if not employee_id or not date_str or not clock_in_str:
        messages.error(request, 'Empleado, fecha y hora de entrada son obligatorios.')
        return redirect('attendance_view')

    employee = get_object_or_404(Employee, id=employee_id, tenant=tenant)

    try:
        log_date = datetime.date.fromisoformat(date_str)
    except ValueError:
        messages.error(request, 'Fecha inválida.')
        return redirect('attendance_view')

    try:
        clock_in = datetime.time.fromisoformat(clock_in_str)
    except ValueError:
        messages.error(request, 'Hora de entrada inválida.')
        return redirect('attendance_view')

    clock_out = None
    if clock_out_str:
        try:
            clock_out = datetime.time.fromisoformat(clock_out_str)
        except ValueError:
            messages.error(request, 'Hora de salida inválida.')
            return redirect('attendance_view')

    try:
        break_minutes = int(break_minutes)
        if break_minutes < 0:
            break_minutes = 0
    except (ValueError, TypeError):
        break_minutes = 0

    # Validate status
    valid_statuses = [s[0] for s in WorkLog.STATUS_CHOICES]
    if status not in valid_statuses:
        status = 'working'

    # Create or update
    work_log, created = WorkLog.objects.update_or_create(
        employee=employee,
        date=log_date,
        defaults={
            'clock_in': clock_in,
            'clock_out': clock_out,
            'break_minutes': break_minutes,
            'status': status,
            'notes': notes,
        }
    )

    # Auto-calculate total hours
    work_log.calculate_hours()
    work_log.save()

    action = 'registrada' if created else 'actualizada'
    messages.success(request, f'Asistencia de {employee.full_name} {action}.')
    return redirect('attendance_view')
