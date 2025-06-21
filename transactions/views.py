from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView

from django.db import transaction
from accounts.models import UserBankAccount 


from transactions.constants import DEPOSIT, WITHDRAWAL,TRANSFER
from transactions.forms import (
    DepositForm,
    TransactionDateRangeForm,
    WithdrawForm,
    FundTransferForm,
)
from transactions.models import Transaction,LoanApplication
from .forms import LoanApplicationForm

#add5
from accounts.constants import MANAGER



class TransactionRepostView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    form_data = {}

    def get(self, request, *args, **kwargs):
        form = TransactionDateRangeForm(request.GET or None)
        if form.is_valid():
            self.form_data = form.cleaned_data

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        #add5
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )

        if self.request.user.role == MANAGER:
            customer_id = self.request.GET.get('customer_id')
            if customer_id:
                queryset = super().get_queryset().filter(
                    account__pk=customer_id
                )

        daterange = self.form_data.get("daterange")

        if daterange:
            queryset = queryset.filter(timestamp__date__range=daterange)

        return queryset.distinct()


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Determine which account's details to show
        target_account = self.request.user.account
        if self.request.user.role == MANAGER:
            customer_id = self.request.GET.get('customer_id')
            if customer_id:
                try:
                    target_account = UserBankAccount.objects.get(pk=customer_id)
                except UserBankAccount.DoesNotExist:
                    # Fallback to the manager's own account if customer not found
                    pass
        
        context.update({
            'account': target_account,
            'form': TransactionDateRangeForm(self.request.GET or None)
        })

        return context


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    # template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transactions:transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })

        return context


class DepositMoneyView(TransactionCreateMixin):
    template_name = 'transactions/transaction_form.html'
    form_class = DepositForm
    title = 'Deposit Money to Your Account'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account

        if not account.initial_deposit_date:
            now = timezone.now()
            next_interest_month = int(
                12 / account.account_type.interest_calculation_per_year
            )
            account.initial_deposit_date = now
            account.interest_start_date = (
                now + relativedelta(
                    months=+next_interest_month
                )
            )

        account.balance += amount
        account.save(
            update_fields=[
                'initial_deposit_date',
                'balance',
                'interest_start_date'
            ]
        )

        messages.success(
            self.request,
            f'{amount}$ was deposited to your account successfully'
        )

        return super().form_valid(form)

class WithdrawMoneyView(TransactionCreateMixin):
    template_name = 'transactions/transaction_form.html'
    form_class = WithdrawForm
    title = 'Withdraw Money from Your Account'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')

        self.request.user.account.balance -= form.cleaned_data.get('amount')
        self.request.user.account.save(update_fields=['balance'])

        messages.success(
            self.request,
            f'Successfully withdrawn {amount}$ from your account'
        )

        return super().form_valid(form)

    #add3
class FundTransferView(TransactionCreateMixin):
    #add3
    template_name = 'transactions/transfer_form.html'

    form_class = FundTransferForm
    title = 'Transfer Money to Another Account'
    

    def get_initial(self):
        initial = {'transaction_type': TRANSFER}
        return initial

    def form_valid(self, form):
        # Use a database transaction to ensure all operations succeed or fail together.
        with transaction.atomic():
            amount = form.cleaned_data.get('amount')
            to_account_no = form.cleaned_data.get('to_account_no')

            # --- Debit from the sender's account ---
            sender_account = self.request.user.account
            sender_account.balance -= amount
            sender_account.save(update_fields=['balance'])
            # Create a transaction record for the sender
            Transaction.objects.create(
                account=sender_account,
                amount=amount,
                balance_after_transaction=sender_account.balance,
                transaction_type=TRANSFER,
            )

            # --- Credit to the recipient's account ---
            recipient_account = UserBankAccount.objects.get(account_no=to_account_no)
            recipient_account.balance += amount
            recipient_account.save(update_fields=['balance'])
            # Create a transaction record for the recipient
            Transaction.objects.create(
                account=recipient_account,
                amount=amount,
                balance_after_transaction=recipient_account.balance,
                transaction_type=TRANSFER,
            )

        messages.success(
            self.request,
            f'Successfully transferred {amount}$ to account #{to_account_no}.'
        )
        return super().form_valid(form)
    
    #add 4
class LoanRequestView(LoginRequiredMixin, CreateView):
    model = LoanApplication
    form_class = LoanApplicationForm
    template_name = 'transactions/loan_request_form.html'
    success_url = reverse_lazy('transactions:loan_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Request a Loan'
        return context

    def form_valid(self, form):
        # Assign the current user's account to the loan application
        form.instance.user_account = self.request.user.account
        messages.success(
            self.request,
            'Your loan request has been submitted successfully. '
            'A manager will review it shortly.'
        )
        return super().form_valid(form)


class LoanListView(LoginRequiredMixin, ListView):
    model = LoanApplication
    template_name = 'transactions/loan_list.html'
    context_object_name = 'loans'

    def get_queryset(self):
        # A customer can only see their own loan applications
        return LoanApplication.objects.filter(user_account=self.request.user.account)