import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from core.models import SiteSettings
from .models import CakeStyle, CustomCakeOrder

class CustomCakeWizardView(View):
    def get(self, request):
        cake_styles = CakeStyle.objects.filter(is_active=True).order_by('order')
        selected_style_id = request.GET.get('estilo')
        selected_style = None
        if selected_style_id:
            selected_style = CakeStyle.objects.filter(id=selected_style_id, is_active=True).first()

        site_settings = SiteSettings.objects.first()

        return render(request, 'custom_orders/wizard.html', {
            'cake_styles': cake_styles,
            'selected_style': selected_style,
            'site_settings': site_settings,
        })

    def post(self, request):
        style_id = request.POST.get('cake_style')
        cake_style = get_object_or_404(CakeStyle, id=style_id)

        portions = int(request.POST.get('portions', 12))
        sponge_flavor = request.POST.get('sponge_flavor', 'Red Velvet')
        filling_flavor = request.POST.get('filling_flavor', 'Frosting de queso crema')
        frosting_type = request.POST.get('frosting_type', 'Buttercream suave')
        color_palette = request.POST.get('color_palette', '')
        message_on_cake = request.POST.get('message_on_cake', '')
        topper = request.POST.get('topper', '')
        allergies_restrictions = request.POST.get('allergies_restrictions', '')

        desired_date = request.POST.get('desired_date')
        delivery_preference = request.POST.get('delivery_preference', 'pickup')
        estimated_budget_str = request.POST.get('estimated_budget', '')
        estimated_budget = int(estimated_budget_str) if estimated_budget_str.isdigit() else None

        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_notes = request.POST.get('customer_notes', '').strip()

        if not (desired_date and customer_name and customer_email and customer_phone):
            messages.error(request, "Por favor completa la fecha deseada y tus datos de contacto.")
            return redirect('custom_orders:wizard')

        custom_order = CustomCakeOrder.objects.create(
            user=request.user if request.user.is_authenticated else None,
            cake_style=cake_style,
            portions=portions,
            sponge_flavor=sponge_flavor,
            filling_flavor=filling_flavor,
            frosting_type=frosting_type,
            color_palette=color_palette,
            message_on_cake=message_on_cake,
            topper=topper,
            allergies_restrictions=allergies_restrictions,
            desired_date=desired_date,
            delivery_preference=delivery_preference,
            estimated_budget=estimated_budget,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_notes=customer_notes,
            reference_image_1=request.FILES.get('reference_image_1'),
            reference_image_2=request.FILES.get('reference_image_2'),
            reference_image_3=request.FILES.get('reference_image_3'),
        )

        messages.success(request, "¡Tu solicitud de torta personalizada ha sido enviada con éxito! Te contactaremos a la brevedad.")
        return redirect('custom_orders:confirmation', order_number=custom_order.order_number)


class CustomCakeConfirmationView(View):
    def get(self, request, order_number):
        custom_order = get_object_or_404(CustomCakeOrder, order_number=order_number)
        site_settings = SiteSettings.objects.first()
        wa_phone = site_settings.whatsapp_phone if site_settings else "56912345678"

        wa_text = f"¡Hola Daca Pastelería! Acabo de enviar mi cotización de torta personalizada *{custom_order.order_number}* para el estilo *{custom_order.cake_style.name}* ({custom_order.portions} personas) para la fecha *{custom_order.desired_date}*. Mi nombre es *{custom_order.customer_name}*."
        wa_url = f"https://wa.me/{wa_phone}?text={urllib.parse.quote(wa_text)}"

        return render(request, 'custom_orders/confirmation.html', {
            'custom_order': custom_order,
            'whatsapp_url': wa_url,
            'site_settings': site_settings,
        })


class MyCustomOrdersView(LoginRequiredMixin, View):
    def get(self, request):
        custom_orders = CustomCakeOrder.objects.filter(user=request.user)
        return render(request, 'custom_orders/my_orders.html', {'custom_orders': custom_orders})


class ApproveQuoteView(LoginRequiredMixin, View):
    def post(self, request, order_number):
        custom_order = get_object_or_404(CustomCakeOrder, order_number=order_number, user=request.user)
        if custom_order.status == 'quoted':
            custom_order.status = 'approved'
            custom_order.save()
            messages.success(request, f"¡Has aprobado la cotización de tu pedido {custom_order.order_number}! Ahora puedes coordinar el anticipo.")
        return redirect('custom_orders:my_orders')
