# accounts/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class AppAccessRestrictionMiddleware(MiddlewareMixin):
    """
    Restrict access to apps based on user's allowed apps.
    Superusers bypass all restrictions.
    """
    # List of all apps in your project
    ALLOWED_APPS = [
        "humanresource", "housing", "hardservice", "softservice", "utility",
        "fls", "logistics", "procurement", "warehouse", "qhse",
        "ict", "ticket", "training"
    ]

    def process_request(self, request):
        user = request.user

        # Skip if not authenticated
        if not user.is_authenticated:
            return None

        # Superusers bypass all restrictions
        if user.is_superuser:
            return None

        profile = getattr(user, "profile", None)
        allowed_apps = profile.allowed_apps.values_list("code", flat=True) if profile else []

        # Extract the app label from the URL
        path_parts = request.path.strip("/").split("/")
        if not path_parts:
            return None

        app_name = path_parts[0]

        # Only enforce restriction for known apps
        if app_name in self.ALLOWED_APPS and app_name not in allowed_apps:
            # Redirect to a safe page (e.g., dashboard or home)
            return redirect(reverse("home"))

        return None
