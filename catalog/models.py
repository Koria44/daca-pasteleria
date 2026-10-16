from django.db import models
from django.urls import reverse

class Category(models.Model):
    name = models.CharField("Nombre", max_length=150)
    slug = models.SlugField("Slug", unique=True, max_length=160)
    description = models.TextField("Descripción", blank=True)
    image = models.ImageField("Imagen de categoría", upload_to='categories/', blank=True, null=True)
    icon_svg = models.TextField("SVG / Ícono", blank=True, help_text="Opcional código SVG para ícono")
    order = models.PositiveIntegerField("Orden", default=0)
    is_active = models.BooleanField("Activa", default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Categoría")
    name = models.CharField("Nombre del producto", max_length=200)
    slug = models.SlugField("Slug", unique=True, max_length=220)
    short_description = models.CharField("Descripción corta", max_length=255)
    description = models.TextField("Descripción detallada")
    base_price = models.PositiveIntegerField("Precio base (CLP)", help_text="Para tortas, precio desde la porción menor")
    is_active = models.BooleanField("Activo en tienda", default=True)
    is_featured = models.BooleanField("Destacado en Home", default=False)
    is_new = models.BooleanField("Producto Nuevo", default=False)
    is_cake = models.BooleanField("¿Es torta? (habilita selector de porciones)", default=False)
    preparation_time = models.CharField("Tiempo de preparación", max_length=100, default="24 a 48 horas")
    stock = models.IntegerField("Stock disponible (-1 si es ilimitado/bajo demanda)", default=-1)
    allergens = models.CharField("Alérgenos", max_length=255, default="Gluten, lácteos, huevo. Puede contener trazas de nueces.")
    storage_instructions = models.CharField("Conservación", max_length=255, default="Mantener refrigerado entre 2°C y 5°C. Consumir dentro de 4 días.")
    meta_title = models.CharField("Meta Title (SEO)", max_length=160, blank=True)
    meta_description = models.CharField("Meta Description (SEO)", max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-is_featured', '-is_new', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    @property
    def main_image(self):
        first_img = self.images.filter(is_main=True).first()
        if not first_img:
            first_img = self.images.first()
        return first_img

    @property
    def gallery_images(self):
        return self.images.all().order_by('-is_main', 'order')

    @property
    def has_variants(self):
        return self.variants.filter(is_active=True).exists()

    @property
    def min_price(self):
        active_vars = self.variants.filter(is_active=True)
        if active_vars.exists():
            return min(v.price for v in active_vars)
        return self.base_price

    @property
    def max_price(self):
        active_vars = self.variants.filter(is_active=True)
        if active_vars.exists():
            return max(v.price for v in active_vars)
        return self.base_price


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Producto")
    image = models.ImageField("Imagen", upload_to='products/')
    alt_text = models.CharField("Texto alternativo (alt)", max_length=200, blank=True)
    order = models.PositiveIntegerField("Orden", default=0)
    is_main = models.BooleanField("Imagen principal", default=False)

    class Meta:
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de producto"
        ordering = ['-is_main', 'order']

    def __str__(self):
        return f"{self.product.name} - Imagen {self.order}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Producto")
    name = models.CharField("Nombre de variante / Porción", max_length=150, help_text="Ej: 8 Personas, 12 Personas, Caja 6 unid")
    portions = models.PositiveIntegerField("Cantidad de personas / unidades", default=8, help_text="Para ordenar y filtrar")
    dimensions = models.CharField("Dimensiones referenciales", max_length=120, blank=True, help_text="Ej: 16 cm diámetro / 10 cm alto")
    price = models.PositiveIntegerField("Precio (CLP)")
    stock = models.IntegerField("Stock (-1 si ilimitado)", default=-1)
    is_active = models.BooleanField("Activa", default=True)
    order = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Variante / Porción"
        verbose_name_plural = "Variantes / Porciones"
        ordering = ['order', 'portions', 'price']

    def __str__(self):
        return f"{self.product.name} - {self.name} (${self.price:,})".replace(",", ".")


class Flavor(models.Model):
    FLAVOR_TYPES = [
        ('sponge', 'Bizcocho / Masa'),
        ('filling', 'Relleno'),
        ('frosting', 'Cobertura / Frosting'),
    ]
    name = models.CharField("Nombre del sabor", max_length=120)
    flavor_type = models.CharField("Tipo", max_length=20, choices=FLAVOR_TYPES, default='filling')
    description = models.CharField("Descripción", max_length=200, blank=True)
    extra_price = models.PositiveIntegerField("Recargo extra (CLP)", default=0)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Sabor"
        verbose_name_plural = "Sabores"
        ordering = ['flavor_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_flavor_type_display()})"


class AddOn(models.Model):
    name = models.CharField("Nombre del extra", max_length=120)
    description = models.CharField("Descripción", max_length=200, blank=True)
    price = models.PositiveIntegerField("Precio (CLP)", default=1990)
    image = models.ImageField("Foto opcional", upload_to='addons/', blank=True, null=True)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Extra / AddOn"
        verbose_name_plural = "Extras / AddOns"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (${self.price:,})".replace(",", ".")
