from django import forms
from .models import Loan, LoanRepayment


class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['principal', 'repayment_months']
        widgets = {
            'principal': forms.NumberInput(attrs={'class': 'form-control', 'min': '1000'}),
            'repayment_months': forms.Select(
                choices=[(i, f'{i} Month{"s" if i > 1 else ""}') for i in range(1, 7)],
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, member=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.member = member

    def clean_principal(self):
        amount = self.cleaned_data['principal']
        if self.member:
            limit = self.member.available_loan_limit
            if amount > limit:
                raise forms.ValidationError(f'Amount exceeds your loan limit of KES {limit:,.2f}')
            active = self.member.loans.filter(status='active').exists()
            if active:
                raise forms.ValidationError('You already have an active loan.')
        return amount


class RecordRepaymentForm(forms.ModelForm):
    class Meta:
        model = LoanRepayment
        fields = ['amount_paid', 'payment_date', 'notes']
        widgets = {
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
