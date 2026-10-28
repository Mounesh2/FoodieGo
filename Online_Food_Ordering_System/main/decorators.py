from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        profile = getattr(request.user, 'profile', None)
        if (
            request.user.is_superuser
            or request.user.is_staff
            or (profile and profile.role == 'ADMIN')
        ):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Administrator privileges required to access this area.")
        return redirect('main:home')
    return wrapper_func


def restaurant_required(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        profile = getattr(request.user, 'profile', None)
        is_staff = (
            request.user.is_superuser
            or request.user.is_staff
            or (profile and (profile.role == 'RESTAURANT' or profile.role == 'ADMIN'))
            or request.user.groups.filter(name='admin_owner').exists()
        )
        if is_staff:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access restricted to registered restaurant partners.")
        return redirect('main:home')
    return wrapper_func


def delivery_required(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        profile = getattr(request.user, 'profile', None)
        is_rider = (
            request.user.is_superuser
            or (profile and (profile.role == 'DELIVERY' or profile.role == 'ADMIN'))
            or request.user.groups.filter(name='delivery_partner').exists()
        )
        if is_rider:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access restricted to verified delivery partners.")
        return redirect('main:home')
    return wrapper_func