#!/usr/bin/env bash
# Script de construcción para host gratuito (ej: Render)
set -o errexit

# Instalar dependencias Python
pip install -r requirements.txt

# Recolectar archivos estáticos para WhiteNoise
python manage.py collectstatic --no-input

# Ejecutar migraciones de base de datos
python manage.py migrate

# Cargar catálogo y datos iniciales de demostración
python manage.py seed_demo
