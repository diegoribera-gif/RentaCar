"""
WSGI config for VercelApp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""


import os
import sys

# AÑADIR ESTO - MUY IMPORTANTE
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VercelApp.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()