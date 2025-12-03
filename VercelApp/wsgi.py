# VercelApp/wsgi.py - VERSIÓN QUE SÍ FUNCIONA EN VERCEL
import os
import sys

# Añadir el directorio del proyecto al path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VercelApp.settings')

from django.core.wsgi import get_wsgi_application

# Crear la aplicación WSGI
django_application = get_wsgi_application()

# ⭐⭐ SOLUCIÓN: Exportar como MÓDULO, no como instancia ⭐⭐
# Vercel necesita acceder a 'application' como atributo del módulo
application = django_application

# OPCIÓN ALTERNATIVA: Exportar la función get_wsgi_application
# para que Vercel pueda llamarla y obtener la instancia
def app(event, context):
    """Handler para Vercel Serverless Functions"""
    return django_application(event, context)