from django.shortcuts import render, redirect, get_object_or_404, reverse, Http404
from django.core.paginator import Paginator
from .models import Cash, Balance, Project
from .forms import CashForm
from utils.excel_exporter import export_to_excel
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone  # <-- Add this import
import decimal
from django.db.models import Sum
from Olivia.constants import HR_TABS
from django.urls import reverse


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

def hr_staff_hiring_eval(request):
    return _render_template(request, 'staff_hiring_evaluation')

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
        "VAT", "Import Duty", "Discount", "Total", "Project", "Submitted Date"
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
            str(c.project_name) if c.project_name else "",  # Convert Project object to string
            c.submitted_date.strftime("%Y-%m-%d") if c.submitted_date else "",
            # c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else "",
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
                amount=new_amount
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
                project_name=project_instance
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