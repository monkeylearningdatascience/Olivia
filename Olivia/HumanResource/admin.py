from django.contrib import admin
from .models import Cash, Balance, Project

# Use the decorator to register the Cash model with its custom Admin class
@admin.register(Cash)
class CashAdmin(admin.ModelAdmin):
    list_display = (
        'date', 
        'supplier_name', 
        'department', 
        'item_description', 
        'invoice_number', 
        'amount', 
        'vat', 
        'import_duty', 
        'discount', 
        'total', 
        'project_name', 
        'submitted_date',
        'attachments', # Ensure attachments field is also displayed
    )
    list_filter = ('department', 'project_name', 'submitted_date')
    search_fields = ('supplier_name', 'item_description', 'invoice_number')

# Register other models without a custom class using the standard method
admin.site.register(Project)

# Use the decorator for your custom BalanceAdmin class
@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = (
        'activity',
        'project_name',
        'amount',
    )
    list_filter = ('activity', 'project_name',)
    search_fields = ('activity', 'project_name',)
