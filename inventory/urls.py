from django.urls import path
from . import views

urlpatterns = [
    path('', views.ingredient_list, name='inventory'),
    path('create/', views.ingredient_create, name='ingredient_create'),
    path('<int:ingredient_id>/edit/', views.ingredient_edit, name='ingredient_edit'),
    path('<int:ingredient_id>/delete/', views.ingredient_delete, name='ingredient_delete'),
    path('movements/', views.stock_movements, name='stock_movements'),
    path('movements/add/', views.stock_movement_add, name='stock_movement_add'),
    path('suppliers/', views.supplier_list, name='suppliers'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:supplier_id>/edit/', views.supplier_edit, name='supplier_edit'),
]
