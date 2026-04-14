from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Cycle, Savings, InterestDistribution, SMSLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'phone', 'role', 'is_active_member', 'credit_score', 'total_savings']
    list_filter = ['role', 'is_active_member']
    fieldsets = UserAdmin.fieldsets + (
        ('Taji Info', {'fields': ('role', 'phone', 'id_number', 'registration_fee_paid', 'date_joined_group', 'is_active_member', 'credit_score')}),
    )


@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = ['cycle_number', 'start_date', 'end_date', 'is_active']


@admin.register(Savings)
class SavingsAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'date', 'cycle']
    list_filter = ['cycle']


admin.site.register(InterestDistribution)
admin.site.register(SMSLog)
