"""
ASGI config for VercelApp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import sys
from django.core.asgi import get_asgi_application

# Añade el directorio del proyecto al path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VercelApp.settings')

application = get_asgi_application()
