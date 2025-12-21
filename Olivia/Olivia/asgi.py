"""
ASGI config for Olivia project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Olivia.settings')

application = get_asgi_application()

# Ensure admin auto-registration runs when the ASGI app starts
try:
	import admin_autoregister  # noqa: F401
except Exception:
	pass
