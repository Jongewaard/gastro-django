from django.urls import path
from . import views

urlpatterns = [
    path('', views.cash_register_view, name='cash_register'),
    path('open/', views.cash_open, name='cash_open'),
    path('close/', views.cash_close, name='cash_close'),
    path('movement/', views.cash_movement_add, name='cash_movement_add'),
    path('expenses/', views.expense_list, name='expenses'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('reports/', views.reports_view, name='reports'),
]
