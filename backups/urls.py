from django.urls import path

from . import views

urlpatterns = [
    path('', views.backup_dashboard, name='backup_dashboard'),
    path('config/', views.backup_save_config, name='backup_save_config'),
    path('create/', views.backup_create_now, name='backup_create_now'),
    path('<int:record_id>/download/', views.backup_download, name='backup_download'),
    path('<int:record_id>/delete/', views.backup_delete, name='backup_delete'),
    path('cleanup/', views.backup_cleanup, name='backup_cleanup'),
]
