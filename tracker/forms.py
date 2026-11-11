from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'amount', 'category', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        help_texts = {'category': 'Leave blank to auto-predict from the description.'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount


class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'
