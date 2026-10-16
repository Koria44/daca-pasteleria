import logging
from django.conf import settings
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction

logger = logging.getLogger(__name__)

class WebpayService:
    """
    Service wrapper for Transbank Webpay Plus REST API.
    Supports Integration (testing) and Production modes configured via environment variables.

    ESTADO: estructura base. Pendiente de completar/verificar manualmente:
      - TODO: validar contra la doc vigente (transbankdevelopers.cl) los nombres de
              clases/métodos del SDK (WebpayOptions, IntegrationType, Transaction).
      - TODO: confirmar formato de buy_order (máx. 26 caracteres) y session_id.
      - TODO: verificar que commit()/refund() devuelvan dict (o adaptar el parseo
              en orders/views.py -> WebpayReturnView / dashboard OrderWebpayRefundView).
      - TODO: probar flujo real en integración (aprobado, rechazado, anulado, timeout).
    Puntos de conexión ya creados:
      - Modelo: orders.models.WebpayTransaction
      - Vistas: orders.views (CheckoutView rama 'webpay', WebpayReturnView,
                WebpayReceiptView, WebpayFailureView, WebpayRetryView)
      - URLs: orders/urls.py (webpay_return, webpay_receipt, webpay_failure, webpay_retry)
      - Templates: templates/orders/webpay_*.html
      - Dashboard: dashboard.views.OrderWebpayRefundView
      - Tests con mocks: orders/tests.py (WebpayIntegrationTestCase)
    """

    PAYMENT_TYPE_MAP = {
        'VD': 'Tarjeta de Débito (Redcompra)',
        'VN': 'Tarjeta de Crédito (Sin cuotas)',
        'VC': 'Tarjeta de Crédito (Cuotas normales)',
        'SI': 'Tarjeta de Crédito (3 cuotas sin interés)',
        'S2': 'Tarjeta de Crédito (2 cuotas sin interés)',
        'NC': 'Tarjeta de Crédito (N cuotas sin interés)',
        'VP': 'Tarjeta Prepago',
    }

    def __init__(self, tx_instance=None):
        if tx_instance:
            self.tx = tx_instance
            return

        self.env = getattr(settings, 'TBK_ENVIRONMENT', 'integration').lower()
        self.commerce_code = str(getattr(settings, 'TBK_COMMERCE_CODE', '597055555532'))
        self.api_key = str(getattr(settings, 'TBK_API_KEY', '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'))

        if self.env == 'production':
            self.options = WebpayOptions(
                commerce_code=self.commerce_code,
                api_key=self.api_key,
                integration_type=IntegrationType.LIVE
            )
        else:
            self.options = WebpayOptions(
                commerce_code=self.commerce_code,
                api_key=self.api_key,
                integration_type=IntegrationType.TEST
            )
        self.tx = Transaction(self.options)

    def create_transaction(self, order, session_id, return_url):
        """
        Initiates a Webpay transaction.
        Amount is strictly calculated on the server in whole CLP.
        buy_order is max 26 characters.
        """
        # Ensure buy_order is <= 26 chars
        clean_order_num = order.order_number.replace('-', '')
        buy_order = f"DACA{clean_order_num}"[:26]
        amount = int(order.total)

        response = self.tx.create(
            buy_order=buy_order,
            session_id=str(session_id)[:60],
            amount=amount,
            return_url=return_url
        )
        return {
            'token': response.get('token'),
            'url': response.get('url'),
            'buy_order': buy_order,
            'amount': amount,
        }

    def commit_transaction(self, token):
        """
        Commits a transaction using the token returned by Webpay.
        """
        return self.tx.commit(token=token)

    def refund_transaction(self, token, amount):
        """
        Reverses or refunds an authorized transaction.
        """
        return self.tx.refund(token=token, amount=int(amount))

    @classmethod
    def get_payment_type_description(cls, code):
        return cls.PAYMENT_TYPE_MAP.get(code, f'Tarjeta bancaria ({code or "Webpay"})')
