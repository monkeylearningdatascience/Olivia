"""
Approval Workflow Models
Handles multi-level approval workflows across all apps
"""
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from .models import OrganizationalLevel


class ApprovalAuthority(models.Model):
    """
    Defines who can approve what based on department, position, and organizational level.
    Maps approval authority to specific combinations.
    """
    APPROVAL_LEVEL_CHOICES = [
        (1, 'Level 1 - Direct Manager'),
        (2, 'Level 2 - Department Head'),
        (3, 'Level 3 - Operations Manager'),
        (4, 'Level 4 - Project Manager'),
        (5, 'Level 5 - Final Authority'),
    ]
    
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
    
    REQUEST_TYPE_CHOICES = [
        ('petty_cash', 'Petty Cash'),
        ('leave', 'Leave Request'),
        ('clearance', 'Clearance'),
        ('work_notice', 'Work Notice'),
        ('vehicle_request', 'Vehicle Request'),
        ('purchase_request', 'Purchase Request'),
        ('maintenance', 'Maintenance Request'),
        ('housing_allocation', 'Housing Allocation'),
        ('training_request', 'Training Request'),
        ('overtime', 'Overtime Request'),
        ('transfer', 'Transfer Request'),
        ('hiring', 'Hiring Request'),
        ('general', 'General Request'),
    ]
    
    app = models.CharField(max_length=50, choices=APP_CHOICES)
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES)
    department = models.CharField(max_length=100, blank=True, help_text="Leave blank for all departments")
    
    # Approval level configuration
    approval_level = models.IntegerField(choices=APPROVAL_LEVEL_CHOICES)
    required_organizational_level = models.ForeignKey(
        OrganizationalLevel, 
        on_delete=models.CASCADE,
        help_text="Minimum organizational level required to approve at this level"
    )
    
    # Amount thresholds (optional, for financial approvals)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Workflow configuration
    is_required = models.BooleanField(default=True, help_text="Is this approval level mandatory?")
    can_skip_if_unavailable = models.BooleanField(default=False, help_text="Skip if no approver available")
    auto_approve_after_days = models.IntegerField(null=True, blank=True, help_text="Auto-approve if no response after X days")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['app', 'request_type', 'approval_level']
        verbose_name = 'Approval Authority'
        verbose_name_plural = 'Approval Authorities'
    
    def __str__(self):
        dept_str = f" - {self.department}" if self.department else ""
        amount_str = ""
        if self.min_amount or self.max_amount:
            min_amt = self.min_amount or 0
            max_amt = self.max_amount or "∞"
            amount_str = f" (${min_amt}-${max_amt})"
        return f"{self.app} - {self.request_type}{dept_str} - L{self.approval_level}{amount_str}"


class ApproverAssignment(models.Model):
    """
    Maps specific employees to approval authority.
    Links Employee model to approval capabilities.
    """
    from HumanResource.models import Employee
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='approval_assignments')
    approval_authority = models.ForeignKey(ApprovalAuthority, on_delete=models.CASCADE, related_name='assigned_approvers')
    
    # Override settings
    is_primary = models.BooleanField(default=True, help_text="Primary approver for this authority")
    is_backup = models.BooleanField(default=False, help_text="Backup approver (acts when primary unavailable)")
    
    # Delegation
    delegate_to = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='delegated_approvals',
        help_text="Temporary delegate while this approver is unavailable"
    )
    delegation_start = models.DateField(null=True, blank=True)
    delegation_end = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('employee', 'approval_authority')
        ordering = ['approval_authority', '-is_primary', 'employee']
    
    def __str__(self):
        role = "Primary" if self.is_primary else "Backup"
        return f"{self.employee.full_name} - {role} - {self.approval_authority}"


class ApprovalWorkflow(models.Model):
    """
    Tracks the approval workflow for any request across the system.
    Uses GenericForeignKey to link to any model (petty cash, leave, etc.)
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned for Revision'),
    ]
    
    # Generic relationship to any request object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    request_object = GenericForeignKey('content_type', 'object_id')
    
    # Request metadata
    app = models.CharField(max_length=50)
    request_type = models.CharField(max_length=50)
    request_title = models.CharField(max_length=255)
    request_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Requestor information
    from HumanResource.models import Employee
    requestor = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='submitted_requests')
    requestor_department = models.CharField(max_length=100)
    
    # Workflow status
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    current_approval_level = models.IntegerField(default=1)
    total_approval_levels = models.IntegerField(default=1)
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional metadata
    urgency = models.CharField(
        max_length=20, 
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')],
        default='medium'
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['current_status', 'current_approval_level']),
            models.Index(fields=['requestor', 'current_status']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.request_title} - {self.get_current_status_display()} - Level {self.current_approval_level}/{self.total_approval_levels}"


class ApprovalStep(models.Model):
    """
    Individual approval steps within a workflow.
    Tracks each level of approval.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped'),
        ('delegated', 'Delegated'),
    ]
    
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.CASCADE, related_name='approval_steps')
    approval_level = models.IntegerField()
    approval_authority = models.ForeignKey(ApprovalAuthority, on_delete=models.CASCADE)
    
    # Assigned approver
    from HumanResource.models import Employee
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assigned_approvals')
    
    # Approval action
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='completed_approvals'
    )
    
    # Timestamps
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    action_date = models.DateTimeField(null=True, blank=True)
    
    # Comments and attachments
    comments = models.TextField(blank=True)
    attachments = models.FileField(upload_to='approvals/attachments/', blank=True, null=True)
    
    # Escalation tracking
    is_escalated = models.BooleanField(default=False)
    escalated_to = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_approvals'
    )
    escalation_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['workflow', 'approval_level']
        unique_together = ('workflow', 'approval_level')
    
    def __str__(self):
        return f"{self.workflow.request_title} - Level {self.approval_level} - {self.get_status_display()}"


class ApprovalLog(models.Model):
    """
    Audit log for all approval actions.
    Tracks every action taken on any approval.
    """
    ACTION_CHOICES = [
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
        ('delegated', 'Delegated'),
        ('escalated', 'Escalated'),
        ('commented', 'Commented'),
        ('viewed', 'Viewed'),
    ]
    
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.CASCADE, related_name='logs')
    approval_step = models.ForeignKey(ApprovalStep, on_delete=models.CASCADE, null=True, blank=True)
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Previous and new values (for audit trail)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    
    comments = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"{actor_name} - {self.get_action_display()} - {self.workflow.request_title}"
