import requests
from django.conf import settings
from decimal import Decimal
from .models import SMSLog, InterestDistribution, User


def send_sms(recipient_user, message):
    """Send SMS via BlessedTexts and log it."""
    phone = recipient_user.phone
    if phone and not phone.startswith('+'):
        phone = '+254' + phone.lstrip('0')
    
    try:
        status = _send_sms_blessedtexts(phone, message)
    except Exception as e:
        status = f'failed: {str(e)}'
    
    SMSLog.objects.create(recipient=recipient_user, message=message, status=status)
    return status


def _send_sms_blessedtexts(phone, message):
    """Send SMS via BlessedTexts API."""
    import logging
    logger = logging.getLogger(__name__)
    
    api_key = getattr(settings, 'BLESSEDTEXTS_API_KEY', '')
    sender_id = getattr(settings, 'BLESSEDTEXTS_SENDER_ID', 'BLESSEDTEXTS')
    
    # Format phone: remove +254, keep local format (e.g., 714952656)
    phone_for_api = phone.replace('+254', '').lstrip('0')
    
    url = "https://blessedtexts.com/api/send"
    payload = {
        "apikey": api_key,
        "senderid": sender_id,
        "number": phone_for_api,
        "message": message
    }
    logger.info(f"BlessedTexts request: {payload}")
    response = requests.post(url, json=payload, timeout=30)
    logger.info(f"BlessedTexts response: {response.status_code} - {response.text}")
    if response.status_code == 200:
        return 'sent'
    return f'failed: {response.status_code} - {response.text}'


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
