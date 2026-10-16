from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Usuario")
    phone = models.CharField("Teléfono / WhatsApp", max_length=40, blank=True)
    rut = models.CharField("RUT", max_length=20, blank=True)
    birth_date = models.DateField("Fecha de cumpleaños", blank=True, null=True)
    default_address_street = models.CharField("Calle y número", max_length=200, blank=True)
    default_address_details = models.CharField("Depto / Casa", max_length=100, blank=True)
    default_commune = models.CharField("Comuna", max_length=100, default="La Florida")
    dietary_preferences = models.CharField("Preferencias alimentarias o alergias", max_length=255, blank=True)
    newsletter_subscribed = models.BooleanField("Suscrito a novedades y promociones", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"Perfil de {self.user.get_full_name() or self.user.username}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_addresses', verbose_name="Usuario")
    title = models.CharField("Nombre de dirección (ej: Casa, Oficina)", max_length=80, default="Casa")
    recipient_name = models.CharField("Nombre de quien recibe", max_length=150)
    recipient_phone = models.CharField("Teléfono de contacto", max_length=40)
    street = models.CharField("Calle y número", max_length=200)
    details = models.CharField("Depto / Casa / Referencia", max_length=100, blank=True)
    commune = models.CharField("Comuna", max_length=100, default="La Florida")
    is_default = models.BooleanField("Dirección principal", default=False)

    class Meta:
        verbose_name = "Dirección guardada"
        verbose_name_plural = "Direcciones guardadas"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title}: {self.street}, {self.commune}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
