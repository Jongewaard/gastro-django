from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('pos/', views.pos_view, name='pos'),
    path('orders/', views.orders_view, name='orders'),
]
