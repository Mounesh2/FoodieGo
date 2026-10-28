from .models import CartItems

def cart_context(request):
    if request.user.is_authenticated:
        count = sum(ci.quantity for ci in CartItems.objects.filter(user=request.user, ordered=False))
        profile = getattr(request.user, 'profile', None)
        role = profile.role if profile else ('ADMIN' if request.user.is_superuser else 'CUSTOMER')
        restaurant = profile.restaurant if profile else None
        return {
            'cart_count': count,
            'current_user_role': role,
            'user_restaurant': restaurant,
            'is_restaurant_role': role in ['RESTAURANT', 'ADMIN'] or request.user.is_superuser,
            'is_delivery_role': role in ['DELIVERY', 'ADMIN'] or request.user.is_superuser,
            'is_admin_role': role == 'ADMIN' or request.user.is_superuser or request.user.is_staff,
        }
    return {
        'cart_count': 0,
        'current_user_role': 'GUEST',
        'user_restaurant': None,
        'is_restaurant_role': False,
        'is_delivery_role': False,
        'is_admin_role': False,
    }

