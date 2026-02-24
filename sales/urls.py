from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.sale_create, name='sale_create'),
    path('<int:pk>/status/', views.sale_update_status, name='sale_update_status'),
    path('<int:pk>/cancel/', views.sale_cancel, name='sale_cancel'),
]
