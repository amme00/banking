import datetime

from django import forms
from django.conf import settings

from .models import Transaction, LoanApplication
#add3
from accounts.models import UserBankAccount
from accounts.constants import ACTIVE 


class TransactionForm(forms.ModelForm):

    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):

    def clean_amount(self):
        min_deposit_amount = settings.MINIMUM_DEPOSIT_AMOUNT
        amount = self.cleaned_data.get('amount')

        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )

        return amount
    

class FundTransferForm(TransactionForm):
    to_account_no = forms.IntegerField()

    def clean_to_account_no(self):
        to_account_no = self.cleaned_data.get('to_account_no')

        try:
            # Check if the destination account exists and is active
            to_account = UserBankAccount.objects.get(
                account_no=to_account_no, status=ACTIVE
            )
        except UserBankAccount.DoesNotExist:
            raise forms.ValidationError("The destination account does not exist or is not active.")
        
        # Check that the user is not transferring to their own account
        if self.account.account_no == to_account_no:
            raise forms.ValidationError("You cannot transfer money to your own account.")

        return to_account_no

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        # Check if sender has enough balance
        if self.account.balance < amount:
            raise forms.ValidationError(
                f'You do not have enough balance to make this transfer. '
                f'Your current balance is {self.account.balance} $.'
            )
        return amount

class WithdrawForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = settings.MINIMUM_WITHDRAWAL_AMOUNT
        max_withdraw_amount = (
            account.account_type.maximum_withdrawal_amount
        )
        balance = account.balance

        amount = self.cleaned_data.get('amount')

        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )

        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance} $ in your account. '
                'You can not withdraw more than your account balance'
            )

        return amount
   
#add4
class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model = LoanApplication
        fields = ['amount']

class TransactionDateRangeForm(forms.Form):
    daterange = forms.CharField(required=False)

    def clean_daterange(self):
        daterange = self.cleaned_data.get("daterange")
        print(daterange)

        try:
            daterange = daterange.split(' - ')
            print(daterange)
            if len(daterange) == 2:
                for date in daterange:
                    datetime.datetime.strptime(date, '%Y-%m-%d')
                return daterange
            else:
                raise forms.ValidationError("Please select a date range.")
        except (ValueError, AttributeError):
            raise forms.ValidationError("Invalid date range")
