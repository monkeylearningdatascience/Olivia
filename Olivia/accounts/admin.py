from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Profile, AppAccess, OrganizationalLevel, Permission, RolePermission,
    ApprovalAuthority, ApproverAssignment, ApprovalWorkflow, ApprovalStep, ApprovalLog
)

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

# ==================== APPROVAL WORKFLOW ADMIN ====================

@admin.register(ApprovalAuthority)
class ApprovalAuthorityAdmin(admin.ModelAdmin):
    list_display = ('app', 'request_type', 'department', 'approval_level', 'required_organizational_level', 'min_amount', 'max_amount', 'is_required')
    list_filter = ('app', 'request_type', 'approval_level', 'is_required')
    search_fields = ('app', 'request_type', 'department')
    ordering = ('app', 'request_type', 'approval_level')
    
@admin.register(ApproverAssignment)
class ApproverAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'approval_authority', 'is_primary', 'is_backup', 'is_active', 'delegate_to')
    list_filter = ('is_primary', 'is_backup', 'is_active', 'approval_authority__app')
    search_fields = ('employee__full_name', 'employee__staffid')
    raw_id_fields = ('employee', 'delegate_to')
    
@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ('request_title', 'app', 'request_type', 'requestor', 'current_status', 'current_approval_level', 'total_approval_levels', 'submitted_at')
    list_filter = ('current_status', 'app', 'request_type', 'urgency')
    search_fields = ('request_title', 'requestor__full_name', 'requestor__staffid')
    raw_id_fields = ('requestor',)
    date_hierarchy = 'created_at'
    
@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'approval_level', 'assigned_to', 'status', 'approved_by', 'assigned_at', 'action_date')
    list_filter = ('status', 'is_escalated')
    search_fields = ('workflow__request_title', 'assigned_to__full_name', 'approved_by__full_name')
    raw_id_fields = ('workflow', 'assigned_to', 'approved_by', 'escalated_to')
    date_hierarchy = 'assigned_at'
    
@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'action', 'actor', 'previous_status', 'new_status', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('workflow__request_title', 'actor__username', 'comments')
    raw_id_fields = ('workflow', 'approval_step')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'ip_address', 'user_agent')