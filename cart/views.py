import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse
from catalog.models import Product, ProductVariant
from .cart import Cart

class CartDetailView(View):
    def get(self, request):
        cart = Cart(request)
        return render(request, 'cart/cart_detail.html', {'cart': cart})


class CartAddView(View):
    def post(self, request):
        cart = Cart(request)
        product_id = request.POST.get('product_id')
        variant_id = request.POST.get('variant_id')
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1
        notes = request.POST.get('notes', '').strip()

        # Addon IDs can come as a list
        addon_ids = request.POST.getlist('addon_ids')
        if not addon_ids:
            addon_ids = request.POST.getlist('addon_ids[]')

        product = get_object_or_404(Product, id=product_id, is_active=True)
        variant = None
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product, is_active=True)

        cart.add(product=product, variant=variant, quantity=quantity, notes=notes, addon_ids=addon_ids)

        # If requested by HTMX, return drawer content with OOB badge and open-cart trigger
        if request.headers.get('HX-Request'):
            response = render(request, 'cart/partials/_cart_drawer_content.html', {'cart': cart})
            response['HX-Trigger'] = json.dumps({'cartUpdated': True, 'open-cart': True})
            return response

        return redirect('cart:detail')


class CartUpdateView(View):
    def post(self, request):
        cart = Cart(request)
        item_key = request.POST.get('item_key')
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

        cart.update_quantity(item_key, quantity)

        if request.headers.get('HX-Request'):
            is_full_page = request.POST.get('is_full_page') == '1'
            if is_full_page:
                template = 'cart/partials/_cart_page_items.html'
            else:
                template = 'cart/partials/_cart_drawer_content.html'
            response = render(request, template, {'cart': cart})
            response['HX-Trigger'] = json.dumps({'cartUpdated': True})
            return response

        return redirect('cart:detail')


class CartRemoveView(View):
    def post(self, request):
        cart = Cart(request)
        item_key = request.POST.get('item_key')
        cart.remove(item_key)

        if request.headers.get('HX-Request'):
            is_full_page = request.POST.get('is_full_page') == '1'
            if is_full_page:
                template = 'cart/partials/_cart_page_items.html'
            else:
                template = 'cart/partials/_cart_drawer_content.html'
            response = render(request, template, {'cart': cart})
            response['HX-Trigger'] = json.dumps({'cartUpdated': True})
            return response

        return redirect('cart:detail')


class CartDrawerView(View):
    def get(self, request):
        cart = Cart(request)
        return render(request, 'cart/partials/_cart_drawer_content.html', {'cart': cart})


class CartBadgeView(View):
    def get(self, request):
        cart = Cart(request)
        if cart.total_items > 0:
            badge_html = f'<span id="cart-count-badge" data-count="{cart.total_items}" class="absolute -top-1 -right-1 bg-heart text-white text-[11px] font-bold rounded-full h-5 w-5 flex items-center justify-center animate-pulse-subtle">{cart.total_items}</span>'
        else:
            badge_html = '<span id="cart-count-badge" data-count="0"></span>'
        return HttpResponse(badge_html)
