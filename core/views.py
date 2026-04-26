from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

from .models import User, Cycle, Savings, InterestDistribution, SMSLog, RegistrationPayment
from .forms import MemberRegistrationForm, LoginForm, RecordSavingsForm, AddSavingsForm, SendSMSForm, RegistrationPaymentForm
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
def add_savings(request):
    if request.user.role == 'admin':
        return redirect('record_savings')
    form = AddSavingsForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        saving = form.save(commit=False)
        saving.member = request.user
        saving.cycle = Cycle.get_current()
        saving.recorded_by = request.user
        saving.save()
        if not saving.member.is_active_member and saving.member.total_savings >= 50:
            saving.member.is_active_member = True
            saving.member.registration_fee_paid = True
            saving.member.save()
        messages.success(request, f'Savings of KES {saving.amount} recorded successfully!')
        return redirect('add_savings')
    recent = Savings.objects.filter(member=request.user).order_by('-date')[:8]
    interest_earned = InterestDistribution.objects.filter(member=request.user).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    return render(
        request,
        'core/add_savings.html',
        {
            'form': form,
            'recent': recent,
            'cycle': Cycle.get_current(),
            'total_savings': request.user.total_savings,
            'loan_limit': request.user.available_loan_limit,
            'loan_level': request.user.loan_level,
            'interest_earned': interest_earned,
        },
    )


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


@login_required
def guarantors(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    from loans.models import Guarantor
    
    # Handle approval/rejection
    if request.method == 'POST':
        guarantor_id = request.POST.get('guarantor_id')
        action = request.POST.get('action')
        guarantor = get_object_or_404(Guarantor, pk=guarantor_id)
        
        if action == 'approve':
            guarantor.status = 'approved'
            guarantor.approved_by = request.user
            guarantor.approved_at = timezone.now()
            guarantor.save()
            messages.success(request, f'{guarantor.member} approved as guarantor for Loan #{guarantor.loan.pk}')
        elif action == 'reject':
            guarantor.status = 'rejected'
            guarantor.approved_by = request.user
            guarantor.approved_at = timezone.now()
            guarantor.save()
            messages.warning(request, f'{guarantor.member} rejected as guarantor for Loan #{guarantor.loan.pk}')
        
        return redirect('guarantors')
    
    # Get all guarantors
    guarantors = Guarantor.objects.select_related('loan', 'loan__member', 'member', 'approved_by').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        guarantors = guarantors.filter(status=status_filter)
    
    # Get stats
    pending_count = Guarantor.objects.filter(status='pending').count()
    approved_count = Guarantor.objects.filter(status='approved').count()
    rejected_count = Guarantor.objects.filter(status='rejected').count()
    
    return render(request, 'core/guarantors.html', {
        'guarantors': guarantors,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })


@login_required
def recovery_log(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    from loans.models import Loan, Recovery
    loans = Loan.objects.filter(status='defaulted').select_related('member').order_by('-applied_date')
    recovery_logs = Recovery.objects.select_related('loan', 'loan__member', 'recorded_by').order_by('-recorded_at')
    return render(request, 'core/recovery_log.html', {'loans': loans, 'recovery_logs': recovery_logs})


@login_required
def loan_checker(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    query = request.GET.get('q', '')
    members = []
    results = []
    
    if query:
        from django.db.models import Q
        members = User.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(phone__icontains=query) |
            Q(id_number__icontains=query),
            role='member'
        ).select_related()
        
        # Check loan eligibility for each member
        for member in members:
            from loans.models import Loan
            
            # Get member's active loans
            active_loans = Loan.objects.filter(member=member, status='active').count()
            
            # Qualification criteria
            is_active = member.is_active_member
            has_savings = member.total_savings > 0
            days_in_group = member.days_in_group
            min_days = 30  # Minimum days in group
            credit_score = member.credit_score
            min_credit = 40  # Minimum credit score
            available_limit = member.available_loan_limit
            can_borrow = available_limit > 0
            max_active_loans = 1  # Only 1 active loan at a time
            
            # Determine qualification status
            qualifies = (
                is_active and 
                has_savings and 
                days_in_group >= min_days and 
                credit_score >= min_credit and 
                can_borrow and 
                active_loans < max_active_loans
            )
            
            # Determine reasons for not qualifying
            reasons = []
            if not is_active:
                reasons.append("Not an active member")
            if not has_savings:
                reasons.append("No savings recorded")
            if days_in_group < min_days:
                reasons.append(f"Only {days_in_group} days in group (need {min_days})")
            if credit_score < min_credit:
                reasons.append(f"Credit score {credit_score}/100 (need {min_credit})")
            if not can_borrow:
                reasons.append("Loan limit exhausted")
            if active_loans >= max_active_loans:
                reasons.append(f"Already has {active_loans} active loan(s)")
            
            results.append({
                'member': member,
                'qualifies': qualifies,
                'reasons': reasons,
                'total_savings': member.total_savings,
                'available_limit': available_limit,
                'loan_level': member.loan_level,
                'credit_score': credit_score,
                'days_in_group': days_in_group,
                'active_loans': active_loans,
            })
    
    return render(request, 'core/loan_checker.html', {
        'results': results,
        'query': query,
        'members': members
    })

@login_required
def admin_statements(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    query = request.GET.get('q', '')
    selected_member = None
    member_data = None
    
    if query:
        from django.db.models import Q
        # Search for members
        members = User.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(phone__icontains=query) |
            Q(id_number__icontains=query),
            role='member'
        ).order_by('first_name')
        
        # If there's a specific member ID selected
        member_id = request.GET.get('member_id')
        if member_id:
            try:
                selected_member = User.objects.get(pk=member_id, role='member')
                # Get member's financial data
                savings = selected_member.savings_set.all().order_by('-date')
                loans = selected_member.loans.all().order_by('-applied_date')
                interest = selected_member.interestdistribution_set.all().order_by('-date')
                
                member_data = {
                    'member': selected_member,
                    'savings': savings,
                    'loans': loans,
                    'interest': interest,
                }
            except User.DoesNotExist:
                selected_member = None
    else:
        members = []
    
    return render(request, 'core/admin_statements.html', {
        'query': query,
        'members': members if query and not selected_member else [],
        'selected_member': selected_member,
        'member_data': member_data,
    })