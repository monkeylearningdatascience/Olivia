from django.shortcuts import render, redirect, get_object_or_404, reverse, Http404
from django.core.paginator import Paginator
from .models import Cash, Balance, Project, Employee, Manager
from .forms import CashForm, EmployeeForm
from utils.excel_exporter import export_to_excel
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone  # <-- Add this import
import decimal
from django.db.models import Sum
from Olivia.constants import HR_TABS
from django.urls import reverse
import pandas as pd


def _render_template(request, template_name):
    return render(request, f'humanresource/{template_name}.html')

def home(request):
    return _render_template(request, 'home')

def hr_leave(request):
    return _render_template(request, 'leave')

def hr_work_notice(request):
    return _render_template(request, 'work_notice')

def hr_clearance(request):
    return _render_template(request, 'clearance')

def hr_work_letters(request):
    return _render_template(request, 'work_letters')

def hr_medical_declarations(request):
    return _render_template(request, 'medical_declarations')

def hr_hiring(request):
    return _render_template(request, 'hiring')

def hr_transfer_request(request):
    return _render_template(request, 'transfer_request')

def hr_contract_amendments(request):
    return _render_template(request, 'contract_amendments')

def hr_contract_termination(request):
    return _render_template(request, 'contract_termination')

def hr_monthly_attendance(request):
    return _render_template(request, 'monthly_attendance')

def hr_overtime(request):
    return _render_template(request, 'overtime')

def hr_petty_cash(request):
    if request.method == 'POST':
        # Handles deletion from the form
        if 'selected_ids' in request.POST:
            selected_ids = request.POST.getlist('selected_ids')
            if selected_ids:
                try:
                    Cash.objects.filter(id__in=selected_ids).delete()
                    return JsonResponse({'success': True})
                except Exception as e:
                    return JsonResponse({'success': False, 'message': str(e)}, status=500)

        # --- Handle Add/Update ---
        cash_id = request.POST.get('cash_id')
        instance = None
        if cash_id and cash_id.isdigit():
            instance = get_object_or_404(Cash, id=cash_id)
        
        form = CashForm(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            # Get data from the cleaned form
            cash_entry = form.save(commit=False)
            
            # Set audit fields
            if not instance:  # Creating new
                cash_entry.created_by = request.user
            cash_entry.modified_by = request.user
            
            # --- THIS IS THE CRITICAL FIX ---
            # Get the total from the POST data directly
            total_from_post = request.POST.get('total')
            
            # Set a default value to None
            manual_total = None
            if total_from_post:
                try:
                    # Attempt to convert the POST value to a Decimal
                    manual_total = decimal.Decimal(total_from_post)
                except (decimal.InvalidOperation, TypeError):
                    # If conversion fails, manual_total remains None
                    pass
            
            # If a valid manual total was found, use it. Otherwise, calculate.
            if manual_total is not None:
                cash_entry.total = manual_total
            else:
                # Fallback calculation
                amount = request.POST.get('amount', 0)
                vat = request.POST.get('vat', 0)
                import_duty = request.POST.get('import_duty', 0)
                discount = request.POST.get('discount', 0)

                # Ensure values are Decimal before calculation
                try:
                    amount = decimal.Decimal(amount or 0)
                    vat = decimal.Decimal(vat or 0)
                    import_duty = decimal.Decimal(import_duty or 0)
                    discount = decimal.Decimal(discount or 0)
                    
                    cash_entry.total = amount + vat + import_duty - discount
                except (decimal.InvalidOperation, TypeError):
                    # A final failsafe if all values are bad
                    return JsonResponse({'error': 'Invalid numeric data provided.'}, status=400)

            # Now save the instance with the guaranteed valid total
            cash_entry.save()
            return HttpResponse(status=200)
        else:
            print("Form errors:", form.errors)
            return JsonResponse({'errors': form.errors}, status=400)

    # --- Handle GET Request (Page Load) ---
    cash_list = Cash.objects.all().order_by('-created_at')
    paginator = Paginator(cash_list, 15)
    page_number = request.GET.get('page')
    cash_entries = paginator.get_page(page_number)
    form = CashForm()
    
    context = {
        'cash_entries': cash_entries,
        'form': form,
    }
    return render(request, 'humanresource/petty_cash.html', context)

def export_petty_cash(request):
    queryset = Cash.objects.all().order_by('-created_at')

    headers = [
        "Date", "Supplier", "Department", "Description", "Invoice #", "Amount",
        "VAT", "Import Duty", "Discount", "Total", "Project", "Submitted Date",
        "Created By", "Created Date", "Modified By", "Modified Date"
    ]

    def row_data(c):
        return [
            c.date,
            c.supplier_name or "",
            c.department or "",
            c.item_description or "",
            c.invoice_number or "",
            c.amount,
            c.vat or 0,
            c.import_duty or 0,
            c.discount or 0,
            c.total,
            str(c.project_name) if c.project_name else "",
            c.submitted_date.strftime("%Y-%m-%d") if c.submitted_date else "",
            c.created_by.username if c.created_by else "",
            c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else "",
            c.modified_by.username if c.modified_by else "",
            c.modified_at.strftime("%Y-%m-%d %H:%M:%S") if c.modified_at else "",
        ]

    return export_to_excel(queryset, headers, row_data, file_prefix="petty_cash")

def create_balance_entry(request):
    if request.method == 'POST':
        entered_amount = request.POST.get('amount')
        selected_activity = request.POST.get('activity')
        selected_project_name = request.POST.get('project_name')

        try:
            project_instance = Project.objects.get(project_name=selected_project_name)
            new_amount = float(entered_amount)
            
            # Create a new Balance entry
            Balance.objects.create(
                activity=selected_activity,
                project_name=project_instance,
                amount=new_amount,
                created_by=request.user,
                modified_by=request.user
            )

            if selected_activity == 'submitted':
                cash_entry = Cash.objects.filter(
                    project_name=project_instance,
                    submitted_date__isnull=True
                ).order_by('-created_at').first()

                if cash_entry:
                    cash_entry.submitted_date = timezone.now()
                    cash_entry.save()
        
        except (Project.DoesNotExist, ValueError):
            # You can handle this gracefully with a message to the user
            pass

    return redirect(reverse('humanresource_home'))

def update_balance_entry(request):
    if request.method == 'POST':
        try:
            balance_id = request.POST.get('balance_id')
            entered_amount = request.POST.get('amount')
            selected_activity = request.POST.get('activity')
            selected_project_name = request.POST.get('project_name')

            project_instance = get_object_or_404(Project, project_name=selected_project_name)

            # Create new Balance entry
            Balance.objects.create(
                amount=float(entered_amount),
                activity=selected_activity,
                project_name=project_instance,
                created_by=request.user,
                modified_by=request.user
            )

            # Update Cash table only if activity is 'submitted'
            if selected_activity == 'submitted':
                Cash.objects.filter(
                    project_name=project_instance,
                    submitted_date__isnull=True
                ).update(submitted_date=timezone.now())

            return JsonResponse({'success': True})
        except Exception as e:
            print("Error updating balance:", e)
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


def get_submitted_total(request):
    if request.method == 'GET':
        project_name = request.GET.get('project_name')
        if not project_name:
            return JsonResponse({'total': '0.00'})

        try:
            project_instance = Project.objects.get(project_name=project_name)
        except Project.DoesNotExist:
            return JsonResponse({'total': '0.00'})

        total_sum = Cash.objects.filter(
            project_name=project_instance,
            submitted_date__isnull=True
        ).aggregate(Sum('total'))['total__sum'] or 0.0

        return JsonResponse({'total': f"{total_sum:.2f}"})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

from django.db.models import Sum
from .models import Project, Balance

from django.db.models import Sum
from django.utils import timezone
from .models import Project, Balance, Cash

def humanresource_home(request):
    projects = Project.objects.all()
    project_balances = []

    for project in projects:
        # Sum of Opening Balance
        opening_balance = Balance.objects.filter(
            project_name=project,
            activity='opening'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Sum of Replenishment from HQ
        replenishment = Balance.objects.filter(
            project_name=project,
            activity='received'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Total from balances table
        total_balance = opening_balance + replenishment

        # Cash table amounts
        submitted_blank = Cash.objects.filter(
            project_name=project,
            submitted_date__isnull=True
        ).aggregate(total=Sum('total'))['total'] or 0

        submitted_nonblank = Cash.objects.filter(
            project_name=project,
            submitted_date__isnull=False
        ).aggregate(total=Sum('total'))['total'] or 0

        # Available balance after subtracting cash totals
        available_balance = total_balance - submitted_blank - submitted_nonblank

        project_balances.append({
            'name': project.project_name,
            'opening_balance': opening_balance,
            'replenishment': replenishment,
            'total_balance': total_balance,
            'submitted_blank': submitted_blank,
            'submitted_nonblank': submitted_nonblank,
            'available_balance': available_balance,
        })

    context = {
        'project_balances': project_balances
    }
    return render(request, 'humanresource/home.html', context)


def staff_create(request):
    """Handle POST request to create a new employee via AJAX."""
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.created_by = request.user
            employee.modified_by = request.user
            employee.save()
            photo_url_value = employee.photo_url.url if employee.photo_url else ''
            return JsonResponse({'success': True, 'id': employee.id, 'message': 'Employee created successfully', 'photo_url': photo_url_value})
        else:
            # Return field-level errors for display in modal
            field_errors = {field: [str(err) for err in errors] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': field_errors}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def staff_update(request, id):
    """Handle POST request to update an employee, or GET to fetch employee data for populate."""
    employee = get_object_or_404(Employee, id=id)
    
    if request.method == 'GET':
        # Return employee data as JSON for form population
        data = {
            'id': employee.id,
            'staffid': employee.staffid,
            'full_name': employee.full_name,
            'position': employee.position,
            'department': employee.department,
            'manager': employee.manager_id,
            'nationality': getattr(employee.nationality, 'code', str(employee.nationality)) if employee.nationality else '',
            'email': employee.email,
            'iqama_number': employee.iqama_number,
            'passport_number': employee.passport_number,
            'gender': employee.gender,
            'location': employee.location,
            'start_date': employee.start_date.isoformat() if employee.start_date else '',
            'photo_url': employee.photo_url.url if employee.photo_url else '',
            'employment_status': employee.employment_status,
        }
        return JsonResponse(data)
    
    elif request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.modified_by = request.user
            employee.save()
            photo_url_value = employee.photo_url.url if employee.photo_url else ''
            return JsonResponse({'success': True, 'id': employee.id, 'message': 'Employee updated successfully', 'photo_url': photo_url_value})
        else:
            # Return field-level errors for display in modal
            field_errors = {field: [str(err) for err in errors] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': field_errors}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def staff_delete(request, id):
    """Handle POST request to delete a single employee."""
    if request.method == 'POST':
        employee = get_object_or_404(Employee, id=id)
        try:
            employee.delete()
            return JsonResponse({'success': True, 'message': 'Employee deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def staff(request):
    # Handle POST for Create/Update/Delete via AJAX
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"DEBUG: action = '{action}'")
        print(f"DEBUG: POST keys = {list(request.POST.keys())}")
        
        if action == 'delete':
            # Delete selected employees
            selected_ids = request.POST.getlist('selected_ids')
            # Filter out empty strings and convert to integers
            selected_ids = [int(id) for id in selected_ids if id.strip()]
            print(f"DEBUG: selected_ids = {selected_ids}")
            if selected_ids:
                try:
                    Employee.objects.filter(id__in=selected_ids).delete()
                    return JsonResponse({'success': True, 'message': 'Employees deleted successfully'})
                except Exception as e:
                    print(f"DEBUG: Delete exception: {e}")
                    return JsonResponse({'success': False, 'message': str(e)}, status=500)
            else:
                return JsonResponse({'success': False, 'message': 'No valid IDs selected'}, status=400)

        # Create or update an employee using EmployeeForm
        try:
            emp_id = request.POST.get('employee_id')
            instance = None
            if emp_id:
                try:
                    instance = Employee.objects.get(id=emp_id)
                except Employee.DoesNotExist:
                    instance = None

            form = EmployeeForm(request.POST, request.FILES, instance=instance)
            if form.is_valid():
                employee = form.save(commit=False)
                if not instance:  # Creating new
                    employee.created_by = request.user
                employee.modified_by = request.user
                employee.save()
                message = 'Employee updated successfully' if instance else 'Employee created successfully'
                photo_url_value = employee.photo_url.url if employee.photo_url else ''
                return JsonResponse({'success': True, 'id': employee.id, 'message': message, 'photo_url': photo_url_value})
            else:
                # Return field-level errors for display in modal
                field_errors = {field: [str(err) for err in errors] for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': field_errors}, status=400)
        except Exception as e:
            print(f"DEBUG: Form processing exception: {e}")
            return JsonResponse({'success': False, 'message': f'Form processing error: {str(e)}'}, status=500)

    # GET - render staff list with pagination
    employees_qs = Employee.objects.all().order_by('-created_at')  # Newest first
    active_count = employees_qs.filter(employment_status='active').count()
    on_notice = employees_qs.filter(employment_status='on_notice').count()
    exited = employees_qs.filter(employment_status='exited').count()

    # Paginate the staff list (25 per page)
    page_number = request.GET.get('page', 1)
    paginator = Paginator(employees_qs, 15)
    staff_entries = paginator.get_page(page_number)

    context = {
        'employees': employees_qs,
        'staff_entries': staff_entries,
        'active_count': active_count,
        'on_notice': on_notice,
        'exited': exited,
        'form': EmployeeForm(),  # Empty form for modal rendering
    }
    return render(request, 'humanresource/staff.html', context)


def export_staff(request):
    # simple CSV/Excel export for employees — reuse export_to_excel if available
    queryset = Employee.objects.all().order_by('full_name')
    headers = [
        'Staff ID', 'Full Name', 'Position', 'Department', 'Manager', 'Nationality', 'Email', 
        'Iqama', 'Passport', 'Gender', 'Location', 'Start Date', 'Status',
        'Created By', 'Created Date', 'Modified By', 'Modified Date'
    ]

    def row_data(e):
        return [
            e.staffid or '',
            e.full_name or '',
            e.position or '',
            e.department or '',
            e.manager.name if e.manager else '',
            e.nationality.name if getattr(e, 'nationality', None) else '',
            e.email or '',
            e.iqama_number or '',
            e.passport_number or '',
            e.gender or '',
            e.location or '',
            e.start_date.strftime('%B %d, %Y') if e.start_date else '',
            e.employment_status or '',
            e.created_by.username if e.created_by else '',
            e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else '',
            e.modified_by.username if e.modified_by else '',
            e.modified_at.strftime('%Y-%m-%d %H:%M:%S') if e.modified_at else '',
        ]

    try:
        return export_to_excel(queryset, headers, row_data, file_prefix='staff')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def import_staff(request):
    """Handles bulk import of staff data from Excel file."""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    if 'excel_file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded.'}, status=400)
    
    excel_file = request.FILES['excel_file']
    
    try:
        df = pd.read_excel(excel_file)
        
        # Column mapping from Excel to model fields
        column_mapping = {
            'staffid': 'staffid',
            'full_name': 'full_name',
            'position': 'position',
            'department': 'department',
            'nationality': 'nationality',
            'email': 'email',
            'iqama_number': 'iqama_number',
            'passport_number': 'passport_number',
            'gender': 'gender',
            'location': 'location',
            'start_date': 'start_date',
            'employment_status': 'employment_status',
        }
        
        imported_count = 0
        updated_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                employee_data = {}
                
                # Map and clean data
                for excel_col, model_field in column_mapping.items():
                    value = row.get(excel_col)
                    if pd.isna(value) or value is pd.NaT:
                        employee_data[model_field] = None
                    else:
                        employee_data[model_field] = value
                
                # staffid is the unique identifier for upsert
                staffid = employee_data.get('staffid')
                if not staffid:
                    errors.append(f"Row {index + 1}: Missing staffid")
                    continue
                
                # Try to update existing or create new
                employee, created = Employee.objects.update_or_create(
                    staffid=staffid,
                    defaults=employee_data
                )
                
                if created:
                    imported_count += 1
                else:
                    updated_count += 1
                    
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
                continue
        
        return JsonResponse({
            'success': True,
            'imported': imported_count,
            'updated': updated_count,
            'errors': errors,
            'message': f'Successfully imported {imported_count} and updated {updated_count} staff records.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'File processing error: {str(e)}'}, status=400)

def humanresource_tab(request, tab):
    return render(request, "humanresource/base.html", {
        "tabs": HR_TABS,
        "active_tab": tab,
    })

def manager_create(request):
    """Handle POST request to create a new manager via AJAX."""
    if request.method == 'POST':
        try:
            Manager.objects.create(
                staffid=request.POST.get('staffid'),
                name=request.POST.get('name'),
                email=request.POST.get('email', ''),
                designation=request.POST.get('designation', ''),
                department=request.POST.get('department', ''),
                created_by=request.user,
                modified_by=request.user
            )
            return JsonResponse({'success': True, 'message': 'Manager created successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def manager_update(request, id):
    """Handle GET to fetch manager data or POST to update manager."""
    manager = get_object_or_404(Manager, id=id)
    
    if request.method == 'GET':
        data = {
            'id': manager.id,
            'staffid': manager.staffid,
            'name': manager.name,
            'email': manager.email,
            'designation': manager.designation,
            'department': manager.department,
        }
        return JsonResponse(data)
    
    elif request.method == 'POST':
        try:
            manager.staffid = request.POST.get('staffid', manager.staffid)
            manager.name = request.POST.get('name', manager.name)
            manager.email = request.POST.get('email', manager.email)
            manager.designation = request.POST.get('designation', manager.designation)
            manager.department = request.POST.get('department', manager.department)
            manager.modified_by = request.user
            manager.save()
            return JsonResponse({'success': True, 'message': 'Manager updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)