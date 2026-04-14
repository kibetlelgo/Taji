from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal

from .models import Loan, LoanRepayment
from .forms import LoanApplicationForm, RecordRepaymentForm
from core.models import Cycle
from core.utils import distribute_interest, update_credit_score, send_sms


@login_required
def apply_loan(request):
    member = request.user
    if not member.is_active_member:
        messages.error(request, 'Your account is not yet active. Please pay the registration fee.')
        return redirect('dashboard')
    if member.loans.filter(status='active').exists():
        messages.error(request, 'You already have an active loan.')
        return redirect('dashboard')

    form = LoanApplicationForm(member=member, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        loan = form.save(commit=False)
        loan.member = member
        loan.cycle = Cycle.get_current()
        loan.loan_level = member.loan_level
        loan.save()
        # Auto-approve based on eligibility
        loan.approve()
        update_credit_score(member, 'consistent_saving')
        messages.success(
            request,
            f'Loan approved. KES {loan.amount_disbursed:,.2f} will be disbursed after processing fee deduction.'
        )
        try:
            send_sms(member, f'Taji: Your loan of KES {loan.principal:,.2f} has been approved. You receive KES {loan.amount_disbursed:,.2f}. Repay by {loan.due_date}.')
        except Exception:
            pass
        return redirect('loan_detail', pk=loan.pk)

    context = {
        'form': form,
        'loan_limit': member.available_loan_limit,
        'loan_level': member.loan_level,
        'total_savings': member.total_savings,
    }
    return render(request, 'loans/apply.html', context)


@login_required
def loan_detail(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    if request.user.role != 'admin' and loan.member != request.user:
        return redirect('dashboard')
    repayments = loan.repayments.all()
    return render(request, 'loans/detail.html', {'loan': loan, 'repayments': repayments})


@login_required
def loan_list(request):
    if request.user.role == 'admin':
        loans = Loan.objects.all().select_related('member')
    else:
        loans = Loan.objects.filter(member=request.user)
    status_filter = request.GET.get('status', '')
    if status_filter:
        loans = loans.filter(status=status_filter)
    return render(request, 'loans/list.html', {'loans': loans, 'status_filter': status_filter})


@login_required
def record_repayment(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    loan = get_object_or_404(Loan, pk=pk, status='active')
    form = RecordRepaymentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        repayment = form.save(commit=False)
        repayment.loan = loan
        repayment.recorded_by = request.user
        repayment.balance_before = loan.outstanding_balance

        # Calculate interest and principal portions (reducing balance)
        monthly_rate = loan.interest_rate / Decimal('100') / Decimal('12')
        interest_due = (loan.outstanding_balance * monthly_rate).quantize(Decimal('0.01'))

        # Check early repayment (within 7 days of loan approval)
        days_since_approval = (timezone.now().date() - loan.approved_date).days if loan.approved_date else 999
        if days_since_approval <= 7:
            interest_due = (interest_due * Decimal('0.5')).quantize(Decimal('0.01'))
            repayment.is_early = True
            update_credit_score(loan.member, 'early_repayment')

        principal_paid = min(repayment.amount_paid - interest_due, loan.outstanding_balance)
        if principal_paid < 0:
            principal_paid = Decimal('0')
            interest_due = repayment.amount_paid

        repayment.interest_portion = interest_due
        repayment.principal_portion = principal_paid
        loan.outstanding_balance -= principal_paid
        repayment.balance_after = loan.outstanding_balance
        repayment.save()

        # Distribute interest to all members
        if interest_due > 0:
            from core.utils import distribute_interest
            distribute_interest(loan, interest_due)

        # Check if loan is fully paid
        if loan.outstanding_balance <= Decimal('0.01'):
            loan.outstanding_balance = Decimal('0')
            loan.status = 'completed'
            loan.completed_date = timezone.now().date()
            update_credit_score(loan.member, 'on_time_payment')

        # Check for late payment
        if loan.is_overdue:
            update_credit_score(loan.member, 'late_payment')

        loan.save()
        messages.success(request, f'Repayment of KES {repayment.amount_paid:,.2f} recorded.')
        try:
            send_sms(loan.member, f'Taji: Payment of KES {repayment.amount_paid:,.2f} received. Balance: KES {loan.outstanding_balance:,.2f}.')
        except Exception:
            pass
        return redirect('loan_detail', pk=loan.pk)

    return render(request, 'loans/repayment.html', {'loan': loan, 'form': form})
