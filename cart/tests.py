import json
from django.test import TestCase, RequestFactory, Client
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User
from django.urls import reverse
from catalog.models import Category, Product, ProductVariant, AddOn
from cart.cart import Cart
from cart.models import UserCart, UserCartItem

class CartTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.category = Category.objects.create(name="Tortas Tradicionales", slug="tortas-tradicionales")
        self.product = Product.objects.create(
            category=self.category,
            name="Torta Red Velvet",
            slug="torta-red-velvet",
            short_description="Bizcocho suave",
            description="Descripción detallada",
            base_price=18990,
            is_cake=True
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            name="16 Personas",
            portions=16,
            price=24990
        )
        self.addon_topper = AddOn.objects.create(name="Topper Feliz Cumpleaños", price=2990, is_active=True)
        self.addon_caja = AddOn.objects.create(name="Caja de Regalo Boutique", price=3490, is_active=True)

        self.user = User.objects.create_user(username="testuser", password="password123", email="test@daca.cl")

    def _get_request_with_session(self, user=None):
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        if user:
            request.user = user
        else:
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
        return request

    def test_cart_add_and_totals(self):
        """Test adding items and calculating subtotals correctly."""
        request = self._get_request_with_session()
        cart = Cart(request)
        self.assertEqual(len(cart), 0)

        cart.add(self.product, quantity=2)
        self.assertEqual(cart.total_items, 2)
        self.assertEqual(cart.subtotal, 18990 * 2)

    def test_cart_sum_quantity_same_line(self):
        """Adding the exact same item, variant, addons, and notes should sum quantity in same line."""
        request = self._get_request_with_session()
        cart = Cart(request)

        cart.add(self.product, variant=self.variant, quantity=1, notes="Feliz Cumple", addon_ids=[self.addon_topper.id])
        self.assertEqual(cart.total_items, 1)
        self.assertEqual(len(cart.cart), 1)

        # Add again with exact same parameters
        cart.add(self.product, variant=self.variant, quantity=2, notes="Feliz Cumple", addon_ids=[self.addon_topper.id])
        self.assertEqual(cart.total_items, 3)
        self.assertEqual(len(cart.cart), 1, "Should not create a duplicate line")

        # Add with different notes -> creates separate line
        cart.add(self.product, variant=self.variant, quantity=1, notes="Otra dedicatoria", addon_ids=[self.addon_topper.id])
        self.assertEqual(cart.total_items, 4)
        self.assertEqual(len(cart.cart), 2, "Different notes must produce a distinct line")

    def test_cart_update_quantity_and_remove(self):
        """Updating quantity and removing items works accurately."""
        request = self._get_request_with_session()
        cart = Cart(request)
        cart.add(self.product, quantity=2)
        item_key = list(cart.cart.keys())[0]

        # Update to 5
        cart.update_quantity(item_key, 5)
        self.assertEqual(cart.total_items, 5)
        self.assertEqual(cart.subtotal, 18990 * 5)

        # Update to 0 removes the item
        cart.update_quantity(item_key, 0)
        self.assertEqual(cart.total_items, 0)
        self.assertEqual(len(cart), 0)

    def test_cart_with_variants_and_extras_totals(self):
        """Pricing is strictly calculated by server based on variant price + active addons prices."""
        request = self._get_request_with_session()
        cart = Cart(request)

        # Variant: 24990, Topper: 2990, Caja: 3490 => Unit: 31470
        cart.add(self.product, variant=self.variant, quantity=2, addon_ids=[self.addon_topper.id, self.addon_caja.id])
        expected_unit_price = 24990 + 2990 + 3490
        self.assertEqual(cart.subtotal, expected_unit_price * 2)

        item = list(cart)[0]
        self.assertEqual(item['price'], expected_unit_price)
        self.assertEqual(item['total_price'], expected_unit_price * 2)
        self.assertIn("Topper Feliz Cumpleaños", item['addons_text'])
        self.assertIn("Caja de Regalo Boutique", item['addons_text'])

    def test_cart_merge_with_user_on_login(self):
        """Anonymous guest cart merges with user's persistent DB cart on login."""
        # Create an existing item in user's DB cart
        user_cart = UserCart.objects.create(user=self.user)
        UserCartItem.objects.create(
            cart=user_cart,
            product=self.product,
            variant=self.variant,
            quantity=2,
            notes="Nota guardada"
        )

        # Guest adds an item to session
        request = self._get_request_with_session()
        guest_cart = Cart(request)
        guest_cart.add(self.product, quantity=1)
        self.assertEqual(guest_cart.total_items, 1)

        # Merge with user
        guest_cart.merge_with_user(self.user)

        # Total items should be 1 guest item + 2 db items = 3
        self.assertEqual(guest_cart.total_items, 3)
        self.assertEqual(len(guest_cart.cart), 2)

    def test_htmx_cart_add_view_response(self):
        """HTMX POST to cart:add returns partial drawer with OOB badge and triggers."""
        response = self.client.post(
            reverse('cart:add'),
            {
                'product_id': self.product.id,
                'variant_id': self.variant.id,
                'quantity': 1,
                'addon_ids': [self.addon_topper.id],
                'notes': 'Felicidades'
            },
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('cart-count-badge-container', response.content.decode('utf-8'))
        self.assertIn('hx-swap-oob="innerHTML"', response.content.decode('utf-8'))
        trigger = json.loads(response['HX-Trigger'])
        self.assertTrue(trigger.get('cartUpdated'))
        self.assertTrue(trigger.get('open-cart'))
