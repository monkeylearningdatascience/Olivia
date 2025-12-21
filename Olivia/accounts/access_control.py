"""
Access Control Utilities
Provides decorators and helpers for checking user permissions.
"""
from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from .models import Permission


def permission_required(app, feature, action='view'):
    """
    Decorator to check if user has permission for a specific action.
    Usage: @permission_required('humanresource', 'staff', 'view')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(reverse('login'))
            
            # Superusers bypass permission checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            try:
                profile = request.user.profile
                if not profile.has_permission(app, feature, action):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': 'Permission denied'}, status=403)
                    return HttpResponseForbidden('You do not have permission to access this resource.')
            except:
                return HttpResponseForbidden('User profile not found.')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def app_access_required(app_name):
    """
    Decorator to check if user has access to an app.
    Usage: @app_access_required('humanresource')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(reverse('login'))
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            try:
                profile = request.user.profile
                if not profile.has_app_access(app_name):
                    return HttpResponseForbidden('You do not have access to this application.')
            except:
                return HttpResponseForbidden('User profile not found.')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def check_permission(user, app, feature, action='view'):
    """
    Function to check permission (useful in templates or views).
    Returns: True if user has permission, False otherwise.
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        return user.profile.has_permission(app, feature, action)
    except:
        return False


def get_user_permissions(user):
    """Get all permissions for a user."""
    if not user.is_authenticated:
        return Permission.objects.none()
    
    if user.is_superuser:
        return Permission.objects.all()
    
    try:
        return user.profile.get_all_permissions()
    except:
        return Permission.objects.none()
