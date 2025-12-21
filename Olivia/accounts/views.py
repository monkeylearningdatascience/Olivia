from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
import json

from .models import OrganizationalLevel, Permission, RolePermission, Profile
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from .forms import OrganizationalLevelForm, PermissionForm, RolePermissionForm, AssignOrgLevelForm


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_active and u.is_superuser)(view_func)


@login_required
@superuser_required
@require_http_methods(["GET", "POST"])
def organizational_levels(request):
    """List or create organizational levels (superusers only)."""
    if request.method == 'GET':
        levels = list(OrganizationalLevel.objects.values('id', 'name', 'level', 'description'))
        return JsonResponse({'levels': levels})

    # POST - create
    try:
        payload = json.loads(request.body.decode()) if request.body else request.POST
    except Exception:
        return HttpResponseBadRequest('Invalid JSON payload')

    name = payload.get('name')
    level = payload.get('level')
    description = payload.get('description', '')
    if not name or level is None:
        return HttpResponseBadRequest('`name` and `level` are required')

    obj = OrganizationalLevel.objects.create(name=name, level=level, description=description)
    return JsonResponse({'success': True, 'id': obj.id, 'name': obj.name})


@login_required
@superuser_required
@require_http_methods(["GET", "POST", "DELETE"])
def organizational_level_detail(request, pk):
    obj = get_object_or_404(OrganizationalLevel, pk=pk)

    if request.method == 'GET':
        return JsonResponse({'id': obj.id, 'name': obj.name, 'level': obj.level, 'description': obj.description})

    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode()) if request.body else request.POST
        except Exception:
            return HttpResponseBadRequest('Invalid JSON payload')
        obj.name = payload.get('name', obj.name)
        obj.level = payload.get('level', obj.level)
        obj.description = payload.get('description', obj.description)
        obj.save()
        return JsonResponse({'success': True})

    # DELETE
    obj.delete()
    return JsonResponse({'success': True})


@login_required
@superuser_required
@require_http_methods(["GET", "POST"])
def permissions_list(request):
    if request.method == 'GET':
        perms = list(Permission.objects.values('id', 'app', 'feature', 'action', 'description'))
        return JsonResponse({'permissions': perms})

    try:
        payload = json.loads(request.body.decode()) if request.body else request.POST
    except Exception:
        return HttpResponseBadRequest('Invalid JSON payload')

    app = payload.get('app')
    feature = payload.get('feature')
    action = payload.get('action')
    description = payload.get('description', '')
    if not app or not feature or not action:
        return HttpResponseBadRequest('`app`, `feature`, and `action` are required')

    perm, created = Permission.objects.get_or_create(app=app, feature=feature, action=action, defaults={'description': description})
    return JsonResponse({'success': True, 'id': perm.id, 'created': created})


@login_required
@superuser_required
@require_http_methods(["GET", "POST", "DELETE"])
def permission_detail(request, pk):
    perm = get_object_or_404(Permission, pk=pk)
    if request.method == 'GET':
        return JsonResponse({'id': perm.id, 'app': perm.app, 'feature': perm.feature, 'action': perm.action, 'description': perm.description})

    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode()) if request.body else request.POST
        except Exception:
            return HttpResponseBadRequest('Invalid JSON payload')
        perm.app = payload.get('app', perm.app)
        perm.feature = payload.get('feature', perm.feature)
        perm.action = payload.get('action', perm.action)
        perm.description = payload.get('description', perm.description)
        perm.save()
        return JsonResponse({'success': True})

    perm.delete()
    return JsonResponse({'success': True})


@login_required
@superuser_required
@require_http_methods(["GET", "POST"])
def role_permissions(request):
    """List or create role-permission mappings."""
    if request.method == 'GET':
        mappings = list(RolePermission.objects.select_related('organizational_level', 'permission').values(
            'id', 'organizational_level__id', 'organizational_level__name',
            'permission__id', 'permission__app', 'permission__feature', 'permission__action'
        ))
        return JsonResponse({'role_permissions': mappings})

    try:
        payload = json.loads(request.body.decode()) if request.body else request.POST
    except Exception:
        return HttpResponseBadRequest('Invalid JSON payload')

    org_level_id = payload.get('organizational_level_id')
    permission_id = payload.get('permission_id')
    if not org_level_id or not permission_id:
        return HttpResponseBadRequest('`organizational_level_id` and `permission_id` are required')

    org = get_object_or_404(OrganizationalLevel, pk=org_level_id)
    perm = get_object_or_404(Permission, pk=permission_id)
    obj, created = RolePermission.objects.get_or_create(organizational_level=org, permission=perm)
    return JsonResponse({'success': True, 'id': obj.id, 'created': created})


@login_required
@superuser_required
@require_http_methods(["DELETE"])
def role_permission_delete(request, pk):
    obj = get_object_or_404(RolePermission, pk=pk)
    obj.delete()
    return JsonResponse({'success': True})


@login_required
@superuser_required
@require_http_methods(["POST"])
def assign_org_level_to_user(request):
    """Assign organizational level to a user profile.
    Payload: {"username": "jdoe", "organizational_level_id": 3}
    """
    try:
        payload = json.loads(request.body.decode()) if request.body else request.POST
    except Exception:
        return HttpResponseBadRequest('Invalid JSON payload')

    username = payload.get('username')
    user_id = payload.get('user_id')
    org_level_id = payload.get('organizational_level_id')
    if not (username or user_id) or not org_level_id:
        return HttpResponseBadRequest('`username` or `user_id` and `organizational_level_id` are required')

    try:
        if user_id:
            profile = Profile.objects.get(user__id=user_id)
        else:
            profile = Profile.objects.get(user__username=username)
    except Profile.DoesNotExist:
        return HttpResponseBadRequest('Profile not found')

    org = get_object_or_404(OrganizationalLevel, pk=org_level_id)
    profile.organizational_level = org
    profile.save(update_fields=['organizational_level'])
    return JsonResponse({'success': True})


# ---------- Web admin UI views ----------


@login_required
@superuser_required
def admin_org_levels(request):
    """Web UI: list and create organizational levels."""
    if request.method == 'POST':
        form = OrganizationalLevelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Organizational level created')
            return redirect(reverse('accounts:admin_org_levels'))
    else:
        form = OrganizationalLevelForm()

    levels = OrganizationalLevel.objects.all()
    return render(request, 'accounts/admin_levels.html', {'levels': levels, 'form': form})


@login_required
@superuser_required
def admin_org_level_edit(request, pk):
    obj = get_object_or_404(OrganizationalLevel, pk=pk)
    if request.method == 'POST':
        form = OrganizationalLevelForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Organizational level updated')
            return redirect(reverse('accounts:admin_org_levels'))
    else:
        form = OrganizationalLevelForm(instance=obj)
    return render(request, 'accounts/admin_levels.html', {'levels': OrganizationalLevel.objects.all(), 'form': form, 'editing': obj})


@login_required
@superuser_required
def admin_permissions(request):
    if request.method == 'POST':
        form = PermissionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Permission created')
            return redirect(reverse('accounts:admin_permissions'))
    else:
        form = PermissionForm()
    perms = Permission.objects.all()
    return render(request, 'accounts/admin_permissions.html', {'permissions': perms, 'form': form})


@login_required
@superuser_required
def admin_permission_edit(request, pk):
    obj = get_object_or_404(Permission, pk=pk)
    if request.method == 'POST':
        form = PermissionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Permission updated')
            return redirect(reverse('accounts:admin_permissions'))
    else:
        form = PermissionForm(instance=obj)
    return render(request, 'accounts/admin_permissions.html', {'permissions': Permission.objects.all(), 'form': form, 'editing': obj})


@login_required
@superuser_required
def admin_role_permissions(request):
    if request.method == 'POST':
        form = RolePermissionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role permission assigned')
            return redirect(reverse('accounts:admin_role_permissions'))
    else:
        form = RolePermissionForm()
    mappings = RolePermission.objects.select_related('organizational_level', 'permission').all()
    return render(request, 'accounts/admin_role_permissions.html', {'mappings': mappings, 'form': form})


@login_required
@superuser_required
def admin_assign_level(request):
    if request.method == 'POST':
        form = AssignOrgLevelForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            user_id = form.cleaned_data.get('user_id')
            org_level = form.cleaned_data.get('organizational_level')
            try:
                if user_id:
                    profile = Profile.objects.get(user__id=user_id)
                else:
                    profile = Profile.objects.get(user__username=username)
                profile.organizational_level = org_level
                profile.save(update_fields=['organizational_level'])
                messages.success(request, 'Organizational level assigned')
                return redirect(reverse('accounts:admin_assign_level'))
            except Profile.DoesNotExist:
                messages.error(request, 'Profile not found')
    else:
        form = AssignOrgLevelForm()
    return render(request, 'accounts/admin_assign_level.html', {'form': form})
from django.shortcuts import render

# Create your views here.
def no_access(request):
    return render(request, "accounts/no_access.html", status=403)