# VercelApp/wsgi.py - VERSIÓN MÍNIMA FUNCIONAL
import os
import sys
from django.core.wsgi import get_wsgi_application

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VercelApp.settings')

# SOLO exportar la función, no la instancia
application = get_wsgi_application