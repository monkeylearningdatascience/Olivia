from django import forms
from .models import OrganizationalLevel, Permission, RolePermission
from django.contrib.auth.models import User


class OrganizationalLevelForm(forms.ModelForm):
    class Meta:
        model = OrganizationalLevel
        fields = ['name', 'level', 'description']


class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = ['app', 'feature', 'action', 'description']


class RolePermissionForm(forms.ModelForm):
    class Meta:
        model = RolePermission
        fields = ['organizational_level', 'permission']


class AssignOrgLevelForm(forms.Form):
    username = forms.CharField(required=False, help_text='Username')
    user_id = forms.IntegerField(required=False, help_text='User ID')
    organizational_level = forms.ModelChoiceField(queryset=OrganizationalLevel.objects.all())
