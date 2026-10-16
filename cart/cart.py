from catalog.models import Product, ProductVariant, AddOn

class Cart:
    """
    Session-based cart implementation for Daca Pastelería.
    Supports anonymous guest carts, live reactivity, addons/extras,
    and automatic database synchronization/merging when users log in.
    """
    def __init__(self, request):
        self.session = request.session
        self.request = request
        cart = self.session.get('cart')
        if cart is None:
            cart = self.session['cart'] = {}
            if hasattr(request, 'user') and request.user.is_authenticated:
                self.cart = cart
                self._load_from_db(request.user)
                return
        self.cart = cart

    def __iter__(self):
        for item_key, item_data in list(self.cart.items()):
            yield {
                'key': item_key,
                'product_id': item_data.get('product_id'),
                'variant_id': item_data.get('variant_id'),
                'name': item_data.get('name'),
                'variant_name': item_data.get('variant_name', ''),
                'price': item_data.get('price', 0),
                'quantity': item_data.get('quantity', 1),
                'image_url': item_data.get('image_url', ''),
                'notes': item_data.get('notes', ''),
                'addon_ids': item_data.get('addon_ids', []),
                'addons_text': item_data.get('addons_text', ''),
                'addons': item_data.get('addons', []),
                'total_price': item_data.get('price', 0) * item_data.get('quantity', 1),
            }

    def __len__(self):
        return sum(item.get('quantity', 1) for item in self.cart.values())

    @property
    def total_items(self):
        return len(self)

    @property
    def subtotal(self):
        return sum(item.get('price', 0) * item.get('quantity', 1) for item in self.cart.values())

    @property
    def total_price(self):
        return self.subtotal

    def add(self, product, variant=None, quantity=1, notes="", addon_ids=None):
        """
        Add a product (with optional variant and validated addons) to the cart.
        Recalculates pricing strictly on the server.
        """
        if quantity <= 0:
            return

        # Server-side validation of addons
        active_addons = []
        if addon_ids:
            # Filter valid integers and query database
            clean_ids = [int(i) for i in addon_ids if str(i).isdigit()]
            if clean_ids:
                active_addons = list(AddOn.objects.filter(id__in=clean_ids, is_active=True))

        sorted_addon_ids = sorted([a.id for a in active_addons])
        addon_data_list = [{'id': a.id, 'name': a.name, 'price': int(a.price)} for a in active_addons]
        addons_price = sum(a['price'] for a in addon_data_list)
        addons_text = ", ".join([f"{a['name']} (+${a['price']:,})".replace(",", ".") for a in addon_data_list])

        base_price = int(variant.price if variant else product.base_price)
        unit_price = base_price + addons_price

        # Build consistent line-item key
        addons_key = "-".join(str(i) for i in sorted_addon_ids) if sorted_addon_ids else "none"
        clean_notes = notes.strip()
        item_key = f"{product.id}_{variant.id if variant else 'base'}_{addons_key}_{clean_notes.lower()}"

        if item_key not in self.cart:
            image_url = ""
            if product.main_image and hasattr(product.main_image, 'image') and product.main_image.image:
                try:
                    image_url = product.main_image.image.url
                except Exception:
                    image_url = ""

            self.cart[item_key] = {
                'product_id': product.id,
                'variant_id': variant.id if variant else None,
                'name': product.name,
                'variant_name': variant.name if variant else "",
                'price': unit_price,
                'quantity': 0,
                'image_url': image_url,
                'notes': clean_notes,
                'addon_ids': sorted_addon_ids,
                'addons_text': addons_text,
                'addons': addon_data_list,
            }

        self.cart[item_key]['quantity'] += quantity
        if clean_notes:
            self.cart[item_key]['notes'] = clean_notes
        self.save()

    def update_quantity(self, item_key, quantity):
        if item_key in self.cart:
            if quantity <= 0:
                self.remove(item_key)
            else:
                self.cart[item_key]['quantity'] = quantity
                self.save()

    def remove(self, item_key):
        if item_key in self.cart:
            del self.cart[item_key]
            self.save()

    def clear(self):
        self.cart.clear()
        self.session['cart'] = {}
        self.session.modified = True
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            self._sync_to_db(self.request.user)

    def save(self):
        self.session['cart'] = self.cart
        self.session.modified = True
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            self._sync_to_db(self.request.user)

    def merge_with_user(self, user):
        """
        Merges guest session cart with the user's persistent DB cart upon login.
        """
        if not user or not user.is_authenticated:
            return

        from .models import UserCart, UserCartItem
        user_cart, _ = UserCart.objects.get_or_create(user=user)

        # Merge DB items into session
        db_items = user_cart.items.select_related('product', 'variant').all()
        for db_item in db_items:
            addons_ids = db_item.addon_ids or []
            active_addons = list(AddOn.objects.filter(id__in=addons_ids, is_active=True)) if addons_ids else []
            sorted_addon_ids = sorted([a.id for a in active_addons])
            addons_key = "-".join(str(i) for i in sorted_addon_ids) if sorted_addon_ids else "none"
            clean_notes = (db_item.notes or "").strip()
            item_key = f"{db_item.product.id}_{db_item.variant.id if db_item.variant else 'base'}_{addons_key}_{clean_notes.lower()}"

            if item_key in self.cart:
                self.cart[item_key]['quantity'] += db_item.quantity
            else:
                addon_data_list = [{'id': a.id, 'name': a.name, 'price': int(a.price)} for a in active_addons]
                addons_price = sum(a['price'] for a in addon_data_list)
                base_price = int(db_item.variant.price if db_item.variant else db_item.product.base_price)
                addons_text = ", ".join([f"{a['name']} (+${a['price']:,})".replace(",", ".") for a in addon_data_list])

                image_url = ""
                if db_item.product.main_image and hasattr(db_item.product.main_image, 'image') and db_item.product.main_image.image:
                    try:
                        image_url = db_item.product.main_image.image.url
                    except Exception:
                        image_url = ""

                self.cart[item_key] = {
                    'product_id': db_item.product.id,
                    'variant_id': db_item.variant.id if db_item.variant else None,
                    'name': db_item.product.name,
                    'variant_name': db_item.variant.name if db_item.variant else "",
                    'price': base_price + addons_price,
                    'quantity': db_item.quantity,
                    'image_url': image_url,
                    'notes': clean_notes,
                    'addon_ids': sorted_addon_ids,
                    'addons_text': addons_text,
                    'addons': addon_data_list,
                }

        self.save()
        self._sync_to_db(user)

    def _load_from_db(self, user):
        """Loads items from user's persistent cart when session is fresh."""
        from .models import UserCart
        user_cart = UserCart.objects.filter(user=user).first()
        if not user_cart:
            return

        for db_item in user_cart.items.select_related('product', 'variant').all():
            addons_ids = db_item.addon_ids or []
            active_addons = list(AddOn.objects.filter(id__in=addons_ids, is_active=True)) if addons_ids else []
            sorted_addon_ids = sorted([a.id for a in active_addons])
            addons_key = "-".join(str(i) for i in sorted_addon_ids) if sorted_addon_ids else "none"
            clean_notes = (db_item.notes or "").strip()
            item_key = f"{db_item.product.id}_{db_item.variant.id if db_item.variant else 'base'}_{addons_key}_{clean_notes.lower()}"

            addon_data_list = [{'id': a.id, 'name': a.name, 'price': int(a.price)} for a in active_addons]
            addons_price = sum(a['price'] for a in addon_data_list)
            base_price = int(db_item.variant.price if db_item.variant else db_item.product.base_price)
            addons_text = ", ".join([f"{a['name']} (+${a['price']:,})".replace(",", ".") for a in addon_data_list])

            image_url = ""
            if db_item.product.main_image and hasattr(db_item.product.main_image, 'image') and db_item.product.main_image.image:
                try:
                    image_url = db_item.product.main_image.image.url
                except Exception:
                    image_url = ""

            self.cart[item_key] = {
                'product_id': db_item.product.id,
                'variant_id': db_item.variant.id if db_item.variant else None,
                'name': db_item.product.name,
                'variant_name': db_item.variant.name if db_item.variant else "",
                'price': base_price + addons_price,
                'quantity': db_item.quantity,
                'image_url': image_url,
                'notes': clean_notes,
                'addon_ids': sorted_addon_ids,
                'addons_text': addons_text,
                'addons': addon_data_list,
            }
        self.session['cart'] = self.cart
        self.session.modified = True

    def _sync_to_db(self, user):
        """Synchronizes current session cart to UserCart in database."""
        try:
            from .models import UserCart, UserCartItem
            user_cart, _ = UserCart.objects.get_or_create(user=user)
            user_cart.items.all().delete()
            for item in self.cart.values():
                product_id = item.get('product_id')
                variant_id = item.get('variant_id')
                if product_id:
                    UserCartItem.objects.create(
                        cart=user_cart,
                        product_id=product_id,
                        variant_id=variant_id,
                        quantity=item.get('quantity', 1),
                        notes=item.get('notes', ''),
                        addon_ids=item.get('addon_ids', []),
                    )
        except Exception:
            pass
