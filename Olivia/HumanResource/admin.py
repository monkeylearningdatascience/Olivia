from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from .models import Cash, Balance, Project, Employee, Manager
from utils.excel_exporter import export_to_excel


# Inline to display Cash entries on Project page
class CashInline(admin.TabularInline):
    model = Cash
    extra = 0
    fields = ('date', 'supplier_name', 'amount', 'invoice_number', 'total', 'submitted_date')
    readonly_fields = ('total',)


# Inline to display Balance entries on Project page
class BalanceInline(admin.TabularInline):
    model = Balance
    extra = 0
    fields = ('activity', 'amount')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_name',)
    search_fields = ('project_name',)
    inlines = (BalanceInline, CashInline)


@admin.register(Cash)
class CashAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'supplier_name',
        'department',
        'item_description_short',
        'invoice_number',
        'amount',
        'vat',
        'import_duty',
        'discount',
        'total',
        'project_name',
        'submitted_date',
    )
    list_filter = ('department', 'project_name', 'submitted_date')
    search_fields = ('supplier_name', 'item_description', 'invoice_number')
    readonly_fields = ('total',)

    def item_description_short(self, obj):
        if obj.item_description and len(obj.item_description) > 60:
            return obj.item_description[:57] + '...'
        return obj.item_description
    item_description_short.short_description = 'Description'


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = (
        'activity',
        'project_name',
        'amount',
    )
    list_filter = ('activity', 'project_name',)
    search_fields = ('activity', 'project_name__project_name')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'staffid',
        'full_name',
        'position',
        'employment_status',
        'department',
        'manager',
        'email',
        'start_date',
        'photo_preview',
    )
    # Allow quick inline edits for these fields
    list_editable = ('position', 'employment_status')
    # Make staffid the link to the change view (must not be in list_editable)
    list_display_links = ('staffid',)
    list_filter = ('department', 'employment_status', 'position', 'gender')
    search_fields = ('staffid', 'full_name', 'email', 'iqama_number', 'passport_number')
    readonly_fields = ('photo_url',)
    date_hierarchy = 'start_date'
    ordering = ('full_name',)
    actions = ['export_selected_employees']

    fieldsets = (
        ('Basic Info', {
            'fields': ('staffid', 'full_name', 'position', 'department', 'manager', 'employment_status')
        }),
        ('Contact', {
            'fields': ('email', 'location')
        }),
        ('IDs', {
            'fields': ('iqama_number', 'passport_number', 'nationality')
        }),
        ('Other', {
            'fields': ('start_date', 'gender', 'photo_url')
        }),
    )

    # Use autocomplete for selecting a manager to improve admin UX and performance
    autocomplete_fields = ('manager',)

    def photo_preview(self, obj):
        url = getattr(obj, 'photo_url', None) or (obj.photo.url if getattr(obj, 'photo', None) else None)
        if url:
            return format_html('<img src="{}" style="max-height:80px;" />', url)
        return '-'
    photo_preview.short_description = 'Photo'

    def export_selected_employees(self, request, queryset):
        """Admin action: export selected employees to Excel using export_to_excel util."""
        headers = [
            'Staff ID', 'Full Name', 'Position', 'Department', 'Nationality', 'Email', 'Iqama', 'Passport', 'Gender', 'Location', 'Start Date', 'Status'
        ]

        def row_data(e):
            return [
                e.staffid or '',
                e.full_name or '',
                e.position or '',
                e.department or '',
                e.nationality.name if getattr(e, 'nationality', None) else '',
                e.email or '',
                e.iqama_number or '',
                e.passport_number or '',
                e.gender or '',
                e.location or '',
                e.start_date.strftime('%B %d, %Y') if e.start_date else '',
                e.employment_status or '',
            ]

        try:
            return export_to_excel(queryset, headers, row_data, file_prefix='employees')
        except Exception as exc:
            self.message_user(request, f'Export failed: {exc}', level='error')
            return None

    export_selected_employees.short_description = 'Export selected employees to Excel'

@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ('staffid', 'name', 'email', 'designation', 'department')
    search_fields = ('staffid', 'name', 'email', 'designation', 'department')
    list_filter = ('department', 'designation')
