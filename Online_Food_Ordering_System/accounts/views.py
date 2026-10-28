from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile, CustomerAddress
from .forms import NewUSerForm

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('main:home')

    if request.method == 'POST':
        form = NewUSerForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to FoodieGo, {user.username}! Your account is ready.")
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('main:home')
        else:
            messages.error(request, "Please correct the registration errors below.")
    else:
        form = NewUSerForm()
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('main:home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out of FoodieGo.")
    return redirect('main:home')


@login_required
def profile_view(request):
    """
    Page 9: Profile and Addresses.
    Allows user to view/update profile, manage saved delivery addresses, and view role credentials.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    saved_addresses = CustomerAddress.objects.filter(user=request.user)

    if request.method == 'POST' and 'update_profile' in request.POST:
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()

        request.user.first_name = first_name
        request.user.last_name = last_name
        if email:
            request.user.email = email
        request.user.save()

        profile.phone_number = phone
        if address:
            profile.address = address
        profile.save()

        messages.success(request, "Your profile details have been successfully updated.")
        return redirect('accounts:profile')

    context = {
        'profile': profile,
        'saved_addresses': saved_addresses,
        'orders_count': request.user.customer_orders.count(),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def add_address(request):
    """
    Add a new delivery address for the customer.
    """
    if request.method == 'POST':
        title = request.POST.get('title', 'Home').strip()
        address_line = request.POST.get('address_line', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        area = request.POST.get('area', 'Koramangala').strip()
        city = request.POST.get('city', 'Bengaluru').strip()
        pincode = request.POST.get('pincode', '560034').strip()
        phone = request.POST.get('phone', '').strip()
        is_default = request.POST.get('is_default') == 'on'

        if not address_line or len(address_line) < 5:
            messages.error(request, "Please enter a complete address line.")
            return redirect('accounts:profile')

        CustomerAddress.objects.create(
            user=request.user,
            title=title,
            address_line=address_line,
            landmark=landmark,
            area=area,
            city=city,
            pincode=pincode,
            phone=phone or getattr(request.user.profile, 'phone_number', ''),
            is_default=is_default
        )
        messages.success(request, f"New delivery address '{title}' saved successfully.")

    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('accounts:profile')


@login_required
def delete_address(request, pk):
    """
    Delete a saved delivery address.
    """
    addr = get_object_or_404(CustomerAddress, pk=pk, user=request.user)
    title = addr.title
    addr.delete()
    messages.info(request, f"Address '{title}' removed.")
    return redirect('accounts:profile')


@login_required
def set_default_address(request, pk):
    """
    Mark a saved address as the default delivery address.
    """
    addr = get_object_or_404(CustomerAddress, pk=pk, user=request.user)
    addr.is_default = True
    addr.save()
    messages.success(request, f"'{addr.title}' set as your default delivery address.")
    return redirect('accounts:profile')