from django.contrib import admin
from .models import Employee, WorkSchedule, WorkLog


class WorkScheduleInline(admin.TabularInline):
    model = WorkSchedule
    extra = 0


class WorkLogInline(admin.TabularInline):
    model = WorkLog
    extra = 0


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position', 'tenant', 'phone', 'is_active', 'hire_date']
    list_filter = ['tenant', 'position', 'is_active']
    search_fields = ['first_name', 'last_name', 'dni']
    inlines = [WorkScheduleInline, WorkLogInline]


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'shift_start', 'shift_end', 'scheduled_hours']
    list_filter = ['employee__tenant', 'date']
    date_hierarchy = 'date'


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'clock_in', 'clock_out', 'total_hours', 'status']
    list_filter = ['employee__tenant', 'status', 'date']
    date_hierarchy = 'date'
