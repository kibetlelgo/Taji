from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from decimal import Decimal


class User(AbstractUser):
    ROLE_CHOICES = [('admin', 'Admin'), ('member', 'Member')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    id_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    registration_fee_paid = models.BooleanField(default=False)
    date_joined_group = models.DateField(null=True, blank=True)
    is_active_member = models.BooleanField(default=False)
    credit_score = models.IntegerField(default=50)

    def __str__(self):
        return f"{self.get_full_name() or self.username}"

    @property
    def days_in_group(self):
        if self.date_joined_group:
            return (timezone.now().date() - self.date_joined_group).days
        return 0

    @property
    def loan_level(self):
        days = self.days_in_group
        if days >= 100:
            return 'premium'
        elif days >= 60:
            return 'full'
        return 'basic'

    @property
    def loan_limit_percentage(self):
        return {'basic': Decimal('0.75'), 'full': Decimal('0.80'), 'premium': Decimal('0.90')}[self.loan_level]

    @property
    def total_savings(self):
        return self.savings_set.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

    @property
    def available_loan_limit(self):
        return self.total_savings * self.loan_limit_percentage

    @property
    def rank_category(self):
        savings = self.total_savings
        if savings >= 10000:
            return 'Top Saver'
        elif savings >= 5000:
            return 'Strong Saver'
        return 'Rising Saver'


class Cycle(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    cycle_number = models.IntegerField(default=1)

    class Meta:
        ordering = ['-cycle_number']

    def __str__(self):
        return f"Cycle {self.cycle_number} ({self.start_date} - {self.end_date})"

    @classmethod
    def get_current(cls):
        return cls.objects.filter(is_active=True).first()

    @classmethod
    def create_next(cls):
        last = cls.objects.order_by('-cycle_number').first()
        if last:
            start = last.end_date + timezone.timedelta(days=1)
            number = last.cycle_number + 1
        else:
            start = timezone.now().date()
            number = 1
        end = start + timezone.timedelta(days=59)
        last and cls.objects.filter(is_active=True).update(is_active=False)
        return cls.objects.create(start_date=start, end_date=end, cycle_number=number, is_active=True)


class Savings(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_savings')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.member} - KES {self.amount} on {self.date}"


class InterestDistribution(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    source_loan_id = models.IntegerField(null=True, blank=True)  # avoid circular FK
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.member} earned KES {self.amount} interest"


class RegistrationPayment(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]
    member = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reg_payment')
    mpesa_code = models.CharField(max_length=20, unique=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_payments')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.member} – {self.mpesa_code} ({self.status})"


class SMSLog(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent')

    def __str__(self):
        return f"SMS to {self.recipient} at {self.sent_at}"


class Guarantor(models.Model):
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='guarantors')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guaranteed_loans')
    status = models.CharField(max_length=20, default='pending')  # pending, approved, rejected
    agreed_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='guarantor_responses')

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.member} - Guarantee for Loan #{self.loan_id}"


class RecoveryLog(models.Model):
    ACTION_CHOICES = [
        ('sms_sent', 'SMS Sent'),
        ('phone_call', 'Phone Call'),
        ('visit', 'Home Visit'),
        ('legal_notice', 'Legal Notice'),
        ('write_off', 'Write Off'),
        ('partial_payment', 'Partial Payment'),
        ('full_payment', 'Full Payment'),
    ]
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='recovery_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recovery_logs')
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.get_action_display()} - Loan #{self.loan_id} - {self.recorded_at}"
