from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('pedidos/', views.OrderListView.as_view(), name='orders_list'),
    path('pedidos/<int:pk>/', views.OrderDetailAdminView.as_view(), name='order_detail'),
    path('pedidos/<int:pk>/estado/', views.OrderUpdateStatusView.as_view(), name='order_update_status'),
    path('pedidos/<int:pk>/comanda/', views.OrderPrintTicketView.as_view(), name='order_print_ticket'),
    path('pedidos/<int:pk>/reembolsar-webpay/', views.OrderWebpayRefundView.as_view(), name='order_webpay_refund'),
    path('pedidos/exportar-csv/', views.ExportOrdersCSVView.as_view(), name='orders_export_csv'),
    path('personalizados/', views.CustomOrdersAdminListView.as_view(), name='custom_orders_list'),
    path('personalizados/<int:pk>/', views.CustomOrderDetailAdminView.as_view(), name='custom_order_detail'),
    path('personalizados/<int:pk>/cotizar/', views.CustomOrderQuoteView.as_view(), name='custom_order_quote'),
    path('productos/', views.ProductAdminListView.as_view(), name='products_list'),
    path('productos/nuevo/', views.ProductAdminCreateView.as_view(), name='product_create'),
    path('productos/<int:pk>/editar/', views.ProductAdminUpdateView.as_view(), name='product_update'),
    path('productos/<int:pk>/toggle-activo/', views.ProductToggleActiveView.as_view(), name='product_toggle_active'),
    path('clientes/', views.CustomerAdminListView.as_view(), name='customers_list'),
    path('banners/', views.BannerAdminListView.as_view(), name='banners_list'),
    path('configuracion/', views.SettingsAdminView.as_view(), name='settings'),
]
