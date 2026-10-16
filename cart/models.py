from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product, ProductVariant

class UserCart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='db_cart', verbose_name="Usuario")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrito persistente"
        verbose_name_plural = "Carritos persistentes"

    def __str__(self):
        return f"Carrito de {self.user.username}"


class UserCartItem(models.Model):
    cart = models.ForeignKey(UserCart, on_delete=models.CASCADE, related_name='items', verbose_name="Carrito")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Producto")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Variante / Porción")
    quantity = models.PositiveIntegerField("Cantidad", default=1)
    notes = models.CharField("Notas o dedicatoria", max_length=255, blank=True)
    addon_ids = models.JSONField("IDs de extras", default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ítem de carrito persistente"
        verbose_name_plural = "Ítems de carrito persistente"

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
