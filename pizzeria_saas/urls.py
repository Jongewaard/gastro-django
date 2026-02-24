from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
    path('', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
