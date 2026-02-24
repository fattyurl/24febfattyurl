"""
ASGI config for fattyurl project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# WhiteNoise is configured via middleware in fattyurl/settings.py.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fattyurl.settings')

application = get_asgi_application()
