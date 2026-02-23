from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('pos/', views.pos_view, name='pos'),
    path('products/', views.products_view, name='products'),
    path('reports/', views.reports_view, name='reports'),
]