from django.db import models

class SiteSettings(models.Model):
    store_name = models.CharField("Nombre de la tienda", max_length=150, default="Daca Pastelería")
    slogan = models.CharField("Eslogan", max_length=255, default="Pastelería Artesanal en La Florida")
    address = models.CharField("Dirección", max_length=255, default="Rojas Magallanes 055, La Florida, Santiago")
    whatsapp_phone = models.CharField("Teléfono WhatsApp (con código país)", max_length=50, default="56912345678")
    instagram = models.CharField("Instagram", max_length=100, default="@dacapasteleria")
    email = models.EmailField("Correo de contacto", default="contacto@dacapasteleria.cl")
    opening_hours = models.CharField("Horarios de atención", max_length=255, default="Lunes a Domingo: 10:00 a 20:30 hrs")
    special_notice = models.CharField("Aviso especial en barra superior", max_length=300, default="¡Horneamos todos los días! Entregas y retiros disponibles hasta las 20:30 hrs")
    shipping_cost = models.PositiveIntegerField("Costo de despacho base (CLP)", default=3990)
    min_order_amount = models.PositiveIntegerField("Monto mínimo de pedido (CLP)", default=5000)
    anticipation_hours = models.PositiveIntegerField("Anticipación mínima para pedidos (horas)", default=24)
    blocked_dates = models.TextField("Fechas bloqueadas (separadas por coma YYYY-MM-DD)", blank=True, help_text="Ej: 2026-12-25, 2027-01-01")

    class Meta:
        verbose_name = "Configuración del Sitio"
        verbose_name_plural = "Configuración del Sitio"

    def __str__(self):
        return self.store_name


class Banner(models.Model):
    title = models.CharField("Título principal", max_length=200)
    subtitle = models.CharField("Subtítulo", max_length=300, blank=True)
    badge = models.CharField("Etiqueta destacada", max_length=80, blank=True, help_text="Ej: San Valentín, Nueva Temporada")
    image_desktop = models.ImageField("Imagen escritorio", upload_to='banners/', blank=True, null=True)
    image_mobile = models.ImageField("Imagen móvil", upload_to='banners/', blank=True, null=True)
    button_text = models.CharField("Texto del botón", max_length=80, default="Ver catálogo")
    button_url = models.CharField("Enlace del botón", max_length=255, default="/catalogo/")
    secondary_button_text = models.CharField("Texto botón secundario", max_length=80, blank=True, default="Pide tu torta")
    secondary_button_url = models.CharField("Enlace botón secundario", max_length=255, blank=True, default="/personalizadas/")
    order = models.PositiveIntegerField("Orden", default=0)
    is_active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    client_name = models.CharField("Nombre del cliente", max_length=150)
    quote = models.TextField("Testimonio")
    rating = models.PositiveSmallIntegerField("Calificación (1-5 estrellas)", default=5)
    occasion = models.CharField("Ocasión o producto comprado", max_length=150, blank=True, help_text="Ej: Torta Red Velvet para Cumpleaños")
    is_active = models.BooleanField("Activo", default=True)
    order = models.PositiveIntegerField("Orden", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Testimonio"
        verbose_name_plural = "Testimonios"
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.client_name} - {self.rating}★"


class ContactMessage(models.Model):
    name = models.CharField("Nombre", max_length=150)
    email = models.EmailField("Correo electrónico")
    phone = models.CharField("Teléfono", max_length=50, blank=True)
    subject = models.CharField("Asunto", max_length=200, blank=True)
    message = models.TextField("Mensaje")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField("Leído", default=False)

    class Meta:
        verbose_name = "Mensaje de contacto"
        verbose_name_plural = "Mensajes de contacto"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"
