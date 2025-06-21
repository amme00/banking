from django.db import models

from .constants import TRANSACTION_TYPE_CHOICES
from accounts.models import UserBankAccount

#add4
PENDING = 'pending'
APPROVED = 'approved'
DENIED = 'denied'

LOAN_STATUS_CHOICES = (
    (PENDING, 'Pending'),
    (APPROVED, 'Approved'),
    (DENIED, 'Denied'),
)


class Transaction(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='transactions',
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    balance_after_transaction = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    transaction_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.account.account_no)

    class Meta:
        ordering = ['timestamp']

#add4
class LoanApplication(models.Model):
    user_account = models.ForeignKey(
        UserBankAccount,
        related_name='loan_applications',
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    status = models.CharField(
        max_length=10,
        choices=LOAN_STATUS_CHOICES,
        default=PENDING
    )
    application_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Loan for {self.user_account.user.email} - {self.status}"
