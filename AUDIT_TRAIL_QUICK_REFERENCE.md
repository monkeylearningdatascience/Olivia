# Audit Trail Quick Reference

## Field Naming Convention

### HumanResource App
- `created_by`: ForeignKey to User (who created)
- `created_at`: DateTimeField (when created)
- `modified_by`: ForeignKey to User (who last modified)
- `modified_at`: DateTimeField (when last modified)

### Housing App
- `created_by`: ForeignKey to User (who created)
- `created_date`: DateTimeField (when created)
- `modified_by`: ForeignKey to User (who last modified)
- `modified_date`: DateTimeField (when last modified)

## How to Add Audit Fields to New Models

### Option 1: HumanResource (Use Direct Fields)
```python
from django.db import models
from django.contrib.auth.models import User

class MyModel(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='created_mymodels')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='modified_mymodels')
    modified_at = models.DateTimeField(auto_now=True)
```

### Option 2: Housing (Use AuditModel Mixin)
```python
from django.db import models
from Housing.models import AuditModel

class MyModel(AuditModel):
    name = models.CharField(max_length=100)
    # Automatically gets: created_by, created_date, modified_by, modified_date
```

## Setting Audit Fields in Views

### Create Operation
```python
def create_my_object(request):
    if request.method == 'POST':
        obj = MyModel.objects.create(
            name=request.POST.get('name'),
            created_by=request.user,
            modified_by=request.user
        )
        return JsonResponse({'success': True, 'id': obj.id})
```

Or with form:
```python
def create_my_object(request):
    if request.method == 'POST':
        form = MyModelForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.modified_by = request.user
            obj.save()
            return JsonResponse({'success': True})
```

### Update Operation
```python
def update_my_object(request, id):
    obj = get_object_or_404(MyModel, id=id)
    if request.method == 'POST':
        form = MyModelForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.modified_by = request.user  # Only update modified_by
            obj.save()
            return JsonResponse({'success': True})
```

## Querying with Audit Information

```python
from django.utils import timezone
from datetime import timedelta

# Find who created a record
employee = Employee.objects.get(id=1)
print(f"Created by: {employee.created_by.username}")
print(f"Created on: {employee.created_at}")

# Find recently modified records
recent = Employee.objects.filter(
    modified_at__gte=timezone.now() - timedelta(days=7)
)

# Find records modified by specific user
admin_changes = Employee.objects.filter(modified_by__username='admin')

# Get audit trail for specific record
audit_trail = {
    'created': {
        'by': employee.created_by.get_full_name() if employee.created_by else 'System',
        'at': employee.created_at.isoformat()
    },
    'modified': {
        'by': employee.modified_by.get_full_name() if employee.modified_by else 'System',
        'at': employee.modified_at.isoformat()
    }
}
```

## Exporting with Audit Data

```python
def export_my_data(request):
    queryset = MyModel.objects.all()
    
    headers = [
        'Name', 'Created By', 'Created Date', 'Modified By', 'Modified Date'
    ]
    
    def row_data(obj):
        return [
            obj.name,
            obj.created_by.username if obj.created_by else '',
            obj.created_at.strftime('%Y-%m-%d %H:%M:%S') if obj.created_at else '',
            obj.modified_by.username if obj.modified_by else '',
            obj.modified_at.strftime('%Y-%m-%d %H:%M:%S') if obj.modified_at else '',
        ]
    
    return export_to_excel(queryset, headers, row_data, file_prefix='my_data')
```

## Displaying in Templates

### Admin List Display
```python
class MyModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at', 'modified_by', 'modified_at']
    readonly_fields = ['created_by', 'created_at', 'modified_by', 'modified_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
```

### HTML Template
```html
<div class="audit-info">
    <small>
        Created by <strong>{{ object.created_by.get_full_name }}</strong>
        on {{ object.created_at|date:"Y-m-d H:i:s" }}<br>
        Last modified by <strong>{{ object.modified_by.get_full_name }}</strong>
        on {{ object.modified_at|date:"Y-m-d H:i:s" }}
    </small>
</div>
```

## Common Issues & Solutions

### Issue: `created_by` showing as None
**Solution**: Ensure `commit=False` is used before setting the field:
```python
obj = form.save(commit=False)  # Don't save yet
obj.created_by = request.user  # Set audit field
obj.save()  # Now save
```

### Issue: `modified_at` not updating
**Solution**: Make sure field has `auto_now=True`:
```python
modified_at = models.DateTimeField(auto_now=True)  # Correct
modified_at = models.DateTimeField(auto_now_add=True)  # Wrong - won't update
```

### Issue: Queryset filtering by user not working
**Solution**: Use related_name correctly:
```python
# Wrong - assuming related_name is 'created_by'
# Employee.objects.filter(created_by__username='admin')

# Correct - use the defined related_name
Employee.objects.filter(created_employees__username='admin')  # This is wrong too

# Best approach
User.objects.get(username='admin').created_employees.all()
```

## Reports You Can Generate

1. **Who Modified What**: 
   ```python
   Employee.objects.filter(modified_by=user).count()
   ```

2. **Modification Timeline**:
   ```python
   Employee.objects.filter(
       modified_at__date='2025-12-22'
   ).order_by('modified_at')
   ```

3. **User Activity**:
   ```python
   from django.contrib.auth.models import User
   user = User.objects.get(username='l.mathew')
   
   created = user.created_employees.count()
   modified = user.modified_employees.count()
   ```

4. **Data Quality**:
   ```python
   # Records without audit info (shouldn't happen for new records)
   Employee.objects.filter(created_by__isnull=True)
   ```

## Backward Compatibility

Existing records may have NULL values in `created_by` and `modified_by`. Handle this gracefully:

```python
# In templates
{{ object.created_by.get_full_name|default:"Unknown" }}

# In Python
created_by = employee.created_by.username if employee.created_by else "System"
```

## Notes

- Always set BOTH `created_by` and `modified_by` when creating records
- Only set `modified_by` when updating records (leave `created_by` unchanged)
- Use `request.user` to get the current logged-in user
- Ensure users are authenticated before creating records
- Never manually set `created_at` or `modified_at` - let Django handle these
