from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import Category, Product
from core.models import Banner

class PublicPagesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Tortas", slug="tortas")
        self.product = Product.objects.create(
            category=self.category,
            name="Torta Red Velvet Test",
            slug="torta-red-velvet-test",
            short_description="Corta desc",
            description="Larga desc",
            base_price=22990,
            is_cake=True
        )

    def test_public_pages_load(self):
        pages = [
            reverse('core:home'),
            reverse('core:about'),
            reverse('core:contact'),
            reverse('core:faq'),
            reverse('core:terms'),
            reverse('core:privacy'),
            reverse('catalog:product_list'),
            reverse('catalog:category_detail', kwargs={'slug': 'tortas'}),
            reverse('catalog:product_detail', kwargs={'slug': 'torta-red-velvet-test'}),
            reverse('cart:detail'),
            reverse('accounts:login'),
            reverse('accounts:register'),
            reverse('custom_orders:wizard'),
        ]

        for url in pages:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Error en URL: {url}")
