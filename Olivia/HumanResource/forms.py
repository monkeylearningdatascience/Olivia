from django import forms
from .models import Cash, Employee
from django_countries.widgets import CountrySelectWidget
import datetime

class CashForm(forms.ModelForm):
    class Meta:
        model = Cash
        fields = '__all__'
        exclude = ('submitted_date', 'total',) # Exclude these fields to prevent form validation errors
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'item_description': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'vat': forms.NumberInput(attrs={'class': 'form-control'}),
            'import_duty': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'project_name': forms.Select(attrs={'class': 'form-select'}),
            'attachments': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    # Exclude 'submitted_date' from the form's fields to prevent validation errors
    # as it's not present in the HTML form.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['submitted_date'].required = False
        self.fields.pop('submitted_date', None)

    # def save(self, commit=True):
    #     """Override the save method to set the submitted_date automatically."""
    #     instance = super().save(commit=False)
    #     instance.submitted_date = datetime.date.today()
    #     if commit:
    #         instance.save()
    #     return instance


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
        exclude = ('documents',)  # Keep documents excluded; include photo so uploads are handled by the form
        widgets = {
            'staffid': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': CountrySelectWidget(attrs={'class': 'form-select'}),
            'photo_url': forms.URLInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'iqama_number': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo_url': forms.URLInput(attrs={'class': 'form-control'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure required fields are set properly
        self.fields['staffid'].required = True
        self.fields['full_name'].required = True
        self.fields['department'].required = True

