
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, View
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum

from accounts.models import User 

from accounts.models import UserBankAccount
from accounts.constants import MANAGER, PENDING, ACTIVE
from transactions.models import LoanApplication, Transaction
from transactions.constants import LOAN

#add5
from django.views.generic.detail import DetailView 
from accounts.constants import CUSTOMER, FROZEN, ACTIVE

# Define constants from the loan model here or import them
LOAN_PENDING = 'pending'
LOAN_APPROVED = 'approved'
LOAN_DENIED = 'denied'


class ManagerRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != MANAGER:
            messages.error(
                self.request,
                "You do not have permission to access this page."
            )
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class ManagerDashboardView(ManagerRequiredMixin, TemplateView):
    template_name = "manager/dashboard.html"
    model = UserBankAccount # Base model for the view
    context_object_name = "accounts" # Default context name

    def get_context_data(self, **kwargs):
        # Get the default context from the parent class
        context = super().get_context_data(**kwargs)

        # --- Query for the STAT CARDS ---
        # Get counts for different user/account types
        context['total_customers'] = User.objects.filter(role=CUSTOMER).count()
        context['active_accounts'] = UserBankAccount.objects.filter(status=ACTIVE).count()
        context['pending_accounts_count'] = UserBankAccount.objects.filter(status=PENDING).count()
        context['pending_loans_count'] = LoanApplication.objects.filter(status='pending').count()
        
        # Calculate total assets in the bank
        total_assets_query = UserBankAccount.objects.aggregate(total=Sum('balance'))
        context['total_assets'] = total_assets_query['total'] or 0 # Use 0 if bank is empty

        # --- Query for the RECENT ACTIVITY TABLES ---
        # Get the 5 most recently registered customers
        context['recent_customers'] = User.objects.filter(
            role=CUSTOMER
        ).order_by('-date_joined')[:5]

        # Get the 5 most recent high-value transactions (e.g., > $1000)
        context['recent_transactions'] = Transaction.objects.filter(
            amount__gt=1000
        ).order_by('-timestamp')[:5]

        return context


class PendingAccountsListView(ManagerRequiredMixin, ListView):
    model = UserBankAccount
    template_name = 'manager/pending_accounts_list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return UserBankAccount.objects.filter(status=PENDING).select_related('user')


class ApproveAccountView(ManagerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # ... this view is correct and unchanged
        account_pk = self.kwargs.get('pk')
        try:
            account = UserBankAccount.objects.get(pk=account_pk)
            account.status = ACTIVE
            account.save()
            messages.success(
                self.request,
                f"Account #{account.account_no} has been approved successfully."
            )
        except UserBankAccount.DoesNotExist:
            messages.error(
                self.request,
                "The requested account does not exist."
            )

        return redirect(reverse_lazy("manager:pending_accounts"))


class DenyAccountView(ManagerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # ... this view is correct and unchanged
        account_pk = self.kwargs.get('pk')
        try:
            account = UserBankAccount.objects.get(pk=account_pk)
            user_to_delete = account.user
            account_no = account.account_no
            user_to_delete.delete()
            messages.success(
                self.request,
                f"Account request for former account #{account_no} has been denied."
            )
        except UserBankAccount.DoesNotExist:
            messages.error(
                self.request,
                "The requested account does not exist."
            )

        return redirect(reverse_lazy("manager:pending_accounts"))


# --- LOAN VIEWS ---

class PendingLoansListView(ManagerRequiredMixin, ListView):
    model = LoanApplication
    template_name = 'manager/pending_loans_list.html'
    context_object_name = 'loans'
    
    def get_queryset(self):
        return LoanApplication.objects.filter(status=LOAN_PENDING).select_related('user_account__user')


class ApproveLoanView(ManagerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        loan_pk = self.kwargs.get('pk')
        try:
            with transaction.atomic():
                loan = LoanApplication.objects.get(pk=loan_pk, status=LOAN_PENDING)
                account = loan.user_account
                
                loan.status = LOAN_APPROVED
                loan.approval_date = timezone.now()
                loan.save()

                account.balance += loan.amount
                account.save(update_fields=['balance'])

                Transaction.objects.create(
                    account=account,
                    amount=loan.amount,
                    balance_after_transaction=account.balance,
                    transaction_type=LOAN
                )
                
                messages.success(
                    request,
                    f"Loan #{loan.pk} for {account.user.email} has been approved."
                )
        except LoanApplication.DoesNotExist:
            messages.error(request, "This loan application does not exist or has already been processed.")

        return redirect(reverse_lazy("manager:pending_loans"))


class DenyLoanView(ManagerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        loan_pk = self.kwargs.get('pk')
        try:
            loan = LoanApplication.objects.get(pk=loan_pk, status=LOAN_PENDING)
            loan.status = LOAN_DENIED
            loan.save()
            messages.info(
                request,
                f"Loan #{loan.pk} for {loan.user_account.user.email} has been denied."
            )
        except LoanApplication.DoesNotExist:
            messages.error(request, "This loan application does not exist or has already been processed.")
            
        return redirect(reverse_lazy("manager:pending_loans"))

#add5
class CustomerListView(ManagerRequiredMixin, ListView):
    model = UserBankAccount
    template_name = 'manager/customer_list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        # We only want to see users who are customers and have active accounts
        return UserBankAccount.objects.filter(user__role=CUSTOMER)


class CustomerDetailView(ManagerRequiredMixin, DetailView):
    model = UserBankAccount
    template_name = 'manager/customer_detail.html'
    context_object_name = 'customer'
    # Use 'pk' from URL to look up the UserBankAccount
    pk_url_kwarg = 'pk'


class FreezeAccountView(ManagerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        account_pk = self.kwargs.get('pk')
        try:
            account = UserBankAccount.objects.get(pk=account_pk)
            
            if account.status == FROZEN:
                account.status = ACTIVE
                messages.success(request, f"Account #{account.account_no} has been unfrozen.")
            else:
                account.status = FROZEN
                messages.warning(request, f"Account #{account.account_no} has been frozen.")
            
            account.save(update_fields=['status'])

        except UserBankAccount.DoesNotExist:
            messages.error(request, "This account does not exist.")

        return redirect('manager:customer_detail', pk=account_pk)