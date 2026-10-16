from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('confirmacion/<str:order_number>/', views.OrderConfirmationView.as_view(), name='confirmation'),
    path('comprobante/<str:order_number>/', views.UploadProofView.as_view(), name='upload_proof'),
    path('seguimiento/<str:order_number>/', views.OrderDetailView.as_view(), name='detail'),
    path('mis-pedidos/', views.MyOrdersView.as_view(), name='my_orders'),

    # Webpay Plus routes
    path('webpay/retorno/', views.WebpayReturnView.as_view(), name='webpay_return'),
    path('webpay/comprobante/<str:order_number>/', views.WebpayReceiptView.as_view(), name='webpay_receipt'),
    path('webpay/fallo/<str:order_number>/', views.WebpayFailureView.as_view(), name='webpay_failure'),
    path('webpay/reintentar/<str:order_number>/', views.WebpayRetryView.as_view(), name='webpay_retry'),
]
