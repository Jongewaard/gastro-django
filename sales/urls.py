from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.sale_create, name='sale_create'),
    path('<int:sale_id>/status/', views.sale_update_status, name='sale_update_status'),
    path('<int:sale_id>/cancel/', views.sale_cancel, name='sale_cancel'),
]
