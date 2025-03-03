from django import forms
from .models import PerfumeTransaction
from datetime import date

class PerfumeTransactionForm(forms.ModelForm):
    class Meta:
        model = PerfumeTransaction
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'value': date.today()}),
            'price': forms.NumberInput(attrs={'step': '0.01'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate dropdowns with existing values
        for field in ['perfumer', 'fragrance', 'package', 'bottle', 'origin', 'location', 'purchase_currency']:
            existing_values = PerfumeTransaction.objects.values_list(field, flat=True).distinct()
            self.fields[field].widget = forms.Select(choices=[(v, v) for v in existing_values])
