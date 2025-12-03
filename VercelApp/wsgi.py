# VercelApp/wsgi.py - VERSIÓN QUE SÍ FUNCIONA
import os
import sys

# Añadir el directorio del proyecto al path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VercelApp.settings')

from django.core.wsgi import get_wsgi_application

# ⭐⭐ ESTAS TRES LÍNEAS SON CRÍTICAS ⭐⭐
application = get_wsgi_application()
app = application
handler = application  # Algunas versiones de Vercel usan 'handler'