# Housing/admin.py

from django.contrib import admin
from .models import Unit, CompanyGroup, UserCompany, HousingUser, UnitAllocation, UnitAssignment, Reservation, CheckInCheckOut

# --- 1. Unit Model Admin ---
@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        "unit_number",
        "bed_number",
        "unit_location",
        "zone",
        "accomodation_type",
        "separable",
        "wave",
        "area",
        "block",
        "building",
        "floor",
        "occupancy_status",
    )
    search_fields = ("unit_number", "building", "floor", "zone")
    list_filter = ("building", "floor", "zone", "occupancy_status")

# --- 2. CompanyGroup Model Admin (Corrected Class Name) ---
# NOTE: CompanyGroup should only contain group-level fields. 
# Assuming it only has 'name' and possibly audit fields.
@admin.register(CompanyGroup)
class CompanyGroupAdmin(admin.ModelAdmin):
    list_display = (
        'company_name', 
        'created_date', 
        'modified_date',
    )
    search_fields = ('company_name',)
    list_filter = ('created_date',)


# --- 3. UserCompany Model Admin (Registered with its correct class) ---
# This class contains details about an actual Company.
@admin.register(UserCompany)
class UserCompanyAdmin(admin.ModelAdmin):
    # This list explicitly tells Django which columns to display
    list_display = (
        'company_name', 
        'company_group', 
        'cr_number', 
        'vat_number', 
        'contact_name', 
        'email_address', 
        'mobile', 
        'phone', 
        'created_date', 
        'modified_date',
    )
    list_filter = ('company_group', 'created_date')
    search_fields = ('company_name', 'cr_number', 'vat_number', 'contact_name')


# --- 4. HousingUser Model Admin ---
@admin.register(HousingUser)
class HousingUserAdmin(admin.ModelAdmin):
    list_display = ("username", 
                    "group", 
                    "company", 
                    "status")
    
    # Use FK lookups for searching related fields
    search_fields = ("username", "group__company_name", "company__company_name")
    list_filter = ("group", "company", "status")


# --- 5. UnitAllocation Model Admin ---
@admin.register(UnitAllocation)
class UnitAllocationAdmin(admin.ModelAdmin):
    list_display = (
        'uua_number',
        'allocation_type',
        'company_group',
        'company',
        'start_date',
        'end_date',
        'total_rooms_beds',
        'allocation_status',
        'created_date',
        'modified_date',
    )
    list_filter = ('allocation_type', 'allocation_status', 'company_group', 'created_date')
    search_fields = ('uua_number', 'company__company_name', 'company_group__company_name')
    readonly_fields = ('total_rooms_beds', 'created_date', 'modified_date', 'created_by', 'modified_by')


# --- 6. UnitAssignment Model Admin ---
@admin.register(UnitAssignment)
class UnitAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'allocation',
        'unit',
        'accommodation_type',
        'created_date',
        'modified_date',
    )
    list_filter = ('accommodation_type', 'allocation__allocation_type', 'created_date')
    search_fields = ('allocation__uua_number', 'unit__unit_number')
    readonly_fields = ('created_date', 'modified_date', 'created_by', 'modified_by')


# --- 7. Reservation Model Admin ---
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'housing_user',
        'assignment',
        'intended_checkin_date',
        'intended_checkout_date',
        'intended_stay_duration',
        'occupancy_status',
        'created_date',
        'modified_date',
    )
    list_filter = ('occupancy_status', 'intended_checkin_date', 'created_date')
    search_fields = ('housing_user__username', 'assignment__unit__unit_number', 'assignment__allocation__uua_number')
    readonly_fields = ('intended_stay_duration', 'created_date', 'modified_date', 'created_by', 'modified_by')


# --- 8. CheckInCheckOut Model Admin ---
@admin.register(CheckInCheckOut)
class CheckInCheckOutAdmin(admin.ModelAdmin):
    list_display = (
        'reservation',
        'actual_checkin_datetime',
        'actual_checkout_datetime',
        'actual_stay_duration',
        'created_date',
        'modified_date',
    )
    list_filter = ('actual_checkin_datetime', 'actual_checkout_datetime', 'created_date')
    search_fields = ('reservation__housing_user__username', 'reservation__assignment__unit__unit_number')
    readonly_fields = ('actual_stay_duration', 'created_date', 'modified_date', 'created_by', 'modified_by')