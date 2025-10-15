from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile, AppAccess

# Register your models here.
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    filter_horizontal = ("allowed_apps",)  # nicer multi-select UI in admin

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

@admin.register(AppAccess)
class AppAccessAdmin(admin.ModelAdmin):
    list_display = ('name',)       # Use actual fields from the model
    ordering = ('name',)           # Use actual fields from the model

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('allowed_apps',)

# Unregister the original User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)