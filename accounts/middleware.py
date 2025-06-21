from .constants import MANAGER

class RoleBasedSessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # This code is executed for each request before the view is called.

        # We only care about authenticated users.
        if request.user.is_authenticated:
            # Check if the user is a manager or a superuser.
            if request.user.role == MANAGER or request.user.is_superuser:
                # Set a 5-minute (300 seconds) timeout for managers.
                request.session.set_expiry(250)
            # else:
            #   Customers will automatically fall back to the default
            #   SESSION_COOKIE_AGE (120 seconds) set in settings.py.
            #   So no action is needed here for customers.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response