from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Savings, RegistrationPayment


class MemberRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    phone = forms.CharField(max_length=15, required=True, help_text="e.g. 0712345678")
    id_number = forms.CharField(max_length=20, required=True, label="ID Number")
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone', 'id_number', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class RecordSavingsForm(forms.ModelForm):
    class Meta:
        model = Savings
        fields = ['member', 'amount', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = User.objects.filter(role='member', is_active_member=True)
        self.fields['member'].widget.attrs.update({'class': 'form-control'})


class SendSMSForm(forms.Form):
    RECIPIENT_CHOICES = [('all', 'All Members'), ('individual', 'Individual Member')]
    recipient_type = forms.ChoiceField(choices=RECIPIENT_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    member = forms.ModelChoiceField(
        queryset=User.objects.filter(role='member'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), max_length=160)


class RegistrationPaymentForm(forms.ModelForm):
    class Meta:
        model = RegistrationPayment
        fields = ['mpesa_code']
        widgets = {
            'mpesa_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. QHX4K2ABCD',
                'style': 'text-transform:uppercase;letter-spacing:1px;'
            })
        }
        labels = {'mpesa_code': 'M-Pesa Transaction Code'}

    def clean_mpesa_code(self):
        code = self.cleaned_data['mpesa_code'].strip().upper()
        if RegistrationPayment.objects.filter(mpesa_code=code).exists():
            raise forms.ValidationError('This M-Pesa code has already been submitted.')
        return code
