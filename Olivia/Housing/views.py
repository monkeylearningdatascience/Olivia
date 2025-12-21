import pandas as pd
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, Http404, HttpResponseBadRequest, HttpResponse
from django.db import transaction, connection
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from utils.excel_exporter import export_to_excel
from django.contrib import messages
from django_countries import countries
from datetime import datetime
import logging


# NOTE: Ensure these imports are correct based on your project structure
from Olivia.constants import HOUSING_TABS
from Housing.models import Unit, CompanyGroup, UserCompany, HousingUser


# =======================================================
# HELPERS
# =======================================================

def _calculate_unit_location(request_data):
    """Helper function to calculate unit_location."""
    area = request_data.get("area", "")
    block = request_data.get("block", "")
    building = request_data.get("building", "")
    # Note: request_data should be a dict-like object (like request.POST)
    floor = request_data.get("floor", "") 
    
    # Calculate unit_location (e.g., Area-Block-Building-Floor)
    location_parts = [area, block, building, floor]
    # Filter out empty strings and join
    unit_location = '-'.join(filter(None, location_parts))
    return unit_location

def _get_auditing_user(request):
    """Helper to safely get the username for auditing."""
    if request.user.is_authenticated:
        return request.user.username
    # If the user is not authenticated, return a placeholder (should be handled by login_required)
    return "SYSTEM/ANONYMOUS" 

# =======================================================
# GENERAL VIEWS
# =======================================================

def housing_home(request):
    return render(request, "housing/home.html", {"tabs": HOUSING_TABS, "active_tab": "housing_home"})


def housing_tab_view(request, tab_name=None, **kwargs):
    if not tab_name:
        tab_name = kwargs.get('tab_name')

    tab = next((t for t in HOUSING_TABS if t['url_name'] == tab_name), None)
    if not tab:
        raise Http404(f"Tab '{tab_name}' not found.")

    template_name = f"housing/{tab_name.replace('housing_', '')}.html"

    context = {
        "tabs": HOUSING_TABS,
        "active_tab": tab_name,
    }

    # Populate the users for the "user" tab
    if tab_name == "user":
        context["users"] = HousingUser.objects.select_related("group", "company").all()

    return render(request, template_name, context)


# =======================================================
# COMPANY LIST VIEW
# =======================================================

def company_list_view(request):
    print("\n--- DEBUG: company_list_view EXECUTING ---")

    try:
        connection.close()
        connection.ensure_connection()
    except Exception as db_e:
        print(f"DEBUG: DB Connection Error (safe to ignore if minor): {db_e}")

    # Eager load the related company_group to prevent N+1 queries in the template
    all_groups = CompanyGroup.objects.all()

    try:
        # 1️⃣ Query all companies directly
        all_companies = UserCompany.objects.select_related("company_group").order_by("-id")
        print(f"DEBUG: Found {all_companies.count()} companies in DB")

        # 2️⃣ Paginate (optional)
        paginator = Paginator(all_companies, 15)
        page_number = request.GET.get("page", 1)
        try:
            company_page = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            company_page = paginator.page(1)

        # 3️⃣ Log first company for sanity
        if company_page.object_list: # Check if list is not empty
            print(f"DEBUG: First company on this page: {company_page.object_list[0].company_name}")

        # 4️⃣ Send context
        context = {
            "companies": company_page.object_list,
            "company_page": company_page,
            "company_groups": all_groups,
            "tabs": HOUSING_TABS,      
            "active_tab": "company",    
        }

    except Exception as e:
        print(f"!!! ERROR in company_list_view: {e}")
        context = {
            "companies": [],
            "company_page": None,
            "company_groups": all_groups,
            "tabs": HOUSING_TABS,
            "active_tab": "company",
        }

    return render(request, "housing/company.html", context)


# =======================================================
# LIST/SEARCH VIEW (units_list)
# =======================================================

def units_list(request):
    # Base queryset for all units, ordered by '-id' (newest first)
    units_list_queryset = Unit.objects.all().order_by("-id")
    
    # --- 1. Handle Search Logic ---
    search_query = request.GET.get('search', None)
    
    if search_query:
        # Define fields to search across
        search_fields = [
            'unit_number', 'zone', 'separable', 'wave', 'area', 
            'block', 'building', 'floor', 'room_utilization_type', 'unit_location'
        ]
        
        q_objects = Q()
        for field in search_fields:
            # Create an 'OR' condition for case-insensitive partial match
            q_objects |= Q(**{f'{field}__icontains': search_query})
        
        # Apply the combined filter to the queryset
        units_list_queryset = units_list_queryset.filter(q_objects)

    # --- 2. Handle AJAX Response (from JavaScript search) ---
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # This returns JSON data for the AJAX request
        
        # Get all necessary fields for the JavaScript to render the table row
        unit_data = list(units_list_queryset.values(
            'id', 'unit_number', 'bed_number', 'unit_location', 'zone', 
            'accomodation_type', 'wave', 'area', 'block', 'building', 'floor', 
            'occupancy_status', 'room_physical_status',
            'created_date', 'created_by', 'modified_date', 'modified_by'
            # Add all other necessary fields here
        ))
        
        # We return the raw data and let the JS render it
        return JsonResponse({'units': unit_data})


    # --- 3. Handle Initial Page Load and Pagination ---
    # Pagination is only applied when not an AJAX request
    paginator = Paginator(units_list_queryset, 15) 
    page_number = request.GET.get('page')
    units_page = paginator.get_page(page_number)

    context = {
        # Ensure HOUSING_TABS is defined or imported
        "tabs": HOUSING_TABS, 
        "active_tab": "units", 
        "units": units_page, # For iterating through the page of units
        "units_page": units_page, # For pagination links
    }
    return render(request, "housing/units.html", context)

# =======================================================
# CREATE/UPDATE/DELETE VIEWS (Unit)
# =======================================================

def create_unit(request):
    if request.method == "POST":
        # 🔒 Authentication Check
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "Authentication required."}, status=403)
            
        try:
            unit_location = _calculate_unit_location(request.POST)
            auditing_user = _get_auditing_user(request) # Get the username

            # Create and Save the Unit
            unit = Unit(
                unit_number=request.POST.get("unit_number"),
                bed_number=request.POST.get("bed_number"),
                unit_location=unit_location, 
                zone=request.POST.get("zone"),
                accomodation_type=request.POST.get("accomodation_type"),
                separable=request.POST.get("separable"),
                wave=request.POST.get("wave"),
                area=request.POST.get("area"),
                block=request.POST.get("block"),
                building=request.POST.get("building"),
                floor=request.POST.get("floor"),
                occupancy_status=request.POST.get("occupancy_status"),
                room_utilization_type=request.POST.get("room_utilization_type"),
                actual_type=request.POST.get("actual_type"),
                current_type=request.POST.get("current_type"),
                room_physical_status=request.POST.get("room_physical_status"),
                # --- AUDITING FIELD ADDED ---
                created_by=auditing_user, 
            )
            unit.save()
            
            return JsonResponse({"success": True, "action": "created"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)


def update_unit(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)

    if request.method == "GET":
        # Return JSON data for populating the modal
        data = {
            "id": unit.id,
            "unit_number": unit.unit_number,
            "bed_number": unit.bed_number,
            "unit_location": unit.unit_location,
            "zone": unit.zone,
            "accomodation_type": unit.accomodation_type,
            "separable": unit.separable,
            "wave": unit.wave,
            "area": unit.area,
            "block": unit.block,
            "building": unit.building,
            "floor": unit.floor,
            "occupancy_status": unit.occupancy_status,
            "room_utilization_type": unit.room_utilization_type,
            "actual_type": unit.actual_type,
            "current_type": unit.current_type,
            "room_physical_status": unit.room_physical_status,
        }
        return JsonResponse(data)

    elif request.method == "POST":
        # 🔒 Authentication Check
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "Authentication required."}, status=403)
            
        try:
            unit_location = _calculate_unit_location(request.POST)
            auditing_user = _get_auditing_user(request) # Get the username

            # Update the fields
            unit.unit_number = request.POST.get("unit_number")
            unit.bed_number = request.POST.get("bed_number")
            unit.unit_location = unit_location
            unit.zone = request.POST.get("zone")
            unit.accomodation_type = request.POST.get("accomodation_type")
            unit.separable = request.POST.get("separable")
            unit.wave = request.POST.get("wave")
            unit.area = request.POST.get("area")
            unit.block = request.POST.get("block")
            unit.building = request.POST.get("building")
            unit.floor = request.POST.get("floor")
            unit.occupancy_status = request.POST.get("occupancy_status")
            unit.room_utilization_type = request.POST.get("room_utilization_type")
            unit.actual_type = request.POST.get("actual_type")
            unit.current_type = request.POST.get("current_type")
            unit.room_physical_status = request.POST.get("room_physical_status")
            
            # --- AUDITING FIELD ADDED ---
            unit.modified_by = auditing_user
            
            unit.save() 
            return JsonResponse({"success": True, "action": "updated"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)


@require_POST
def delete_units(request):
    """Handles the bulk deletion of selected units based on a list of IDs."""
    
    if request.content_type != 'application/json':
        return JsonResponse({'success': False, 'error': 'Invalid content type.'}, status=400)
    
    try:
        data = json.loads(request.body)
        unit_ids = data.get('ids', [])
        
        if not unit_ids:
            return JsonResponse({'success': False, 'error': 'No unit IDs provided for deletion.'}, status=400)

        # Ensure all IDs are integers before processing
        unit_ids = [int(id) for id in unit_ids]

        # Use a transaction to ensure all or none are deleted
        with transaction.atomic():
            deleted_count, _ = Unit.objects.filter(id__in=unit_ids).delete()
        
        return JsonResponse({
            'success': True, 
            'count': deleted_count,
            'message': f'Successfully deleted {deleted_count} unit(s).'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format.'}, status=400)
    except Exception as e:
        print(f"Error during bulk unit deletion: {e}")
        return JsonResponse({'success': False, 'error': f'A server error occurred: {e}'}, status=500)

@require_POST
def import_units(request):
    """Handles the upsert (update or insert) of unit data based on unit_number."""

    if 'excel_file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded.'}, status=400)
        
    # 🔒 Authentication Check
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Authentication required for import."}, status=403)

    excel_file = request.FILES['excel_file']
    auditing_user = _get_auditing_user(request) # Get the username
    
    try:
        df = pd.read_excel(excel_file)
        
        # --- COLUMN MAPPING ---
        column_mapping = {
            'unit_number': 'unit_number',
            'bed_number': 'bed_number',
            'unit_location': 'unit_location',
            'zone': 'zone',
            'accomodation_type': 'accomodation_type', 
            'separable': 'separable',
            'wave': 'wave',
            'area': 'area',
            'block': 'block',
            'building': 'building',
            'floor': 'floor',
            'room_utilization_type': 'room_utilization_type',
            'actual_type': 'actual_type',
            'current_type': 'current_type',
            'occupancy_status': 'occupancy_status',
            'room_physical_status': 'room_physical_status',
        }

        # 1. Prepare data and collect all unit numbers from the Excel file
        imported_data = []
        imported_unit_numbers = []
        
        for index, row in df.iterrows():
            unit_data = {}
            valid_row = True
            
            # Map data
            for excel_col, model_field in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value) or value is pd.NaT:
                    unit_data[model_field] = None
                else:
                    unit_data[model_field] = value

            # Basic validation check for unit_number (required for unique key)
            if not unit_data.get('unit_number'):
                print(f"Skipping row {index}: unit_number is missing.")
                valid_row = False
            
            if valid_row:
                imported_data.append(unit_data)
                imported_unit_numbers.append(unit_data['unit_number'])

        # 2. Query existing units in the database
        existing_units_map = {
            unit.unit_number: unit for unit in Unit.objects.filter(
                unit_number__in=imported_unit_numbers
            )
        }
        
        units_to_create = []
        units_to_update = []
        
        # Fields to check for changes during update
        update_fields = [
            'bed_number', 'unit_location', 'zone', 'accomodation_type', 'wave', 
            'area', 'block', 'building', 'floor', 'room_utilization_type',
            'occupancy_status', 'room_physical_status', 'actual_type', 'current_type',
            'separable' 
        ]
        
        # 3. Categorize units for create or update
        for data in imported_data:
            unit_number = data['unit_number']
            
            if unit_number in existing_units_map:
                # Update logic
                existing_unit = existing_units_map[unit_number]
                has_changed = False
                
                # Check for changes in any relevant field
                for field in update_fields:
                    imported_value = data.get(field)
                    current_value = getattr(existing_unit, field)
                    
                    imported_str = str(imported_value).strip() if imported_value is not None else None
                    current_str = str(current_value).strip() if current_value is not None else None

                    # Set new value only if it's different
                    if imported_str != current_str:
                        setattr(existing_unit, field, imported_value)
                        has_changed = True
                
                if has_changed:
                    # --- AUDITING FIELD: Set modified_by for update (Correct) ---
                    existing_unit.modified_by = auditing_user
                    units_to_update.append(existing_unit)
                
            else:
                # Create logic (Unit number is new)
                try:
                    # --- AUDITING FIELD: Set created_by for creation (Correct) ---
                    data['created_by'] = auditing_user
                    
                    # Attempt to create the Unit object to trigger model validation
                    new_unit = Unit(**data)
                    units_to_create.append(new_unit)
                except Exception as e:
                    print(f"Skipping unit {unit_number} due to validation error: {e}")

        
        # 4. Perform bulk operations within a transaction
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            # A. Bulk Create New Units
            if units_to_create:
                created_objects = Unit.objects.bulk_create(units_to_create)
                created_count = len(created_objects)

            # B. Bulk Update Existing Units
            if units_to_update:
                Unit.objects.bulk_update(
                    units_to_update, 
                    # Note: We must include all fields we manually updated, including the auditing fields
                    fields=update_fields + ['modified_by', 'modified_date'] 
                )
                updated_count = len(units_to_update)

        total_processed = created_count + updated_count

        return JsonResponse({
            'success': True, 
            'count': total_processed,
            'message': f'Import successful! Created {created_count} new records and updated {updated_count} existing records.'
        })

    except Exception as e:
        print(f"--- CRITICAL SERVER ERROR DURING IMPORT ---: {e}")
        return JsonResponse({'success': False, 'error': f'A critical server error occurred during processing: {e}'}, status=500)
    
# =======================================================
# EXPORT VIEW (Unit)
# =======================================================

def export_units(request):
    """
    Fetches all Unit records, extracts the required fields, and exports them 
    to an Excel file using the shared utility function.
    """
    # 1. Fetch the queryset (all units, ordered by unit_number)
    queryset = Unit.objects.all().order_by('unit_number')

    # 2. Define the header row for the Excel file
    headers = [
        "Unit Number", "Beds", "Location", "Zone", "Accommodation Type", 
        "Separable", "Wave", "Area", "Block", "Building", "Floor", "Room Utilization Type",
        "Actual Type", "Current Type", "Occupancy Status", "Physical Status",
        # ✅ ADDED: Auditing fields to the Excel headers
        "Created Date", "Created By", "Modified Date", "Modified By"
    ]

    # 3. Define the function to extract data from a single Unit object (u)
    def row_data(u):
        created_date_str = u.created_date.strftime("%Y-%m-%d %H:%M:%S") if u.created_date else ""
        modified_date_str = u.modified_date.strftime("%Y-%m-%d %H:%M:%S") if u.modified_date else ""
        return [
            u.unit_number,
            u.bed_number,
            u.unit_location or "",
            u.zone or "",
            u.accomodation_type or "",
            str(u.separable) if u.separable is not None else "", 
            u.wave or "",
            u.area or "",
            u.block or "",
            u.building or "",
            u.floor or "",
            u.room_utilization_type or "",
            u.actual_type or "",
            u.current_type or "",
            u.occupancy_status or "",
            u.room_physical_status or "",
            # ✅ ADDED: Auditing field values
            created_date_str,
            u.created_by or "",
            modified_date_str,
            u.modified_by or "",
        ]

    # 4. Call the generic export utility with the custom settings
    return export_to_excel(
        queryset, 
        headers, 
        row_data, 
        file_prefix="roomdb"
    )

# =======================================================
# COMPANY API VIEWS (AUDITING FIXES APPLIED HERE)
# =======================================================
@csrf_exempt
def create_company_api(request):
    if request.method == 'POST':
        # 🔒 Authentication Check: Ensure user is logged in
        if not request.user.is_authenticated:
             return JsonResponse({"error": "Authentication required."}, status=403)
             
        auditing_user = _get_auditing_user(request) # Get username

        try:
            data = json.loads(request.body)
            
            # --- Field Retrieval and Validation ---
            group_id = data.get('company_group_id')
            group = None
            if group_id:
                group = get_object_or_404(CompanyGroup, id=group_id)

            # --- Create Object ---
            new_company = UserCompany.objects.create(
                company_name=data.get('company_name'),
                company_group=group, 
                company_details=data.get('company_details'),
                cr_number=data.get('cr_number'),
                vat_number=data.get('vat_number'),
                address_text=data.get('address_text'),
                contact_name=data.get('contact_name'),
                email_address=data.get('email_address'),
                mobile=data.get('mobile'),
                phone=data.get('phone'),
                # ✅ AUDITING FIX: Set created_by on creation
                created_by=auditing_user, 
            )
            
            # --- Prepare Response Data ---
            response_data = {
                'id': new_company.id,
                'company_name': new_company.company_name,
                'company_group_id': new_company.company_group.id if new_company.company_group else None,
                'company_group_name': new_company.company_group.company_name if new_company.company_group else '-',
                'cr_number': new_company.cr_number,
                'vat_number': new_company.vat_number,
                'contact_name': new_company.contact_name,
                'email_address': new_company.email_address,
                'mobile': new_company.mobile,
                'phone': new_company.phone,
                'company_details': new_company.company_details,
                # Include auditing fields in the response for frontend refresh (optional but helpful)
                'created_by': new_company.created_by,
                'modified_by': new_company.modified_by,
            }
            
            return JsonResponse(response_data, status=201)

        except json.JSONDecodeError:
            return HttpResponseBadRequest(JsonResponse({'error': 'Invalid JSON format.'}, status=400))
        except Exception as e:
            return JsonResponse({'error': f'Data validation error: {e}'}, status=400)
    
    return JsonResponse({'error': 'Only POST method allowed.'}, status=405)

@csrf_exempt
def create_company_group_api(request):
    if request.method == 'POST':
        # NOTE: If you want auditing on CompanyGroup, you need to add the checks here too.
        try:
            data = json.loads(request.body)
            company_name = data.get('company_name', '').strip()
            
            # Assuming CompanyGroup is simple and doesn't require created_by/modified_by logic in the view
            # If it did, you would add the auditing_user assignment here (e.g., new_group.created_by = auditing_user)

            if not company_name:
                return JsonResponse({'error': 'Name required.'}, status=400)

            new_group = CompanyGroup.objects.create(company_name=company_name)

            response_data = {'id': new_group.id, 'company_name': new_group.company_name}
            return JsonResponse(response_data, status=201)

        except Exception as e:
            print(f"DATABASE SAVE ERROR: {e}") 
            return JsonResponse({'error': f'Failed to save group: {e}'}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def list_company_groups_api(request):
    """Handles AJAX GET request to fetch all CompanyGroup records."""
    if request.method == 'GET':
        groups = CompanyGroup.objects.all().order_by('company_name')
        groups_list = list(groups.values('id', 'company_name'))
        return JsonResponse(groups_list, safe=False)
    
    return JsonResponse({'error': 'Only GET method allowed.'}, status=405)

@csrf_exempt
@require_http_methods(["PUT"])
def company_update_view(request, pk):
    """
    Handles PUT request to update an existing UserCompany record.
    """
    try:
        # 🔒 Authentication Check: Ensure user is logged in
        if not request.user.is_authenticated:
             return JsonResponse({"error": "Authentication required."}, status=403)
             
        auditing_user = _get_auditing_user(request) # Get username
        
        company = get_object_or_404(UserCompany, pk=pk)
        data = json.loads(request.body)

        # 1. Update simple fields
        company.company_name = data.get("company_name", company.company_name)
        company.company_details = data.get("company_details", company.company_details)
        company.cr_number = data.get("cr_number", company.cr_number)
        company.vat_number = data.get("vat_number", company.vat_number)
        company.contact_name = data.get("contact_name", company.contact_name)
        company.email_address = data.get("email_address", company.email_address)
        company.mobile = data.get("mobile", company.mobile)
        company.phone = data.get("phone", company.phone)
        company.address_text = data.get("address_text", company.address_text)

        # 2. Handle the Foreign Key update
        group_id = data.get('company_group_id')
        
        if group_id:
            company.company_group = get_object_or_404(CompanyGroup, id=group_id)
        else:
            company.company_group = None
            
        # ✅ AUDITING FIX: Set modified_by on update
        company.modified_by = auditing_user
            
        company.save()
        
        # 3. Prepare response data for the frontend table update
        response_data = {
            'id': company.id,
            'company_name': company.company_name,
            'company_group_id': company.company_group.id if company.company_group else None,
            'company_group_name': company.company_group.company_name if company.company_group else '-',
            'cr_number': company.cr_number,
            'vat_number': company.vat_number,
            'contact_name': company.contact_name,
            'email_address': company.email_address,
            'mobile': company.mobile,
            'phone': company.phone,
            'company_details': company.company_details,
            'address_text': company.address_text,
            # Include auditing fields in the response
            'created_by': company.created_by,
            'modified_by': company.modified_by,
        }

        return JsonResponse(response_data, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except UserCompany.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)
    except Exception as e:
        print(f"Update error: {e}")
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)


@require_POST # Ensures only POST requests are allowed
def company_delete_view(request):
    try:
        # 1. Parse JSON data
        data = json.loads(request.body)
        ids = data.get("ids", [])
        
        # 2. Validate IDs exist
        if not ids:
            return JsonResponse({"success": False, "error": "No items selected"}, status=400)

        # 3. Atomic Delete
        with transaction.atomic():
            deleted_count, _ = UserCompany.objects.filter(id__in=ids).delete()
        
        return JsonResponse({"success": True, "message": f"Deleted {deleted_count} companies."})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# =======================================================
# COMPANY EXPORT VIEW
# =======================================================

def export_companies(request):
    """
    Fetches all UserCompany records, extracts the required fields, and exports them 
    to an Excel file using the shared utility function.
    """
    try:
        queryset = UserCompany.objects.select_related('company_group').order_by('company_name')

        headers = [
            "Company Name", "Group", "CR Number", "VAT Number", "Contact Name", 
            "Email Address", "Mobile", "Phone", "Address", "Details", 
            "Created Date", "Created By", "Modified Date", "Modified By"
        ]

        def row_data(c):
            group_name = c.company_group.company_name if c.company_group else ""
            created_date_str = c.created_date.strftime("%Y-%m-%d %H:%M") if c.created_date else ""
            modified_date_str = c.modified_date.strftime("%Y-%m-%d %H:%M") if c.modified_date else ""

            return [
                c.company_name or "",
                group_name,
                c.cr_number or "",
                c.vat_number or "",
                c.contact_name or "",
                c.email_address or "",
                c.mobile or "",
                c.phone or "",
                c.address_text or "",
                c.company_details or "",
                created_date_str,
                c.created_by or "",
                modified_date_str,
                c.modified_by or "",
            ]

        return export_to_excel(
            queryset, 
            headers, 
            row_data, 
            file_prefix="companies"
        )
    
    except Exception as e:
        print(f"Error during company export: {e}")
        return HttpResponse(f"An error occurred during export: {e}", status=500)
    
# =======================================================
# USER VIEW
# =======================================================

# -------------------------------
# PAGE VIEW: Users Table
# -------------------------------
def users_page(request):
    try:
        # 🌟 CRITICAL DEBUG POINT 🌟 This line MUST run now.
        print("\n!!! VIEW ENTERED: users_page has been called !!!") 
        
        # 1. Fetch the full queryset
        users_qs = HousingUser.objects.all().order_by('-id') 
        
        # 2. Create the Paginator
        paginator = Paginator(users_qs, 15) # 15 users per page
        page_number = request.GET.get('page', 1) 
        
        try:
            user_page = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            user_page = paginator.page(paginator.num_pages)
        
        # 3. Handle 'countries' SAFELY
        # Define a safe default list
        countries_list = []
        
        # Only attempt to process 'countries' if it's found in the global scope 
        # (this prevents a NameError from crashing the view)
        if 'countries' in globals():
            try:
                # Process the list if it exists
                countries_list = [{'code': c.code, 'name': c.name} for c in globals()['countries']]
            except Exception as e:
                # Catch any errors during list comprehension (e.g., if objects lack .code)
                print(f"WARNING: Error processing 'countries': {e}")
                countries_list = []

        # 🌟 DATA DEBUG BLOCK 🌟 
        print("\n--- USER PAGE DATA DEBUG ---")
        total_db_count = users_qs.count()
        page_items_length = len(user_page.object_list)
        print(f"DB Count from QuerySet: {total_db_count}") 
        print(f"Paginator Total Count: {user_page.paginator.count}") 
        print(f"Items on Current Page: {page_items_length}")
        print("--- DEBUG END ---")

        # 4. Define Context
        context = {
            'users': user_page, # The full Page object
            'groups': CompanyGroup.objects.all(),
            'countries': countries_list, # Use the safely defined list
            'active_tab': 'user',
        }

        return render(request, 'housing/user.html', context)

    except Exception as e:
        # If an error still occurs, this will print the traceback
        print(f"\n!!! UNEXPECTED EXCEPTION CAUGHT: {e} !!!") 
        # Reraise the error so you can see the full traceback in the terminal
        raise

# -------------------------------
# API: Create User
# -------------------------------
@csrf_exempt
def create_user_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed.'}, status=405)

    try:
        data = json.loads(request.body)

        # Convert dob string to date
        dob_str = data.get('dob')
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None

        # Get related group/company
        group = get_object_or_404(CompanyGroup, id=data.get('group_id')) if data.get('group_id') else None
        company = get_object_or_404(UserCompany, id=data.get('company_id')) if data.get('company_id') else None

        # Create user
        new_user = HousingUser.objects.create(
            username=data.get('username'),
            group=group,
            company=company,
            government_id=data.get('government_id'),
            id_type=data.get('id_type'),
            neom_id=data.get('neom_id'),
            dob=dob,
            mobile=data.get('mobile'),
            email=data.get('email'),
            nationality=data.get('nationality'),
            religion=data.get('religion'),
            status=data.get('status', 'Active'),
        )

        response_data = {
            'id': new_user.id,
            'username': new_user.username,
            'group_id': new_user.group.id if new_user.group else None,
            'group_name': new_user.group.company_name if new_user.group else '-',
            'company_id': new_user.company.id if new_user.company else None,
            'company_name': new_user.company.company_name if new_user.company else '-',
            'government_id': new_user.government_id,
            'id_type': new_user.id_type,
            'neom_id': new_user.neom_id,
            'dob': new_user.dob.isoformat() if new_user.dob else '',
            'mobile': new_user.mobile,
            'email': new_user.email,
            'nationality': new_user.nationality.name if new_user.nationality else '', 
            'religion': new_user.religion,
            'status': new_user.status,
        }

        return JsonResponse(response_data, status=201)

    except Exception as e:
        return JsonResponse({'error': f'Data validation error: {e}'}, status=400)


# -------------------------------
# API: Update User
# -------------------------------
@csrf_exempt
@require_http_methods(["PUT"])
def user_update_view(request, pk):
    try:
        user = get_object_or_404(HousingUser, pk=pk)
        data = json.loads(request.body)

        nationality_name = data.get('nationality')  # e.g. "SA"

        user.username = data.get('username', user.username)
        user.group = get_object_or_404(CompanyGroup, id=data['group_id']) if data.get('group_id') else None
        user.company = get_object_or_404(UserCompany, id=data['company_id']) if data.get('company_id') else None
        user.government_id = data.get('government_id', user.government_id)
        user.id_type = data.get('id_type', user.id_type)
        user.neom_id = data.get('neom_id', user.neom_id)
        user.dob = datetime.strptime(data['dob'], "%Y-%m-%d").date() if data.get('dob') else user.dob
        user.mobile = data.get('mobile', user.mobile)
        user.email = data.get('email', user.email)
        user.nationality = nationality_name if nationality_name else None
        user.religion = data.get('religion', user.religion)
        user.status = data.get('status', user.status)

        user.save()

        response_data = {
            'id': user.id,
            'username': user.username,
            'group_id': user.group.id if user.group else None,
            'group_name': user.group.company_name if user.group else '-',
            'company_id': user.company.id if user.company else None,
            'company_name': user.company.company_name if user.company else '-',
            'government_id': user.government_id,
            'id_type': user.id_type,
            'neom_id': user.neom_id,
            'dob': user.dob.isoformat() if user.dob else '',
            'mobile': user.mobile,
            'email': user.email,
            'nationality': user.nationality.name if user.nationality else '',
            'religion': user.religion,
            'status': user.status,
        }
        return JsonResponse(response_data, status=200)

    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {e}"}, status=500)


# -------------------------------
# API: Delete Users
# -------------------------------
@require_POST
def user_delete_view(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            return JsonResponse({"success": False, "error": "No items selected"}, status=400)

        with transaction.atomic():
            deleted_count, _ = HousingUser.objects.filter(id__in=ids).delete()

        return JsonResponse({"success": True, "message": f"Deleted {deleted_count} user(s)."})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# -------------------------------
# API: List Groups
# -------------------------------
def list_company_groups_api(request):
    groups = CompanyGroup.objects.all().order_by('company_name')
    groups_list = list(groups.values('id', 'company_name'))
    return JsonResponse(groups_list, safe=False)


# -------------------------------
# API: List Companies
# -------------------------------
def list_companies_api(request):
    companies = UserCompany.objects.all().order_by('company_name')
    companies_list = list(companies.values('id', 'company_name'))
    return JsonResponse(companies_list, safe=False)


# -------------------------------
# API: Get Companies by Group
# -------------------------------
def get_companies(request):
    group_id = request.GET.get('group_id')
    if not group_id:
        return JsonResponse({'error': 'No group_id provided'}, status=400)

    try:
        group_id = int(group_id)
        companies_qs = UserCompany.objects.filter(company_group_id=group_id).order_by('company_name')
        # remove duplicates
        seen = set()
        companies = []
        for c in companies_qs:
            if c.company_name not in seen:
                companies.append({'id': c.id, 'company_name': c.company_name})
                seen.add(c.company_name)
        return JsonResponse(companies, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# -------------------------------
# API: Save User from POST Form (optional)
# -------------------------------
def save_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed."}, status=405)

    user_id = request.POST.get("user_id")
    dob_str = request.POST.get("dob")
    dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None

    user = HousingUser.objects.get(id=user_id) if user_id else HousingUser()

    # Get nationality code string
    nationality_name = request.POST.get("nationality")  # e.g. "SA"
    
    # Assign values
    user.username = request.POST.get("username")
    user.group_id = request.POST.get("group_id") or None
    user.company_id = request.POST.get("company_id") or None
    user.government_id = request.POST.get("government_id")
    user.id_type = request.POST.get("id_type")
    user.neom_id = request.POST.get("neom_id")
    user.mobile = request.POST.get("mobile")
    user.email = request.POST.get("email")
    user.nationality = nationality_name if nationality_name else None
    user.religion = request.POST.get("religion")
    user.status = request.POST.get("status")
    user.dob = dob

    user.save()

    # JSON-safe response
    response_data = {
        "id": user.id,
        "username": user.username,
        "group_id": user.group.id if user.group else None,
        "group_name": user.group.company_name if user.group else "",
        "company_id": user.company.id if user.company else None,
        "company_name": user.company.company_name if user.company else "",
        "government_id": user.government_id,
        "id_type": user.id_type,
        "neom_id": user.neom_id,
        "dob": user.dob.isoformat() if user.dob else "",
        "mobile": user.mobile,
        "email": user.email,
        'nationality': user.nationality.name if user.nationality else '',
        "religion": user.religion,
        "status": user.status,
    }

    return JsonResponse(response_data, status=200)

# =======================================================
# EXPORT VIEW (HousingUser)
# =======================================================

def export_users(request):
    """
    Export HousingUser records to Excel.
    """
    try:
        queryset = HousingUser.objects.select_related(
            'group', 'company'
        ).order_by('username')

        headers = [
            "Username",
            "Government ID",
            "ID Type",
            "NEOM ID",
            "Date of Birth",
            "Mobile",
            "Email",
            "Nationality",
            "Religion",
            "Status",
            "Group",
            "Company",
        ]

        def row_data(u):
            return [
                u.username or "",
                u.government_id or "",
                u.id_type or "",
                u.neom_id or "",
                u.dob.strftime("%Y-%m-%d") if u.dob else "",
                u.mobile or "",
                u.email or "",
                u.nationality.name if u.nationality else "",
                u.religion or "",
                u.status or "",
                u.group.company_name if u.group else "",
                u.company.company_name if u.company else "",
            ]

        return export_to_excel(
            queryset,
            headers,
            row_data,
            file_prefix="housing_users"
        )

    except Exception as e:
        print(f"Error during user export: {e}")
        return HttpResponse(f"An error occurred during export: {e}", status=500)

