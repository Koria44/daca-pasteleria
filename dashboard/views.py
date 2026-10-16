import csv
import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from orders.models import Order, OrderItem
from custom_orders.models import CustomCakeOrder
from catalog.models import Product, Category, ProductVariant
from core.models import SiteSettings, Banner

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class DashboardHomeView(StaffRequiredMixin, View):
    def get(self, request):
        today = timezone.localdate()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        tomorrow = today + timedelta(days=1)

        # KPIs - STRICTLY counting paid orders as requested
        today_revenue = Order.objects.filter(created_at__date=today, payment_status='paid').aggregate(total=Sum('total'))['total'] or 0
        weekly_revenue = Order.objects.filter(created_at__date__gte=week_ago, payment_status='paid').aggregate(total=Sum('total'))['total'] or 0
        monthly_revenue = Order.objects.filter(created_at__date__gte=month_ago, payment_status='paid').aggregate(total=Sum('total'))['total'] or 0

        new_orders_count = Order.objects.filter(created_at__date=today).count()
        pending_orders_count = Order.objects.filter(status='pending').count()
        in_prep_orders_count = Order.objects.filter(status='in_preparation').count()

        pending_custom_quotes = CustomCakeOrder.objects.filter(status='received').count()

        avg_ticket = Order.objects.filter(payment_status='paid').aggregate(avg=Avg('total'))['avg'] or 0
        new_customers_count = User.objects.filter(date_joined__date__gte=month_ago).count()

        # Deliveries for Today and Tomorrow
        deliveries_today = Order.objects.filter(delivery_date=today).exclude(status='cancelled').order_by('delivery_time_slot')
        deliveries_tomorrow = Order.objects.filter(delivery_date=tomorrow).exclude(status='cancelled').order_by('delivery_time_slot')

        # Stock Alerts
        low_stock_products = Product.objects.filter(is_active=True, stock__gte=0, stock__lte=5)

        # Revenue Chart Data (Last 7 days - Paid only)
        chart_labels = []
        chart_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_total = Order.objects.filter(created_at__date=day, payment_status='paid').aggregate(s=Sum('total'))['s'] or 0
            chart_labels.append(day.strftime('%d/%m'))
            chart_data.append(day_total)

        # Orders by status distribution
        status_pending = Order.objects.filter(status='pending').count()
        status_confirmed = Order.objects.filter(status='confirmed').count()
        status_in_prep = Order.objects.filter(status='in_preparation').count()
        status_ready_delivered = Order.objects.filter(status__in=['ready', 'delivered']).count()
        status_chart_data = json.dumps([status_pending, status_confirmed, status_in_prep, status_ready_delivered])

        # Categories sales distribution
        category_sales = OrderItem.objects.filter(product__category__isnull=False).values('product__category__name').annotate(total_qty=Sum('quantity'), total_amount=Sum('subtotal')).order_by('-total_amount')[:5]

        return render(request, 'dashboard/home.html', {
            'today_revenue': today_revenue,
            'weekly_revenue': weekly_revenue,
            'monthly_revenue': monthly_revenue,
            'new_orders_count': new_orders_count,
            'pending_orders_count': pending_orders_count,
            'in_prep_orders_count': in_prep_orders_count,
            'pending_custom_quotes': pending_custom_quotes,
            'avg_ticket': int(avg_ticket),
            'new_customers_count': new_customers_count,
            'deliveries_today': deliveries_today,
            'deliveries_tomorrow': deliveries_tomorrow,
            'low_stock_products': low_stock_products,
            'chart_labels': json.dumps(chart_labels),
            'chart_data': json.dumps(chart_data),
            'status_chart_data': status_chart_data,
            'category_sales': category_sales,
        })


class OrderListView(StaffRequiredMixin, View):
    def get(self, request):
        orders = Order.objects.all().prefetch_related('items')
        status = request.GET.get('estado')
        payment_status = request.GET.get('pago')
        delivery_type = request.GET.get('entrega')
        search = request.GET.get('q')

        if status:
            orders = orders.filter(status=status)
        if payment_status:
            orders = orders.filter(payment_status=payment_status)
        if delivery_type:
            orders = orders.filter(delivery_type=delivery_type)
        if search:
            orders = orders.filter(Q(order_number__icontains=search) | Q(full_name__icontains=search) | Q(email__icontains=search) | Q(phone__icontains=search))

        return render(request, 'dashboard/orders_list.html', {
            'orders': orders[:100],
            'current_status': status,
            'current_payment_status': payment_status,
            'current_delivery_type': delivery_type,
            'search': search,
            'STATUS_CHOICES': Order.STATUS_CHOICES,
            'PAYMENT_STATUS_CHOICES': Order.PAYMENT_STATUS_CHOICES,
        })


class OrderDetailAdminView(StaffRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order.objects.prefetch_related('items', 'webpay_transactions'), pk=pk)
        webpay_transactions = order.webpay_transactions.all()
        return render(request, 'dashboard/order_detail.html', {
            'order': order,
            'webpay_transactions': webpay_transactions,
        })


class OrderWebpayRefundView(StaffRequiredMixin, View):
    """
    Staff action to refund or reverse an authorized Webpay transaction via Transbank SDK.
    """
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        tx = order.webpay_transactions.filter(status='AUTHORIZED').first()
        if not tx:
            messages.error(request, "No se encontró ninguna transacción Webpay autorizada para reversar en este pedido.")
            return redirect('dashboard:order_detail', pk=order.pk)

        try:
            from orders.services.webpay_service import WebpayService
            service = WebpayService()
            refund_res = service.refund_transaction(tx.token, tx.amount)

            tx.status = 'REFUNDED'
            tx.refund_raw_response = refund_res if isinstance(refund_res, dict) else {'response': str(refund_res)}
            tx.save()

            order.payment_status = 'refunded'
            order.status = 'cancelled'
            order.save()

            messages.success(request, f"¡Transacción Webpay {tx.buy_order} reembolsada exitosamente por ${tx.amount:,} CLP!".replace(",", "."))
        except Exception as e:
            messages.error(request, f"Error al procesar el reembolso en Transbank: {str(e)}")

        return redirect('dashboard:order_detail', pk=order.pk)


class OrderUpdateStatusView(StaffRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('status')
        new_payment_status = request.POST.get('payment_status')

        if new_status and new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
        if new_payment_status and new_payment_status in dict(Order.PAYMENT_STATUS_CHOICES):
            order.payment_status = new_payment_status

        order.internal_notes = request.POST.get('internal_notes', order.internal_notes)
        order.save()
        messages.success(request, f"Pedido {order.order_number} actualizado correctamente.")
        return redirect('dashboard:order_detail', pk=order.pk)


class OrderPrintTicketView(StaffRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)
        return render(request, 'dashboard/print_ticket.html', {'order': order})


class ExportOrdersCSVView(StaffRequiredMixin, View):
    def get(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="pedidos_daca.csv"'
        response.write('\ufeff') # UTF-8 BOM for Excel in Windows

        writer = csv.writer(response)
        writer.writerow(['Nro Pedido', 'Fecha', 'Cliente', 'Email', 'Telefono', 'Tipo Entrega', 'Fecha Entrega', 'Total CLP', 'Estado Pedido', 'Estado Pago'])

        for o in Order.objects.all().order_by('-created_at'):
            writer.writerow([
                o.order_number,
                o.created_at.strftime('%Y-%m-%d %H:%M'),
                o.full_name,
                o.email,
                o.phone,
                o.get_delivery_type_display(),
                o.delivery_date,
                o.total,
                o.get_status_display(),
                o.get_payment_status_display()
            ])

        return response


class CustomOrdersAdminListView(StaffRequiredMixin, View):
    def get(self, request):
        custom_orders = CustomCakeOrder.objects.all().select_related('cake_style')
        status = request.GET.get('estado')
        if status:
            custom_orders = custom_orders.filter(status=status)
        return render(request, 'dashboard/custom_orders_list.html', {
            'custom_orders': custom_orders,
            'current_status': status,
            'STATUS_CHOICES': CustomCakeOrder.STATUS_CHOICES,
        })


class CustomOrderDetailAdminView(StaffRequiredMixin, View):
    def get(self, request, pk):
        custom_order = get_object_or_404(CustomCakeOrder.objects.select_related('cake_style'), pk=pk)
        return render(request, 'dashboard/custom_order_detail.html', {'custom_order': custom_order})


class CustomOrderQuoteView(StaffRequiredMixin, View):
    def post(self, request, pk):
        custom_order = get_object_or_404(CustomCakeOrder, pk=pk)
        final_price = request.POST.get('final_price')
        deposit_required = request.POST.get('deposit_required')
        bakery_response = request.POST.get('bakery_response', '').strip()
        new_status = request.POST.get('status', custom_order.status)

        if final_price:
            custom_order.final_price = int(final_price)
        if deposit_required:
            custom_order.deposit_required = int(deposit_required)
        if bakery_response:
            custom_order.bakery_response = bakery_response
        if new_status:
            custom_order.status = new_status

        custom_order.internal_notes = request.POST.get('internal_notes', custom_order.internal_notes)
        custom_order.save()
        messages.success(request, f"Cotización de pedido {custom_order.order_number} actualizada.")
        return redirect('dashboard:custom_order_detail', pk=custom_order.pk)


class ProductAdminListView(StaffRequiredMixin, View):
    def get(self, request):
        products = Product.objects.all().select_related('category').prefetch_related('images', 'variants')
        return render(request, 'dashboard/products_list.html', {'products': products})


class ProductAdminCreateView(StaffRequiredMixin, View):
    def get(self, request):
        categories = Category.objects.filter(is_active=True)
        return render(request, 'dashboard/product_form.html', {'categories': categories})

    def post(self, request):
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        base_price = request.POST.get('base_price')
        short_description = request.POST.get('short_description', '')
        description = request.POST.get('description', '')
        is_cake = request.POST.get('is_cake') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        is_new = request.POST.get('is_new') == 'on'

        from django.utils.text import slugify
        slug = slugify(name)
        count = 1
        orig_slug = slug
        while Product.objects.filter(slug=slug).exists():
            slug = f"{orig_slug}-{count}"
            count += 1

        product = Product.objects.create(
            name=name,
            slug=slug,
            category_id=category_id,
            base_price=int(base_price),
            short_description=short_description,
            description=description,
            is_cake=is_cake,
            is_featured=is_featured,
            is_new=is_new
        )

        messages.success(request, f"Producto '{product.name}' creado con éxito.")
        return redirect('dashboard:products_list')


class ProductAdminUpdateView(StaffRequiredMixin, View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        categories = Category.objects.filter(is_active=True)
        return render(request, 'dashboard/product_form.html', {'product': product, 'categories': categories})

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.name = request.POST.get('name', product.name)
        product.category_id = request.POST.get('category', product.category_id)
        product.base_price = int(request.POST.get('base_price', product.base_price))
        product.short_description = request.POST.get('short_description', product.short_description)
        product.description = request.POST.get('description', product.description)
        product.is_cake = request.POST.get('is_cake') == 'on'
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.is_new = request.POST.get('is_new') == 'on'
        product.is_active = request.POST.get('is_active') == 'on'
        product.save()

        messages.success(request, f"Producto '{product.name}' actualizado con éxito.")
        return redirect('dashboard:products_list')


class ProductToggleActiveView(StaffRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_active = not product.is_active
        product.save()
        messages.info(request, f"Producto '{product.name}' ahora está {'activo' if product.is_active else 'inactivo'}.")
        return redirect('dashboard:products_list')


class CustomerAdminListView(StaffRequiredMixin, View):
    def get(self, request):
        customers = User.objects.filter(is_staff=False).annotate(
            orders_count=Count('orders'),
            total_spent=Sum('orders__total')
        ).order_by('-orders_count')
        return render(request, 'dashboard/customers_list.html', {'customers': customers})


class BannerAdminListView(StaffRequiredMixin, View):
    def get(self, request):
        banners = Banner.objects.all().order_by('order')
        return render(request, 'dashboard/banners_list.html', {'banners': banners})


class SettingsAdminView(StaffRequiredMixin, View):
    def get(self, request):
        settings_obj = SiteSettings.objects.first()
        if not settings_obj:
            settings_obj = SiteSettings.objects.create()
        return render(request, 'dashboard/settings.html', {'settings_obj': settings_obj})

    def post(self, request):
        settings_obj = SiteSettings.objects.first()
        if not settings_obj:
            settings_obj = SiteSettings.objects.create()

        settings_obj.store_name = request.POST.get('store_name', settings_obj.store_name)
        settings_obj.slogan = request.POST.get('slogan', settings_obj.slogan)
        settings_obj.address = request.POST.get('address', settings_obj.address)
        settings_obj.whatsapp_phone = request.POST.get('whatsapp_phone', settings_obj.whatsapp_phone)
        settings_obj.instagram = request.POST.get('instagram', settings_obj.instagram)
        settings_obj.email = request.POST.get('email', settings_obj.email)
        settings_obj.opening_hours = request.POST.get('opening_hours', settings_obj.opening_hours)
        settings_obj.special_notice = request.POST.get('special_notice', settings_obj.special_notice)
        settings_obj.shipping_cost = int(request.POST.get('shipping_cost', settings_obj.shipping_cost))
        settings_obj.min_order_amount = int(request.POST.get('min_order_amount', settings_obj.min_order_amount))
        settings_obj.anticipation_hours = int(request.POST.get('anticipation_hours', settings_obj.anticipation_hours))
        settings_obj.blocked_dates = request.POST.get('blocked_dates', settings_obj.blocked_dates)
        settings_obj.save()

        messages.success(request, "Configuración del sitio guardada exitosamente.")
        return redirect('dashboard:settings')
