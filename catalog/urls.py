from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('categoria/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('producto/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('htmx/filter/', views.ProductFilterHTMXView.as_view(), name='htmx_filter'),
]
