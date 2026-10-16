from django.contrib import admin
from .models import CakeStyle, CustomCakeOrder

@admin.register(CakeStyle)
class CakeStyleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'base_price', 'order', 'is_active')
    list_editable = ('base_price', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


@admin.register(CustomCakeOrder)
class CustomCakeOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'cake_style', 'portions', 'desired_date', 'status', 'final_price', 'created_at')
    list_filter = ('status', 'cake_style', 'desired_date')
    search_fields = ('order_number', 'customer_name', 'customer_email', 'customer_phone')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    fieldsets = (
        ('Identificación y Cliente', {
            'fields': ('order_number', 'user', 'customer_name', 'customer_email', 'customer_phone')
        }),
        ('Detalles de la Torta Personalizada', {
            'fields': ('cake_style', 'portions', 'sponge_flavor', 'filling_flavor', 'frosting_type', 'color_palette', 'message_on_cake', 'topper', 'allergies_restrictions', 'customer_notes')
        }),
        ('Referencias Fotográficas', {
            'fields': ('reference_image_1', 'reference_image_2', 'reference_image_3')
        }),
        ('Fecha y Presupuesto', {
            'fields': ('desired_date', 'delivery_preference', 'estimated_budget')
        }),
        ('Respuesta y Cotización de la Pastelería', {
            'fields': ('status', 'final_price', 'deposit_required', 'deposit_paid', 'bakery_response', 'internal_notes')
        }),
    )
