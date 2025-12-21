from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile, AppAccess, OrganizationalLevel, Permission, RolePermission

# Register your models here.
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    filter_horizontal = ("allowed_apps", "custom_permissions")

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

@admin.register(AppAccess)
class AppAccessAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)

@admin.register(OrganizationalLevel)
class OrganizationalLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'description')
    list_filter = ('level',)
    search_fields = ('name',)
    ordering = ('level',)

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('app', 'feature', 'action', 'description')
    list_filter = ('app', 'action')
    search_fields = ('feature', 'description')
    ordering = ('app', 'feature', 'action')

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('organizational_level', 'permission')
    list_filter = ('organizational_level', 'permission__app')
    search_fields = ('organizational_level__name', 'permission__feature')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('organizational_level', 'permission')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('allowed_apps',)

# Unregister the original User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)