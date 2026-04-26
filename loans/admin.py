from django.contrib import admin
from .models import Loan, LoanRepayment, Recovery, Guarantor


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['id', 'member', 'principal', 'outstanding_balance', 'status', 'applied_date', 'due_date']
    list_filter = ['status', 'loan_level']


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'amount_paid', 'interest_portion', 'principal_portion', 'payment_date']


@admin.register(Recovery)
class RecoveryAdmin(admin.ModelAdmin):
    list_display = ['loan', 'action', 'amount', 'recorded_by', 'recorded_at']
    list_filter = ['action', 'recorded_at']
    search_fields = ['loan__member__first_name', 'loan__member__last_name', 'notes']


@admin.register(Guarantor)
class GuarantorAdmin(admin.ModelAdmin):
    list_display = ['loan', 'member', 'status', 'created_at', 'approved_by']
    list_filter = ['status', 'created_at']
    search_fields = ['member__first_name', 'member__last_name', 'loan__member__first_name']
