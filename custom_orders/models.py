import uuid
from django.db import models
from django.contrib.auth.models import User

class CakeStyle(models.Model):
    name = models.CharField("Nombre del estilo", max_length=150)
    slug = models.SlugField("Slug", unique=True, max_length=160)
    description = models.TextField("Descripción")
    image = models.ImageField("Imagen referencial", upload_to='cake_styles/')
    base_price = models.PositiveIntegerField("Precio base referencial (CLP)", default=25000)
    order = models.PositiveIntegerField("Orden", default=0)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Estilo de torta"
        verbose_name_plural = "Estilos de tortas personalizadas"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} (desde ${self.base_price:,})".replace(",", ".")


class CustomCakeOrder(models.Model):
    STATUS_CHOICES = [
        ('received', 'Recibida - En revisión'),
        ('quoted', 'Cotizada - Esperando aprobación'),
        ('approved', 'Aprobada por cliente'),
        ('in_preparation', 'En preparación'),
        ('ready', 'Lista para retiro / entrega'),
        ('delivered', 'Entregada'),
        ('rejected', 'Rechazada / Cancelada'),
    ]

    order_number = models.CharField("Número de cotización", max_length=32, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='custom_orders', verbose_name="Usuario")

    # Style & Configuration
    cake_style = models.ForeignKey(CakeStyle, on_delete=models.PROTECT, related_name='orders', verbose_name="Estilo de torta")
    portions = models.PositiveIntegerField("Porciones / Personas", default=12)
    sponge_flavor = models.CharField("Sabor del bizcocho", max_length=120, default="Red Velvet")
    filling_flavor = models.CharField("Relleno", max_length=150, default="Frosting de queso crema y manjar")
    frosting_type = models.CharField("Tipo de cobertura", max_length=120, default="Buttercream suave")
    color_palette = models.CharField("Paleta de colores / Temática", max_length=150, blank=True, help_text="Ej: Rosado blush, dorado y blanco")
    message_on_cake = models.CharField("Texto o dedicatoria en la torta", max_length=150, blank=True, help_text="Ej: Feliz Cumpleaños Vale!")
    topper = models.CharField("Topper / Decoración especial", max_length=120, blank=True, help_text="Ej: Topper acrílico 'Feliz Cumpleaños'")
    allergies_restrictions = models.CharField("Alergias o restricciones", max_length=255, blank=True)

    # Reference images (up to 3)
    reference_image_1 = models.ImageField("Foto de referencia 1", upload_to='custom_cakes/', blank=True, null=True)
    reference_image_2 = models.ImageField("Foto de referencia 2", upload_to='custom_cakes/', blank=True, null=True)
    reference_image_3 = models.ImageField("Foto de referencia 3", upload_to='custom_cakes/', blank=True, null=True)

    # Timing & Delivery
    desired_date = models.DateField("Fecha deseada de entrega / retiro")
    delivery_preference = models.CharField("Preferencia de entrega", max_length=30, choices=[('pickup', 'Retiro en local'), ('delivery', 'Despacho a domicilio')], default='pickup')
    estimated_budget = models.PositiveIntegerField("Presupuesto estimado (CLP)", blank=True, null=True)

    # Customer Contact
    customer_name = models.CharField("Nombre completo", max_length=150)
    customer_email = models.EmailField("Correo electrónico")
    customer_phone = models.CharField("Teléfono / WhatsApp", max_length=40)
    customer_notes = models.TextField("Detalles adicionales o ideas del cliente", blank=True)

    # Bakery Response
    status = models.CharField("Estado", max_length=30, choices=STATUS_CHOICES, default='received')
    final_price = models.PositiveIntegerField("Precio final cotizado (CLP)", blank=True, null=True)
    deposit_required = models.PositiveIntegerField("Anticipo requerido (CLP)", blank=True, null=True)
    deposit_paid = models.BooleanField("Anticipo pagado", default=False)
    bakery_response = models.TextField("Respuesta de la pastelería", blank=True)
    internal_notes = models.TextField("Notas internas", blank=True)

    created_at = models.DateTimeField("Fecha de solicitud", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)

    class Meta:
        verbose_name = "Pedido personalizado"
        verbose_name_plural = "Pedidos personalizados (Tortas a pedido)"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"CUSTOM-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.customer_name} ({self.cake_style.name})"
