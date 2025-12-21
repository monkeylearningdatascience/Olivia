"""
Auto-register all app models with Django admin for quick visibility.
This registers any model not already registered using a simple ModelAdmin.
"""
from django.apps import apps
from django.contrib import admin
from django.db import models as django_models


def _make_admin_for_model(model):
    # Build a simple ModelAdmin with list_display and search_fields
    field_names = [f.name for f in model._meta.fields]
    # Limit list_display to first 10 fields to avoid very wide tables
    list_display = field_names[:10]
    # Use CharField/TextField for search
    search_fields = [f.name for f in model._meta.fields if isinstance(f, (django_models.CharField, django_models.TextField))][:5]

    attrs = {
        'list_display': list_display,
        'search_fields': search_fields,
    }
    return type(f"{model.__name__}AutoAdmin", (admin.ModelAdmin,), attrs)


def register_all_models():
    """Register all models that are not already registered in admin."""
    # Skip built-in Django apps to avoid URL reversal issues
    skip_apps = {'admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles'}
    
    for model in apps.get_models():
        app_label = getattr(model._meta, 'app_label', None)
        # Skip models from built-in Django apps — registering those can cause
        # the admin URL resolver to be built without those app labels,
        # leading to NoReverseMatch when templates try to reverse
        # 'admin:app_list' for an app_label not in the registered set.
        if app_label in skip_apps:
            continue
        try:
            # Skip proxy models
            if model._meta.proxy:
                continue
        except Exception:
            pass

        try:
            admin.site.register(model, _make_admin_for_model(model))
        except admin.sites.AlreadyRegistered:
            # Already registered elsewhere (often in app admin.py)
            continue
        except Exception:
            # Ignore models that cannot be registered for any reason
            continue


# Run registration immediately on import (safe when Django is configured)
try:
    register_all_models()
except Exception:
    # If Django isn't ready yet (e.g. during manage.py startup before setup), ignore.
    pass
