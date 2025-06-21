from django.urls import path

from .views_manager import (
    CustomerListView,
    CustomerDetailView,
    FreezeAccountView,
    ManagerDashboardView,
    PendingAccountsListView,
    ApproveAccountView,
    DenyAccountView,
    PendingLoansListView,
    ApproveLoanView,
    DenyLoanView as ManagerDenyLoanView, # Use an alias to avoid name clash
)

from transactions.views import TransactionRepostView


app_name = 'manager'

urlpatterns = [
    # Account Management URLs
    path(
        "dashboard/",
        ManagerDashboardView.as_view(),
        name="dashboard"
    ),
    path(
        "pending-accounts/",
        PendingAccountsListView.as_view(),
        name="pending_accounts"
    ),
    path(
        "approve-account/<int:pk>/",
        ApproveAccountView.as_view(),
        name="approve_account"
    ),
    path(
        "deny-account/<int:pk>/",
        DenyAccountView.as_view(), # This is for denying an account registration
        name="deny_account"
    ),

    # Loan Management URLs
    path(
        "pending-loans/",
        PendingLoansListView.as_view(),
        name="pending_loans"
    ),
    path(
        "approve-loan/<int:pk>/",
        ApproveLoanView.as_view(),
        name="approve_loan"
    ),
    # --- THIS IS THE CORRECTED LINE ---
    path(
        "deny-loan/<int:pk>/",
        ManagerDenyLoanView.as_view(), # This is for denying a loan request
        name="deny_loan"
    ),

    #add5
    path("customers/", CustomerListView.as_view(), name="customer_list"),
    path(
        "customer/<int:pk>/",
        CustomerDetailView.as_view(),
        name="customer_detail"
    ),
    path(
        "customer/<int:pk>/freeze/",
        FreezeAccountView.as_view(),
        name="freeze_account"
    ),
    # This URL uses the customer-facing view but is namespaced for managers
    path(
        "customer/report/",
        TransactionRepostView.as_view(),
        name="customer_report"
    ),
]