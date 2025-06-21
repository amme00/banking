#add 
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import HttpResponseRedirect, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView

from .constants import MANAGER
from .forms import UserRegistrationForm, UserAddressForm
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit


User = get_user_model()


class UserRegistrationView(TemplateView):
    model = User
    #form_class = UserRegistrationForm
    template_name = 'accounts/user_registration.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(
                reverse_lazy('transactions:transaction_report')
            )
        return super().dispatch(request, *args, **kwargs)
    
    #add
    def get(self, request, *args, **kwargs):
        # On a GET request, we create fresh, empty instances of the forms.
        registration_form = UserRegistrationForm()
        address_form = UserAddressForm()
        context = self.get_context_data(
            registration_form=registration_form,
            address_form=address_form
        )
        return self.render_to_response(context)


    def post(self, request, *args, **kwargs):
        registration_form = UserRegistrationForm(self.request.POST)
        address_form = UserAddressForm(self.request.POST)

        if registration_form.is_valid() and address_form.is_valid():
            user = registration_form.save()
            address = address_form.save(commit=False)
            address.user = user
            address.save()

            messages.success(
                self.request,
                (
                    'Your account registration request has been submitted successfully. '
                    'You will be notified once it has been approved by a bank manager.'
                )
            )
            return HttpResponseRedirect(
                reverse_lazy('accounts:user_login')
            )

        return self.render_to_response(
            self.get_context_data(
                registration_form=registration_form,
                address_form=address_form
            )
        )

    def get_context_data(self, **kwargs):
       #add
        # if 'registration_form' not in kwargs:
        #     kwargs['registration_form'] = UserRegistrationForm()
        # if 'address_form' not in kwargs:
        #     kwargs['address_form'] = UserAddressForm()

        return super().get_context_data(**kwargs)


class UserLoginView(LoginView):
    template_name='accounts/user_login.html'
    redirect_authenticated_user = False

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        user = form.get_user()

        # Log the user in first.
        login(self.request, user)

        # Redirect based on role and status.
        # We will create the 'manager:dashboard' URL in the next phase.
        
        #add2
        if user.is_superuser or user.role == MANAGER:
            # Redirect to the new manager dashboard instead of the admin site.
            return HttpResponseRedirect(reverse_lazy('manager:dashboard'))

        # It's a customer, check their account object.
        # It's possible the account was deleted by an admin.
        if not hasattr(user, 'account'):
            logout(self.request)
            messages.error(self.request, "No bank account associated with this user. Please contact support.")
            return redirect('accounts:user_login')

        account_status = user.account.status
        if account_status == 'pending':
            logout(self.request)
            messages.warning(self.request, "Your account is pending approval. Please wait for a manager to review it.")
            return redirect('accounts:user_login')
        elif account_status == 'frozen':
            logout(self.request)
            messages.error(self.request, "Your account has been frozen. Please contact the bank for assistance.")
            return redirect('accounts:user_login')
        
        # If status is active, redirect to the success_url.
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        # Default redirect for active customers.
        return reverse_lazy('transactions:transaction_report')


class LogoutView(RedirectView):
    pattern_name = 'home'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        return super().get_redirect_url(*args, **kwargs)