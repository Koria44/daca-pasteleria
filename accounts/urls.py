from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('registro/', views.UserRegisterView.as_view(), name='register'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('perfil/', views.ProfileView.as_view(), name='profile'),
    path('direcciones/nueva/', views.AddressCreateView.as_view(), name='address_create'),
    path('direcciones/<int:pk>/eliminar/', views.AddressDeleteView.as_view(), name='address_delete'),
]
