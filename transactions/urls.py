from django.urls import path

from .views import (
    DepositMoneyView,
    WithdrawMoneyView,
    TransactionRepostView,
    FundTransferView,
    LoanRequestView,
    LoanListView,
)

app_name = 'transactions'

urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("transfer/", FundTransferView.as_view(), name="transfer_money"),
    
    # These are the correct customer-facing loan URLs
    path("request-loan/", LoanRequestView.as_view(), name="request_loan"),
    path("loans/", LoanListView.as_view(), name="loan_list"),
]