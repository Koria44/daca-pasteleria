def cart_context(request):
    """
    Context processor to provide the active cart to all templates.
    """
    try:
        from cart.cart import Cart
        cart = Cart(request)
        return {'cart': cart}
    except Exception:
        return {'cart': {'items': [], 'total_items': 0, 'total_price': 0}}
