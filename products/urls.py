from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='products'),
    path('create/', views.product_create, name='product_create'),
    path('<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('<int:product_id>/toggle/', views.product_toggle, name='product_toggle'),
    path('categories/', views.category_list, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
]
