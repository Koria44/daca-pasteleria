from django.contrib import admin
from .models import Order, OrderItem, Coupon

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'variant_name', 'unit_price', 'quantity', 'subtotal', 'notes')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'delivery_type', 'delivery_date', 'total', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'delivery_type', 'delivery_date')
    search_fields = ('order_number', 'full_name', 'email', 'phone')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'subtotal', 'total')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Identificación del Pedido', {
            'fields': ('order_number', 'user', 'status', 'created_at')
        }),
        ('Datos del Cliente', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Entrega y Despacho', {
            'fields': ('delivery_type', 'address_street', 'address_details', 'commune', 'delivery_date', 'delivery_time_slot', 'customer_notes')
        }),
        ('Pago y Totales', {
            'fields': ('subtotal', 'shipping_cost', 'discount', 'total', 'coupon', 'payment_method', 'payment_status', 'payment_proof')
        }),
        ('Gestión Interna', {
            'fields': ('internal_notes',)
        }),
    )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_purchase', 'valid_until', 'current_uses', 'is_active')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)
