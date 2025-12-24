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
from Housing.models import Unit, CompanyGroup, UserCompany, HousingUser, UnitAllocation, UnitAssignment, Reservation, CheckInCheckOut


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
        created_date_str = u.created_date.strftime("%m/%d/%Y %H:%M:%S") if u.created_date else ""
        modified_date_str = u.modified_date.strftime("%m/%d/%Y %H:%M:%S") if u.modified_date else ""
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
                created_by=request.user,
                modified_by=request.user
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

            new_group = CompanyGroup.objects.create(
                company_name=company_name,
                created_by=request.user,
                modified_by=request.user
            )

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
@require_http_methods(["GET", "PUT"])
def company_update_view(request, pk):
    """
    Handles GET request to fetch company details and PUT request to update an existing UserCompany record.
    """
    try:
        # 🔒 Authentication Check: Ensure user is logged in
        if not request.user.is_authenticated:
             return JsonResponse({"error": "Authentication required."}, status=403)
             
        company = get_object_or_404(UserCompany, pk=pk)
        
        # Handle GET request - return company details
        if request.method == 'GET':
            response_data = {
                'id': company.id,
                'company_name': company.company_name,
                'company_group_id': company.company_group.id if company.company_group else None,
                'company_group_name': company.company_group.company_name if company.company_group else '-',
                'cr_number': company.cr_number or '',
                'vat_number': company.vat_number or '',
                'contact_name': company.contact_name or '',
                'email_address': company.email_address or '',
                'mobile': company.mobile or '',
                'phone': company.phone or '',
                'company_details': company.company_details or '',
                'address_text': company.address_text or '',
            }
            return JsonResponse(response_data)
        
        # Handle PUT request - update company
        auditing_user = _get_auditing_user(request) # Get username
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
            created_date_str = c.created_date.strftime("%m/%d/%Y %H:%M") if c.created_date else ""
            modified_date_str = c.modified_date.strftime("%m/%d/%Y %H:%M") if c.modified_date else ""

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
            created_by=request.user,
            modified_by=request.user,
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
        user.modified_by = request.user

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
                u.dob.strftime("%m/%d/%Y") if u.dob else "",
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


# =======================================================
# ALLOCATION VIEWS
# =======================================================

def allocation_list_view(request):
    """List all unit allocations with pagination"""
    query = request.GET.get('q', '')
    allocations = UnitAllocation.objects.select_related('company_group', 'company').all()
    
    if query:
        allocations = allocations.filter(
            Q(uua_number__icontains=query) |
            Q(company__company_name__icontains=query) |
            Q(company_group__company_name__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(allocations, 25)
    page = request.GET.get('page', 1)
    
    try:
        allocations_page = paginator.page(page)
    except PageNotAnInteger:
        allocations_page = paginator.page(1)
    except EmptyPage:
        allocations_page = paginator.page(paginator.num_pages)
    
    # Get company groups and companies for the modal
    company_groups = CompanyGroup.objects.all()
    companies = UserCompany.objects.select_related('company_group').all()
    
    context = {
        'tabs': HOUSING_TABS,
        'active_tab': 'allocation',
        'allocations': allocations_page,
        'company_groups': company_groups,
        'companies': companies,
        'query': query,
    }
    
    return render(request, 'housing/allocation.html', context)


@require_http_methods(["POST"])
def allocation_create_view(request):
    """Create a new unit allocation"""
    try:
        allocation_type = request.POST.get('allocation_type')
        uua_number = request.POST.get('uua_number')
        company_group_id = request.POST.get('company_group')
        company_id = request.POST.get('company')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        a_rooms_beds = request.POST.get('a_rooms_beds', '')
        b_rooms_beds = request.POST.get('b_rooms_beds', '')
        c_rooms_beds = request.POST.get('c_rooms_beds', '')
        d_rooms_beds = request.POST.get('d_rooms_beds', '')
        allocation_status = request.POST.get('allocation_status', 'Active')
        security_deposit = request.POST.get('security_deposit') or None
        advance_payment = request.POST.get('advance_payment') or None
        
        # Create the allocation
        allocation = UnitAllocation(
            allocation_type=allocation_type,
            uua_number=uua_number,
            company_group_id=company_group_id,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            a_rooms_beds=a_rooms_beds,
            b_rooms_beds=b_rooms_beds,
            c_rooms_beds=c_rooms_beds,
            d_rooms_beds=d_rooms_beds,
            allocation_status=allocation_status,
            security_deposit=security_deposit,
            advance_payment=advance_payment,
            created_by=request.user,
            modified_by=request.user,
        )
        allocation.save()
        
        messages.success(request, f'Allocation {uua_number} created successfully!')
        return JsonResponse({'success': True, 'message': 'Allocation created successfully'})
        
    except IntegrityError as e:
        return JsonResponse({'success': False, 'error': 'UUA Number already exists'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET", "POST"])
def allocation_update_view(request, pk):
    """Update an existing unit allocation"""
    allocation = get_object_or_404(UnitAllocation, pk=pk)
    
    if request.method == 'GET':
        data = {
            'id': allocation.id,
            'allocation_type': allocation.allocation_type,
            'uua_number': allocation.uua_number,
            'company_group': allocation.company_group_id,
            'company': allocation.company_id,
            'start_date': allocation.start_date.strftime('%m/%d/%Y'),
            'end_date': allocation.end_date.strftime('%m/%d/%Y'),
            'a_rooms_beds': allocation.a_rooms_beds,
            'b_rooms_beds': allocation.b_rooms_beds,
            'c_rooms_beds': allocation.c_rooms_beds,
            'd_rooms_beds': allocation.d_rooms_beds,
            'allocation_status': allocation.allocation_status,
            'security_deposit': str(allocation.security_deposit) if allocation.security_deposit else '',
            'advance_payment': str(allocation.advance_payment) if allocation.advance_payment else '',
        }
        return JsonResponse(data)
    
    elif request.method == 'POST':
        try:
            allocation.allocation_type = request.POST.get('allocation_type')
            allocation.uua_number = request.POST.get('uua_number')
            allocation.company_group_id = request.POST.get('company_group')
            allocation.company_id = request.POST.get('company')
            allocation.start_date = request.POST.get('start_date')
            allocation.end_date = request.POST.get('end_date')
            allocation.a_rooms_beds = request.POST.get('a_rooms_beds', '')
            allocation.b_rooms_beds = request.POST.get('b_rooms_beds', '')
            allocation.c_rooms_beds = request.POST.get('c_rooms_beds', '')
            allocation.d_rooms_beds = request.POST.get('d_rooms_beds', '')
            allocation.allocation_status = request.POST.get('allocation_status', 'Active')
            allocation.security_deposit = request.POST.get('security_deposit') or None
            allocation.advance_payment = request.POST.get('advance_payment') or None
            allocation.modified_by = request.user
            
            allocation.save()
            
            messages.success(request, f'Allocation {allocation.uua_number} updated successfully!')
            return JsonResponse({'success': True, 'message': 'Allocation updated successfully'})
            
        except IntegrityError as e:
            return JsonResponse({'success': False, 'error': 'UUA Number already exists'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def allocation_delete_view(request):
    """Delete a unit allocation"""
    try:
        allocation_id = request.POST.get('allocation_id')
        allocation = get_object_or_404(UnitAllocation, pk=allocation_id)
        uua_number = allocation.uua_number
        allocation.delete()
        
        messages.success(request, f'Allocation {uua_number} deleted successfully!')
        return JsonResponse({'success': True, 'message': 'Allocation deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def allocation_export_view(request):
    """Export allocations to Excel"""
    try:
        query = request.GET.get('q', '')
        queryset = UnitAllocation.objects.select_related('company_group', 'company', 'created_by', 'modified_by').all()
        
        if query:
            queryset = queryset.filter(
                Q(uua_number__icontains=query) |
                Q(company__company_name__icontains=query) |
                Q(company_group__company_name__icontains=query)
            )
        
        headers = [
            'UUA Number',
            'Allocation Type',
            'Company Group',
            'Company',
            'Start Date',
            'End Date',
            'A (Rooms/Beds)',
            'B (Rooms/Beds)',
            'C (Rooms/Beds)',
            'D (Rooms/Beds)',
            'Total (Rooms/Beds)',
            'Allocation Status',
            'Security Deposit',
            'Advance Payment',
            'Created By',
            'Created Date',
            'Modified By',
            'Modified Date',
        ]
        
        def row_data(a):
            return [
                a.uua_number or "",
                a.allocation_type or "",
                a.company_group.company_name if a.company_group else "",
                a.company.company_name if a.company else "",
                a.start_date.strftime("%m/%d/%Y") if a.start_date else "",
                a.end_date.strftime("%m/%d/%Y") if a.end_date else "",
                a.a_rooms_beds or "",
                a.b_rooms_beds or "",
                a.c_rooms_beds or "",
                a.d_rooms_beds or "",
                a.total_rooms_beds or "",
                a.allocation_status or "",
                str(a.security_deposit) if a.security_deposit else "",
                str(a.advance_payment) if a.advance_payment else "",
                a.created_by.username if a.created_by else "",
                a.created_date.strftime("%m/%d/%Y %H:%M:%S") if a.created_date else "",
                a.modified_by.username if a.modified_by else "",
                a.modified_date.strftime("%m/%d/%Y %H:%M:%S") if a.modified_date else "",
            ]
        
        return export_to_excel(
            queryset,
            headers,
            row_data,
            file_prefix="unit_allocations"
        )
        
    except Exception as e:
        print(f"Error during allocation export: {e}")
        return HttpResponse(f"An error occurred during export: {e}", status=500)


# =======================================================
# ASSIGNMENT VIEWS
# =======================================================

def assignment_list_view(request):
    """List all unit assignments with pagination"""
    query = request.GET.get('q', '')
    assignments = UnitAssignment.objects.select_related(
        'allocation__company_group', 
        'allocation__company', 
        'unit'
    ).all()
    
    if query:
        assignments = assignments.filter(
            Q(allocation__uua_number__icontains=query) |
            Q(unit__unit_number__icontains=query) |
            Q(accommodation_type__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(assignments, 25)
    page = request.GET.get('page', 1)
    
    try:
        assignments_page = paginator.page(page)
    except PageNotAnInteger:
        assignments_page = paginator.page(1)
    except EmptyPage:
        assignments_page = paginator.page(paginator.num_pages)
    
    # Get only essential data for the modal - defer heavy queries
    company_groups = CompanyGroup.objects.all()
    # Only load companies and units when modal is opened, not on page load
    companies = UserCompany.objects.select_related('company_group').only('id', 'company_name', 'company_group_id')
    units = Unit.objects.filter(occupancy_status='Vacant Ready').only('id', 'unit_number', 'accomodation_type', 'zone', 'area', 'block', 'building', 'floor')
    
    context = {
        'tabs': HOUSING_TABS,
        'active_tab': 'assigning',
        'assignments': assignments_page,
        'company_groups': company_groups,
        'companies': companies,
        'units': units,
        'query': query,
    }
    
    return render(request, 'housing/assigning.html', context)


@require_http_methods(["POST"])
def assignment_create_view(request):
    """Create a new unit assignment"""
    try:
        allocation_id = request.POST.get('allocationId')
        unit_id = request.POST.get('unit')
        accommodation_type = request.POST.get('accommodationType')
        
        if not allocation_id:
            return JsonResponse({'success': False, 'error': 'Allocation is required'}, status=400)
        
        # Get the allocation
        allocation = UnitAllocation.objects.get(id=allocation_id)
        
        # Check if the accommodation type is available in the allocation
        available_beds = 0
        field_name = f"{accommodation_type.lower()}_rooms_beds"
        
        if hasattr(allocation, field_name):
            rooms_beds_value = getattr(allocation, field_name)
            if rooms_beds_value:
                # Parse "2/4" format to get number of beds (second number)
                try:
                    available_beds = int(rooms_beds_value.split('/')[1])
                except:
                    available_beds = 0
        
        if available_beds == 0:
            return JsonResponse({
                'success': False, 
                'error': f'No {accommodation_type} type beds available in this allocation'
            }, status=400)
        
        # Count existing assignments for this allocation and accommodation type
        existing_count = UnitAssignment.objects.filter(
            allocation_id=allocation_id,
            accommodation_type=accommodation_type
        ).count()
        
        if existing_count >= available_beds:
            return JsonResponse({
                'success': False, 
                'error': f'All {accommodation_type} type beds ({available_beds}) have been assigned for this allocation'
            }, status=400)
        
        # Create the assignment
        assignment = UnitAssignment(
            allocation_id=allocation_id,
            unit_id=unit_id,
            accommodation_type=accommodation_type,
            created_by=request.user,
            modified_by=request.user,
        )
        assignment.save()
        
        # Update unit occupancy_status to 'Assigned'
        try:
            unit = Unit.objects.get(id=unit_id)
            unit.occupancy_status = 'Assigned'
            unit.save()
        except Unit.DoesNotExist:
            pass
        
        # Check if all room types are fully assigned
        def get_bed_count(alloc, room_type):
            field = f"{room_type.lower()}_rooms_beds"
            if hasattr(alloc, field):
                value = getattr(alloc, field)
                if value:
                    try:
                        return int(value.split('/')[1])  # Get beds (second number)
                    except:
                        return 0
            return 0
        
        all_assigned = True
        for room_type in ['A', 'B', 'C', 'D']:
            required = get_bed_count(allocation, room_type)
            if required > 0:
                assigned = UnitAssignment.objects.filter(
                    allocation_id=allocation_id,
                    accommodation_type=room_type
                ).count()
                if assigned < required:
                    all_assigned = False
                    break
        
        # Update allocation remarks if all assigned
        if all_assigned:
            allocation.remarks = 'Done'
            allocation.save()
        
        messages.success(request, 'Unit assignment created successfully!')
        return JsonResponse({'success': True, 'message': 'Assignment created successfully'})
        
    except IntegrityError as e:
        return JsonResponse({'success': False, 'error': 'This unit is already assigned to this allocation with this accommodation type'}, status=400)
    except UnitAllocation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Allocation not found'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET", "POST"])
def assignment_update_view(request, pk):
    """Update an existing unit assignment"""
    assignment = get_object_or_404(UnitAssignment, pk=pk)
    
    if request.method == 'GET':
        # Return data for populating the edit modal
        allocation = assignment.allocation
        unit = assignment.unit
        
        data = {
            'id': assignment.id,
            'allocation_id': allocation.id,
            'company_group_id': allocation.company_group_id,
            'company_id': allocation.company_id,
            'allocation_type': allocation.allocation_type,
            'uua_number': allocation.uua_number,
            'start_date': allocation.start_date.strftime('%m/%d/%Y'),
            'end_date': allocation.end_date.strftime('%m/%d/%Y'),
            'unit_id': unit.id,
            'accommodation_type': assignment.accommodation_type,
            'zone': unit.zone if hasattr(unit, 'zone') else '',
            'area': unit.area if hasattr(unit, 'area') else '',
            'block': unit.block if hasattr(unit, 'block') else '',
            'building': unit.building if hasattr(unit, 'building') else '',
            'floor': unit.floor if hasattr(unit, 'floor') else '',
        }
        return JsonResponse(data)
    
    elif request.method == 'POST':
        try:
            allocation_id = request.POST.get('allocationId')  # Changed from 'allocation'
            unit_id = request.POST.get('unit')
            accommodation_type = request.POST.get('accommodationType')  # Changed from 'accommodation_type'
            
            if not allocation_id:
                return JsonResponse({'success': False, 'error': 'Allocation is required'}, status=400)
            
            assignment.allocation_id = allocation_id
            assignment.unit_id = unit_id
            assignment.accommodation_type = accommodation_type
            assignment.modified_by = request.user
            
            assignment.save()
            
            messages.success(request, 'Unit assignment updated successfully!')
            return JsonResponse({'success': True, 'message': 'Assignment updated successfully'})
            
        except IntegrityError as e:
            return JsonResponse({'success': False, 'error': 'This unit is already assigned to this allocation with this accommodation type'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def assignment_delete_view(request):
    """Delete a unit assignment"""
    try:
        assignment_id = request.POST.get('assignment_id')
        assignment = get_object_or_404(UnitAssignment, pk=assignment_id)
        
        # Get the unit before deleting assignment
        unit_id = assignment.unit_id
        
        assignment.delete()
        
        # Update unit occupancy_status back to 'Vacant Ready'
        try:
            unit = Unit.objects.get(id=unit_id)
            unit.occupancy_status = 'Vacant Ready'
            unit.save()
        except Unit.DoesNotExist:
            pass
        
        messages.success(request, 'Unit assignment deleted successfully!')
        return JsonResponse({'success': True, 'message': 'Assignment deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def assignment_export_view(request):
    """Export assignments to Excel"""
    try:
        query = request.GET.get('q', '')
        queryset = UnitAssignment.objects.select_related(
            'allocation', 'unit', 'allocation__company_group', 'allocation__company',
            'created_by', 'modified_by'
        ).all()
        
        if query:
            queryset = queryset.filter(
                Q(allocation__uua_number__icontains=query) |
                Q(unit__unit_number__icontains=query) |
                Q(accommodation_type__icontains=query)
            )
        
        headers = [
            'UUA Number',
            'Allocation Type',
            'Company Group',
            'Company',
            'Start Date',
            'End Date',
            'Unit Number',
            'Accommodation Type',
            'Zone',
            'Area',
            'Block',
            'Building',
            'Floor',
            'Created By',
            'Created Date',
            'Modified By',
            'Modified Date',
        ]
        
        def row_data(a):
            return [
                a.allocation.uua_number if a.allocation else "",
                a.allocation.allocation_type if a.allocation else "",
                a.allocation.company_group.company_name if a.allocation and a.allocation.company_group else "",
                a.allocation.company.company_name if a.allocation and a.allocation.company else "",
                a.allocation.start_date.strftime("%m/%d/%Y") if a.allocation and a.allocation.start_date else "",
                a.allocation.end_date.strftime("%m/%d/%Y") if a.allocation and a.allocation.end_date else "",
                a.unit.unit_number if a.unit else "",
                a.accommodation_type or "",
                a.unit.zone if a.unit and hasattr(a.unit, 'zone') else "",
                a.unit.area if a.unit and hasattr(a.unit, 'area') else "",
                a.unit.block if a.unit and hasattr(a.unit, 'block') else "",
                a.unit.building if a.unit and hasattr(a.unit, 'building') else "",
                a.unit.floor if a.unit and hasattr(a.unit, 'floor') else "",
                a.created_by.username if a.created_by else "",
                a.created_date.strftime("%m/%d/%Y %H:%M:%S") if a.created_date else "",
                a.modified_by.username if a.modified_by else "",
                a.modified_date.strftime("%m/%d/%Y %H:%M:%S") if a.modified_date else "",
            ]
        
        return export_to_excel(
            queryset,
            headers,
            row_data,
            file_prefix="unit_assignments"
        )
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_allocations_by_company(request):
    """Get all active allocations for a specific company"""
    company_id = request.GET.get('company_id')
    
    if not company_id:
        return JsonResponse({'error': 'No company_id provided'}, status=400)
    
    try:
        allocations = UnitAllocation.objects.filter(
            company_id=company_id,
            allocation_status='Active'
        ).select_related('company_group', 'company').order_by('-created_date')
        
        result = []
        for allocation in allocations:
            # Count existing assignments for each type
            def get_available_count(alloc, room_type):
                field = f"{room_type.lower()}_rooms_beds"
                if hasattr(alloc, field):
                    value = getattr(alloc, field)
                    if value:
                        try:
                            total = int(value.split('/')[0])
                            assigned = UnitAssignment.objects.filter(
                                allocation_id=alloc.id,
                                accommodation_type=room_type
                            ).count()
                            return f"{assigned}/{total}"
                        except:
                            return "0/0"
                return "0/0"
            
            result.append({
                'id': allocation.id,
                'allocation_type': allocation.allocation_type,
                'uua_number': allocation.uua_number,
                'start_date': allocation.start_date.strftime('%m/%d/%Y'),
                'end_date': allocation.end_date.strftime('%m/%d/%Y'),
                'a_assigned': get_available_count(allocation, 'A'),
                'b_assigned': get_available_count(allocation, 'B'),
                'c_assigned': get_available_count(allocation, 'C'),
                'd_assigned': get_available_count(allocation, 'D'),
            })
        
        return JsonResponse(result, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
        
    except Exception as e:
        print(f"Error during assignment export: {e}")
        return HttpResponse(f"An error occurred during export: {e}", status=500)


@require_http_methods(["GET"])
def get_allocation_by_company_group(request):
    """API endpoint to get allocation details by company group"""
    company_group_id = request.GET.get('company_group_id')
    
    if not company_group_id:
        return JsonResponse({'error': 'Company group ID is required'}, status=400)
    
    try:
        # Get the most recent active allocation for this company group
        allocation = UnitAllocation.objects.filter(
            company_group_id=company_group_id,
            allocation_status='Active'
        ).select_related('company_group', 'company').order_by('-created_date').first()
        
        if not allocation:
            return JsonResponse({'error': 'No active allocation found for this company group'}, status=404)
        
        # Get available accommodation types from this allocation
        available_types = []
        if allocation.a_rooms_beds:
            available_types.append('A')
        if allocation.b_rooms_beds:
            available_types.append('B')
        if allocation.c_rooms_beds:
            available_types.append('C')
        if allocation.d_rooms_beds:
            available_types.append('D')
        
        data = {
            'allocation_id': allocation.id,
            'allocation_type': allocation.allocation_type,
            'uua_number': allocation.uua_number,
            'company_id': allocation.company_id,
            'company_name': allocation.company.company_name,
            'start_date': allocation.start_date.strftime('%m/%d/%Y'),
            'end_date': allocation.end_date.strftime('%m/%d/%Y'),
            'available_accommodation_types': available_types,
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =======================================================
# RESERVATION VIEWS
# =======================================================

def reservation_list_view(request):
    """List all reservations with pagination"""
    query = request.GET.get('q', '')
    reservations = Reservation.objects.select_related(
        'assignment', 'housing_user', 'assignment__allocation', 'assignment__unit'
    ).all()
    
    if query:
        reservations = reservations.filter(
            Q(housing_user__username__icontains=query) |
            Q(assignment__unit__unit_number__icontains=query) |
            Q(assignment__allocation__uua_number__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(reservations, 25)
    page = request.GET.get('page', 1)
    
    try:
        reservations_page = paginator.page(page)
    except PageNotAnInteger:
        reservations_page = paginator.page(1)
    except EmptyPage:
        reservations_page = paginator.page(paginator.num_pages)
    
    # Get data for the modal
    # Get assignments where:
    # 1. Unit has Assigned occupancy status
    # 2. Unit does NOT have any active reservations with Reserved or Hold status
    reserved_or_hold_unit_ids = Reservation.objects.filter(
        occupancy_status__in=['Reserved', 'Hold']
    ).values_list('unit_id', flat=True)
    
    assignments = UnitAssignment.objects.select_related(
        'allocation', 'unit', 'allocation__company_group', 'allocation__company'
    ).filter(
        unit__occupancy_status='Assigned'
    ).exclude(
        unit_id__in=reserved_or_hold_unit_ids
    )
    
    # Get unique housing users based on username (first occurrence of each unique username)
    seen_usernames = set()
    housing_users = []
    for user in HousingUser.objects.select_related('group', 'company').order_by('username', 'id'):
        if user.username not in seen_usernames:
            seen_usernames.add(user.username)
            housing_users.append(user)
    
    assigned_units = Unit.objects.filter(occupancy_status='Assigned').exclude(id__in=reserved_or_hold_unit_ids)
    
    context = {
        'tabs': HOUSING_TABS,
        'active_tab': 'reservation',
        'reservations': reservations_page,
        'assignments': assignments,
        'housing_users': housing_users,
        'assigned_units': assigned_units,
        'query': query,
    }
    
    return render(request, 'housing/reservation.html', context)


@require_http_methods(["POST"])
def reservation_create_view(request):
    """Create a new reservation"""
    try:
        from datetime import datetime
        
        assignment_id = request.POST.get('assignment')
        housing_user_id = request.POST.get('housing_user')
        intended_checkin_date_str = request.POST.get('intended_checkin_date')
        intended_checkout_date_str = request.POST.get('intended_checkout_date')
        occupancy_status = request.POST.get('occupancy_status', 'Reserved')
        remarks = request.POST.get('remarks', '')
        
        # Convert date strings to date objects
        intended_checkin_date = datetime.strptime(intended_checkin_date_str, '%Y-%m-%d').date() if intended_checkin_date_str else None
        intended_checkout_date = datetime.strptime(intended_checkout_date_str, '%Y-%m-%d').date() if intended_checkout_date_str else None
        
        # Get additional fields from form
        allocation_type = request.POST.get('allocation_type', '')
        uua_number = request.POST.get('uua_number', '')
        company_group_id = request.POST.get('company_group')
        company_id = request.POST.get('company')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        accomodation_type = request.POST.get('accomodation_type', '')
        unit_id = request.POST.get('unit')
        unit_location_code = request.POST.get('unit_location_code', '')
        
        # Convert start and end dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        
        # Get housing user fields
        govt_id_number = request.POST.get('govt_id_number', '')
        id_type = request.POST.get('id_type', '')
        neom_id = request.POST.get('neom_id', '')
        dob_str = request.POST.get('dob')
        mobile_number = request.POST.get('mobile_number', '')
        email = request.POST.get('email', '')
        nationality = request.POST.get('nationality', '')
        religion = request.POST.get('religion', '')
        
        # Convert dob
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        # Convert dob
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        
        # Create the reservation
        reservation = Reservation(
            assignment_id=assignment_id,
            housing_user_id=housing_user_id,
            intended_checkin_date=intended_checkin_date,
            intended_checkout_date=intended_checkout_date,
            occupancy_status=occupancy_status,
            remarks=remarks,
            allocation_type=allocation_type,
            uua_number=uua_number,
            company_group_id=company_group_id if company_group_id else None,
            company_id=company_id if company_id else None,
            start_date=start_date,
            end_date=end_date,
            accomodation_type=accomodation_type,
            unit_id=unit_id if unit_id else None,
            unit_location_code=unit_location_code,
            govt_id_number=govt_id_number,
            id_type=id_type,
            neom_id=neom_id,
            dob=dob,
            mobile_number=mobile_number,
            email=email,
            nationality=nationality,
            religion=religion,
            created_by=request.user,
            modified_by=request.user,
        )
        reservation.save()
        
        # Update unit occupancy status to match reservation status (Reserved or Hold)
        if unit_id:
            unit = Unit.objects.get(id=unit_id)
            # Set unit status to Reserved or Hold based on reservation occupancy status
            if occupancy_status in ['Reserved', 'Hold']:
                unit.occupancy_status = occupancy_status
                unit.save()
        
        messages.success(request, 'Reservation created successfully!')
        return JsonResponse({'success': True, 'message': 'Reservation created successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET", "POST"])
def reservation_update_view(request, pk):
    """Update an existing reservation"""
    reservation = get_object_or_404(Reservation, pk=pk)
    
    if request.method == 'GET':
        data = {
            'id': reservation.id,
            'assignment': reservation.assignment_id,
            'housing_user': reservation.housing_user_id,
            'intended_checkin_date': reservation.intended_checkin_date.strftime('%m/%d/%Y'),
            'intended_checkout_date': reservation.intended_checkout_date.strftime('%m/%d/%Y'),
            'intended_stay_duration': reservation.intended_stay_duration,
            'occupancy_status': reservation.occupancy_status,
            'remarks': reservation.remarks,
            # Assignment fields
            'allocation_type': reservation.allocation_type,
            'uua_number': reservation.uua_number,
            'company_group': reservation.company_group_id,
            'company_group_name': reservation.company_group.company_name if reservation.company_group else '',
            'company': reservation.company_id,
            'company_name': reservation.company.company_name if reservation.company else '',
            'start_date': reservation.start_date.strftime('%m/%d/%Y') if reservation.start_date else '',
            'end_date': reservation.end_date.strftime('%m/%d/%Y') if reservation.end_date else '',
            'accomodation_type': reservation.accomodation_type,
            'unit': reservation.unit_id,
            'unit_location_code': reservation.unit_location_code,
            # Housing user fields
            'govt_id_number': reservation.govt_id_number,
            'id_type': reservation.id_type,
            'neom_id': reservation.neom_id,
            'dob': reservation.dob.strftime('%m/%d/%Y') if reservation.dob else '',
            'mobile_number': reservation.mobile_number,
            'email': reservation.email,
            'nationality': str(reservation.nationality) if reservation.nationality else '',
            'religion': reservation.religion,
        }
        return JsonResponse(data)
    
    elif request.method == 'POST':
        try:
            from datetime import datetime
            
            reservation.assignment_id = request.POST.get('assignment')
            reservation.housing_user_id = request.POST.get('housing_user')
            
            # Convert date strings to date objects
            intended_checkin_date_str = request.POST.get('intended_checkin_date')
            intended_checkout_date_str = request.POST.get('intended_checkout_date')
            reservation.intended_checkin_date = datetime.strptime(intended_checkin_date_str, '%Y-%m-%d').date() if intended_checkin_date_str else None
            reservation.intended_checkout_date = datetime.strptime(intended_checkout_date_str, '%Y-%m-%d').date() if intended_checkout_date_str else None
            
            # Update assignment fields
            reservation.allocation_type = request.POST.get('allocation_type', '')
            reservation.uua_number = request.POST.get('uua_number', '')
            company_group_id = request.POST.get('company_group')
            company_id = request.POST.get('company')
            reservation.company_group_id = company_group_id if company_group_id else None
            reservation.company_id = company_id if company_id else None
            
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')
            reservation.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            reservation.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
            
            reservation.accomodation_type = request.POST.get('accomodation_type', '')
            unit_id = request.POST.get('unit')
            reservation.unit_id = unit_id if unit_id else None
            reservation.unit_location_code = request.POST.get('unit_location_code', '')
            
            # Update housing user fields
            reservation.govt_id_number = request.POST.get('govt_id_number', '')
            reservation.id_type = request.POST.get('id_type', '')
            reservation.neom_id = request.POST.get('neom_id', '')
            dob_str = request.POST.get('dob')
            reservation.dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
            reservation.mobile_number = request.POST.get('mobile_number', '')
            reservation.email = request.POST.get('email', '')
            reservation.nationality = request.POST.get('nationality', '')
            reservation.religion = request.POST.get('religion', '')
            
            reservation.occupancy_status = request.POST.get('occupancy_status', 'Reserved')
            reservation.remarks = request.POST.get('remarks', '')
            reservation.modified_by = request.user
            
            reservation.save()
            
            # Update unit occupancy status to match reservation status (Reserved or Hold)
            if reservation.unit:
                if reservation.occupancy_status in ['Reserved', 'Hold']:
                    reservation.unit.occupancy_status = reservation.occupancy_status
                    reservation.unit.save()
            
            messages.success(request, 'Reservation updated successfully!')
            return JsonResponse({'success': True, 'message': 'Reservation updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def reservation_delete_view(request):
    """Delete a reservation"""
    try:
        reservation_id = request.POST.get('reservation_id')
        reservation = get_object_or_404(Reservation, pk=reservation_id)
        
        # Revert unit status back to Vacant Ready when reservation is deleted
        if reservation.unit:
            reservation.unit.occupancy_status = 'Vacant Ready'
            reservation.unit.save()
        
        reservation.delete()
        
        messages.success(request, 'Reservation deleted successfully!')
        return JsonResponse({'success': True, 'message': 'Reservation deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def reservation_export_view(request):
    """Export reservations to Excel"""
    try:
        query = request.GET.get('q', '')
        queryset = Reservation.objects.select_related(
            'assignment', 'housing_user', 'assignment__allocation', 'assignment__unit',
            'created_by', 'modified_by'
        ).all()
        
        if query:
            queryset = queryset.filter(
                Q(housing_user__username__icontains=query) |
                Q(assignment__unit__unit_number__icontains=query) |
                Q(assignment__allocation__uua_number__icontains=query)
            )
        
        headers = [
            'Allocation Type',
            'UUA Number',
            'Company Group',
            'Company',
            'Start Date',
            'End Date',
            'Accommodation Type',
            'Unit Number',
            'Unit Location Code',
            'User Name',
            'Govt ID Number',
            'ID Type',
            'NEOM ID',
            'D.O.B',
            'Mobile Number',
            'Email',
            'Nationality',
            'Religion',
            'Occupancy Status',
            'Intended Check-In Date',
            'Intended Check-Out Date',
            'Intended Stay Duration (Days)',
            'Created By',
            'Created Date',
            'Modified By',
            'Modified Date',
        ]
        
        def row_data(r):
            return [
                r.allocation_type or "",
                r.uua_number or "",
                r.company_group.company_name if r.company_group else "",
                r.company.company_name if r.company else "",
                r.start_date.strftime("%m/%d/%Y") if r.start_date else "",
                r.end_date.strftime("%m/%d/%Y") if r.end_date else "",
                r.accomodation_type or "",
                r.unit.unit_number if r.unit else "",
                r.unit_location_code or "",
                r.housing_user.username if r.housing_user else "",
                r.govt_id_number or "",
                r.id_type or "",
                r.neom_id or "",
                r.dob.strftime("%m/%d/%Y") if r.dob else (r.housing_user.dob.strftime("%m/%d/%Y") if r.housing_user and r.housing_user.dob else ""),
                r.mobile_number or "",
                r.email or "",
                r.nationality.name if r.nationality else "",
                r.religion or "",
                r.occupancy_status or "",
                r.intended_checkin_date.strftime("%m/%d/%Y") if r.intended_checkin_date else "",
                r.intended_checkout_date.strftime("%m/%d/%Y") if r.intended_checkout_date else "",
                str(r.intended_stay_duration) if r.intended_stay_duration else "",
                r.created_by.username if r.created_by else "",
                r.created_date.strftime("%m/%d/%Y %H:%M:%S") if r.created_date else "",
                r.modified_by.username if r.modified_by else "",
                r.modified_date.strftime("%m/%d/%Y %H:%M:%S") if r.modified_date else "",
            ]
        
        return export_to_excel(
            queryset,
            headers,
            row_data,
            file_prefix="reservations"
        )
        
    except Exception as e:
        print(f"Error during reservation export: {e}")
        return HttpResponse(f"An error occurred during export: {e}", status=500)


# =======================================================
# CHECK-IN/CHECK-OUT VIEWS
# =======================================================

def checkin_checkout_list_view(request):
    """List all check-ins/check-outs with pagination"""
    query = request.GET.get('q', '')
    checkins = CheckInCheckOut.objects.select_related(
        'reservation', 'reservation__housing_user', 'reservation__assignment__unit'
    ).all()
    
    if query:
        checkins = checkins.filter(
            Q(reservation__housing_user__username__icontains=query) |
            Q(reservation__assignment__unit__unit_number__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(checkins, 25)
    page = request.GET.get('page', 1)
    
    try:
        checkins_page = paginator.page(page)
    except PageNotAnInteger:
        checkins_page = paginator.page(1)
    except EmptyPage:
        checkins_page = paginator.page(paginator.num_pages)
    
    # Get data for the modal - include all related fields
    reservations = Reservation.objects.select_related(
        'housing_user', 
        'assignment__unit',
        'assignment__allocation',
        'assignment__allocation__company',
        'assignment__allocation__company_group',
        'unit',
        'company',
        'company_group'
    ).filter(occupancy_status__in=['Reserved', 'Assigned'])
    
    context = {
        'tabs': HOUSING_TABS,
        'active_tab': 'checkin_checkout',
        'checkins': checkins_page,
        'reservations': reservations,
        'query': query,
    }
    
    return render(request, 'housing/checkin_checkout.html', context)


@require_http_methods(["POST"])
def checkin_checkout_create_view(request):
    """Create a new check-in/check-out record"""
    try:
        from datetime import datetime
        
        print("POST data:", dict(request.POST))
        print("User:", request.user, "Is authenticated:", request.user.is_authenticated)
        
        # Extract only the fields we need
        reservation_id = request.POST.get('reservation')
        actual_checkin_datetime_str = request.POST.get('actual_checkin_datetime') or None
        actual_checkout_datetime_str = request.POST.get('actual_checkout_datetime') or None
        remarks = request.POST.get('remarks', '')
        
        if not reservation_id:
            return JsonResponse({'success': False, 'error': 'Reservation is required'}, status=400)
        
        # Convert string datetime to datetime object
        actual_checkin_datetime = None
        actual_checkout_datetime = None
        
        if actual_checkin_datetime_str:
            actual_checkin_datetime = datetime.strptime(actual_checkin_datetime_str, '%Y-%m-%dT%H:%M')
            
        if actual_checkout_datetime_str:
            actual_checkout_datetime = datetime.strptime(actual_checkout_datetime_str, '%Y-%m-%dT%H:%M')
        
        # Create the check-in/check-out record with only the fields we specify
        checkin = CheckInCheckOut(
            reservation_id=reservation_id,
            actual_checkin_datetime=actual_checkin_datetime,
            actual_checkout_datetime=actual_checkout_datetime,
            remarks=remarks,
        )
        # Set audit fields explicitly
        checkin.created_by = request.user
        checkin.modified_by = request.user
        checkin.save()
        
        # Update reservation and unit status
        reservation = Reservation.objects.get(pk=reservation_id)
        if actual_checkin_datetime and not actual_checkout_datetime:
            reservation.occupancy_status = 'Occupied'
            reservation.save()
            # Update unit status to Occupied
            if reservation.unit:
                reservation.unit.occupancy_status = 'Occupied'
                reservation.unit.save()
        elif actual_checkout_datetime:
            reservation.occupancy_status = 'Checked Out'
            reservation.save()
            # Update unit status to Vacant Dirty
            if reservation.unit:
                reservation.unit.occupancy_status = 'Vacant Dirty'
                reservation.unit.save()
        
        messages.success(request, 'Check-in/check-out record created successfully!')
        return JsonResponse({'success': True, 'message': 'Check-in/check-out created successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET", "POST"])
def checkin_checkout_update_view(request, pk):
    """Update an existing check-in/check-out record"""
    checkin = get_object_or_404(CheckInCheckOut, pk=pk)
    
    if request.method == 'GET':
        # Get the reservation with all related data
        res = checkin.reservation
        
        data = {
            'id': checkin.id,
            'reservation': checkin.reservation_id,
            'reservation_username': res.housing_user.username,
            'actual_checkin_datetime': checkin.actual_checkin_datetime.strftime('%Y-%m-%dT%H:%M') if checkin.actual_checkin_datetime else '',
            'actual_checkout_datetime': checkin.actual_checkout_datetime.strftime('%Y-%m-%dT%H:%M') if checkin.actual_checkout_datetime else '',
            'actual_stay_duration': checkin.actual_stay_duration,
            'remarks': checkin.remarks or '',
            # Add all reservation details for auto-population
            'allocation_type': res.allocation_type or '',
            'uua_number': res.uua_number or '',
            'allocation_code': res.unit_location_code or '',
            'company_group': res.company_group.company_name if res.company_group else '',
            'company': res.company.company_name if res.company else '',
            'start_date': res.start_date.strftime('%m/%d/%Y') if res.start_date else '',
            'end_date': res.end_date.strftime('%m/%d/%Y') if res.end_date else '',
            'accomodation_type': res.accomodation_type or '',
            'unit': res.unit.unit_number if res.unit else '',
            'unit_location': res.unit_location_code or '',
            'govt_id': res.govt_id_number or '',
            'id_type': res.id_type or '',
            'neom_id': res.neom_id or '',
            'dob': res.dob.strftime('%m/%d/%Y') if res.dob else (res.housing_user.dob.strftime('%m/%d/%Y') if res.housing_user.dob else ''),
            'mobile': res.mobile_number or '',
            'email': res.email or '',
            'nationality': res.nationality.name if res.nationality else '',
            'religion': res.religion or '',
            'occupancy_status': res.occupancy_status or '',
        }
        return JsonResponse(data)
    
    elif request.method == 'POST':
        try:
            from datetime import datetime
            
            checkin.reservation_id = request.POST.get('reservation')
            actual_checkin_datetime = request.POST.get('actual_checkin_datetime') or None
            actual_checkout_datetime = request.POST.get('actual_checkout_datetime') or None
            remarks = request.POST.get('remarks', '')
            
            # Convert string datetime to datetime object
            if actual_checkin_datetime:
                checkin.actual_checkin_datetime = datetime.strptime(actual_checkin_datetime, '%Y-%m-%dT%H:%M')
            else:
                checkin.actual_checkin_datetime = None
                
            if actual_checkout_datetime:
                checkin.actual_checkout_datetime = datetime.strptime(actual_checkout_datetime, '%Y-%m-%dT%H:%M')
            else:
                checkin.actual_checkout_datetime = None
            
            checkin.remarks = remarks
            checkin.modified_by = request.user
            
            checkin.save()
            
            # Update reservation and unit status
            reservation = checkin.reservation
            if actual_checkin_datetime and not actual_checkout_datetime:
                reservation.occupancy_status = 'Occupied'
                reservation.save()
                # Update unit status to Occupied
                if reservation.unit:
                    reservation.unit.occupancy_status = 'Occupied'
                    reservation.unit.save()
            elif actual_checkout_datetime:
                reservation.occupancy_status = 'Checked Out'
                reservation.save()
                # Update unit status to Vacant Dirty
                if reservation.unit:
                    reservation.unit.occupancy_status = 'Vacant Dirty'
                    reservation.unit.save()
            
            messages.success(request, 'Check-in/check-out record updated successfully!')
            return JsonResponse({'success': True, 'message': 'Check-in/check-out updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def checkin_checkout_delete_view(request):
    """Delete a check-in/check-out record"""
    try:
        checkin_id = request.POST.get('checkin_id')
        checkin = get_object_or_404(CheckInCheckOut, pk=checkin_id)
        checkin.delete()
        
        messages.success(request, 'Check-in/check-out record deleted successfully!')
        return JsonResponse({'success': True, 'message': 'Check-in/check-out deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def checkin_checkout_export_view(request):
    """Export check-ins/check-outs to Excel"""
    try:
        query = request.GET.get('q', '')
        queryset = CheckInCheckOut.objects.select_related(
            'reservation', 'reservation__housing_user', 'reservation__assignment__unit',
            'reservation__assignment__allocation', 'created_by', 'modified_by'
        ).all()
        
        if query:
            queryset = queryset.filter(
                Q(reservation__housing_user__username__icontains=query) |
                Q(reservation__assignment__unit__unit_number__icontains=query)
            )
        
        headers = [
            'Allocation Type',
            'UUA Number',
            'Allocation Code',
            'Company Group',
            'Company',
            'Start Date',
            'End Date',
            'Accommodation Type',
            'Unit Number',
            'Unit Location Code',
            'Govt ID Number',
            'ID Type',
            'NEOM ID',
            'D.O.B',
            'Mobile Number',
            'Email',
            'Nationality',
            'Religion',
            'Occupancy Status',
            'Actual Check-In Date & Time',
            'Actual Check-Out Date & Time',
            'Actual Stay Duration (Days)',
            'Remarks',
            'Created By',
            'Created Date',
            'Modified By',
            'Modified Date',
        ]
        
        def row_data(c):
            res = c.reservation
            return [
                res.allocation_type or "",
                res.uua_number or "",
                res.unit_location_code or "",
                res.company_group.company_name if res and res.company_group else "",
                res.company.company_name if res and res.company else "",
                res.start_date.strftime("%m/%d/%Y") if res and res.start_date else "",
                res.end_date.strftime("%m/%d/%Y") if res and res.end_date else "",
                res.accomodation_type or "",
                res.unit.unit_number if res and res.unit else "",
                res.unit_location_code or "",
                res.govt_id_number or "",
                res.id_type or "",
                res.neom_id or "",
                res.dob.strftime("%m/%d/%Y") if res and res.dob else (res.housing_user.dob.strftime("%m/%d/%Y") if res and res.housing_user and res.housing_user.dob else ""),
                res.mobile_number or "",
                res.email or "",
                res.nationality.name if res and res.nationality else "",
                res.religion or "",
                res.occupancy_status or "",
                c.actual_checkin_datetime.strftime("%m/%d/%Y %H:%M:%S") if c.actual_checkin_datetime else "",
                c.actual_checkout_datetime.strftime("%m/%d/%Y %H:%M:%S") if c.actual_checkout_datetime else "",
                str(c.actual_stay_duration) if c.actual_stay_duration else "",
                c.remarks or "",
                c.created_by.username if c.created_by else "",
                c.created_date.strftime("%m/%d/%Y %H:%M:%S") if c.created_date else "",
                c.modified_by.username if c.modified_by else "",
                c.modified_date.strftime("%m/%d/%Y %H:%M:%S") if c.modified_date else "",
            ]
        
        return export_to_excel(
            queryset,
            headers,
            row_data,
            file_prefix="checkins_checkouts"
        )
        
    except Exception as e:
        print(f"Error during check-in/check-out export: {e}")
        return HttpResponse(f"An error occurred during export: {e}", status=500)



