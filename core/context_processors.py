from decouple import config

def site_settings(request):
    """
    Context processor to provide global site settings to all templates.
    """
    try:
        from core.models import SiteSettings
        settings_obj = SiteSettings.objects.first()
    except Exception:
        settings_obj = None

    default_data = {
        'store_name': 'Daca Pastelería',
        'address': config('STORE_ADDRESS', default='Rojas Magallanes 055, La Florida, Santiago, Chile'),
        'whatsapp_phone': config('WHATSAPP_PHONE', default='56912345678'),
        'instagram': config('INSTAGRAM_USER', default='@dacapasteleria'),
        'hours': 'Lunes a Domingo: 10:00 - 20:30 hrs',
        'special_notice': 'Entregas y retiros disponibles hasta las 20:30 hrs.',
        'shipping_cost': 3990,
        'min_order_amount': 5000,
        'anticipation_hours': 24,
    }

    return {
        'site_settings': settings_obj or default_data,
        'WHATSAPP_PHONE': config('WHATSAPP_PHONE', default='56912345678'),
        'INSTAGRAM_USER': config('INSTAGRAM_USER', default='@dacapasteleria'),
        'STORE_ADDRESS': config('STORE_ADDRESS', default='Rojas Magallanes 055, La Florida, Santiago, Chile'),
    }
