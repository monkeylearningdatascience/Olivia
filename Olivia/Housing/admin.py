# Housing/admin.py

from django.contrib import admin
from .models import Unit, CompanyGroup, UserCompany, HousingUser

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