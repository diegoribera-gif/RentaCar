import os
import sys

# Añadir el directorio del proyecto al path
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VercelApp.settings')

from django.core.wsgi import get_wsgi_application

# ⚠️ IMPORTANTE: Vercel necesita 'app' o 'handler'
application = get_wsgi_application()
app = application  # ← AÑADE ESTA LÍNEA