# 🍰 Daca Pastelería Artesanal · Sitio Web & Tienda Online

Sitio web oficial y plataforma de pedidos para **Daca Pastelería** (Rojas Magallanes 055, La Florida, Santiago, Chile; Instagram: [@dacapasteleria](https://instagram.com/dacapasteleria)).

Construido con **Django 6**, **Tailwind CSS v3**, **Alpine.js**, **HTMX**, **GSAP + ScrollTrigger**, **Swiper.js** y **Chart.js**.

---

## 🎨 Identidad Visual & Diseño
- **Estética**: Pastelería boutique cálida y artesanal inspirada en el local físico (cajas kraft, mimbre, madera clara y detalles botánicos).
- **Paleta de Colores**:
  - `cream` (`#FBF6EF`): Fondo principal cálido.
  - `kraft` (`#C9A27A`): Acento artesanal y botones secundarios.
  - `cocoa` (`#3B2418`): Tipografía de alto contraste y fondos de acento.
  - `heart` (`#D7263D`): Rojo corazón emblemático del logo Daca para CTAs y estados clave.
  - `blush` (`#F4D6D0`): Rosado suave pastel para destacados y fondos tenues.
  - `gold` (`#D8B45A`): Detalles festivos, etiquetas y badges de excelencia.
- **Tipografías**: *Cormorant Garamond* / *Playfair Display* (títulos serif de alta repostería), *DM Sans* (interfaz y lectura ágil), *Dancing Script* (caligrafía artesanal).
- **Localización Chilena**: Moneda **CLP** con formato formal `$12.990` (sin decimales, separador de miles por punto) y zona horaria `America/Santiago`.

---

## 🚀 Requisitos del Sistema
- **Python**: 3.12, 3.13 o 3.14 (entorno virtual `env` ya configurado en la raíz).
- **Node.js**: v18+ y `npm` (para compilar Tailwind CSS).

---

## 🛠️ Instalación y Puesta en Marcha

### 1. Activar el Entorno Virtual
En Windows (PowerShell):
```powershell
.\env\Scripts\Activate.ps1
```
En Bash / macOS / Linux:
```bash
source env/bin/activate
```

### 2. Instalar Dependencias de Python
```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
Copia el archivo de ejemplo `.env.example` a `.env`:
```bash
copy .env.example .env
```

Variables principales en `.env`:
```ini
SECRET_KEY=clave_secreta_django
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
WHATSAPP_PHONE=56912345678
INSTAGRAM_USER=@dacapasteleria
STORE_ADDRESS=Rojas Magallanes 055, La Florida, Santiago, Chile
```

### 4. Compilar Tailwind CSS
Instala los paquetes npm (Tailwind CSS, plugins de formularios y tipografía):
```bash
npm install
```
Para compilar los estilos de producción:
```bash
npm run build:css
```
Para desarrollo activo con auto-recarga al editar templates:
```bash
npm run watch:css
```

### 5. Aplicar Migraciones de la Base de Datos
```bash
python manage.py migrate
```

### 6. Cargar Datos de Demostración (Seed)
Ejecuta el comando personalizado de carga:
```bash
python manage.py seed_demo
```
Este comando cargará automáticamente:
- **Superusuario Administrador**:
  - Usuario: `admin`
  - Contraseña: `admin123`
- **Cliente Demo**:
  - Usuario: `cliente_demo`
  - Contraseña: `cliente123`
- Categorías reales (Tortas, Mini Cakes, Mini Postres, Tartaletas, Brownies y Cookies, Salado, Café y Bebidas, Helados, Cajas y Regalos).
- Catálogo de productos con variantes por porciones (8, 12, 16, 20 personas) y precios en CLP.
- Estilos de tortas personalizadas (Bento cake, Red Velvet, Clásica, Drip cake, Floral, etc.).
- Imágenes placeholder de alta resolución generadas con Pillow y paleta de la marca en `media/`.
- Banners promocionales administrables.
- Pedidos de ejemplo y cotizaciones para visualización inmediata en el Dashboard.

### 7. Ejecutar el Servidor de Desarrollo
```bash
python manage.py runserver
```
Abre en tu navegador:
- **Tienda Pública**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Panel de Control Staff**: [http://127.0.0.1:8000/panel/](http://127.0.0.1:8000/panel/)
- **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 📁 Estructura del Proyecto

```
daca/
├── accounts/          # Perfiles de usuario, direcciones guardadas y autenticación
├── cart/              # Carrito en sesión, persistencia en BD y Drawer HTMX
├── catalog/           # Categorías, productos, variantes por porciones y fotos
├── core/              # Home animada, páginas estáticas, banners y settings globales
├── custom_orders/     # Asistente wizard paso a paso de tortas personalizadas
├── dashboard/         # Panel administrativo propio con KPIs y gráficos Chart.js
├── orders/            # Pedidos, checkout, cupones, comprobantes y WhatsApp
├── pasteleria_daca/   # Configuración de Django (settings, urls, wsgi/asgi)
├── static/
│   ├── css/
│   │   ├── input.css  # Directivas de Tailwind y estilos boutique
│   │   └── output.css # CSS compilado y minificado
├── templates/         # Templates HTML organizados con base.html y parciales
├── media/             # Archivos multimedia subidos (banners, productos, estilos)
├── manage.py
├── package.json       # Scripts de compilación de Tailwind CSS
├── tailwind.config.js # Configuración del tema y paleta Daca
└── requirements.txt
```

---

## 🖼️ Reemplazo de Imágenes Placeholder por Fotos Reales

Las fotos generadas por `seed_demo` se guardan en la carpeta `media/`:
1. **Productos**: `media/products/`
2. **Estilos de tortas personalizadas**: `media/cake_styles/`
3. **Banners principales**: `media/banners/`
4. **Categorías**: `media/categories/`

Para subir tus fotos reales:
- Puedes reemplazarlas directamente desde el **Panel de Administración propio** en `/panel/productos/` o mediante el **Django Admin** en `/admin/`.
- O bien reemplazar los archivos en la carpeta `media/` conservando los nombres de archivo.

---

## 💳 Integración Webpay Plus (Transbank)

> **Estado:** estructura base lista (modelo, servicio, vistas, URLs, templates y tests con mocks). La conexión real con Transbank **no está verificada** y queda pendiente de completar manualmente. Ver checklist `TODO` en `orders/services/webpay_service.py`.

La plataforma integra **Webpay Plus** utilizando el **SDK oficial de Python de Transbank (`transbank-sdk`)**.

### Variables de Entorno (`.env`)
El cambio de ambiente se controla exclusivamente mediante variables de entorno:

```ini
# Para ambiente de pruebas (Integración):
TBK_ENVIRONMENT=integration
TBK_COMMERCE_CODE=597055555532
TBK_API_KEY=579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C

# Para ambiente de producción (debes ingresar tus credenciales provistas por Transbank):
# TBK_ENVIRONMENT=production
# TBK_COMMERCE_CODE=tu_codigo_de_comercio_real
# TBK_API_KEY=tu_api_key_secreta_real
```

### Tarjetas Oficiales de Prueba de Transbank (Ambiente Integración)

| Tipo de Tarjeta | Número de Tarjeta (PAN) | Vencimiento | CVV | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **Crédito VISA** | `4051 8856 0044 6623` | Fecha futura (ej: `12/28`) | `123` | **Aprobada** (`AUTHORIZED`, resp `0`) |
| **Crédito AMEX** | `3700 0000 0002 032` | Fecha futura (ej: `12/28`) | `1234` | **Aprobada** (`AUTHORIZED`, resp `0`) |
| **Prepago VISA** | `4051 8860 0005 6590` | Fecha futura (ej: `12/28`) | `123` | **Aprobada** (`AUTHORIZED`, resp `0`) |
| **Débito Redcompra** | `4051 8842 3993 7763` | Fecha futura (ej: `12/28`) | `123` | **Aprobada** (`AUTHORIZED`, resp `0`) |
| **Crédito Mastercard** | `5186 0595 5959 0568` | Fecha futura (ej: `12/28`) | `123` | **Rechazada** (`FAILED`, resp `-1`) |
| **Débito Rechazada** | `5186 0085 4123 3829` | Fecha futura (ej: `12/28`) | `123` | **Rechazada** (`FAILED`, resp `-1`) |

#### Autenticación en la pantalla de simulación del Banco:
- **RUT:** `11.111.111-1`
- **Clave:** `123`

### Flujo y Casos Manejados
1. **Creación:** En el checkout, al seleccionar Webpay se crea el pedido en estado `pending`, con monto estrictamente calculado en el servidor (enteros CLP), `buy_order` único y se genera la transacción con Transbank.
2. **Retorno Exitoso:** Al retornar `token_ws` se hace `commit()`. Si es `AUTHORIZED` y `response_code == 0`, se marca el pedido como pagado, se vacía el carrito, se envía el correo de confirmación y se muestra el comprobante normativo con todos los datos exigidos por Transbank.
3. **Anulación por Usuario:** Si el cliente presiona "Anular y volver al comercio" en Webpay, se captura `TBK_TOKEN`, se marca como cancelado, **se preserva el carrito** y se permite reintentar o cambiar a transferencia sin perder el pedido.
4. **Timeout:** Si la sesión expira en Webpay, se captura `TBK_ORDEN_COMPRA` sin token, se registra el estado y **se preserva el carrito**.
5. **Idempotencia / Doble Retorno:** Si el cliente refresca la pantalla de retorno cuando el pedido ya está pagado, no se vuelve a hacer commit a Transbank y se redirige limpiamente al comprobante.
6. **Reembolso / Anulación desde el Dashboard:** Los usuarios staff pueden reversar transacciones autorizadas directamente desde `/panel/pedidos/<id>/`.

---

## 🧪 Ejecución de Tests Automatizados
El proyecto cuenta con 24 pruebas automatizadas con mocks para Transbank, adición reactiva de carrito, addons, porciones y persistencia:

```bash
python manage.py test
```

