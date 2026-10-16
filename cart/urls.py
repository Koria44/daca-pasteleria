from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartDetailView.as_view(), name='detail'),
    path('agregar/', views.CartAddView.as_view(), name='add'),
    path('actualizar/', views.CartUpdateView.as_view(), name='update'),
    path('eliminar/', views.CartRemoveView.as_view(), name='remove'),
    path('drawer/', views.CartDrawerView.as_view(), name='drawer'),
    path('badge/', views.CartBadgeView.as_view(), name='badge'),
]
