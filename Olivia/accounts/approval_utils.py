"""
Approval Workflow Utility Functions
Helper functions to manage approval workflows across the system
"""
from django.utils import timezone
from django.db import models
from django.contrib.contenttypes.models import ContentType
from .models import (
    ApprovalAuthority, ApproverAssignment, ApprovalWorkflow, 
    ApprovalStep, ApprovalLog
)
from HumanResource.models import Employee


def initiate_approval_workflow(request_object, app, request_type, requestor, title, amount=None, urgency='medium'):
    """
    Initialize an approval workflow for any request object.
    
    Args:
        request_object: The Django model instance requiring approval
        app: App name (e.g., 'humanresource', 'logistics')
        request_type: Type of request (e.g., 'petty_cash', 'leave')
        requestor: Employee instance who is submitting the request
        title: Human-readable title for the request
        amount: Optional amount for financial requests
        urgency: Urgency level (low, medium, high, urgent)
    
    Returns:
        ApprovalWorkflow instance
    """
    content_type = ContentType.objects.get_for_model(request_object)
    
    # Get applicable approval authorities
    authorities = get_approval_authorities(
        app=app,
        request_type=request_type,
        department=requestor.department,
        amount=amount
    )
    
    if not authorities:
        raise ValueError(f"No approval authorities configured for {app}.{request_type}")
    
    # Create workflow
    workflow = ApprovalWorkflow.objects.create(
        content_type=content_type,
        object_id=request_object.pk,
        app=app,
        request_type=request_type,
        request_title=title,
        request_amount=amount,
        requestor=requestor,
        requestor_department=requestor.department,
        current_status='submitted',
        current_approval_level=1,
        total_approval_levels=len(authorities),
        submitted_at=timezone.now(),
        urgency=urgency
    )
    
    # Create approval steps
    for authority in authorities:
        # Find the appropriate approver
        approver = get_approver_for_authority(authority, requestor)
        
        if approver:
            ApprovalStep.objects.create(
                workflow=workflow,
                approval_level=authority.approval_level,
                approval_authority=authority,
                assigned_to=approver,
                status='pending' if authority.approval_level == 1 else 'pending'
            )
    
    # Log submission
    ApprovalLog.objects.create(
        workflow=workflow,
        action='submitted',
        actor=requestor.user if hasattr(requestor, 'user') else None,
        new_status='submitted',
        comments=f"Workflow initiated for {title}"
    )
    
    return workflow


def get_approval_authorities(app, request_type, department=None, amount=None):
    """
    Get applicable approval authorities based on request parameters.
    
    Args:
        app: Application name
        request_type: Type of request
        department: Department (optional)
        amount: Amount for financial approvals (optional)
    
    Returns:
        QuerySet of ApprovalAuthority ordered by approval_level
    """
    query = ApprovalAuthority.objects.filter(
        app=app,
        request_type=request_type,
        is_required=True
    )
    
    # Filter by department if specified
    if department:
        query = query.filter(
            models.Q(department='') | models.Q(department__iexact=department)
        )
    else:
        query = query.filter(department='')
    
    # Filter by amount if applicable
    if amount is not None:
        query = query.filter(
            models.Q(min_amount__isnull=True) | models.Q(min_amount__lte=amount),
            models.Q(max_amount__isnull=True) | models.Q(max_amount__gte=amount)
        )
    
    return query.order_by('approval_level')


def get_approver_for_authority(authority, requestor):
    """
    Find the appropriate approver for a given authority and requestor.
    
    Priority:
    1. Direct manager (if Level 1)
    2. Assigned primary approvers for the authority
    3. Assigned backup approvers
    4. Escalate to higher level if none found
    
    Args:
        authority: ApprovalAuthority instance
        requestor: Employee instance
    
    Returns:
        Employee instance or None
    """
    # Level 1: Try direct manager first
    if authority.approval_level == 1 and requestor.manager:
        return requestor.manager
    
    # Check assigned approvers
    assignments = ApproverAssignment.objects.filter(
        approval_authority=authority,
        is_active=True
    ).select_related('employee', 'delegate_to')
    
    # Try primary approvers first
    for assignment in assignments.filter(is_primary=True):
        # Check if there's an active delegate
        if assignment.delegate_to and assignment.delegation_start and assignment.delegation_end:
            today = timezone.now().date()
            if assignment.delegation_start <= today <= assignment.delegation_end:
                return assignment.delegate_to
        return assignment.employee
    
    # Try backup approvers
    for assignment in assignments.filter(is_backup=True):
        if assignment.delegate_to and assignment.delegation_start and assignment.delegation_end:
            today = timezone.now().date()
            if assignment.delegation_start <= today <= assignment.delegation_end:
                return assignment.delegate_to
        return assignment.employee
    
    return None


def approve_step(workflow_id, approval_level, approver, comments=''):
    """
    Approve a specific step in the workflow.
    
    Args:
        workflow_id: ID of the ApprovalWorkflow
        approval_level: The level being approved
        approver: Employee instance doing the approval
        comments: Optional comments
    
    Returns:
        Updated ApprovalWorkflow instance
    """
    workflow = ApprovalWorkflow.objects.get(pk=workflow_id)
    step = ApprovalStep.objects.get(workflow=workflow, approval_level=approval_level)
    
    # Update step
    step.status = 'approved'
    step.approved_by = approver
    step.action_date = timezone.now()
    step.comments = comments
    step.save()
    
    # Log approval
    ApprovalLog.objects.create(
        workflow=workflow,
        approval_step=step,
        action='approved',
        actor=approver.user if hasattr(approver, 'user') else None,
        previous_status=workflow.current_status,
        new_status='pending' if approval_level < workflow.total_approval_levels else 'approved',
        comments=comments
    )
    
    # Update workflow
    if approval_level >= workflow.total_approval_levels:
        # Final approval
        workflow.current_status = 'approved'
        workflow.completed_at = timezone.now()
    else:
        # Move to next level
        workflow.current_approval_level = approval_level + 1
        workflow.current_status = 'pending'
    
    workflow.save()
    
    return workflow


def reject_step(workflow_id, approval_level, approver, reason=''):
    """
    Reject a specific step in the workflow.
    
    Args:
        workflow_id: ID of the ApprovalWorkflow
        approval_level: The level being rejected
        approver: Employee instance doing the rejection
        reason: Reason for rejection
    
    Returns:
        Updated ApprovalWorkflow instance
    """
    workflow = ApprovalWorkflow.objects.get(pk=workflow_id)
    step = ApprovalStep.objects.get(workflow=workflow, approval_level=approval_level)
    
    # Update step
    step.status = 'rejected'
    step.approved_by = approver
    step.action_date = timezone.now()
    step.comments = reason
    step.save()
    
    # Log rejection
    ApprovalLog.objects.create(
        workflow=workflow,
        approval_step=step,
        action='rejected',
        actor=approver.user if hasattr(approver, 'user') else None,
        previous_status=workflow.current_status,
        new_status='rejected',
        comments=reason
    )
    
    # Update workflow
    workflow.current_status = 'rejected'
    workflow.completed_at = timezone.now()
    workflow.save()
    
    return workflow


def get_pending_approvals_for_employee(employee):
    """
    Get all pending approval steps assigned to an employee.
    
    Args:
        employee: Employee instance
    
    Returns:
        QuerySet of ApprovalStep instances
    """
    return ApprovalStep.objects.filter(
        assigned_to=employee,
        status='pending',
        workflow__current_status='pending'
    ).select_related('workflow', 'approval_authority').order_by('-workflow__urgency', '-workflow__submitted_at')


def get_approval_history_for_request(request_object):
    """
    Get the complete approval history for a request object.
    
    Args:
        request_object: The Django model instance
    
    Returns:
        QuerySet of ApprovalLog instances
    """
    content_type = ContentType.objects.get_for_model(request_object)
    
    try:
        workflow = ApprovalWorkflow.objects.get(
            content_type=content_type,
            object_id=request_object.pk
        )
        return workflow.logs.all().select_related('actor', 'approval_step')
    except ApprovalWorkflow.DoesNotExist:
        return ApprovalLog.objects.none()


def can_employee_approve(employee, workflow_id, approval_level):
    """
    Check if an employee can approve a specific step.
    
    Args:
        employee: Employee instance
        workflow_id: ID of the ApprovalWorkflow
        approval_level: The level to check
    
    Returns:
        Boolean
    """
    try:
        step = ApprovalStep.objects.get(
            workflow_id=workflow_id,
            approval_level=approval_level
        )
        return (
            step.assigned_to == employee and 
            step.status == 'pending' and
            step.workflow.current_approval_level == approval_level
        )
    except ApprovalStep.DoesNotExist:
        return False
