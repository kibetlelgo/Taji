from django.db import models
from django.utils import timezone
from decimal import Decimal


class Loan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
    ]

    member = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='loans')
    cycle = models.ForeignKey('core.Cycle', on_delete=models.CASCADE, null=True, blank=True)
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    processing_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_disbursed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    repayment_months = models.IntegerField(default=1)
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateField(auto_now_add=True)
    approved_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('8.00'))
    loan_level = models.CharField(max_length=10, default='basic')

    class Meta:
        ordering = ['-applied_date']

    def __str__(self):
        return f"Loan #{self.pk} - {self.member} - KES {self.principal}"

    def calculate_installment(self):
        """Reducing balance monthly installment calculation."""
        r = self.interest_rate / Decimal('100') / Decimal('12')
        n = Decimal(str(self.repayment_months))
        p = self.principal
        if r == 0:
            return p / n
        installment = p * r * (1 + r) ** n / ((1 + r) ** n - 1)
        return installment.quantize(Decimal('0.01'))

    def approve(self):
        self.processing_fee = (self.principal * Decimal('0.02')).quantize(Decimal('0.01'))
        self.amount_disbursed = self.principal - self.processing_fee
        self.outstanding_balance = self.principal
        self.monthly_installment = self.calculate_installment()
        self.status = 'active'
        self.approved_date = timezone.now().date()
        self.due_date = timezone.now().date() + timezone.timedelta(days=30 * self.repayment_months)
        self.loan_level = self.member.loan_level
        self.save()

    @property
    def is_overdue(self):
        if self.due_date and self.status == 'active':
            return timezone.now().date() > self.due_date
        return False

    @property
    def days_overdue(self):
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0

    @property
    def late_penalty(self):
        if self.days_overdue > 0:
            months_late = Decimal(str(self.days_overdue)) / Decimal('30')
            return (self.outstanding_balance * Decimal('0.02') * months_late).quantize(Decimal('0.01'))
        return Decimal('0')


class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    principal_portion = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_portion = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_date = models.DateField(default=timezone.now)
    recorded_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)
    is_early = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Repayment of KES {self.amount_paid} for {self.loan}"
