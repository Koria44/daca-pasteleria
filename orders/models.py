import uuid
from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product, ProductVariant

class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Porcentaje (%)'),
        ('fixed', 'Monto fijo (CLP)'),
    ]
    code = models.CharField("Código de cupón", max_length=50, unique=True)
    discount_type = models.CharField("Tipo de descuento", max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.PositiveIntegerField("Valor del descuento (% o CLP)")
    min_purchase = models.PositiveIntegerField("Compra mínima (CLP)", default=0)
    valid_from = models.DateTimeField("Válido desde")
    valid_until = models.DateTimeField("Válido hasta")
    max_uses = models.IntegerField("Usos máximos (-1 para ilimitado)", default=-1)
    current_uses = models.PositiveIntegerField("Usos actuales", default=0)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Cupón de descuento"
        verbose_name_plural = "Cupones de descuento"

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'percentage' else ' CLP'})"

    def calculate_discount(self, subtotal):
        if not self.is_active or subtotal < self.min_purchase:
            return 0
        if self.discount_type == 'percentage':
            return int(round(subtotal * (self.discount_value / 100.0)))
        return min(self.discount_value, subtotal)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente de confirmación'),
        ('confirmed', 'Confirmado / En cola'),
        ('in_preparation', 'En preparación / Horneando'),
        ('ready', 'Listo para retiro / En despacho'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]

    DELIVERY_CHOICES = [
        ('pickup', 'Retiro en local (Rojas Magallanes 055, La Florida)'),
        ('delivery', 'Despacho a domicilio'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('transfer', 'Transferencia bancaria directa'),
        ('cash_on_delivery', 'Pago al retirar / contra entrega'),
        ('webpay', 'Webpay Plus (Débito / Crédito) [En preparación]'),
        ('mercadopago', 'Mercado Pago [En preparación]'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('failed', 'Fallido / Rechazado'),
        ('refunded', 'Reembolsado'),
    ]

    order_number = models.CharField("Número de pedido", max_length=32, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Usuario")

    # Contact Info
    full_name = models.CharField("Nombre completo", max_length=160)
    email = models.EmailField("Correo electrónico")
    phone = models.CharField("Teléfono / WhatsApp", max_length=40)

    # Delivery Info
    delivery_type = models.CharField("Tipo de entrega", max_length=20, choices=DELIVERY_CHOICES, default='pickup')
    address_street = models.CharField("Dirección / Calle y número", max_length=200, blank=True)
    address_details = models.CharField("Depto / Casa / Referencia", max_length=100, blank=True)
    commune = models.CharField("Comuna", max_length=100, default="La Florida")
    delivery_date = models.DateField("Fecha de entrega / retiro")
    delivery_time_slot = models.CharField("Horario preferido", max_length=80, default="14:00 a 17:00 hrs")

    # Notes
    customer_notes = models.TextField("Notas del cliente / Dedicatoria", blank=True)
    internal_notes = models.TextField("Notas internas de pastelería", blank=True)

    # Financials
    subtotal = models.PositiveIntegerField("Subtotal (CLP)", default=0)
    shipping_cost = models.PositiveIntegerField("Costo de envío (CLP)", default=0)
    discount = models.PositiveIntegerField("Descuento (CLP)", default=0)
    total = models.PositiveIntegerField("Total final (CLP)", default=0)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cupón aplicado")

    # Status
    status = models.CharField("Estado del pedido", max_length=30, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField("Método de pago", max_length=30, choices=PAYMENT_METHOD_CHOICES, default='transfer')
    payment_status = models.CharField("Estado del pago", max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_proof = models.ImageField("Comprobante de transferencia", upload_to='payment_proofs/', blank=True, null=True)

    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"DACA-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.full_name} (${self.total:,})".replace(",", ".")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Pedido")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Producto")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Variante / Porción")
    product_name = models.CharField("Nombre del producto", max_length=200)
    variant_name = models.CharField("Nombre de porción/variante", max_length=150, blank=True)
    unit_price = models.PositiveIntegerField("Precio unitario (CLP)")
    quantity = models.PositiveIntegerField("Cantidad", default=1)
    subtotal = models.PositiveIntegerField("Subtotal (CLP)")
    notes = models.CharField("Notas o dedicatoria", max_length=255, blank=True)
    addons_text = models.CharField("Extras / Sugerencias", max_length=255, blank=True)
    addon_ids = models.JSONField("IDs de addons", default=list, blank=True)

    class Meta:
        verbose_name = "Ítem de pedido"
        verbose_name_plural = "Ítems de pedido"

    def __str__(self):
        return f"{self.quantity}x {self.product_name} ({self.variant_name})"


class WebpayTransaction(models.Model):
    STATUS_CHOICES = [
        ('INITIALIZED', 'Iniciada'),
        ('AUTHORIZED', 'Autorizada / Pagada'),
        ('FAILED', 'Rechazada / Fallida'),
        ('ABORTED', 'Anulada por usuario'),
        ('TIMEOUT', 'Expirada / Timeout'),
        ('REFUNDED', 'Reembolsada / Reversada'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='webpay_transactions', verbose_name="Pedido")
    token = models.CharField("Token Transbank", max_length=100, unique=True, db_index=True)
    buy_order = models.CharField("Orden de compra (buy_order)", max_length=40, db_index=True)
    session_id = models.CharField("ID de sesión", max_length=60)
    amount = models.PositiveIntegerField("Monto (CLP)")
    status = models.CharField("Estado", max_length=30, choices=STATUS_CHOICES, default='INITIALIZED')
    response_code = models.IntegerField("Código de respuesta", null=True, blank=True)
    authorization_code = models.CharField("Código de autorización", max_length=40, blank=True)
    payment_type_code = models.CharField("Tipo de pago", max_length=20, blank=True)
    card_number = models.CharField("Últimos 4 dígitos", max_length=10, blank=True)
    shares_number = models.PositiveIntegerField("Número de cuotas", default=0)
    transaction_date = models.DateTimeField("Fecha de transacción", null=True, blank=True)
    raw_response = models.JSONField("Respuesta cruda de Transbank", default=dict, blank=True)
    refund_raw_response = models.JSONField("Respuesta de reembolso", default=dict, blank=True)
    created_at = models.DateTimeField("Creada", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizada", auto_now=True)

    class Meta:
        verbose_name = "Transacción Webpay"
        verbose_name_plural = "Transacciones Webpay"
        ordering = ['-created_at']

    def __str__(self):
        return f"Webpay {self.buy_order} - {self.status} (${self.amount:,} CLP)".replace(",", ".")

