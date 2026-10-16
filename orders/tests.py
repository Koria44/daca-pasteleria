from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models import Category, Product, ProductVariant
from orders.models import Order, OrderItem, Coupon, WebpayTransaction
from cart.cart import Cart

class OrderTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Tortas", slug="tortas")
        self.product = Product.objects.create(
            category=self.category,
            name="Torta Red Velvet",
            slug="torta-red-velvet",
            short_description="Deliciosa",
            description="Larga descripción",
            base_price=22990,
            is_cake=True
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            name="12 Personas",
            portions=12,
            price=28990
        )

    def test_order_number_auto_generation(self):
        order = Order.objects.create(
            full_name="Constanza Morales",
            email="coni@ejemplo.cl",
            phone="+56912345678",
            delivery_date=timezone.localdate() + timedelta(days=2),
            subtotal=28990,
            total=28990
        )
        self.assertTrue(order.order_number.startswith("DACA-"))
        self.assertEqual(order.status, "pending")

    def test_coupon_calculation(self):
        coupon_pct = Coupon.objects.create(
            code="TEST10",
            discount_type="percentage",
            discount_value=10,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=10)
        )
        discount = coupon_pct.calculate_discount(20000)
        self.assertEqual(discount, 2000)

        coupon_fixed = Coupon.objects.create(
            code="TEST3000",
            discount_type="fixed",
            discount_value=3000,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=10)
        )
        discount_fixed = coupon_fixed.calculate_discount(20000)
        self.assertEqual(discount_fixed, 3000)


class WebpayIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_superuser(username="admin", password="password123", email="admin@daca.cl")
        self.category = Category.objects.create(name="Pasteles", slug="pasteles")
        self.product = Product.objects.create(
            category=self.category,
            name="Torta Lúcuma Manjar",
            slug="torta-lucuma-manjar",
            short_description="Clásica",
            description="Descripción lúcuma",
            base_price=20990
        )
        self.order = Order.objects.create(
            full_name="Valentina Valenzuela",
            email="vale@ejemplo.cl",
            phone="+56998765432",
            delivery_date=timezone.localdate() + timedelta(days=2),
            subtotal=20990,
            total=20990,
            payment_method='webpay',
            payment_status='pending',
            status='pending'
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            unit_price=20990,
            quantity=1,
            subtotal=20990
        )

    @patch('orders.services.webpay_service.Transaction')
    def test_checkout_webpay_initiation(self, mock_tx_cls):
        """Checkout with Webpay creates transaction and renders redirect form."""
        mock_tx_instance = MagicMock()
        mock_tx_instance.create.return_value = {
            'token': 'mocked_token_123',
            'url': 'https://webpay3gint.transbank.cl/webpayserver/initTransaction'
        }
        mock_tx_cls.return_value = mock_tx_instance

        # Populate session cart
        session = self.client.session
        session['cart'] = {
            '1_base': {
                'product_id': self.product.id,
                'name': self.product.name,
                'price': 20990,
                'quantity': 1,
            }
        }
        session.save()

        response = self.client.post(reverse('orders:checkout'), {
            'full_name': 'Ignacio Rojas',
            'email': 'nacho@daca.cl',
            'phone': '+56911223344',
            'delivery_type': 'pickup',
            'delivery_date': str(timezone.localdate() + timedelta(days=2)),
            'payment_method': 'webpay',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://webpay3gint.transbank.cl/webpayserver/initTransaction')
        self.assertContains(response, 'mocked_token_123')

        # WebpayTransaction record created in DB
        tx = WebpayTransaction.objects.filter(token='mocked_token_123').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.status, 'INITIALIZED')

    @patch('orders.services.webpay_service.Transaction')
    def test_webpay_commit_successful(self, mock_tx_cls):
        """Successful payment commits transaction, marks order paid, and clears cart."""
        mock_tx_instance = MagicMock()
        mock_tx_instance.commit.return_value = {
            'vci': 'TSY',
            'amount': 20990,
            'status': 'AUTHORIZED',
            'buy_order': self.order.order_number[:26],
            'session_id': 'sess123',
            'card_detail': {'card_number': '6623'},
            'accounting_date': '1016',
            'transaction_date': '2026-10-16T12:00:00.000Z',
            'authorization_code': '1213',
            'payment_type_code': 'VN',
            'response_code': 0,
            'shares_number': 0
        }
        mock_tx_cls.return_value = mock_tx_instance

        tx = WebpayTransaction.objects.create(
            order=self.order,
            token='token_approved_123',
            buy_order=self.order.order_number[:26],
            session_id='sess123',
            amount=20990,
            status='INITIALIZED'
        )

        # Set cart in session
        session = self.client.session
        session['cart'] = {'item': 'data'}
        session.save()

        # Webpay returns with token_ws
        response = self.client.post(reverse('orders:webpay_return'), {'token_ws': 'token_approved_123'})
        self.assertRedirects(response, reverse('orders:webpay_receipt', kwargs={'order_number': self.order.order_number}))

        self.order.refresh_from_db()
        tx.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.status, 'confirmed')
        self.assertEqual(tx.status, 'AUTHORIZED')
        self.assertEqual(tx.authorization_code, '1213')
        self.assertEqual(tx.card_number, '6623')

        # Cart must be cleared
        cart = Cart(response.wsgi_request)
        self.assertEqual(len(cart), 0)

    @patch('orders.services.webpay_service.Transaction')
    def test_webpay_commit_rejected(self, mock_tx_cls):
        """Rejected payment marks order failed but preserves cart."""
        mock_tx_instance = MagicMock()
        mock_tx_instance.commit.return_value = {
            'amount': 20990,
            'status': 'FAILED',
            'buy_order': self.order.order_number[:26],
            'response_code': -1,
            'card_detail': {'card_number': '0568'},
        }
        mock_tx_cls.return_value = mock_tx_instance

        tx = WebpayTransaction.objects.create(
            order=self.order,
            token='token_rejected_123',
            buy_order=self.order.order_number[:26],
            session_id='sess123',
            amount=20990,
            status='INITIALIZED'
        )

        session = self.client.session
        session['cart'] = {'sample_item': {'quantity': 2, 'price': 10000}}
        session.save()

        response = self.client.post(reverse('orders:webpay_return'), {'token_ws': 'token_rejected_123'})
        self.assertRedirects(response, reverse('orders:webpay_failure', kwargs={'order_number': self.order.order_number}))

        self.order.refresh_from_db()
        tx.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'failed')
        self.assertEqual(tx.status, 'FAILED')

        # Cart is PRESERVED
        cart = Cart(response.wsgi_request)
        self.assertGreater(len(cart), 0)

    def test_webpay_user_cancelled_abort(self):
        """When user clicks Cancel in Webpay, returns TBK_TOKEN, transaction is marked ABORTED and cart is safe."""
        tx = WebpayTransaction.objects.create(
            order=self.order,
            token='token_aborted_123',
            buy_order=self.order.order_number[:26],
            session_id='sess_abort',
            amount=20990,
            status='INITIALIZED'
        )

        session = self.client.session
        session['cart'] = {'cake': {'quantity': 1, 'price': 20990}}
        session.save()

        response = self.client.post(reverse('orders:webpay_return'), {
            'TBK_TOKEN': 'token_aborted_123',
            'TBK_ORDEN_COMPRA': self.order.order_number[:26],
            'TBK_ID_SESION': 'sess_abort'
        })
        self.assertRedirects(response, reverse('orders:webpay_failure', kwargs={'order_number': self.order.order_number}))

        self.order.refresh_from_db()
        tx.refresh_from_db()
        self.assertEqual(tx.status, 'ABORTED')
        self.assertEqual(self.order.payment_status, 'failed')

        cart = Cart(response.wsgi_request)
        self.assertEqual(len(cart), 1)

    def test_webpay_timeout(self):
        """When transaction times out, TBK_ORDEN_COMPRA arrives without token, transaction marked TIMEOUT and cart preserved."""
        tx = WebpayTransaction.objects.create(
            order=self.order,
            token='token_timeout_123',
            buy_order=self.order.order_number[:26],
            session_id='sess_timeout',
            amount=20990,
            status='INITIALIZED'
        )

        response = self.client.post(reverse('orders:webpay_return'), {
            'TBK_ORDEN_COMPRA': self.order.order_number[:26],
            'TBK_ID_SESION': 'sess_timeout'
        })
        self.assertRedirects(response, reverse('orders:webpay_failure', kwargs={'order_number': self.order.order_number}))

        tx.refresh_from_db()
        self.assertEqual(tx.status, 'TIMEOUT')

    @patch('orders.services.webpay_service.Transaction')
    def test_webpay_double_return_idempotency(self, mock_tx_cls):
        """Refreshing return URL when already paid does not execute commit again."""
        mock_tx_instance = MagicMock()
        mock_tx_cls.return_value = mock_tx_instance

        self.order.payment_status = 'paid'
        self.order.status = 'confirmed'
        self.order.save()

        tx = WebpayTransaction.objects.create(
            order=self.order,
            token='token_already_paid',
            buy_order=self.order.order_number[:26],
            session_id='sess_paid',
            amount=20990,
            status='AUTHORIZED'
        )

        response = self.client.get(reverse('orders:webpay_return'), {'token_ws': 'token_already_paid'})
        self.assertRedirects(response, reverse('orders:webpay_receipt', kwargs={'order_number': self.order.order_number}))

        # mock commit must NOT have been called
        mock_tx_instance.commit.assert_not_called()

    @patch('orders.services.webpay_service.Transaction')
    def test_webpay_staff_refund(self, mock_tx_cls):
        """Staff member can refund an authorized transaction from dashboard."""
        mock_tx_instance = MagicMock()
        mock_tx_instance.refund.return_value = {
            'type': 'REVERSED',
            'authorization_code': '998877',
            'authorization_date': '2026-10-16T12:00:00.000Z',
            'nullified_amount': 20990,
            'balance': 0,
            'response_code': 0
        }
        mock_tx_cls.return_value = mock_tx_instance

        self.order.payment_status = 'paid'
        self.order.save()

        tx = WebpayTransaction.objects.create(
            order=self.order,
            token='token_to_refund',
            buy_order=self.order.order_number[:26],
            session_id='sess_refund',
            amount=20990,
            status='AUTHORIZED'
        )

        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('dashboard:order_webpay_refund', kwargs={'pk': self.order.pk}))
        self.assertRedirects(response, reverse('dashboard:order_detail', kwargs={'pk': self.order.pk}))

        self.order.refresh_from_db()
        tx.refresh_from_db()
        self.assertEqual(tx.status, 'REFUNDED')
        self.assertEqual(self.order.payment_status, 'refunded')
        self.assertEqual(self.order.status, 'cancelled')
