from django.contrib import admin
from .models import ExpenseCategory, CashRegister, CashMovement, Expense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'is_active']
    list_filter = ['tenant', 'is_active']


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ['date', 'tenant', 'status', 'opening_amount', 'closing_amount', 'difference']
    list_filter = ['tenant', 'status', 'date']
    date_hierarchy = 'date'


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = ['register', 'movement_type', 'amount', 'description', 'created_by', 'created_at']
    list_filter = ['movement_type', 'register__tenant']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'amount', 'category', 'date', 'tenant', 'paid_by']
    list_filter = ['tenant', 'category', 'date']
    date_hierarchy = 'date'
