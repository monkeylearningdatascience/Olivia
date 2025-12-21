from django.contrib.auth.models import User
from django.db import models

class AppAccess(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class OrganizationalLevel(models.Model):
    """
    Represents organizational hierarchy levels.
    Examples: CEO, Director, Manager, Supervisor, Staff, Intern, etc.
    """
    LEVEL_HIERARCHY = [
        (1, 'Project Manager'),
        (2, 'Operations Manager'),
        (3, 'Manager'),
        (4, 'Supervisor'),
        # (5, 'Team Lead'),
        (5, 'Staff'),
        # (7, 'Intern'),
        # (8, 'Consultant'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    level = models.IntegerField(choices=LEVEL_HIERARCHY, help_text="Lower number = higher authority")
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['level']
    
    def __str__(self):
        return f"{self.name} (Level {self.level})"


class Permission(models.Model):
    """
    Fine-grained permissions for specific screens/features.
    Examples: view_staff, create_staff, approve_petty_cash, etc.
    """
    APP_CHOICES = [
        ('humanresource', 'Human Resource'),
        ('housing', 'Housing'),
        ('logistics', 'Logistics'),
        ('procurement', 'Procurement'),
        ('ict', 'ICT'),
        ('qhse', 'QHSE'),
        ('hardservice', 'Hard Service'),
        ('softservice', 'Soft Service'),
        ('training', 'Training'),
        ('utility', 'Utility'),
        ('warehouse', 'Warehouse'),
        ('fls', 'FLS'),
        ('tickets', 'Tickets'),
    ]
    
    ACTION_CHOICES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('approve', 'Approve'),
        ('submit', 'Submit'),
    ]
    
    app = models.CharField(max_length=50, choices=APP_CHOICES)
    feature = models.CharField(max_length=100, help_text="e.g., 'staff', 'petty_cash', 'units'")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('app', 'feature', 'action')
        ordering = ['app', 'feature', 'action']
    
    def __str__(self):
        return f"{self.app}.{self.feature}.{self.action}"


class RolePermission(models.Model):
    """
    Maps organizational levels to permissions.
    Allows bulk assignment of permissions to all users at a level.
    """
    organizational_level = models.ForeignKey(OrganizationalLevel, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('organizational_level', 'permission')
    
    def __str__(self):
        return f"{self.organizational_level} → {self.permission}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    allowed_apps = models.ManyToManyField(AppAccess, blank=True)
    organizational_level = models.ForeignKey(OrganizationalLevel, on_delete=models.SET_NULL, null=True, blank=True)
    # Custom permissions override (if needed to deviate from organizational level)
    custom_permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.user.username
    
    def get_all_permissions(self):
        """Get all permissions for this user (org level + custom)."""
        if self.organizational_level:
            org_perms = Permission.objects.filter(rolepermission__organizational_level=self.organizational_level)
            custom_perms = self.custom_permissions.all()
            return org_perms | custom_perms
        return self.custom_permissions.all()
    
    def has_permission(self, app, feature, action):
        """Check if user has specific permission."""
        return self.get_all_permissions().filter(
            app=app,
            feature=feature,
            action=action
        ).exists()
    
    def has_app_access(self, app):
        """Check if user can access an app."""
        return self.allowed_apps.filter(name=app).exists() or self.get_all_permissions().filter(app=app).exists()
