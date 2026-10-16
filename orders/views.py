import json
import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.utils import timezone

from cart.cart import Cart
from core.models import SiteSettings
from .models import Order, OrderItem, Coupon, WebpayTransaction
from .services.webpay_service import WebpayService

def send_order_confirmation_email(order, tx=None):
    """Sends professional order confirmation email with payment details."""
    try:
        subject = f"¡Confirmación de Pedido {order.order_number} - Daca Pastelería!"
        tx_info = ""
        if tx and tx.status == 'AUTHORIZED':
            tx_info = f"""
Detalles del Pago Webpay Plus:
Estado: Aprobado / Pagado
Código de Autorización: {tx.authorization_code}
Tarjeta: **** **** **** {tx.card_number}
Tipo de Pago: {WebpayService.get_payment_type_description(tx.payment_type_code)}
Cuotas: {tx.shares_number}
Fecha: {tx.transaction_date.strftime('%d/%m/%Y %H:%M:%S') if tx.transaction_date else ''}
            """
        elif order.payment_method == 'transfer':
            tx_info = """
Datos para Transferencia Bancaria:
Banco: Banco Estado / Banco de Chile
Tipo de cuenta: Cuenta Corriente
Número: 12345678
Nombre: Daca Pastelería SpA
RUT: 77.123.456-7
Correo: transferencias@dacapasteleria.cl
            """

        message_body = f"""Hola {order.full_name},

¡Muchas gracias por tu pedido en Daca Pastelería!
Hemos recibido tu solicitud con número: {order.order_number}

Detalle de Entrega:
Tipo: {order.get_delivery_type_display()}
Fecha: {order.delivery_date} ({order.delivery_time_slot})
Total: ${order.total:,} CLP
{tx_info}

¡Estaremos felices de endulzar tu momento con nuestras recetas artesanales!
Daca Pastelería · Rojas Magallanes 055, La Florida
        """.replace(",", ".")

        send_mail(
            subject,
            message_body,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=True,
        )
    except Exception:
        pass


class CheckoutView(View):
    def get(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            messages.warning(request, "Tu carrito está vacío. Agrega productos deliciosos antes de continuar.")
            return redirect('catalog:product_list')

        site_settings = SiteSettings.objects.first()
        shipping_cost = site_settings.shipping_cost if site_settings else 3990

        user_profile = None
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            user_profile = request.user.profile

        return render(request, 'orders/checkout.html', {
            'cart': cart,
            'shipping_cost': shipping_cost,
            'user_profile': user_profile,
            'site_settings': site_settings,
        })

    def post(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            messages.warning(request, "Tu carrito está vacío.")
            return redirect('catalog:product_list')

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        delivery_type = request.POST.get('delivery_type', 'pickup')
        address_street = request.POST.get('address_street', '').strip()
        address_details = request.POST.get('address_details', '').strip()
        commune = request.POST.get('commune', 'La Florida').strip()
        delivery_date = request.POST.get('delivery_date')
        delivery_time_slot = request.POST.get('delivery_time_slot', '14:00 a 17:00 hrs')
        customer_notes = request.POST.get('customer_notes', '').strip()
        payment_method = request.POST.get('payment_method', 'transfer')

        if not (full_name and email and phone and delivery_date):
            messages.error(request, "Por favor completa todos los campos requeridos.")
            return redirect('orders:checkout')

        subtotal = cart.subtotal
        site_settings = SiteSettings.objects.first()
        base_shipping = site_settings.shipping_cost if site_settings else 3990
        shipping_cost = base_shipping if delivery_type == 'delivery' else 0

        coupon_code = request.POST.get('coupon_code', '').strip()
        coupon = None
        discount = 0
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code, is_active=True).first()
            if coupon:
                discount = coupon.calculate_discount(subtotal)

        total = max(0, subtotal + shipping_cost - discount)

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            delivery_type=delivery_type,
            address_street=address_street if delivery_type == 'delivery' else '',
            address_details=address_details if delivery_type == 'delivery' else '',
            commune=commune if delivery_type == 'delivery' else 'La Florida',
            delivery_date=delivery_date,
            delivery_time_slot=delivery_time_slot,
            customer_notes=customer_notes,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            discount=discount,
            total=total,
            coupon=coupon,
            payment_method=payment_method,
            payment_status='pending',
            status='pending',
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product_id=item['product_id'],
                variant_id=item['variant_id'],
                product_name=item['name'],
                variant_name=item['variant_name'],
                unit_price=item['price'],
                quantity=item['quantity'],
                subtotal=item['total_price'],
                notes=item['notes'],
                addons_text=item.get('addons_text', ''),
                addon_ids=item.get('addon_ids', []),
            )

        # Handle Webpay Plus payment flow
        if payment_method == 'webpay':
            try:
                service = WebpayService()
                session_id = request.session.session_key or 'guest_session'
                return_url = request.build_absolute_uri(reverse('orders:webpay_return'))

                tx_data = service.create_transaction(order, session_id, return_url)

                WebpayTransaction.objects.create(
                    order=order,
                    token=tx_data['token'],
                    buy_order=tx_data['buy_order'],
                    session_id=session_id[:60],
                    amount=tx_data['amount'],
                    status='INITIALIZED'
                )

                # Do NOT clear cart yet! Cart is only cleared on successful payment authorization.
                return render(request, 'orders/webpay_redirect.html', {
                    'url': tx_data['url'],
                    'token': tx_data['token'],
                    'order': order,
                })
            except Exception as e:
                messages.error(request, f"Error al conectar con Webpay Plus: {str(e)}. Puedes reintentar o elegir otro medio de pago.")
                return redirect('orders:checkout')

        # For transfer or cash on delivery:
        cart.clear()
        send_order_confirmation_email(order)
        return redirect('orders:confirmation', order_number=order.order_number)


@method_decorator(csrf_exempt, name='dispatch')
class WebpayReturnView(View):
    """
    Handles return redirect from Transbank Webpay Plus (POST or GET).
    Exempt from CSRF since Transbank posts directly without Django CSRF token.
    """
    def get(self, request):
        return self._process_return(request)

    def post(self, request):
        return self._process_return(request)

    def _process_return(self, request):
        data = request.POST if request.method == 'POST' else request.GET
        token_ws = data.get('token_ws')
        tbk_token = data.get('TBK_TOKEN')
        tbk_orden_compra = data.get('TBK_ORDEN_COMPRA')
        tbk_id_sesion = data.get('TBK_ID_SESION')

        service = WebpayService()

        # CASE 1: Normal authorized flow or rejected by bank
        if token_ws:
            tx = WebpayTransaction.objects.filter(token=token_ws).select_related('order').first()
            if not tx:
                messages.error(request, "Transacción Webpay no encontrada o token inválido.")
                return redirect('catalog:product_list')

            order = tx.order

            # Idempotency check: if already paid (e.g. user refreshed the page)
            if order.payment_status == 'paid' and tx.status == 'AUTHORIZED':
                return redirect('orders:webpay_receipt', order_number=order.order_number)

            try:
                commit_res = service.commit_transaction(token_ws)
            except Exception as e:
                # If Transbank commit fails (e.g. timeout or already committed)
                if order.payment_status == 'paid':
                    return redirect('orders:webpay_receipt', order_number=order.order_number)
                tx.status = 'FAILED'
                tx.raw_response = {'error': str(e)}
                tx.save()
                order.payment_status = 'failed'
                order.save()
                messages.error(request, "No se pudo confirmar la transacción con Transbank. Por favor reintenta.")
                return redirect('orders:webpay_failure', order_number=order.order_number)

            status = commit_res.get('status')
            response_code = commit_res.get('response_code')
            auth_code = commit_res.get('authorization_code', '')
            card_detail = commit_res.get('card_detail', {})
            card_num = card_detail.get('card_number', '') if isinstance(card_detail, dict) else ''
            payment_type = commit_res.get('payment_type_code', '')
            shares_num = commit_res.get('shares_number', 0)
            trans_date_str = commit_res.get('transaction_date')

            tx.raw_response = commit_res
            tx.response_code = response_code
            tx.authorization_code = auth_code
            tx.card_number = card_num
            tx.payment_type_code = payment_type
            tx.shares_number = shares_num or 0
            if trans_date_str:
                from django.utils.dateparse import parse_datetime
                tx.transaction_date = parse_datetime(trans_date_str) or timezone.now()
            else:
                tx.transaction_date = timezone.now()

            if status == 'AUTHORIZED' and response_code == 0:
                tx.status = 'AUTHORIZED'
                tx.save()

                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.save()

                # Clear cart strictly on successful authorization
                Cart(request).clear()

                send_order_confirmation_email(order, tx)
                messages.success(request, f"¡Pago exitoso! Tu pedido {order.order_number} ha sido confirmado y pagado.")
                return redirect('orders:webpay_receipt', order_number=order.order_number)
            else:
                tx.status = 'FAILED'
                tx.save()

                order.payment_status = 'failed'
                order.save()

                # Cart is preserved!
                messages.error(request, "El pago fue rechazado por el banco o emisor de tu tarjeta. Tu carrito sigue guardado para que puedas reintentar.")
                return redirect('orders:webpay_failure', order_number=order.order_number)

        # CASE 2: User cancelled in Webpay portal
        elif tbk_token:
            tx = WebpayTransaction.objects.filter(token=tbk_token).select_related('order').first()
            order = None
            if tx:
                tx.status = 'ABORTED'
                tx.save()
                order = tx.order
                order.payment_status = 'failed'
                order.save()
            elif tbk_orden_compra:
                tx = WebpayTransaction.objects.filter(buy_order=tbk_orden_compra).select_related('order').first()
                if tx:
                    tx.status = 'ABORTED'
                    tx.save()
                    order = tx.order
                    order.payment_status = 'failed'
                    order.save()

            messages.warning(request, "El pago fue cancelado por el usuario en el portal de Webpay. Tu carrito se mantiene intacto.")
            if order:
                return redirect('orders:webpay_failure', order_number=order.order_number)
            return redirect('cart:detail')

        # CASE 3: Timeout in Webpay portal
        elif tbk_orden_compra:
            tx = WebpayTransaction.objects.filter(buy_order=tbk_orden_compra).select_related('order').first()
            order = None
            if tx:
                tx.status = 'TIMEOUT'
                tx.save()
                order = tx.order
                order.payment_status = 'failed'
                order.save()

            messages.error(request, "La sesión de pago con Webpay expiró por tiempo límite. Puedes reintentar cuando gustes.")
            if order:
                return redirect('orders:webpay_failure', order_number=order.order_number)
            return redirect('cart:detail')

        else:
            messages.error(request, "Respuesta inválida desde Webpay.")
            return redirect('catalog:product_list')


class WebpayReceiptView(View):
    """
    Renders official Transbank proof of payment compliant with regulatory requirements.
    """
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        tx = order.webpay_transactions.filter(status='AUTHORIZED').first()
        if not tx:
            tx = order.webpay_transactions.first()

        site_settings = SiteSettings.objects.first()
        payment_type_desc = WebpayService.get_payment_type_description(tx.payment_type_code if tx else '')

        return render(request, 'orders/webpay_receipt.html', {
            'order': order,
            'tx': tx,
            'payment_type_desc': payment_type_desc,
            'site_settings': site_settings,
            'commerce_code': getattr(settings, 'TBK_COMMERCE_CODE', '597055555532'),
        })


class WebpayFailureView(View):
    """
    Shown when payment fails, is aborted, or times out.
    Preserves cart and allows customer to retry or choose another payment method.
    """
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        last_tx = order.webpay_transactions.first()
        site_settings = SiteSettings.objects.first()
        return render(request, 'orders/webpay_failure.html', {
            'order': order,
            'last_tx': last_tx,
            'cart': Cart(request),
            'site_settings': site_settings,
        })


class WebpayRetryView(View):
    """
    Allows retrying Webpay payment for a pending or failed order
    (from Mis Pedidos, dashboard, or failure screen).
    """
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        if order.payment_status == 'paid':
            messages.info(request, "Este pedido ya se encuentra pagado.")
            return redirect('orders:webpay_receipt', order_number=order.order_number)

        try:
            service = WebpayService()
            session_id = request.session.session_key or 'retry_session'
            return_url = request.build_absolute_uri(reverse('orders:webpay_return'))

            tx_data = service.create_transaction(order, session_id, return_url)

            WebpayTransaction.objects.create(
                order=order,
                token=tx_data['token'],
                buy_order=tx_data['buy_order'],
                session_id=session_id[:60],
                amount=tx_data['amount'],
                status='INITIALIZED',
            )

            return render(request, 'orders/webpay_redirect.html', {
                'url': tx_data['url'],
                'token': tx_data['token'],
                'order': order,
            })
        except Exception as e:
            messages.error(request, f"Error al conectar con Webpay: {str(e)}")
            return redirect('orders:webpay_failure', order_number=order.order_number)


class OrderConfirmationView(View):
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        site_settings = SiteSettings.objects.first()
        wa_phone = site_settings.whatsapp_phone if site_settings else "56912345678"

        wa_text = f"¡Hola Daca Pastelería! Acabo de hacer el pedido *{order.order_number}* a nombre de *{order.full_name}* por un total de *${order.total:,} CLP*. Fecha entrega: *{order.delivery_date}*.".replace(",", ".")
        wa_url = f"https://wa.me/{wa_phone}?text={urllib.parse.quote(wa_text)}"

        return render(request, 'orders/confirmation.html', {
            'order': order,
            'whatsapp_url': wa_url,
            'site_settings': site_settings,
        })


class UploadProofView(View):
    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        if 'payment_proof' in request.FILES:
            order.payment_proof = request.FILES['payment_proof']
            order.payment_status = 'pending'
            order.save()
            messages.success(request, "¡Comprobante subido exitosamente! Lo revisaremos a la brevedad.")
        else:
            messages.error(request, "Por favor selecciona un archivo de imagen o comprobante.")
        return redirect('orders:confirmation', order_number=order.order_number)


class OrderDetailView(View):
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        return render(request, 'orders/order_detail.html', {'order': order})


class MyOrdersView(LoginRequiredMixin, View):
    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related('items', 'webpay_transactions')
        return render(request, 'orders/my_orders.html', {'orders': orders})
