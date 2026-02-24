from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employees'),
    path('create/', views.employee_create, name='employee_create'),
    path('<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('schedule/save/', views.schedule_save, name='schedule_save'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('attendance/save/', views.attendance_save, name='attendance_save'),
]
