import functools

from django.shortcuts import redirect


def role_required(required_role: str):
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")
            if request.user.role != required_role:
                return redirect("accounts:login")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
