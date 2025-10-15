from django.db import models

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
