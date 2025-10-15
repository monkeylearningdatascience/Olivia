from django import forms
from .models import Cash
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

