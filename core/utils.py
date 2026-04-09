import africastalking
from django.conf import settings
from decimal import Decimal
from .models import SMSLog, InterestDistribution, User


def send_sms(recipient_user, message):
    """Send SMS via Africa's Talking and log it."""
    try:
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        sms = africastalking.SMS
        phone = recipient_user.phone
        if phone and not phone.startswith('+'):
            phone = '+254' + phone.lstrip('0')
        response = sms.send(message, [phone], settings.AT_SENDER_ID)
        status = 'sent'
    except Exception as e:
        status = f'failed: {str(e)}'
    SMSLog.objects.create(recipient=recipient_user, message=message, status=status)
    return status


def distribute_interest(loan, interest_amount):
    """Distribute interest proportionally among all active members."""
    from .models import Savings
    members = User.objects.filter(role='member', is_active_member=True)
    total_savings = sum(m.total_savings for m in members)
    if total_savings == 0:
        return
    for member in members:
        member_savings = member.total_savings
        if member_savings > 0:
            share = (member_savings / total_savings) * interest_amount
            share = share.quantize(Decimal('0.01'))
            InterestDistribution.objects.create(
                member=member,
                amount=share,
                source_loan_id=loan.pk,
                notes=f"Interest share from Loan #{loan.pk}"
            )
            Savings.objects.create(
                member=member,
                amount=share,
                notes=f"Interest distribution from Loan #{loan.pk}",
                cycle=loan.cycle,
            )


def update_credit_score(member, action):
    """Adjust credit score based on member actions."""
    adjustments = {
        'on_time_payment': +5,
        'early_repayment': +10,
        'consistent_saving': +2,
        'late_payment': -10,
        'default': -25,
    }
    delta = adjustments.get(action, 0)
    member.credit_score = max(0, min(100, member.credit_score + delta))
    member.save(update_fields=['credit_score'])


def check_and_rotate_cycle():
    """Check if current cycle has ended and create next one."""
    from .models import Cycle
    from django.utils import timezone
    current = Cycle.get_current()
    if current and timezone.now().date() > current.end_date:
        Cycle.create_next()
