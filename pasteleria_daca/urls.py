"""
URL configuration for pasteleria_daca project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel/', include('dashboard.urls', namespace='dashboard')),
    path('cuentas/', include('accounts.urls', namespace='accounts')),
    path('catalogo/', include('catalog.urls', namespace='catalog')),
    path('carrito/', include('cart.urls', namespace='cart')),
    path('pedidos/', include('orders.urls', namespace='orders')),
    path('personalizadas/', include('custom_orders.urls', namespace='custom_orders')),
    path('', include('core.urls', namespace='core')),
    # Servir archivos media tanto en desarrollo como en producción (Render)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

