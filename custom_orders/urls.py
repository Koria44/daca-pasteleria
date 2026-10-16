from django.urls import path
from . import views

app_name = 'custom_orders'

urlpatterns = [
    path('', views.CustomCakeWizardView.as_view(), name='wizard'),
    path('confirmacion/<str:order_number>/', views.CustomCakeConfirmationView.as_view(), name='confirmation'),
    path('mis-pedidos-personalizados/', views.MyCustomOrdersView.as_view(), name='my_orders'),
    path('aprobar/<str:order_number>/', views.ApproveQuoteView.as_view(), name='approve_quote'),
]
