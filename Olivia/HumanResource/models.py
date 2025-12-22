from django.db import models
from django_countries.fields import CountryField

# Create your models here.
# class Project(models.Model):
#     PROJECT_CHOICES = [
#         ('NRC9', 'NRC9'),
#         ('NRC5', 'NRC5'),
#     ]
#     project_name = models.CharField(
#         max_length=50,
#         choices=PROJECT_CHOICES,
#         unique=True
#     )

#     def __str__(self):
#         return self.project_name

class Project(models.Model):
    project_name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.project_name

class Balance(models.Model):
    ACTIVITY_CHOICES = [
        ('opening', 'Opening Balance'),
        ('submitted', 'Submitted to HQ'),
        ('received', 'Replenishment from HQ'),
    ]

    activity = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    project_name = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="balances")

    def __str__(self):
        return f"{self.project_name} - {self.activity} - {self.amount}"


class Cash(models.Model):
    DEPARTMENT_CHOICES = [
        ('finance', 'Finance'),
        ('hr', 'Human Resources'),
        ('it', 'IT'),
        ('logistics', 'Logistics'),
        ('procurement', 'Procurement'),
        ('other', 'Other'),
    ]

    supplier_name = models.CharField(max_length=255)
    department = models.CharField(max_length=50) 
    item_description = models.TextField()
    date = models.DateField()
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    vat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    import_duty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    attachments = models.FileField(upload_to='pettycash/attachments/', blank=True, null=True)
    submitted_date = models.DateField(null=True, blank=True)
    project_name = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="cash_entries")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # def save(self, *args, **kwargs):
    #     # Calculate total only if it's not provided or is 0
    #     if self.total is None or self.total == 0:
    #         self.total = self.amount + self.vat + self.import_duty - self.discount
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.supplier_name} - {self.project_name}"
    
def employee_photo_path(instance, filename):
    # Use `staffid` as the unique identifier for employee photo path
    identifier = getattr(instance, 'staffid', None) or getattr(instance, 'id', 'unknown')
    return f'staff/photos/{identifier}/{filename}'

class Employee(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    STATUS_CHOICES = [('active', 'Active'), ('on_notice', 'On Notice'), ('exited', 'Exited')]

    staffid = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    nationality = CountryField(blank_label='(Select Nationality)', null=True, blank=True)
    email = models.EmailField(blank=True)
    iqama_number = models.CharField(max_length=20, blank=True)
    passport_number = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    location = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to=employee_photo_path, blank=True, null=True)
    photo_url = models.URLField(blank=True)  # fallback if using external
    employment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    documents = models.JSONField(default=list, blank=True)  # list of dicts
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Use staffid which exists on the model
        return f"{self.full_name} ({self.staffid})"
