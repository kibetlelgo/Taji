from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

from .models import User, Cycle, Savings, InterestDistribution, SMSLog, RegistrationPayment
from .forms import MemberRegistrationForm, LoginForm, RecordSavingsForm, SendSMSForm, RegistrationPaymentForm
from .utils import send_sms, check_and_rotate_cycle
from loans.models import Loan


def home(request):
    total_members = User.objects.filter(role='member', is_active_member=True).count()
    total_savings = Savings.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_loans = Loan.objects.filter(status__in=['active', 'completed']).count()
    cycle = Cycle.get_current()
    return render(request, 'core/home.html', {
        'total_members': total_members,
        'total_savings': total_savings,
        'total_loans': total_loans,
        'cycle': cycle,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def register(request):
    check_and_rotate_cycle()
    cycle = Cycle.get_current()
    form = MemberRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'member'
        user.date_joined_group = timezone.now().date()
        user.is_active_member = False  # pending fee payment
        user.save()
        messages.success(request, 'Registration successful. Please pay the KES 50 registration fee to activate your account.')
        return redirect('login')
    return render(request, 'core/register.html', {'form': form, 'cycle': cycle})


@login_required
def dashboard(request):
    check_and_rotate_cycle()
    user = request.user
    if user.role == 'admin':
        return redirect('admin_dashboard')
    cycle = Cycle.get_current()
    active_loan = Loan.objects.filter(member=user, status='active').first()
    recent_savings = Savings.objects.filter(member=user).order_by('-date')[:5]
    interest_earned = InterestDistribution.objects.filter(member=user).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    context = {
        'cycle': cycle,
        'active_loan': active_loan,
        'recent_savings': recent_savings,
        'interest_earned': interest_earned,
        'total_savings': user.total_savings,
        'loan_limit': user.available_loan_limit,
        'loan_level': user.loan_level,
        'rank': user.rank_category,
        'credit_score': user.credit_score,
    }
    return render(request, 'core/member_dashboard.html', context)


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    check_and_rotate_cycle()
    cycle = Cycle.get_current()
    members = User.objects.filter(role='member').order_by('-credit_score')
    total_savings = Savings.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    active_loans = Loan.objects.filter(status='active')
    pending_loans = Loan.objects.filter(status='pending')
    context = {
        'cycle': cycle,
        'members': members,
        'total_savings': total_savings,
        'active_loans': active_loans,
        'pending_loans': pending_loans,
        'total_members': members.count(),
        'active_loans_count': active_loans.count(),
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
def member_list(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    members = User.objects.filter(role='member').annotate(
        savings_total=Sum('savings__amount')
    ).order_by('-savings_total')
    return render(request, 'core/member_list.html', {'members': members})


@login_required
def member_detail(request, pk):
    if request.user.role != 'admin' and request.user.pk != pk:
        return redirect('dashboard')
    member = get_object_or_404(User, pk=pk)
    savings = Savings.objects.filter(member=member)
    loans = Loan.objects.filter(member=member)
    interest = InterestDistribution.objects.filter(member=member)
    return render(request, 'core/member_detail.html', {
        'member': member, 'savings': savings, 'loans': loans, 'interest': interest
    })


@login_required
def record_savings(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    form = RecordSavingsForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        saving = form.save(commit=False)
        saving.cycle = Cycle.get_current()
        saving.recorded_by = request.user
        saving.save()
        # Activate member if fee paid
        if not saving.member.is_active_member and saving.member.total_savings >= 50:
            saving.member.is_active_member = True
            saving.member.registration_fee_paid = True
            saving.member.save()
        messages.success(request, f'Savings of KES {saving.amount} recorded for {saving.member}.')
        return redirect('record_savings')
    recent = Savings.objects.order_by('-date')[:10]
    return render(request, 'core/record_savings.html', {'form': form, 'recent': recent})


@login_required
def activate_member(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    member = get_object_or_404(User, pk=pk)
    member.is_active_member = True
    member.registration_fee_paid = True
    if not member.date_joined_group:
        member.date_joined_group = timezone.now().date()
    member.save()
    messages.success(request, f'{member} has been activated.')
    return redirect('member_list')


@login_required
def send_sms_view(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    form = SendSMSForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        msg = form.cleaned_data['message']
        rtype = form.cleaned_data['recipient_type']
        if rtype == 'all':
            recipients = User.objects.filter(role='member', is_active_member=True, phone__isnull=False)
            for r in recipients:
                send_sms(r, msg)
            messages.success(request, f'SMS sent to {recipients.count()} members.')
        else:
            member = form.cleaned_data.get('member')
            if member:
                send_sms(member, msg)
                messages.success(request, f'SMS sent to {member}.')
        return redirect('send_sms')
    logs = SMSLog.objects.order_by('-sent_at')[:20]
    return render(request, 'core/send_sms.html', {'form': form, 'logs': logs})


@login_required
def member_statement(request, pk):
    if request.user.role != 'admin' and request.user.pk != pk:
        return redirect('dashboard')
    member = get_object_or_404(User, pk=pk)
    savings = Savings.objects.filter(member=member).order_by('date')
    loans = Loan.objects.filter(member=member)
    interest = InterestDistribution.objects.filter(member=member)
    return render(request, 'core/statement.html', {
        'member': member, 'savings': savings, 'loans': loans, 'interest': interest
    })


@login_required
def pay_registration_fee(request):
    member = request.user
    if member.is_active_member:
        messages.info(request, 'Your account is already active.')
        return redirect('dashboard')

    # Check if already submitted and pending
    existing = RegistrationPayment.objects.filter(member=member).first()
    if existing and existing.status == 'pending':
        messages.info(request, 'Your payment is already submitted and awaiting admin approval.')
        return redirect('dashboard')

    form = RegistrationPaymentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        payment = form.save(commit=False)
        payment.member = member
        payment.save()
        messages.success(request, f'M-Pesa code {payment.mpesa_code} submitted. Your account will be activated once verified.')
        return redirect('dashboard')

    return render(request, 'core/pay_registration.html', {'form': form, 'existing': existing})


@login_required
def admin_registration_payments(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    payments = RegistrationPayment.objects.select_related('member').order_by('-submitted_at')
    return render(request, 'core/registration_payments.html', {'payments': payments})


@login_required
def approve_registration_payment(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    from django.utils import timezone as tz
    payment = get_object_or_404(RegistrationPayment, pk=pk)
    action = request.POST.get('action')
    if action == 'approve':
        payment.status = 'approved'
        payment.reviewed_by = request.user
        payment.reviewed_at = tz.now()
        payment.save()
        member = payment.member
        member.is_active_member = True
        member.registration_fee_paid = True
        if not member.date_joined_group:
            member.date_joined_group = tz.now().date()
        member.save()
        messages.success(request, f'{member} activated successfully.')
    elif action == 'reject':
        payment.status = 'rejected'
        payment.reviewed_by = request.user
        payment.reviewed_at = tz.now()
        payment.save()
        messages.warning(request, f'Payment for {payment.member} rejected.')
    return redirect('admin_registration_payments')
