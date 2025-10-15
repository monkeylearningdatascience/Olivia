from django.contrib import admin
from .models import Unit, CompanyGroup, UserCompany

# Register your models here.
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

admin.site.register(CompanyGroup)
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
        # Audit Fields
        'created_date', 
        'modified_date',
        # You can add 'address_text' and 'company_details' if you want long text in the list view,
        # but it's usually better for the detail view.
    )

    # Optional: Add filters to the sidebar
    list_filter = ('company_group', 'created_date')

    # Optional: Add search fields
    search_fields = ('company_name', 'cr_number', 'vat_number', 'contact_name')

# Unregister the simple registration and register the custom ModelAdmin
# admin.site.register(UserCompany) # Comment this out if it was there
admin.site.register(UserCompany, UserCompanyAdmin)
