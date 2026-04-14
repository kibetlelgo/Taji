from django.contrib import admin
from .models import Loan, LoanRepayment


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['id', 'member', 'principal', 'outstanding_balance', 'status', 'applied_date', 'due_date']
    list_filter = ['status', 'loan_level']


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'amount_paid', 'interest_portion', 'principal_portion', 'payment_date']
