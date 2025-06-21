from django.contrib import admin

from .models import BankAccountType, User, UserAddress, UserBankAccount

#add3
# We are going to customize the display for UserBankAccount
class UserBankAccountAdmin(admin.ModelAdmin):
    # These are the fields that will be displayed in the list view
    list_display = ('account_no', 'user_email', 'get_user_fullname', 'balance', 'status')
    list_filter = ('status', 'account_type')
    search_fields = ('account_no', 'user__email')

    # A custom method to get the user's email from the related User object
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email' # Column header

    # A custom method to get the user's full name
    def get_user_fullname(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_user_fullname.short_description = 'Full Name' # Column header


admin.site.register(BankAccountType)
admin.site.register(User)
admin.site.register(UserAddress)

admin.site.register(UserBankAccount, UserBankAccountAdmin)
