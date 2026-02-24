"""
WSGI config for fattyurl project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fattyurl.settings')

application = get_wsgi_application()
application = WhiteNoise(application, root=str(settings.STATIC_ROOT), autorefresh=settings.DEBUG)
