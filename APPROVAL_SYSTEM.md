# Approval Workflow System

## Overview
Comprehensive multi-level approval system for managing requests across all departments and applications in Olivia.

## Database Structure

### Core Models

#### 1. **ApprovalAuthority**
Defines approval rules and requirements for different request types.

**Fields:**
- `app`: Application name (humanresource, housing, logistics, etc.)
- `request_type`: Type of request (petty_cash, leave, vehicle_request, etc.)
- `department`: Specific department (optional, blank for all)
- `approval_level`: Level in the approval chain (1-5)
- `required_organizational_level`: Minimum org level needed to approve
- `min_amount/max_amount`: Amount thresholds for financial approvals
- `is_required`: Whether this level is mandatory
- `can_skip_if_unavailable`: Skip if no approver found
- `auto_approve_after_days`: Auto-approve after X days

**Example:**
```python
# Petty cash under $1000 needs 2 levels
ApprovalAuthority(
    app='humanresource',
    request_type='petty_cash',
    approval_level=1,
    max_amount=1000,
    required_organizational_level=manager_level
)
```

#### 2. **ApproverAssignment**
Maps employees to approval authorities.

**Fields:**
- `employee`: Employee assigned as approver
- `approval_authority`: Authority they can approve
- `is_primary`: Primary approver
- `is_backup`: Backup approver
- `delegate_to`: Temporary delegate
- `delegation_start/end`: Delegation period

#### 3. **ApprovalWorkflow**
Tracks the approval process for each request.

**Fields:**
- `content_type/object_id`: Generic FK to any request object
- `app/request_type`: Request classification
- `requestor`: Employee who submitted
- `current_status`: draft, submitted, pending, approved, rejected
- `current_approval_level`: Current level in process
- `total_approval_levels`: Total levels required

#### 4. **ApprovalStep**
Individual approval steps within a workflow.

**Fields:**
- `workflow`: Parent workflow
- `approval_level`: Level number
- `assigned_to`: Employee assigned to approve
- `status`: pending, approved, rejected, skipped
- `approved_by`: Who approved (if completed)
- `comments`: Approval comments

#### 5. **ApprovalLog**
Complete audit trail of all actions.

**Fields:**
- `workflow`: Related workflow
- `action`: submitted, approved, rejected, etc.
- `actor`: User who performed action
- `previous_status/new_status`: Status change
- `ip_address`: Request IP
- `comments`: Action comments

## Usage

### 1. Configure Approval Authorities

First, set up approval levels in the admin:

```python
# Example: Petty cash approval chain
# Level 1: Direct Manager (Supervisor level or higher)
ApprovalAuthority.objects.create(
    app='humanresource',
    request_type='petty_cash',
    approval_level=1,
    required_organizational_level=supervisor_level,
    max_amount=5000,
    is_required=True
)

# Level 2: Department Head (Manager level or higher)
ApprovalAuthority.objects.create(
    app='humanresource',
    request_type='petty_cash',
    approval_level=2,
    required_organizational_level=manager_level,
    min_amount=1000,
    max_amount=10000,
    is_required=True
)

# Level 3: Operations Manager (for amounts over $10k)
ApprovalAuthority.objects.create(
    app='humanresource',
    request_type='petty_cash',
    approval_level=3,
    required_organizational_level=operations_manager_level,
    min_amount=10000,
    is_required=True
)
```

### 2. Assign Approvers

Map employees to authorities:

```python
from accounts.models import ApproverAssignment

# Assign John as primary approver for Level 1 petty cash
ApproverAssignment.objects.create(
    employee=john_employee,
    approval_authority=level1_authority,
    is_primary=True
)

# Assign Jane as backup
ApproverAssignment.objects.create(
    employee=jane_employee,
    approval_authority=level1_authority,
    is_backup=True
)
```

### 3. Initiate Workflow in Views

When a request is submitted:

```python
from accounts.approval_utils import initiate_approval_workflow

def submit_petty_cash(request):
    # Create the cash entry
    cash_entry = Cash.objects.create(
        supplier_name=request.POST['supplier'],
        amount=request.POST['amount'],
        # ... other fields
    )
    
    # Initiate approval workflow
    workflow = initiate_approval_workflow(
        request_object=cash_entry,
        app='humanresource',
        request_type='petty_cash',
        requestor=request.user.profile.employee,  # Assuming user is linked to employee
        title=f"Petty Cash - {cash_entry.supplier_name}",
        amount=cash_entry.total,
        urgency='medium'
    )
    
    return JsonResponse({'success': True, 'workflow_id': workflow.id})
```

### 4. Approve/Reject in Views

```python
from accounts.approval_utils import approve_step, reject_step, can_employee_approve

def approve_request(request, workflow_id, approval_level):
    employee = request.user.profile.employee
    
    # Check if employee can approve this
    if not can_employee_approve(employee, workflow_id, approval_level):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    # Approve
    workflow = approve_step(
        workflow_id=workflow_id,
        approval_level=approval_level,
        approver=employee,
        comments=request.POST.get('comments', '')
    )
    
    return JsonResponse({
        'success': True,
        'status': workflow.current_status,
        'next_level': workflow.current_approval_level
    })

def reject_request(request, workflow_id, approval_level):
    employee = request.user.profile.employee
    
    if not can_employee_approve(employee, workflow_id, approval_level):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    workflow = reject_step(
        workflow_id=workflow_id,
        approval_level=approval_level,
        approver=employee,
        reason=request.POST.get('reason', '')
    )
    
    return JsonResponse({'success': True, 'status': 'rejected'})
```

### 5. Display Pending Approvals

```python
from accounts.approval_utils import get_pending_approvals_for_employee

def my_approvals(request):
    employee = request.user.profile.employee
    pending = get_pending_approvals_for_employee(employee)
    
    return render(request, 'approvals/pending.html', {
        'pending_approvals': pending
    })
```

### 6. Check Approval History

```python
from accounts.approval_utils import get_approval_history_for_request

def view_request(request, cash_id):
    cash_entry = Cash.objects.get(pk=cash_id)
    history = get_approval_history_for_request(cash_entry)
    
    return render(request, 'humanresource/cash_detail.html', {
        'cash': cash_entry,
        'approval_history': history
    })
```

## Workflow States

- **draft**: Created but not yet submitted
- **submitted**: Submitted for approval
- **pending**: Awaiting approval at current level
- **approved**: All levels approved
- **rejected**: Rejected at any level
- **cancelled**: Cancelled by requestor
- **returned**: Sent back for revision

## Approval Levels

1. **Level 1 - Direct Manager**: Immediate supervisor approval
2. **Level 2 - Department Head**: Department manager approval
3. **Level 3 - Operations Manager**: Senior management approval
4. **Level 4 - Project Manager**: Project-level authority
5. **Level 5 - Final Authority**: Executive approval

## Features

### Delegation
Approvers can delegate authority temporarily:
```python
assignment = ApproverAssignment.objects.get(employee=manager)
assignment.delegate_to = substitute_manager
assignment.delegation_start = date.today()
assignment.delegation_end = date.today() + timedelta(days=7)
assignment.save()
```

### Auto-Approval
Set timeout for automatic approval:
```python
authority = ApprovalAuthority.objects.get(...)
authority.auto_approve_after_days = 3
authority.save()
```

### Escalation
Escalate to higher authority if needed:
```python
step = ApprovalStep.objects.get(...)
step.is_escalated = True
step.escalated_to = senior_manager
step.escalation_reason = "Original approver unavailable"
step.save()
```

## Admin Interface

All models are registered in Django admin for configuration:
- `/admin/accounts/approvalauthority/` - Configure approval rules
- `/admin/accounts/approverassignment/` - Assign approvers
- `/admin/accounts/approvalworkflow/` - View all workflows
- `/admin/accounts/approvalstep/` - Manage approval steps
- `/admin/accounts/approvallog/` - Audit trail

## Integration with Employee Model

The system links to `HumanResource.Employee`:
- `Employee.manager`: Direct manager for Level 1 approvals
- `Employee.position`: Used for approval authority matching
- `Employee.department`: Used for department-specific rules

## Next Steps

1. Create UI for pending approvals dashboard
2. Add email notifications for approvers
3. Implement mobile app for approval actions
4. Add approval workflow visualization
5. Create reports for approval metrics
