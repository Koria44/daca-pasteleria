"""
URL configuration for pasteleria_daca project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel/', include('dashboard.urls', namespace='dashboard')),
    path('cuentas/', include('accounts.urls', namespace='accounts')),
    path('catalogo/', include('catalog.urls', namespace='catalog')),
    path('carrito/', include('cart.urls', namespace='cart')),
    path('pedidos/', include('orders.urls', namespace='orders')),
    path('personalizadas/', include('custom_orders.urls', namespace='custom_orders')),
    path('', include('core.urls', namespace='core')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
