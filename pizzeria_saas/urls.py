from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from dashboard.views import simple_login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', simple_login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('products/', include('products.urls')),
    path('employees/', include('employees.urls')),
    path('inventory/', include('inventory.urls')),
    path('cash/', include('accounting.urls')),
    path('api/sales/', include('sales.urls')),
    path('backups/', include('backups.urls')),
    path('', include('dashboard.urls')),
    # Serve media files (local deployment)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
