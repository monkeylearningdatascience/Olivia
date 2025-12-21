"""
WSGI config for Olivia project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Olivia.settings')
application = get_wsgi_application()
# Ensure admin auto-registration runs when the WSGI app starts
try:
	# Import local module that registers models with admin
	import admin_autoregister  # noqa: F401
except Exception:
	# If import fails (Django not fully configured) we ignore silently
	pass

