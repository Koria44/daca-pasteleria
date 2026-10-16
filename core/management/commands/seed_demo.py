import os
from pathlib import Path
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from core.models import SiteSettings, Banner, Testimonial
from catalog.models import Category, Product, ProductImage, ProductVariant, Flavor, AddOn
from custom_orders.models import CakeStyle, CustomCakeOrder
from orders.models import Order, OrderItem, Coupon
from accounts.models import UserProfile, Address

def create_placeholder_image(output_path, text, category_name="Daca Pastelería", width=800, height=800, bg_color=(251, 246, 239), accent_color=(201, 162, 122)):
    """
    Generates a high-quality boutique placeholder image using Pillow.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.exists(output_path):
        return

    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Decorative border
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=accent_color, width=3)
    draw.rectangle([(28, 28), (width - 28, height - 28)], outline=(215, 38, 61), width=1)

    # Center circle
    cx, cy = width // 2, height // 2 - 20
    radius = min(width, height) // 4
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=(244, 214, 208), outline=accent_color, width=2)

    # Simple heart symbol
    heart_points = [
        (cx, cy + 30),
        (cx - 35, cy - 10),
        (cx - 35, cy - 35),
        (cx - 15, cy - 45),
        (cx, cy - 25),
        (cx + 15, cy - 45),
        (cx + 35, cy - 35),
        (cx + 35, cy - 10),
    ]
    draw.polygon(heart_points, fill=(215, 38, 61))

    # Text rendering (simple fallback fonts)
    try:
        font_large = ImageFont.truetype("arial.ttf", 32)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw titles
    draw.text((cx, cy + radius + 40), text[:35], fill=(59, 36, 24), anchor="mm", font=font_large)
    draw.text((cx, cy + radius + 80), f"· {category_name} ·", fill=(201, 162, 122), anchor="mm", font=font_small)
    draw.text((cx, height - 45), "DACA PASTELERÍA ARTESANAL · LA FLORIDA", fill=(143, 107, 69), anchor="mm", font=font_small)

    img.save(output_path, "JPEG", quality=85)


class Command(BaseCommand):
    help = "Carga datos de demostración completos y realistas para Daca Pastelería"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos demo para Daca Pastelería..."))

        # 1. Superuser & Demo User
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser('admin', 'admin@dacapasteleria.cl', 'admin123')
            admin_user.first_name = "Administrador"
            admin_user.last_name = "Daca"
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Superusuario creado: admin / admin123"))

        demo_customer, created = User.objects.get_or_create(
            username='cliente_demo',
            defaults={
                'email': 'cliente@ejemplo.cl',
                'first_name': 'Camila',
                'last_name': 'Silva',
            }
        )
        if created:
            demo_customer.set_password('cliente123')
            demo_customer.save()
            profile, _ = UserProfile.objects.get_or_create(user=demo_customer)
            profile.phone = "+56 9 8765 4321"
            profile.default_address_street = "Av. Vicuña Mackenna 7500"
            profile.default_address_details = "Depto 402"
            profile.default_commune = "La Florida"
            profile.save()
            self.stdout.write(self.style.SUCCESS("Cliente demo creado: cliente_demo / cliente123"))

        # 2. Site Settings
        settings_obj, _ = SiteSettings.objects.get_or_create(id=1)
        settings_obj.store_name = "Daca Pastelería"
        settings_obj.slogan = "Pastelería Artesanal en La Florida"
        settings_obj.address = "Rojas Magallanes 055, La Florida, Santiago"
        settings_obj.whatsapp_phone = "56912345678"
        settings_obj.instagram = "@dacapasteleria"
        settings_obj.email = "contacto@dacapasteleria.cl"
        settings_obj.opening_hours = "Lunes a Domingo: 10:00 a 20:30 hrs"
        settings_obj.special_notice = "¡Horneamos fresco todos los días! Entregas y retiros disponibles hasta las 20:30 hrs"
        settings_obj.shipping_cost = 3990
        settings_obj.min_order_amount = 5000
        settings_obj.anticipation_hours = 24
        settings_obj.save()
        self.stdout.write("Configuración del sitio actualizada.")

        # 3. Banners
        banners_data = [
            {
                'title': 'Pastelería Boutique & Momentos Dulces',
                'subtitle': 'Recetas artesanales preparadas con amor en Rojas Magallanes, La Florida.',
                'badge': 'Horneado Diario',
                'btn': 'Ver Catálogo',
                'btn_url': '/catalogo/',
                'sec_btn': 'Pide tu Torta',
                'sec_url': '/personalizadas/',
                'order': 1,
            },
            {
                'title': 'Diseña tu Torta a tu Medida',
                'subtitle': 'Elige estilo, sabor, colores y dedicatoria. Hacemos realidad la torta de tus sueños.',
                'badge': 'Personalizadas',
                'btn': 'Crear mi Torta',
                'btn_url': '/personalizadas/',
                'sec_btn': 'Ver Galería',
                'sec_url': '/catalogo/',
                'order': 2,
            },
            {
                'title': 'Bento Cakes & Mini Postres',
                'subtitle': 'El detalle perfecto para regalar o compartir. Formatos individuales y cajas surtidas.',
                'badge': 'Tendencia',
                'btn': 'Explorar Mini Cakes',
                'btn_url': '/catalogo/categoria/mini-cakes/',
                'sec_btn': 'Cajas y Regalos',
                'sec_url': '/catalogo/categoria/cajas-y-regalos/',
                'order': 3,
            },
        ]
        media_root = Path(settings.MEDIA_ROOT)
        for b in banners_data:
            banner, _ = Banner.objects.get_or_create(
                title=b['title'],
                defaults={
                    'subtitle': b['subtitle'],
                    'badge': b['badge'],
                    'button_text': b['btn'],
                    'button_url': b['btn_url'],
                    'secondary_button_text': b['sec_btn'],
                    'secondary_button_url': b['sec_url'],
                    'order': b['order'],
                    'is_active': True,
                }
            )
            img_file = f"banners/banner_{b['order']}.jpg"
            create_placeholder_image(media_root / img_file, b['title'], "Daca Banners", width=1400, height=600, bg_color=(251, 246, 239))
            banner.image_desktop = img_file
            banner.save()

        # 4. Testimonials
        testimonials_data = [
            ("Valentina Morales", "La torta Red Velvet de Daca fue el centro de atención en mi cumpleaños. La humedad del bizcocho y el frosting son de otro planeta.", 5, "Cumpleaños 28"),
            ("Matías Carrasco", "Pedí un bento cake con mensaje sorpresa para el aniversario con mi polola y quedó precioso. La atención por WhatsApp un 7.", 5, "Aniversario"),
            ("Francisca Soto", "Los mini postres y la tartaleta de limón son una delicia total. Siempre pasamos al local de Rojas Magallanes.", 5, "Caja 24 mini postres"),
            ("Ignacio Peña", "Puntuales con el despacho y la presentación en caja kraft con cinta y tarjeta le da un toque muy elegante.", 5, "Tiramisú 16 personas"),
        ]
        for name, quote, rating, occasion in testimonials_data:
            Testimonial.objects.get_or_create(
                client_name=name,
                defaults={'quote': quote, 'rating': rating, 'occasion': occasion, 'is_active': True}
            )

        # 5. Cake Styles for Custom Orders
        cake_styles_data = [
            ("Clásica Minimalista", "Diseño pulcro, bordes semi-desnudos o lisos con detalles sutiles de flores o toques dorados.", 24990, "cake_styles/clasica.jpg"),
            ("Bento Cake / Lunchbox", "Mini torta estilo coreano en cajita kraft ecológica, dedicatoria a mano alzada y corazones.", 12990, "cake_styles/bento.jpg"),
            ("Red Velvet con Crema", "Intenso bizcocho rojo aterciopelado con rosetones de queso crema y crumb suave.", 28990, "cake_styles/red_velvet.jpg"),
            ("Drip Cake Festiva", "Elegante goteo de chocolate blanco o ganache oscuro, decorada con macarons, cookies y frutas.", 32990, "cake_styles/drip.jpg"),
            ("Floral & Romántica", "Flores frescas de temporada tratadas para repostería o flores en crema hechas a mano.", 34990, "cake_styles/floral.jpg"),
            ("Infantil & Temática", "Colores vibrantes, modelados temáticos y toppers especiales para los más pequeños.", 31990, "cake_styles/infantil.jpg"),
            ("Boda & Aniversario", "Diseño sofisticado en 2 o más pisos con texturas, pan de oro comestible y flores.", 54990, "cake_styles/boda.jpg"),
            ("Cumpleaños Adulto", "Elegante y moderna con paleta sobria, velas boutique y topper acrílico.", 29990, "cake_styles/cumple.jpg"),
            ("Corporativa con Logo", "Diseño personalizado con disco de azúcar o impresión comestible con la marca de tu empresa.", 36990, "cake_styles/corporativa.jpg"),
        ]
        for idx, (s_name, s_desc, s_price, s_img) in enumerate(cake_styles_data, 1):
            c_style, _ = CakeStyle.objects.get_or_create(
                name=s_name,
                defaults={
                    'slug': slugify(s_name),
                    'description': s_desc,
                    'base_price': s_price,
                    'order': idx,
                    'is_active': True,
                }
            )
            create_placeholder_image(media_root / s_img, s_name, "Estilo de Torta", width=600, height=600)
            c_style.image = s_img
            c_style.save()

        # 6. Categories
        categories_data = [
            ("Tortas", "Nuestra especialidad: bizcochos esponjosos, rellenos generosos y estética boutique.", 1),
            ("Mini Cakes", "Pequeñas obras de arte individuales y lunchbox cakes para regalar amor.", 2),
            ("Mini Postres", "Bocados dulces ideales para celebraciones, cócteles y mesas de té.", 3),
            ("Tartaletas y Postres", "Clásicos de pastelería: tartaletas de limón, flanes y porciones del día.", 4),
            ("Brownies y Cookies", "Galletas artesanales recién horneadas y brownies húmedos con chocolate premium.", 5),
            ("Salado", "Sándwiches en pan ciabatta, croissants hojaldrados y bocados salados.", 6),
            ("Café y Bebidas", "Café de grano seleccionado, lattes helados, milkshakes y smoothies de fruta natural.", 7),
            ("Helados", "Helados artesanales cremosos en cono o vasito para disfrutar a toda hora.", 8),
            ("Cajas y Regalos", "Packs especiales de pastelería en empaque kraft premium para ocasiones especiales.", 9),
        ]
        cats = {}
        for c_name, c_desc, c_order in categories_data:
            c_slug = slugify(c_name)
            cat, _ = Category.objects.get_or_create(
                slug=c_slug,
                defaults={'name': c_name, 'description': c_desc, 'order': c_order, 'is_active': True}
            )
            cat_img = f"categories/{c_slug}.jpg"
            create_placeholder_image(media_root / cat_img, c_name, "Categoría Daca", width=600, height=450)
            cat.image = cat_img
            cat.save()
            cats[c_name] = cat

        # 7. AddOns & Flavors
        addons_data = [
            ("Topper Acrílico 'Feliz Cumpleaños'", "Topper dorado brillante o negro elegante reutilizable", 2990),
            ("Pack 6 Velas Doradas Boutique", "Velas delgadas metalizadas en tonos oro y rose gold", 1990),
            ("Tarjeta Dedicatoria Kraft Caligrafiada", "Tarjeta de cartón kraft escrita con mensaje personalizado a mano", 1490),
            ("Caja de Regalo Premium con Cinta Daca", "Empaque kraft rígido con visor transparente y cinta de tela", 3990),
        ]
        for a_name, a_desc, a_price in addons_data:
            AddOn.objects.get_or_create(name=a_name, defaults={'description': a_desc, 'price': a_price, 'is_active': True})

        flavors_data = [
            ("Red Velvet Tradicional", "sponge", 0),
            ("Chocolate Húmedo Belga", "sponge", 0),
            ("Vainilla Madagascar", "sponge", 0),
            ("Zanahoria y Especias", "sponge", 0),
            ("Frosting de Queso Crema", "filling", 0),
            ("Manjar y Nuez Artesanal", "filling", 1500),
            ("Ganache de Chocolate 60%", "filling", 1500),
            ("Frambuesas Naturales y Crema", "filling", 2000),
            ("Crema Diplomática y Frutillas", "filling", 1500),
            ("Buttercream Suave de Vainilla", "frosting", 0),
            ("Merengue Italiano Horneado", "frosting", 0),
        ]
        for f_name, f_type, f_extra in flavors_data:
            Flavor.objects.get_or_create(name=f_name, defaults={'flavor_type': f_type, 'extra_price': f_extra, 'is_active': True})

        # 8. Coupons
        Coupon.objects.get_or_create(
            code="DACA10",
            defaults={
                'discount_type': 'percentage',
                'discount_value': 10,
                'min_purchase': 15000,
                'valid_from': timezone.now() - timedelta(days=1),
                'valid_until': timezone.now() + timedelta(days=365),
                'is_active': True,
            }
        )
        Coupon.objects.get_or_create(
            code="BIENVENIDA",
            defaults={
                'discount_type': 'fixed',
                'discount_value': 3000,
                'min_purchase': 20000,
                'valid_from': timezone.now() - timedelta(days=1),
                'valid_until': timezone.now() + timedelta(days=365),
                'is_active': True,
            }
        )

        # 9. Realistic Products
        products_data = [
            # Tortas
            {
                'category': 'Tortas',
                'name': 'Torta Red Velvet con Frosting de Queso Crema',
                'short': 'Bizcocho rojo aterciopelado con suave frosting de queso crema Philadelphia.',
                'desc': 'Nuestra torta estrella. Tres capas de bizcocho esponjoso y húmedo saborizado con un toque sutil de cacao, relleno y cubierto con nuestro inconfundible frosting suave de queso crema. Decorada con migas de terciopelo rojo.',
                'price': 22990,
                'is_cake': True,
                'is_featured': True,
                'is_new': False,
                'variants': [
                    ('8 Personas (16 cm)', 8, '16 cm diámetro / 10 cm alto', 22990),
                    ('12 Personas (18 cm)', 12, '18 cm diámetro / 10 cm alto', 28990),
                    ('16 Personas (20 cm)', 16, '20 cm diámetro / 11 cm alto', 34990),
                    ('20 Personas (22 cm)', 20, '22 cm diámetro / 11 cm alto', 39990),
                ]
            },
            {
                'category': 'Tortas',
                'name': 'Torta Tiramisú Clásica',
                'short': 'Bizcochuelo bañado en café espresso, crema de mascarpone y cacao amargo.',
                'desc': 'El auténtico sabor italiano adaptado a nuestro estilo de pastelería artesanal. Galletas soletillas y bizcocho embebidos en café recién tostado, intercalados con suave crema a base de queso mascarpone y una lluvia fina de cacao amargo.',
                'price': 23990,
                'is_cake': True,
                'is_featured': True,
                'is_new': False,
                'variants': [
                    ('8 Personas (16 cm)', 8, '16 cm diámetro / 9 cm alto', 23990),
                    ('12 Personas (18 cm)', 12, '18 cm diámetro / 9 cm alto', 29990),
                    ('16 Personas (20 cm)', 16, '20 cm diámetro / 10 cm alto', 35990),
                    ('20 Personas (22 cm)', 20, '22 cm diámetro / 10 cm alto', 41990),
                ]
            },
            {
                'category': 'Tortas',
                'name': 'Torta Chocolate Intenso',
                'short': 'Capas de húmedo bizcocho de cacao rellenas con ganache sedoso.',
                'desc': 'Para los verdaderos amantes del chocolate. Bizcocho extra húmedo preparado con cacao de origen, relleno de generoso ganache de chocolate semiamargo y cubierto con una capa brillante y rosetones de trufa.',
                'price': 21990,
                'is_cake': True,
                'is_featured': True,
                'is_new': True,
                'variants': [
                    ('8 Personas (16 cm)', 8, '16 cm diámetro / 10 cm alto', 21990),
                    ('12 Personas (18 cm)', 12, '18 cm diámetro / 10 cm alto', 27990),
                    ('16 Personas (20 cm)', 16, '20 cm diámetro / 10 cm alto', 33990),
                    ('20 Personas (22 cm)', 20, '22 cm diámetro / 11 cm alto', 38990),
                ]
            },
            {
                'category': 'Tortas',
                'name': 'Torta de Crema con Nuez Artesanal',
                'short': 'El clásico chileno con manjar de campo, crema fresca batida y nueces tostadas.',
                'desc': 'Tradición y nostalgia en cada bocado. Capas finas de bizcochuelo blanco con abundante manjar artesanal, crema chantilly fresca y trozos crocantes de nueces recién tostadas.',
                'price': 24990,
                'is_cake': True,
                'is_featured': False,
                'is_new': False,
                'variants': [
                    ('8 Personas (16 cm)', 8, '16 cm diámetro / 10 cm alto', 24990),
                    ('12 Personas (18 cm)', 12, '18 cm diámetro / 10 cm alto', 30990),
                    ('16 Personas (20 cm)', 16, '20 cm diámetro / 10 cm alto', 36990),
                    ('20 Personas (22 cm)', 20, '22 cm diámetro / 11 cm alto', 42990),
                ]
            },
            {
                'category': 'Tortas',
                'name': 'Torta San Valentín "Love" (Bento Cake)',
                'short': 'Mini torta corazón con dedicatoria especial en cajita biodegradable kraft.',
                'desc': 'La sensación para expresar todo tu cariño. Formato Bento cake con forma de corazón, bizcocho a elección (red velvet o chocolate) cubierto con buttercream rosado pastel y la palabra "Love" escrita a mano alzada.',
                'price': 13990,
                'is_cake': True,
                'is_featured': True,
                'is_new': True,
                'variants': [
                    ('2 a 4 Personas (Formato Bento)', 3, '12 cm diámetro / 8 cm alto', 13990),
                    ('8 Personas (Formato Mediano)', 8, '16 cm diámetro / 9 cm alto', 22990),
                ]
            },
            # Mini Cakes
            {
                'category': 'Mini Cakes',
                'name': 'Mini Cake Red Velvet Redonda',
                'short': 'Porción individual perfecta de nuestra famosa receta Red Velvet.',
                'desc': 'El mismo sabor irresistible de nuestra torta grande en formato individual de 10 cm. Ideal para celebrar logros personales, regalar a alguien especial o disfrutar con un buen café.',
                'price': 5990,
                'is_cake': False,
                'is_featured': True,
                'is_new': False,
                'variants': []
            },
            # Mini Postres
            {
                'category': 'Mini Postres',
                'name': 'Cajita 24 Mini Postres Surtidos',
                'short': '12 bocados Red Velvet con queso crema y 12 tartaletas de chocolate con ganache.',
                'desc': 'La caja perfecta para tus reuniones y mesas dulces. Presentación en caja kraft con ventana transparente. Incluye 12 mini cupcakes Red Velvet y 12 mini tartaletas de ganache de chocolate belga.',
                'price': 18990,
                'is_cake': False,
                'is_featured': True,
                'is_new': True,
                'variants': [
                    ('Caja 12 unidades', 12, '12 bocados surtidos', 10990),
                    ('Caja 24 unidades', 24, '24 bocados surtidos', 18990),
                    ('Caja 48 unidades', 48, '48 bocados surtidos', 34990),
                ]
            },
            # Tartaletas y Postres
            {
                'category': 'Tartaletas y Postres',
                'name': 'Tartaleta de Limón con Merengue Suizo',
                'short': 'Masa sableé crocante, crema de limón ácido perfecta y merengue suizo dorado.',
                'desc': 'El equilibrio perfecto entre dulzura y acidez cítrica. Base de masa quebrada crujiente rellena con cuajada de limón sutilmente ácida y coronada con generosas ondas de merengue suizo flameado.',
                'price': 15990,
                'is_cake': False,
                'is_featured': True,
                'is_new': False,
                'variants': [
                    ('Individual (1 porción)', 1, '10 cm diámetro', 3490),
                    ('Familiar (6 a 8 porciones)', 8, '22 cm diámetro', 15990),
                ]
            },
            {
                'category': 'Tartaletas y Postres',
                'name': 'Flan de Caramelo Artesanal',
                'short': 'Textura ultrasuave con leche condensada, vaina de vainilla y caramelo líquido.',
                'desc': 'Receta clásica de abuela horneada a baño maría lentamente. Con textura densa y cremosa que se deshace en el paladar, bañado en caramelo dorado intenso.',
                'price': 11990,
                'is_cake': False,
                'is_featured': False,
                'is_new': False,
                'variants': [
                    ('Porción Individual', 1, 'Vaso postre 180ml', 2990),
                    ('Familiar (6 porciones)', 6, 'Molde redondo 20 cm', 11990),
                ]
            },
            {
                'category': 'Tartaletas y Postres',
                'name': 'Rebanada de Torta del Día',
                'short': 'Trozo generoso de la torta horneada en la mañana en nuestro taller.',
                'desc': 'Pregunta por la variedad del día (Red Velvet, Chocolate o Manjar Nuez). Cortada fresca en el momento para acompañar tu pausa dulce.',
                'price': 4290,
                'is_cake': False,
                'is_featured': False,
                'is_new': False,
                'variants': []
            },
            # Brownies y Cookies
            {
                'category': 'Brownies y Cookies',
                'name': 'Brownie Meloso con Nueces Tostadas',
                'short': 'Centro húmedo tipo fudge con chocolate 60% y trozos crujientes de nuez.',
                'desc': 'Nuestra receta secreta de brownie: corteza craquelada brillante, centro denso y chocolateado con nueces seleccionadas. Pruébalo tibio.',
                'price': 2490,
                'is_cake': False,
                'is_featured': True,
                'is_new': False,
                'variants': [
                    ('Unidad Individual', 1, 'Cuadrado 8x8 cm', 2490),
                    ('Pack 4 Brownies', 4, 'Caja kraft de 4 unidades', 8990),
                ]
            },
            {
                'category': 'Brownies y Cookies',
                'name': 'Cookie New York con Chips de Chocolate Belga',
                'short': 'Galleta gruesa estilo NYC, centro suave y borde dorado crocante.',
                'desc': 'Inspirada en las famosas pastelerías de Manhattan. 130 gramos de galleta con abundante chocolate de leche y semi amargo. Horneadas en tandas cortas durante todo el día.',
                'price': 2290,
                'is_cake': False,
                'is_featured': True,
                'is_new': True,
                'variants': [
                    ('Unidad 130g', 1, '1 galleta gigante', 2290),
                    ('Caja 6 Cookies Surtidas', 6, 'Caja de 6 unidades', 11990),
                ]
            },
            # Salado
            {
                'category': 'Salado',
                'name': 'Sándwich Ciabatta Mechada y Queso Mantecoso',
                'short': 'Pan ciabatta de masa madre, carne mechada jugosa y queso fundido.',
                'desc': 'Carne de vacuno desmechada cocinada a fuego lento por 6 horas con hierbas aromáticas, montada en crujiente pan ciabatta artesanal y abundante queso mantecoso de la zona central.',
                'price': 6990,
                'is_cake': False,
                'is_featured': False,
                'is_new': False,
                'variants': []
            },
            {
                'category': 'Salado',
                'name': 'Croissant Relleno Jamón Pierna y Queso',
                'short': 'Masa hojaldrada 100% mantequilla rellena con jamón artesanal y queso.',
                'desc': 'Hojaldre ligero y crocante con capas doradas perfectas, prensado tibio con jamón de pierna seleccionado y queso fundente.',
                'price': 4990,
                'is_cake': False,
                'is_featured': False,
                'is_new': False,
                'variants': []
            },
            # Café y Bebidas
            {
                'category': 'Café y Bebidas',
                'name': 'Frappé de Café Moka Daca',
                'short': 'Café espresso doble licuado con hielo, leche, salsa de chocolate y crema chantilly.',
                'desc': 'La bebida más refrescante de nuestra cafetería. Café de especialidad batido con hielo frappé, salsa de chocolate artesanal y corona de crema montada.',
                'price': 4490,
                'is_cake': False,
                'is_featured': False,
                'is_new': False,
                'variants': []
            },
            {
                'category': 'Café y Bebidas',
                'name': 'Latte Caliente de Especialidad',
                'short': 'Espresso doble con leche texturizada sedosa y arte latte.',
                'desc': 'Preparado con granos 100% arábica de tueste medio. Suave, cremoso y con el dulzor natural de la leche bien vaporizada.',
                'price': 3190,
                'is_cake': False,
                'is_featured': False,
                'is_new': False,
                'variants': []
            },
            {
                'category': 'Café y Bebidas',
                'name': 'Latte Helado con Jarabe de Vainilla',
                'short': 'Café espresso servido sobre hielo, leche fresca y toque de vainilla.',
                'desc': 'Ideal para las tardes calurosas de Santiago. Refrescante, balanceado y energizante.',
                'price': 3690,
                'is_cake': False,
                'is_featured': False,
                'is_new': False,
                'variants': []
            },
            {
                'category': 'Café y Bebidas',
                'name': 'Milkshake de Oreo & Crema',
                'short': 'Helado artesanal de vainilla batido con galletas Oreo trituradas y crema.',
                'desc': 'Batido denso y cremoso con tropezones crocantes de galleta Oreo, terminado con crema chantilly y salsa de chocolate.',
                'price': 4890,
                'is_cake': False,
                'is_featured': True,
                'is_new': False,
                'variants': []
            },
            {
                'category': 'Café y Bebidas',
                'name': 'Milkshake de Frutilla Natural',
                'short': 'Helado de frutilla con pulpa natural y leche entera.',
                'desc': 'Puro sabor a fruta fresca de temporada combinado con la cremosidad de nuestro helado.',
                'price': 4890,
                'is_cake': False,
                'is_featured': False,
                'is_new': False,
                'variants': []
            },
            {
                'category': 'Café y Bebidas',
                'name': 'Smoothie Frutos del Bosque',
                'short': 'Frutillas, arándanos y moras licuados con jugo natural y hielo.',
                'desc': 'Opción 100% frutal, refrescante y sin lácteos. Rico en antioxidantes y sabor natural.',
                'price': 4190,
                'is_cake': False,
                'is_featured': False,
                'is_new': True,
                'variants': []
            },
            # Helados
            {
                'category': 'Helados',
                'name': 'Helado Artesanal en Cono o Vaso',
                'short': 'Sabores de la casa: Manjar con nuez, Chocolate belga, Frutilla a la crema o Maracuyá.',
                'desc': 'Elaborados en pequeños lotes con ingredientes nobles. Elige entre barquillo crocante azucarado o vasito térmico.',
                'price': 2990,
                'is_cake': False,
                'is_featured': False,
                'is_new': False,
                'variants': [
                    ('1 Sabor (Cono o Vaso)', 1, '1 bola generosa', 2990),
                    ('2 Sabores (Cono o Vaso)', 2, '2 bolas surtidas', 4490),
                    ('Pote 1 Litro para Llevar', 4, 'Pote térmico 1000cc', 9990),
                ]
            },
        ]

        for p_data in products_data:
            cat = cats[p_data['category']]
            p_slug = slugify(p_data['name'])
            product, p_created = Product.objects.get_or_create(
                slug=p_slug,
                defaults={
                    'category': cat,
                    'name': p_data['name'],
                    'short_description': p_data['short'],
                    'description': p_data['desc'],
                    'base_price': p_data['price'],
                    'is_cake': p_data['is_cake'],
                    'is_featured': p_data['is_featured'],
                    'is_new': p_data['is_new'],
                    'is_active': True,
                    'preparation_time': '24 a 48 horas' if p_data['is_cake'] else 'Inmediato / En stock',
                    'allergens': 'Contiene gluten, lácteos y huevo. Elaborado en líneas con frutos secos.',
                    'storage_instructions': 'Refrigerar entre 2°C y 5°C. Consumir dentro de 4 días.',
                }
            )

            # Create 3 images per product (Main, Hover, Detail)
            if not product.images.exists():
                for img_idx, img_type in enumerate(['principal', 'detalle', 'corte'], 1):
                    img_filename = f"products/{p_slug}_{img_type}.jpg"
                    create_placeholder_image(
                        media_root / img_filename,
                        f"{p_data['name']} ({img_type.capitalize()})",
                        cat.name,
                        width=800,
                        height=800,
                        bg_color=(251, 246, 239) if img_idx == 1 else (244, 214, 208) if img_idx == 2 else (238, 218, 194)
                    )
                    ProductImage.objects.create(
                        product=product,
                        image=img_filename,
                        alt_text=f"{product.name} - Vista {img_type}",
                        order=img_idx,
                        is_main=(img_idx == 1)
                    )

            # Create variants
            for v_idx, v_tuple in enumerate(p_data['variants'], 1):
                v_name, v_portions, v_dims, v_price = v_tuple
                ProductVariant.objects.get_or_create(
                    product=product,
                    name=v_name,
                    defaults={
                        'portions': v_portions,
                        'dimensions': v_dims,
                        'price': v_price,
                        'is_active': True,
                        'order': v_idx,
                    }
                )

        # 10. Sample Orders for Dashboard Metrics & Deliveries
        today = timezone.localdate()
        sample_orders_data = [
            ("DACA-ORD1001", "María José Valenzuela", "mjose@ejemplo.cl", "+56 9 9123 4567", "pickup", today, "15:00 a 17:00 hrs", 34990, "in_preparation", "paid", "Dedicatoria: ¡Feliz Día Mamá!"),
            ("DACA-ORD1002", "Rodrigo Cifuentes", "rcifuentes@ejemplo.cl", "+56 9 8234 5678", "delivery", today, "17:00 a 19:00 hrs", 28990, "ready", "paid", "Depto 502, llamar al citófono"),
            ("DACA-ORD1003", "Constanza Morales", "cmorales@ejemplo.cl", "+56 9 7345 6789", "pickup", today + timedelta(days=1), "12:00 a 14:00 hrs", 41990, "confirmed", "paid", "Velas doradas por favor"),
            ("DACA-ORD1004", "Felipe Navarrete", "felipe@ejemplo.cl", "+56 9 6456 7890", "delivery", today + timedelta(days=1), "16:00 a 18:00 hrs", 22990, "pending", "pending", "Pagaré contra entrega"),
            ("DACA-ORD1005", "Daniela Gómez", "daniela@ejemplo.cl", "+56 9 5567 8901", "pickup", today - timedelta(days=1), "14:00 a 16:00 hrs", 18990, "delivered", "paid", "Caja 24 mini postres"),
        ]

        torta_rv = Product.objects.filter(slug='torta-red-velvet-con-frosting-de-queso-crema').first()
        tiramisu = Product.objects.filter(slug='torta-tiramisu-clasica').first()

        for o_num, c_name, c_mail, c_phone, del_type, del_date, del_slot, o_total, o_status, o_pay, o_notes in sample_orders_data:
            order, o_created = Order.objects.get_or_create(
                order_number=o_num,
                defaults={
                    'user': demo_customer if c_mail == 'cliente@ejemplo.cl' else None,
                    'full_name': c_name,
                    'email': c_mail,
                    'phone': c_phone,
                    'delivery_type': del_type,
                    'address_street': 'Walker Martínez 1200' if del_type == 'delivery' else '',
                    'commune': 'La Florida',
                    'delivery_date': del_date,
                    'delivery_time_slot': del_slot,
                    'subtotal': o_total,
                    'shipping_cost': 3990 if del_type == 'delivery' else 0,
                    'discount': 0,
                    'total': o_total + (3990 if del_type == 'delivery' else 0),
                    'status': o_status,
                    'payment_method': 'transfer',
                    'payment_status': o_pay,
                    'customer_notes': o_notes,
                }
            )
            if o_created and torta_rv:
                OrderItem.objects.create(
                    order=order,
                    product=torta_rv,
                    product_name=torta_rv.name,
                    variant_name="12 Personas",
                    unit_price=o_total,
                    quantity=1,
                    subtotal=o_total,
                    notes=o_notes
                )

        # 11. Sample Custom Cake Orders for Quotes
        bento_style = CakeStyle.objects.filter(name__icontains="Bento").first() or CakeStyle.objects.first()
        clasica_style = CakeStyle.objects.filter(name__icontains="Clásica").first() or CakeStyle.objects.first()

        CustomCakeOrder.objects.get_or_create(
            order_number="CUSTOM-DEMO01",
            defaults={
                'user': demo_customer,
                'cake_style': bento_style,
                'portions': 4,
                'sponge_flavor': 'Red Velvet',
                'filling_flavor': 'Frosting de queso crema y frambuesa',
                'frosting_type': 'Buttercream suave',
                'color_palette': 'Rosado blush y blanco marfil',
                'message_on_cake': 'Happy 25th Birthday!',
                'desired_date': today + timedelta(days=3),
                'estimated_budget': 16000,
                'customer_name': 'Camila Silva',
                'customer_email': 'cliente@ejemplo.cl',
                'customer_phone': '+56 9 8765 4321',
                'customer_notes': 'Quisiera corazoncitos rojos pequeños alrededor de la dedicatoria.',
                'status': 'received',
            }
        )

        CustomCakeOrder.objects.get_or_create(
            order_number="CUSTOM-DEMO02",
            defaults={
                'user': None,
                'cake_style': clasica_style,
                'portions': 20,
                'sponge_flavor': 'Chocolate Belga',
                'filling_flavor': 'Manjar artesanal y nuez',
                'frosting_type': 'Merengue Italiano',
                'color_palette': 'Blanco con toques dorados pan de oro',
                'message_on_cake': '50 Años Inolvidables',
                'desired_date': today + timedelta(days=5),
                'estimated_budget': 45000,
                'customer_name': 'Álvaro Henríquez',
                'customer_email': 'alvaro@ejemplo.cl',
                'customer_phone': '+56 9 7788 9900',
                'customer_notes': 'Es para las bodas de oro de mis padres.',
                'status': 'quoted',
                'final_price': 42990,
                'deposit_required': 20000,
                'bakery_response': '¡Hola Álvaro! Preciosa ocasión. Podemos hacerla en 2 niveles semi-desnudos con detalles dorados en pan de oro comestible.',
            }
        )

        self.stdout.write(self.style.SUCCESS("¡Seed completado exitosamente! Todos los datos demo, categorías, productos, imágenes placeholder y pedidos han sido cargados."))
