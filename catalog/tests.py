import json
from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import Category, Product, ProductVariant, AddOn
from cart.cart import Cart

class CatalogAddonsAndSuggestionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Tortas Especiales", slug="tortas-especiales")

        self.main_cake = Product.objects.create(
            category=self.category,
            name="Torta Pompadour Plátano Manjar",
            slug="torta-pompadour-platano-manjar",
            short_description="Hojarasca crocante y crema de plátano",
            description="Elaborada artesanalmente con manjar de campo y crema fresca.",
            base_price=18990,
            is_cake=True
        )
        self.variant_8p = ProductVariant.objects.create(
            product=self.main_cake,
            name="8 Personas",
            portions=8,
            price=18990,
            is_active=True
        )
        self.variant_20p = ProductVariant.objects.create(
            product=self.main_cake,
            name="20 Personas",
            portions=20,
            price=29990,
            is_active=True
        )

        self.suggested_cake = Product.objects.create(
            category=self.category,
            name="Torta Amor de Hojarasca",
            slug="torta-amor-de-hojarasca",
            short_description="Frambuesas frescas y crema diplomática",
            description="Clásica chilena con toques modernos.",
            base_price=19990,
            is_cake=True
        )
        self.sugg_variant_8p = ProductVariant.objects.create(
            product=self.suggested_cake,
            name="8 Personas",
            portions=8,
            price=19990,
            is_active=True
        )

        self.addon_velas = AddOn.objects.create(name="Set Velas Doradas", price=1490, is_active=True)
        self.addon_topper = AddOn.objects.create(name="Topper Feliz Cumpleaños", price=2990, is_active=True)
        self.addon_tarjeta = AddOn.objects.create(name="Tarjeta con Dedicatoria", price=1990, is_active=True)
        self.addon_inactive = AddOn.objects.create(name="Extra Desactivado", price=990, is_active=False)

    def test_product_detail_page_renders_addons_and_related(self):
        """Detail page includes interactive addon checkboxes and related products."""
        response = self.client.get(reverse('catalog:product_detail', kwargs={'slug': self.main_cake.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Set Velas Doradas")
        self.assertContains(response, "Topper Feliz Cumpleaños")
        self.assertContains(response, "Torta Amor de Hojarasca")
        self.assertContains(response, "name=\"addon_ids\"")

    def test_add_product_with_extras(self):
        """Adding product with extras recalculates server-side total unit price."""
        response = self.client.post(
            reverse('cart:add'),
            {
                'product_id': self.main_cake.id,
                'variant_id': self.variant_8p.id,
                'quantity': 1,
                'addon_ids': [self.addon_velas.id, self.addon_topper.id],
                'notes': 'Con amor para Mamá'
            },
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)

        # Expected price: 18990 (variant 8p) + 1490 (velas) + 2990 (topper) = 23470
        expected_price = 18990 + 1490 + 2990
        cart = Cart(response.wsgi_request)
        self.assertEqual(cart.total_items, 1)
        self.assertEqual(cart.subtotal, expected_price)
        item = list(cart)[0]
        self.assertEqual(item['price'], expected_price)
        self.assertIn("Set Velas Doradas", item['addons_text'])
        self.assertIn("Topper Feliz Cumpleaños", item['addons_text'])

    def test_change_portions_plus_extras(self):
        """Selecting a 20 persons variant plus multiple extras correctly computes pricing."""
        response = self.client.post(
            reverse('cart:add'),
            {
                'product_id': self.main_cake.id,
                'variant_id': self.variant_20p.id,
                'quantity': 2,
                'addon_ids': [self.addon_topper.id, self.addon_tarjeta.id],
            },
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)

        # Variant 20p: 29990 + Topper: 2990 + Tarjeta: 1990 = 34970 * 2 = 69940
        unit_price = 29990 + 2990 + 1990
        cart = Cart(response.wsgi_request)
        self.assertEqual(cart.total_items, 2)
        self.assertEqual(cart.subtotal, unit_price * 2)

    def test_add_suggested_product_directly(self):
        """Suggested product quick-add button adds the recommended item without leaving the page."""
        response = self.client.post(
            reverse('cart:add'),
            {
                'product_id': self.suggested_cake.id,
                'variant_id': self.sugg_variant_8p.id,
                'quantity': 1,
            },
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('cart-count-badge-container', response.content.decode('utf-8'))
        trigger = json.loads(response['HX-Trigger'])
        self.assertTrue(trigger.get('open-cart'))

        cart = Cart(response.wsgi_request)
        self.assertEqual(cart.total_items, 1)
        self.assertEqual(cart.subtotal, 19990)

    def test_server_side_validation_ignores_inactive_addons(self):
        """Inactive addons or fabricated IDs are strictly ignored by the server."""
        response = self.client.post(
            reverse('cart:add'),
            {
                'product_id': self.main_cake.id,
                'variant_id': self.variant_8p.id,
                'quantity': 1,
                'addon_ids': [self.addon_inactive.id, 99999],
            },
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        cart = Cart(response.wsgi_request)
        # Should only be base variant price: 18990
        self.assertEqual(cart.subtotal, 18990)
        item = list(cart)[0]
        self.assertEqual(item['addons_text'], '')
