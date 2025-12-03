"""
WSGI config for VercelApp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Añade el directorio del proyecto al path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VercelApp.settings')

application = get_wsgi_application()
