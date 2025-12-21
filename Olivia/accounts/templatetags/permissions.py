"""
Permission template tags.
Usage in templates:
  {% load permissions %}
  {% if user|has_permission:"humanresource.staff.view" %}...{% endif %}
  {% if user|has_permission:"humanresource.staff.create" %}...{% endif %}
"""
from django import template
from accounts.models import Permission

register = template.Library()


@register.filter
def has_permission(user, perm_string):
    """
    Check if user has permission.
    Format: "app.feature.action"
    Example: "humanresource.staff.view"
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        parts = perm_string.split('.')
        if len(parts) != 3:
            return False
        
        app, feature, action = parts
        return user.profile.has_permission(app, feature, action)
    except:
        return False


@register.filter
def has_app_access(user, app_name):
    """
    Check if user has access to an app.
    Example: {% if user|has_app_access:"humanresource" %}
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        return user.profile.has_app_access(app_name)
    except:
        return False


@register.simple_tag
def user_org_level(user):
    """Get user's organizational level."""
    try:
        return user.profile.organizational_level
    except:
        return None


@register.simple_tag
def can_create(user, app, feature):
    """Check if user can create."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.has_permission(app, feature, 'create')
    except:
        return False


@register.simple_tag
def can_edit(user, app, feature):
    """Check if user can edit."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.has_permission(app, feature, 'edit')
    except:
        return False


@register.simple_tag
def can_delete(user, app, feature):
    """Check if user can delete."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.has_permission(app, feature, 'delete')
    except:
        return False


@register.simple_tag
def can_approve(user, app, feature):
    """Check if user can approve."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.has_permission(app, feature, 'approve')
    except:
        return False


@register.simple_tag
def can_export(user, app, feature):
    """Check if user can export."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.has_permission(app, feature, 'export')
    except:
        return False


@register.simple_tag
def can_import(user, app, feature):
    """Check if user can import."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.has_permission(app, feature, 'import')
    except:
        return False
