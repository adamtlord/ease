from functools import wraps
from django.http import HttpResponseRedirect
from django.shortcuts import redirect


def profile_signed(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.profile.is_profile_completed:
            return view_func(request, *args, **kwargs)
        else:
            return redirect('dashboard')

    return wrapped_view


def anonymous_required(view_function, redirect_to=None):
    return AnonymousRequired(view_function, redirect_to)


class AnonymousRequired(object):
    def __init__(self, view_function, redirect_to):
        if redirect_to is None:
            from django.conf import settings
            redirect_to = settings.LOGIN_REDIRECT_URL
        self.view_function = view_function
        self.redirect_to = redirect_to

    def __call__(self, request, *args, **kwargs):
        if request.user is not None and request.user.is_authenticated():
            return HttpResponseRedirect(self.redirect_to)
        return self.view_function(request, *args, **kwargs)
