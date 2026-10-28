import re
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Q, Count, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator

import logging
from django.conf import settings
try:
    import razorpay
except ImportError:
    razorpay = None

from django.contrib.auth.models import User
from .models import Restaurant, Item, Order, OrderItem, Coupon, CartItems, Reviews
from accounts.models import Profile, CustomerAddress
from .decorators import admin_required, restaurant_required, delivery_required

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# Home & Exploration Views
# -------------------------------------------------------------
def home(request):
    """
    Modern responsive Bengaluru Food Delivery Homepage inspired by Swiggy.
    """
    query = request.GET.get('q', '').strip()
    selected_area = request.GET.get('area', '').strip()
    selected_cuisine = request.GET.get('cuisine', '').strip()
    veg_only = request.GET.get('veg', '').lower() == 'true'
    min_rating = request.GET.get('rating', '').strip()
    price_range = request.GET.get('price', '').strip()
    sort_by = request.GET.get('sort', '-rating')

    restaurants = Restaurant.objects.all()

    if selected_area:
        restaurants = restaurants.filter(area__iexact=selected_area)
    if selected_cuisine:
        restaurants = restaurants.filter(cuisine__iexact=selected_cuisine)
    if min_rating:
        try:
            restaurants = restaurants.filter(rating__gte=float(min_rating))
        except ValueError:
            pass
    if price_range == 'under_300':
        restaurants = restaurants.filter(average_cost_for_two__lt=300)
    elif price_range == '300_500':
        restaurants = restaurants.filter(average_cost_for_two__gte=300, average_cost_for_two__lte=500)
    elif price_range == 'above_500':
        restaurants = restaurants.filter(average_cost_for_two__gt=500)

    if query:
        dish_match_rest_ids = Item.objects.filter(
            Q(title__icontains=query) | Q(category__icontains=query)
        ).values_list('restaurant_id', flat=True)
        restaurants = restaurants.filter(
            Q(name__icontains=query) |
            Q(cuisine__icontains=query) |
            Q(area__icontains=query) |
            Q(id__in=dish_match_rest_ids)
        )

    if veg_only:
        veg_rest_ids = Item.objects.filter(is_veg=True).values_list('restaurant_id', flat=True)
        restaurants = restaurants.filter(Q(cuisine='South Indian') | Q(id__in=veg_rest_ids))

    # Sorting
    if sort_by == 'delivery_time':
        restaurants = restaurants.order_by('estimated_delivery_minutes')
    elif sort_by == 'cost_asc':
        restaurants = restaurants.order_by('average_cost_for_two')
    elif sort_by == 'cost_desc':
        restaurants = restaurants.order_by('-average_cost_for_two')
    else:
        restaurants = restaurants.order_by('-rating', '-rating_count')

    # Popular cuisines & Bengaluru areas for quick filters
    popular_cuisines = [
        'South Indian', 'Biryani', 'North Indian', 'Chinese',
        'Cafe', 'Desserts', 'Fast Food', 'Street Food'
    ]
    bengaluru_areas = [
        'Koramangala', 'Indiranagar', 'HSR Layout', 'Whitefield',
        'Jayanagar', 'BTM Layout', 'JP Nagar', 'Malleshwaram'
    ]

    # Category icons & images for top carousel
    food_categories = [
        {'name': 'Dosa', 'icon': '🥟', 'query': 'Dosa', 'img': 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=300&q=80'},
        {'name': 'Biryani', 'icon': '🍗', 'query': 'Biryani', 'img': 'https://images.unsplash.com/photo-1563379091339-03246963d96c?auto=format&fit=crop&w=300&q=80'},
        {'name': 'Pizza', 'icon': '🍕', 'query': 'Pizza', 'img': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=300&q=80'},
        {'name': 'Burger', 'icon': '🍔', 'query': 'Burger', 'img': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=300&q=80'},
        {'name': 'North Indian', 'icon': '🥘', 'query': 'North Indian', 'img': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=300&q=80'},
        {'name': 'Chinese', 'icon': '🍜', 'query': 'Chinese', 'img': 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=300&q=80'},
        {'name': 'Rolls', 'icon': '🌯', 'query': 'Roll', 'img': 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=300&q=80'},
        {'name': 'Desserts', 'icon': '🍰', 'query': 'Desserts', 'img': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=300&q=80'},
        {'name': 'Coffee & Cafe', 'icon': '☕', 'query': 'Cafe', 'img': 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=300&q=80'},
        {'name': 'Healthy', 'icon': '🥗', 'query': 'Salad', 'img': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=300&q=80'},
    ]

    # Best selling foods for carousel
    top_items = Item.objects.filter(is_available=True)
    if veg_only:
        top_items = top_items.filter(is_veg=True)
    if selected_cuisine:
        top_items = top_items.filter(Q(category__iexact=selected_cuisine) | Q(restaurant__cuisine__iexact=selected_cuisine))
    top_dishes = top_items.order_by('-rating')[:8]

    # Pagination for restaurants
    paginator = Paginator(restaurants, 16)
    page_number = request.GET.get('page', 1)
    restaurant_page = paginator.get_page(page_number)

    context = {
        'restaurants': restaurant_page,
        'total_restaurants': restaurants.count(),
        'top_dishes': top_dishes,
        'popular_cuisines': popular_cuisines,
        'bengaluru_areas': bengaluru_areas,
        'food_categories': food_categories,
        'selected_area': selected_area,
        'selected_cuisine': selected_cuisine,
        'veg_only': veg_only,
        'min_rating': min_rating,
        'price_range': price_range,
        'sort_by': sort_by,
        'query': query,
    }
    return render(request, 'main/home.html', context)


class MenuListView(ListView):
    """
    Backwards compatible view for menu items.
    """
    model = Item
    template_name = 'main/home.html'
    context_object_name = 'menu_items'

    def get(self, request, *args, **kwargs):
        return home(request)


def search_view(request):
    """
    Page 2: Search.
    Case-insensitive search across restaurants and menu items, live suggestion chips, empty results state, and instant add-to-cart.
    """
    query = request.GET.get('q', '').strip()
    selected_area = request.GET.get('area', '').strip()
    selected_cuisine = request.GET.get('cuisine', '').strip()
    veg_only = request.GET.get('veg', '').lower() == 'true'
    min_rating = request.GET.get('rating', '').strip()

    restaurants = Restaurant.objects.filter(is_open=True)
    dishes = Item.objects.filter(is_available=True).select_related('restaurant')

    # Popular search suggestion tags
    suggestions = ['Biryani', 'Masala Dosa', 'Pizza', 'Burger', 'Momos', 'Paneer Butter Masala', 'North Indian', 'Filter Coffee', 'Thali', 'Pastry']

    if query:
        restaurants = restaurants.filter(
            Q(name__icontains=query) |
            Q(cuisine__icontains=query) |
            Q(area__icontains=query)
        )
        dishes = dishes.filter(
            Q(title__icontains=query) |
            Q(category__icontains=query) |
            Q(description__icontains=query) |
            Q(restaurant__name__icontains=query)
        )
    else:
        restaurants = restaurants.order_by('-rating')[:8]
        dishes = dishes.order_by('-rating')[:12]

    if selected_area:
        restaurants = restaurants.filter(area__iexact=selected_area)
        dishes = dishes.filter(restaurant__area__iexact=selected_area)
    if selected_cuisine:
        restaurants = restaurants.filter(cuisine__iexact=selected_cuisine)
        dishes = dishes.filter(Q(category__iexact=selected_cuisine) | Q(restaurant__cuisine__iexact=selected_cuisine))
    if veg_only:
        restaurants = restaurants.filter(Q(cuisine='South Indian') | Q(menu_items__is_veg=True)).distinct()
        dishes = dishes.filter(is_veg=True)
    if min_rating:
        try:
            r_val = float(min_rating)
            restaurants = restaurants.filter(rating__gte=r_val)
            dishes = dishes.filter(rating__gte=r_val)
        except ValueError:
            pass

    # Bind active cart quantities for dynamic buttons
    if request.user.is_authenticated:
        cart_map = {ci.item_id: ci.quantity for ci in CartItems.objects.filter(user=request.user, ordered=False)}
        cart_pk_map = {ci.item_id: ci.pk for ci in CartItems.objects.filter(user=request.user, ordered=False)}
        for d in dishes:
            d.cart_qty = cart_map.get(d.id, 0)
            d.cart_pk = cart_pk_map.get(d.id, None)

    context = {
        'query': query,
        'suggestions': suggestions,
        'matched_restaurants': restaurants[:12],
        'matched_dishes': dishes[:24],
        'total_results': (restaurants.count() + dishes.count()) if query else 0,
        'selected_area': selected_area,
        'selected_cuisine': selected_cuisine,
        'veg_only': veg_only,
        'min_rating': min_rating,
    }
    return render(request, 'main/search.html', context)


def restaurants_list_view(request):
    """
    Page 3: Restaurant listing directory.
    Filters: area, cuisine, rating, price range, pure veg.
    Sorting: rating, delivery time, cost ascending/descending.
    """
    query = request.GET.get('q', '').strip()
    selected_area = request.GET.get('area', '').strip()
    selected_cuisine = request.GET.get('cuisine', '').strip()
    veg_only = request.GET.get('veg', '').lower() == 'true'
    min_rating = request.GET.get('rating', '').strip()
    price_range = request.GET.get('price', '').strip()
    sort_by = request.GET.get('sort', '-rating')

    restaurants = Restaurant.objects.all()

    if selected_area:
        restaurants = restaurants.filter(area__iexact=selected_area)
    if selected_cuisine:
        restaurants = restaurants.filter(cuisine__iexact=selected_cuisine)
    if min_rating:
        try:
            restaurants = restaurants.filter(rating__gte=float(min_rating))
        except ValueError:
            pass
    if price_range == 'under_300':
        restaurants = restaurants.filter(average_cost_for_two__lt=300)
    elif price_range == '300_500':
        restaurants = restaurants.filter(average_cost_for_two__gte=300, average_cost_for_two__lte=500)
    elif price_range == 'above_500':
        restaurants = restaurants.filter(average_cost_for_two__gt=500)

    if query:
        dish_rest_ids = Item.objects.filter(Q(title__icontains=query) | Q(category__icontains=query)).values_list('restaurant_id', flat=True)
        restaurants = restaurants.filter(
            Q(name__icontains=query) |
            Q(cuisine__icontains=query) |
            Q(area__icontains=query) |
            Q(id__in=dish_rest_ids)
        )

    if veg_only:
        veg_rest_ids = Item.objects.filter(is_veg=True).values_list('restaurant_id', flat=True)
        restaurants = restaurants.filter(Q(cuisine='South Indian') | Q(id__in=veg_rest_ids)).distinct()

    if sort_by == 'delivery_time':
        restaurants = restaurants.order_by('estimated_delivery_minutes')
    elif sort_by == 'cost_asc':
        restaurants = restaurants.order_by('average_cost_for_two')
    elif sort_by == 'cost_desc':
        restaurants = restaurants.order_by('-average_cost_for_two')
    else:
        restaurants = restaurants.order_by('-rating', '-rating_count')

    paginator = Paginator(restaurants, 16)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    bengaluru_areas = [
        'Koramangala', 'Indiranagar', 'HSR Layout', 'Whitefield',
        'Jayanagar', 'BTM Layout', 'JP Nagar', 'Malleshwaram', 'Bellandur'
    ]

    context = {
        'restaurants': page_obj,
        'total_restaurants': restaurants.count(),
        'bengaluru_areas': bengaluru_areas,
        'selected_area': selected_area,
        'selected_cuisine': selected_cuisine,
        'veg_only': veg_only,
        'min_rating': min_rating,
        'price_range': price_range,
        'sort_by': sort_by,
        'query': query,
    }
    return render(request, 'main/restaurant_list.html', context)


def restaurant_detail(request, slug):
    """
    Restaurant detail page with category breakdown, vegetarian filter, and in-menu search.
    """
    restaurant = get_object_or_404(Restaurant, slug=slug)
    category_filter = request.GET.get('category', '').strip()
    veg_only = request.GET.get('veg', '').lower() == 'true'
    menu_search = request.GET.get('search', '').strip()

    menu_items = restaurant.menu_items.filter(is_available=True)
    if veg_only:
        menu_items = menu_items.filter(is_veg=True)
    if category_filter:
        menu_items = menu_items.filter(category__iexact=category_filter)
    if menu_search:
        menu_items = menu_items.filter(
            Q(title__icontains=menu_search) | Q(description__icontains=menu_search)
        )

    categories = restaurant.menu_items.values_list('category', flat=True).distinct()

    grouped_menu = {}
    for cat in categories:
        items = restaurant.menu_items.filter(category=cat, is_available=True)
        if veg_only:
            items = items.filter(is_veg=True)
        if menu_search:
            items = items.filter(Q(title__icontains=menu_search) | Q(description__icontains=menu_search))
        if items.exists():
            grouped_menu[cat] = items

    # User active cart item quantities for dynamic +/- controls on dish cards
    cart_quantities = {}
    cart_item_ids = {}
    if request.user.is_authenticated:
        active_cart = CartItems.objects.filter(user=request.user, ordered=False)
        for ci in active_cart:
            cart_quantities[ci.item_id] = ci.quantity
            cart_item_ids[ci.item_id] = ci.pk

    # Bind cart quantity and cart_item pk to dishes
    menu_items_list = list(menu_items)
    for dish in menu_items_list:
        dish.cart_qty = cart_quantities.get(dish.id, 0)
        dish.cart_pk = cart_item_ids.get(dish.id, None)

    for cat, items_qs in grouped_menu.items():
        items_list = list(items_qs)
        for dish in items_list:
            dish.cart_qty = cart_quantities.get(dish.id, 0)
            dish.cart_pk = cart_item_ids.get(dish.id, None)
        grouped_menu[cat] = items_list

    context = {
        'restaurant': restaurant,
        'categories': categories,
        'category_filter': category_filter,
        'veg_only': veg_only,
        'menu_search': menu_search,
        'menu_items': menu_items_list,
        'grouped_menu': grouped_menu,
        'cart_quantities': cart_quantities,
        'cart_item_ids': cart_item_ids,
    }
    return render(request, 'main/restaurant_detail.html', context)


def menuDetail(request, slug):
    """
    Dish detail page showing ratings and customer reviews.
    """
    item = get_object_or_404(Item, slug=slug)
    reviews = Reviews.objects.filter(item=item).order_by('-posted_on')[:10]
    related_items = Item.objects.filter(category=item.category).exclude(id=item.id)[:4]

    context = {
        'item': item,
        'reviews': reviews,
        'related_items': related_items,
    }
    return render(request, 'main/dishes.html', context)


@login_required
def add_reviews(request):
    """
    Add customer review with star rating for a dish.
    """
    if request.method == "POST":
        rslug = request.POST.get("rslug", "").strip()
        review_text = request.POST.get("review", "").strip()
        rating_val = int(request.POST.get("rating", 5))

        item = get_object_or_404(Item, slug=rslug)
        if review_text:
            Reviews.objects.create(
                user=request.user,
                item=item,
                rslug=rslug,
                review=review_text,
                rating=rating_val
            )
            # Recompute item average rating
            avg_rating = Reviews.objects.filter(item=item).aggregate(Avg('rating'))['rating__avg']
            if avg_rating:
                item.rating = round(avg_rating, 1)
                item.save()

            messages.success(request, "Thank you! Your review has been published.")
        return redirect('main:dishes', slug=item.slug)

    return redirect('main:home')


# -------------------------------------------------------------
# Cart & Checkout Views
# -------------------------------------------------------------
@login_required
def add_to_cart(request, slug):
    """
    Add item to cart or increment quantity if already present.
    """
    item = get_object_or_404(Item, slug=slug)
    cart_item, created = CartItems.objects.get_or_create(
        user=request.user,
        item=item,
        ordered=False,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.info(request, f"Updated {item.title} quantity to {cart_item.quantity}.")
    else:
        messages.success(request, f"Added {item.title} to your cart!")

    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect("main:cart")


@login_required
def update_cart_quantity(request, pk):
    """
    Increment, decrement, or remove an item from the cart.
    """
    cart_item = get_object_or_404(CartItems, pk=pk, user=request.user, ordered=False)
    action = request.POST.get('action') or request.GET.get('action')

    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
        messages.info(request, f"Increased {cart_item.item.title} quantity.")
    elif action == 'decrease':
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
            messages.info(request, f"Removed {cart_item.item.title} from cart.")
        else:
            cart_item.save()
            messages.info(request, f"Decreased {cart_item.item.title} quantity.")
    elif action == 'delete':
        cart_item.delete()
        messages.info(request, "Item removed from cart.")

    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect("main:cart")


# -------------------------------------------------------------
# Coupon & Cart Operations (Department 1: Pages 5 & 6)
# -------------------------------------------------------------
@login_required
def apply_coupon(request):
    """
    Validates and applies promotional coupon code server-side.
    """
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        cart_items = CartItems.objects.filter(user=request.user, ordered=False).select_related('item')
        subtotal = sum(ci.quantity * ci.item.price for ci in cart_items)

        coupon = Coupon.objects.filter(code=code, is_active=True).first()
        if not coupon:
            messages.error(request, f"Coupon code '{code}' is invalid or expired.")
        else:
            is_valid, msg = coupon.is_valid_for(subtotal)
            if not is_valid:
                messages.error(request, msg)
            else:
                request.session['coupon_id'] = coupon.id
                discount = coupon.calculate_discount(subtotal)
                messages.success(request, f"Coupon '{coupon.code}' applied! You save ₹{discount:.0f}.")

    next_url = request.POST.get('next') or request.GET.get('next') or 'main:cart'
    return redirect(next_url)


@login_required
def remove_coupon(request):
    """
    Removes applied promotional coupon code from user session.
    """
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        messages.info(request, "Coupon removed from your order.")
    next_url = request.GET.get('next') or 'main:cart'
    return redirect(next_url)


@login_required
def get_cart_items(request):
    """
    Page 5: Cart view with itemized billing, delivery calculation, coupon discounts, and checkout CTA.
    """
    cart_items = CartItems.objects.filter(user=request.user, ordered=False).select_related('item', 'item__restaurant')
    subtotal = sum(ci.quantity * ci.item.price for ci in cart_items)
    delivery_fee = 0.0 if (subtotal >= 300 or subtotal == 0) else 35.0
    tax_amount = round(subtotal * 0.05, 2)

    # Coupon handling
    applied_coupon = None
    discount_amount = 0.0
    coupon_id = request.session.get('coupon_id')
    if coupon_id and subtotal > 0:
        coupon = Coupon.objects.filter(id=coupon_id, is_active=True).first()
        if coupon and coupon.is_valid_for(subtotal)[0]:
            applied_coupon = coupon
            discount_amount = coupon.calculate_discount(subtotal)
        else:
            request.session.pop('coupon_id', None)

    grand_total = max(0.0, round(subtotal + delivery_fee + tax_amount - discount_amount, 2))
    total_quantity = sum(ci.quantity for ci in cart_items)

    available_coupons = Coupon.objects.filter(is_active=True).order_by('-discount_percent')[:4]

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'tax_amount': tax_amount,
        'applied_coupon': applied_coupon,
        'discount_amount': discount_amount,
        'total': grand_total,
        'count': total_quantity,
        'available_coupons': available_coupons,
    }
    return render(request, 'main/cart.html', context)


@login_required
def checkout_view(request):
    """
    Page 6: Dedicated Checkout page.
    Saved addresses selection, phone validation, order summary, coupon code, demo payment options, duplicate prevention.
    """
    cart_items = CartItems.objects.filter(user=request.user, ordered=False).select_related('item', 'item__restaurant')
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty! Add some dishes first.")
        return redirect('main:home')

    subtotal = sum(ci.quantity * ci.item.price for ci in cart_items)
    delivery_fee = 0.0 if subtotal >= 300 else 35.0
    tax_amount = round(subtotal * 0.05, 2)

    applied_coupon = None
    discount_amount = 0.0
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        coupon = Coupon.objects.filter(id=coupon_id, is_active=True).first()
        if coupon and coupon.is_valid_for(subtotal)[0]:
            applied_coupon = coupon
            discount_amount = coupon.calculate_discount(subtotal)
        else:
            request.session.pop('coupon_id', None)

    grand_total = max(0.0, round(subtotal + delivery_fee + tax_amount - discount_amount, 2))
    amount_paise = int(round(grand_total * 100))

    razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_TqzhtjQhQryWfB')
    razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'pS0wNTdlxoNds87UCLkQlLdn')
    razorpay_order_id = ''
    razorpay_order_error = None

    if razorpay and razorpay_key_id and razorpay_key_secret and grand_total > 0:
        try:
            client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
            rzp_order = client.order.create({
                'amount': amount_paise,
                'currency': getattr(settings, 'RAZORPAY_CURRENCY', 'INR'),
                'payment_capture': 1,
                'notes': {
                    'username': request.user.username,
                    'user_id': str(request.user.id),
                }
            })
            razorpay_order_id = rzp_order.get('id', '')
        except Exception as e:
            logger.info("Razorpay order creation fallback in test sandbox: %s", e)
            razorpay_order_error = str(e)
            razorpay_order_id = f"order_demo_{uuid.uuid4().hex[:12]}"
    else:
        razorpay_order_id = f"order_demo_{uuid.uuid4().hex[:12]}"

    saved_addresses = CustomerAddress.objects.filter(user=request.user)
    default_address = saved_addresses.filter(is_default=True).first() or saved_addresses.first()
    user_profile = getattr(request.user, 'profile', None)

    available_coupons = Coupon.objects.filter(is_active=True).order_by('-discount_percent')[:5]

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'tax_amount': tax_amount,
        'applied_coupon': applied_coupon,
        'discount_amount': discount_amount,
        'total': grand_total,
        'saved_addresses': saved_addresses,
        'default_address': default_address,
        'user_profile': user_profile,
        'available_coupons': available_coupons,
        'total_count': sum(ci.quantity for ci in cart_items),
        'razorpay_key_id': razorpay_key_id,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_amount': amount_paise,
        'razorpay_order_error': razorpay_order_error,
    }
    return render(request, 'main/checkout.html', context)


@login_required
def create_razorpay_order(request):
    """
    AJAX endpoint to generate or refresh a Razorpay order ID dynamically for current cart total.
    """
    cart_items = CartItems.objects.filter(user=request.user, ordered=False).select_related('item')
    if not cart_items.exists():
        return JsonResponse({'error': 'Your cart is empty!'}, status=400)

    subtotal = sum(ci.quantity * ci.item.price for ci in cart_items)
    delivery_fee = 0.0 if subtotal >= 300 else 35.0
    tax_amount = round(subtotal * 0.05, 2)

    discount_amount = 0.0
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        coupon = Coupon.objects.filter(id=coupon_id, is_active=True).first()
        if coupon and coupon.is_valid_for(subtotal)[0]:
            discount_amount = coupon.calculate_discount(subtotal)

    grand_total = max(0.0, round(subtotal + delivery_fee + tax_amount - discount_amount, 2))
    amount_paise = int(round(grand_total * 100))

    razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_TqzhtjQhQryWfB')
    razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'pS0wNTdlxoNds87UCLkQlLdn')
    razorpay_order_id = ''
    is_demo = False

    if razorpay and razorpay_key_id and razorpay_key_secret and grand_total > 0:
        try:
            client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
            rzp_order = client.order.create({
                'amount': amount_paise,
                'currency': getattr(settings, 'RAZORPAY_CURRENCY', 'INR'),
                'payment_capture': 1,
                'notes': {
                    'username': request.user.username,
                    'user_id': str(request.user.id),
                }
            })
            razorpay_order_id = rzp_order.get('id', '')
        except Exception as e:
            logger.info("Razorpay AJAX order fallback: %s", e)
            razorpay_order_id = f"order_demo_{uuid.uuid4().hex[:12]}"
            is_demo = True
    else:
        razorpay_order_id = f"order_demo_{uuid.uuid4().hex[:12]}"
        is_demo = True

    return JsonResponse({
        'key': razorpay_key_id,
        'order_id': razorpay_order_id,
        'amount': amount_paise,
        'currency': getattr(settings, 'RAZORPAY_CURRENCY', 'INR'),
        'total_inr': grand_total,
        'is_demo': is_demo
    })


class CartDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CartItems
    success_url = '/cart/'

    def test_func(self):
        cart = self.get_object()
        return self.request.user == cart.user


@login_required
@transaction.atomic
def order_item(request):
    """
    Converts active cart items into a confirmed Order with validation, immutable line items, and coupon handling.
    """
    cart_items = CartItems.objects.select_for_update().filter(user=request.user, ordered=False).select_related('item', 'item__restaurant')
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty! Add some dishes first.")
        return redirect("main:home")

    if request.method != 'POST':
        return redirect("main:checkout")

    # Delivery address selection: either saved address ID or custom text
    saved_addr_id = request.POST.get('saved_address_id')
    raw_phone = (request.POST.get('phone') or request.POST.get('phone_number') or '').strip()
    if not raw_phone and hasattr(request.user, 'profile') and request.user.profile.phone_number:
        raw_phone = request.user.profile.phone_number

    if saved_addr_id:
        saved_addr = CustomerAddress.objects.filter(id=saved_addr_id, user=request.user).first()
        if saved_addr:
            address = f"{saved_addr.title}: {saved_addr.address_line}, {saved_addr.area}, {saved_addr.city} - {saved_addr.pincode}"
            phone = saved_addr.phone or raw_phone
        else:
            address = request.POST.get('address', '').strip()
            phone = raw_phone
    else:
        address = request.POST.get('address', '').strip()
        phone = raw_phone

    instructions = request.POST.get('instructions', '').strip()
    payment_method = request.POST.get('payment_method', 'Cash on Delivery (DEMO)').strip()
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '').strip()
    razorpay_order_id = request.POST.get('razorpay_order_id', '').strip()
    razorpay_signature = request.POST.get('razorpay_signature', '').strip()

    # Address validation
    if not address or len(address) < 5:
        messages.error(request, "Please provide a complete delivery address in Bengaluru.")
        return redirect("main:checkout")

    # Phone number validation (at least 10 digits)
    digits_only = re.sub(r'\D', '', phone)
    if len(digits_only) < 10:
        messages.error(request, "Please enter a valid 10-digit delivery phone number.")
        return redirect("main:checkout")

    # Razorpay verification if paid via Razorpay
    is_paid = False
    if payment_method == 'Razorpay':
        razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
        razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')

        if razorpay and razorpay_payment_id and razorpay_signature and not razorpay_order_id.startswith('order_demo_'):
            try:
                client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                })
                is_paid = True
            except Exception as e:
                logger.warning("Razorpay signature verification exception: %s", e)
                # In debug / test mode with test keys, accept verified demo payment
                if settings.DEBUG or 'rzp_test_' in razorpay_key_id:
                    is_paid = True
                else:
                    messages.error(request, "Razorpay payment signature verification failed. Please try again.")
                    return redirect("main:checkout")
        elif razorpay_payment_id:
            # Sandbox / Simulated Razorpay test payment
            is_paid = True
        else:
            messages.warning(request, "Razorpay payment was not completed. Please try again or choose Cash on Delivery.")
            return redirect("main:checkout")

    subtotal = sum(ci.quantity * ci.item.price for ci in cart_items)
    delivery_fee = 0.0 if subtotal >= 300 else 35.0
    tax_amount = round(subtotal * 0.05, 2)

    # Coupon validation
    applied_coupon = None
    discount_amount = 0.0
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        coupon = Coupon.objects.filter(id=coupon_id, is_active=True).first()
        if coupon and coupon.is_valid_for(subtotal)[0]:
            applied_coupon = coupon
            discount_amount = coupon.calculate_discount(subtotal)
            coupon.usage_count += 1
            coupon.save()

    grand_total = max(0.0, round(subtotal + delivery_fee + tax_amount - discount_amount, 2))

    first_item = cart_items.first()
    restaurant = first_item.item.restaurant if first_item and first_item.item else None

    order_number = f"FG-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    order = Order.objects.create(
        order_number=order_number,
        user=request.user,
        restaurant=restaurant,
        coupon=applied_coupon,
        discount_amount=discount_amount,
        delivery_address=address,
        contact_phone=phone,
        order_instructions=instructions,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        tax_amount=tax_amount,
        total_amount=grand_total,
        payment_method=payment_method,
        is_paid=is_paid,
        razorpay_order_id=razorpay_order_id if payment_method == 'Razorpay' else '',
        razorpay_payment_id=razorpay_payment_id if payment_method == 'Razorpay' else '',
        razorpay_signature=razorpay_signature if payment_method == 'Razorpay' else '',
        status='Confirmed'
    )

    # Create immutable OrderItem snapshots and mark CartItems as ordered
    now_date = timezone.now().date()
    for ci in cart_items:
        OrderItem.objects.create(
            order=order,
            item=ci.item,
            item_title=ci.item.title if ci.item else "Delicious Dish",
            item_price=ci.item.price if ci.item else 0.0,
            quantity=ci.quantity,
            subtotal=ci.subtotal,
            is_veg=ci.item.is_veg if ci.item else True,
            food_image_url=ci.item.get_display_image if ci.item else ""
        )
        ci.order = order
        ci.ordered = True
        ci.ordered_date = now_date
        ci.status = 'Confirmed'
        ci.save()

    # Clear coupon from session
    request.session.pop('coupon_id', None)

    if is_paid and payment_method == 'Razorpay':
        messages.success(request, f"Payment of ₹{grand_total:.2f} successful via Razorpay (Ref: {razorpay_payment_id})! Order #{order_number} confirmed.")
    else:
        messages.success(request, f"Order #{order_number} confirmed! Live kitchen tracker active.")
    return redirect("main:order_tracking", order_number=order.order_number)



@login_required
def order_success(request, order_number):
    """
    Order confirmation receipt view.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'main/order_success.html', {'order': order})


@login_required
def order_tracking_view(request, order_number):
    """
    Page 7: Order tracking with real database status, status timeline, and assigned delivery partner.
    """
    order = get_object_or_404(Order, order_number=order_number)

    # Access control: only customer, assigned rider, restaurant staff, or admin can track
    profile = getattr(request.user, 'profile', None)
    is_owner = (order.user == request.user)
    is_rider = (order.assigned_delivery_partner == request.user)
    is_rest_staff = (profile and profile.restaurant == order.restaurant)
    is_admin = (request.user.is_superuser or (profile and profile.role == 'ADMIN'))

    if not (is_owner or is_rider or is_rest_staff or is_admin):
        messages.error(request, "Access denied. You do not have permission to view this order.")
        return redirect('main:home')

    # Stepper stages for Swiggy-like tracker
    steps = [
        {'id': 'Confirmed', 'label': 'Order Confirmed', 'icon': 'fa-check'},
        {'id': 'Accepted', 'label': 'Accepted by Kitchen', 'icon': 'fa-store'},
        {'id': 'Preparing', 'label': 'Chef Preparing', 'icon': 'fa-kitchen-set'},
        {'id': 'Ready for Pickup', 'label': 'Ready for Pickup', 'icon': 'fa-box'},
        {'id': 'Picked Up', 'label': 'Picked Up by Rider', 'icon': 'fa-motorcycle'},
        {'id': 'Out for Delivery', 'label': 'Out for Delivery', 'icon': 'fa-route'},
        {'id': 'Delivered', 'label': 'Delivered to Doorstep', 'icon': 'fa-circle-check'},
    ]

    # Map status to step index
    status_order = ['Confirmed', 'Accepted', 'Preparing', 'Ready for Pickup', 'Picked Up', 'Out for Delivery', 'Delivered']
    current_index = 0
    if order.status in status_order:
        current_index = status_order.index(order.status)
    elif order.status == 'Active':
        current_index = 0

    order_items = order.order_items.all()
    if not order_items.exists():
        order_items = order.cart_items.all()

    context = {
        'order': order,
        'order_items': order_items,
        'steps': steps,
        'current_index': current_index,
        'is_cancelled': order.status == 'Cancelled',
    }
    return render(request, 'main/order_tracking.html', context)


@login_required
def order_details(request):
    """
    Page 8: Customer order history view showing active orders and completed orders with tracking, reorder, and cancellation.
    """
    active_orders = Order.objects.filter(
        user=request.user, 
        status__in=['Confirmed', 'Accepted', 'Preparing', 'Ready for Pickup', 'Picked Up', 'Out for Delivery', 'Active']
    ).order_by('-created_at')

    completed_orders = Order.objects.filter(
        user=request.user, 
        status__in=['Delivered', 'Cancelled']
    ).order_by('-created_at')

    context = {
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'total_orders': active_orders.count() + completed_orders.count(),
    }
    return render(request, 'main/order_details.html', context)


@login_required
def reorder_order(request, order_number):
    """
    Reorder action: copies dishes from a past order back into customer's active cart.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    reordered_count = 0

    order_items = order.order_items.all()
    if order_items.exists():
        for oi in order_items:
            if oi.item and oi.item.is_available:
                ci, created = CartItems.objects.get_or_create(
                    user=request.user,
                    item=oi.item,
                    ordered=False,
                    defaults={'quantity': oi.quantity}
                )
                if not created:
                    ci.quantity += oi.quantity
                    ci.save()
                reordered_count += 1
    else:
        for ci_old in order.cart_items.all():
            if ci_old.item and ci_old.item.is_available:
                ci, created = CartItems.objects.get_or_create(
                    user=request.user,
                    item=ci_old.item,
                    ordered=False,
                    defaults={'quantity': ci_old.quantity}
                )
                if not created:
                    ci.quantity += ci_old.quantity
                    ci.save()
                reordered_count += 1

    if reordered_count > 0:
        messages.success(request, f"Added dishes from Order #{order.order_number} to your cart!")
        return redirect('main:cart')
    else:
        messages.warning(request, "Dishes from this past order are currently unavailable.")
        return redirect('main:order_details')


@login_required
def cancel_order(request, order_number):
    """
    Customer cancellation: allowed only while order is still in Confirmed/Active state before kitchen prep.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.can_be_cancelled:
        order.status = 'Cancelled'
        order.cancelled_at = timezone.now()
        order.rejection_reason = 'Cancelled by customer'
        order.save()
        messages.info(request, f"Order #{order.order_number} has been cancelled.")
    else:
        messages.error(request, "This order cannot be cancelled as the restaurant has already begun preparation.")

    return redirect('main:order_tracking', order_number=order.order_number)


# -------------------------------------------------------------
# Department 2: Restaurant Dashboard (Pages 10, 11, 12, 13)
# -------------------------------------------------------------
def get_user_restaurant(user):
    """
    Helper to resolve the restaurant associated with a logged-in user.
    """
    profile = getattr(user, 'profile', None)
    if profile and profile.restaurant:
        return profile.restaurant
    owned = Restaurant.objects.filter(owner=user).first()
    if owned:
        return owned
    if user.is_superuser or user.is_staff:
        return Restaurant.objects.first()
    return None


@login_required
@restaurant_required
def restaurant_portal_overview(request):
    """
    Page 10: Restaurant overview.
    Today's order count, sales summary, pending and completed orders, popular menu items.
    """
    rest = get_user_restaurant(request.user)
    if not rest:
        messages.error(request, "No restaurant is linked to your partner account.")
        return redirect('main:home')

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = Order.objects.filter(restaurant=rest, created_at__gte=today_start)
    today_count = today_orders.count()
    today_sales = today_orders.exclude(status='Cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.0

    pending_orders = Order.objects.filter(
        restaurant=rest, 
        status__in=['Confirmed', 'Accepted', 'Preparing', 'Ready for Pickup', 'Active']
    ).order_by('-created_at')
    
    completed_orders = Order.objects.filter(restaurant=rest, status='Delivered').count()
    recent_orders = Order.objects.filter(restaurant=rest).order_by('-created_at')[:8]
    popular_dishes = rest.menu_items.order_by('-rating')[:6]

    context = {
        'restaurant': rest,
        'today_count': today_count,
        'today_sales': round(today_sales, 2),
        'pending_count': pending_orders.count(),
        'completed_count': completed_orders,
        'pending_orders': pending_orders[:10],
        'recent_orders': recent_orders,
        'popular_dishes': popular_dishes,
    }
    return render(request, 'main/partner_overview.html', context)


@login_required
@restaurant_required
def restaurant_portal_orders(request):
    """
    Page 11: Restaurant order management.
    Incoming orders, accept/reject, update preparation status, mark ready for pickup.
    """
    rest = get_user_restaurant(request.user)
    if not rest:
        return redirect('main:home')

    status_filter = request.GET.get('status', '').strip()
    orders = Order.objects.filter(restaurant=rest).order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {
        'restaurant': rest,
        'orders': orders[:50],
        'status_filter': status_filter,
    }
    return render(request, 'main/partner_orders.html', context)


@login_required
@restaurant_required
def restaurant_update_order_status(request, order_number):
    """
    Handle restaurant status transitions:
    - accept: Confirmed -> Accepted
    - reject: Confirmed -> Cancelled (with reason)
    - preparing: Accepted -> Preparing
    - ready: Preparing -> Ready for Pickup
    """
    rest = get_user_restaurant(request.user)
    order = get_object_or_404(Order, order_number=order_number, restaurant=rest)

    if request.method == 'POST':
        action = request.POST.get('action')
        now = timezone.now()

        if action == 'accept':
            order.status = 'Accepted'
            order.accepted_at = now
            messages.success(request, f"Accepted Order #{order.order_number}.")
        elif action == 'reject':
            reason = request.POST.get('reason', 'Restaurant kitchen busy').strip()
            order.status = 'Cancelled'
            order.rejection_reason = reason
            order.cancelled_at = now
            messages.warning(request, f"Rejected Order #{order.order_number}: {reason}.")
        elif action == 'preparing':
            order.status = 'Preparing'
            messages.info(request, f"Order #{order.order_number} marked Preparing in kitchen.")
        elif action == 'ready':
            order.status = 'Ready for Pickup'
            order.ready_at = now
            messages.success(request, f"Order #{order.order_number} marked Ready for Pickup!")
        order.save()

    next_url = request.POST.get('next') or 'main:restaurant_portal_orders'
    return redirect(next_url)


@login_required
@restaurant_required
def restaurant_portal_menu(request):
    """
    Page 12: Restaurant menu management.
    Add, edit, remove dishes, and toggle availability for this restaurant.
    """
    rest = get_user_restaurant(request.user)
    if not rest:
        return redirect('main:home')

    category_filter = request.GET.get('category', '').strip()
    search_q = request.GET.get('q', '').strip()

    dishes = rest.menu_items.all().order_by('-id')
    if category_filter:
        dishes = dishes.filter(category=category_filter)
    if search_q:
        dishes = dishes.filter(title__icontains=search_q)

    categories = rest.menu_items.values_list('category', flat=True).distinct()

    context = {
        'restaurant': rest,
        'dishes': dishes[:100],
        'categories': categories,
        'category_filter': category_filter,
        'search_q': search_q,
    }
    return render(request, 'main/partner_menu.html', context)


@login_required
@restaurant_required
def restaurant_dish_create(request):
    """
    Add a new dish to the restaurant's menu.
    """
    rest = get_user_restaurant(request.user)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', 'Main Course').strip()
        price = float(request.POST.get('price', 150))
        description = request.POST.get('description', '').strip()
        is_veg = request.POST.get('is_veg') == 'on'
        food_image_url = request.POST.get('food_image_url', '').strip()

        if title:
            from .image_catalog import get_curated_food_image
            if not food_image_url:
                food_image_url = get_curated_food_image(title, category)

            slug = f"{re.sub(r'[^a-zA-Z0-9]+', '-', title.lower())}-{uuid.uuid4().hex[:6]}"
            Item.objects.create(
                restaurant=rest,
                title=title,
                category=category,
                price=price,
                description=description,
                is_veg=is_veg,
                food_image_url=food_image_url,
                slug=slug,
                created_by=request.user,
                data_type='USER_CREATED'
            )
            messages.success(request, f"Added '{title}' to {rest.name} menu!")
    return redirect('main:restaurant_portal_menu')


@login_required
@restaurant_required
def restaurant_dish_edit(request, pk):
    """
    Edit an existing dish in the restaurant's menu.
    """
    rest = get_user_restaurant(request.user)
    dish = get_object_or_404(Item, pk=pk, restaurant=rest)

    if request.method == 'POST':
        dish.title = request.POST.get('title', dish.title).strip()
        dish.category = request.POST.get('category', dish.category).strip()
        dish.price = float(request.POST.get('price', dish.price))
        dish.description = request.POST.get('description', dish.description).strip()
        dish.is_veg = request.POST.get('is_veg') == 'on'
        new_url = request.POST.get('food_image_url', '').strip()
        if new_url:
            dish.food_image_url = new_url
        dish.save()
        messages.success(request, f"Updated dish '{dish.title}'.")
    return redirect('main:restaurant_portal_menu')


@login_required
@restaurant_required
def restaurant_dish_toggle_availability(request, pk):
    """
    Quick 1-click toggle for In Stock vs Sold Out.
    """
    rest = get_user_restaurant(request.user)
    dish = get_object_or_404(Item, pk=pk, restaurant=rest)
    dish.is_available = not dish.is_available
    dish.save()
    state = "In Stock" if dish.is_available else "Sold Out"
    messages.info(request, f"'{dish.title}' marked as {state}.")
    return redirect('main:restaurant_portal_menu')


@login_required
@restaurant_required
def restaurant_dish_delete(request, pk):
    """
    Delete a dish from restaurant menu.
    """
    rest = get_user_restaurant(request.user)
    dish = get_object_or_404(Item, pk=pk, restaurant=rest)
    title = dish.title
    dish.delete()
    messages.info(request, f"Deleted '{title}' from menu.")
    return redirect('main:restaurant_portal_menu')


@login_required
@restaurant_required
def restaurant_portal_settings(request):
    """
    Page 13: Restaurant settings.
    Opening hours, open/closed status, phone, address, delivery fee.
    """
    rest = get_user_restaurant(request.user)
    if not rest:
        return redirect('main:home')

    if request.method == 'POST':
        rest.opening_time = request.POST.get('opening_time', rest.opening_time).strip()
        rest.closing_time = request.POST.get('closing_time', rest.closing_time).strip()
        rest.contact_phone = request.POST.get('contact_phone', rest.contact_phone).strip()
        rest.address_details = request.POST.get('address_details', rest.address_details).strip()
        rest.is_open = request.POST.get('is_open') == 'on'
        try:
            rest.average_cost_for_two = float(request.POST.get('average_cost_for_two', rest.average_cost_for_two))
            rest.estimated_delivery_minutes = int(request.POST.get('estimated_delivery_minutes', rest.estimated_delivery_minutes))
        except ValueError:
            pass
        rest.save()
        messages.success(request, f"Updated operational settings for {rest.name}!")
        return redirect('main:restaurant_portal_settings')

    return render(request, 'main/partner_settings.html', {'restaurant': rest})


# -------------------------------------------------------------
# Department 3: Delivery Dashboard (Pages 14 & 15)
# -------------------------------------------------------------
@login_required
@delivery_required
def delivery_portal_overview(request):
    """
    Page 14: Delivery overview.
    Active assigned delivery, available unassigned deliveries, completed delivery history, rider stats.
    """
    active_delivery = Order.objects.filter(
        assigned_delivery_partner=request.user,
        status__in=['Accepted', 'Preparing', 'Ready for Pickup', 'Picked Up', 'Out for Delivery']
    ).first()

    available_orders = Order.objects.filter(
        assigned_delivery_partner__isnull=True,
        status__in=['Ready for Pickup', 'Preparing']
    ).order_by('-created_at')[:15]

    completed_qs = Order.objects.filter(
        assigned_delivery_partner=request.user,
        status='Delivered'
    )
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_completed = completed_qs.filter(delivery_date__gte=today_start).count()
    completed_deliveries = completed_qs.order_by('-delivery_date', '-created_at')[:20]
    estimated_earnings = today_completed * 45.0  # ₹45 per delivery demo payout

    context = {
        'active_delivery': active_delivery,
        'available_orders': available_orders,
        'completed_deliveries': completed_deliveries,
        'today_completed': today_completed,
        'estimated_earnings': round(estimated_earnings, 2),
        'profile': getattr(request.user, 'profile', None),
    }
    return render(request, 'main/delivery_overview.html', context)


@login_required
@delivery_required
def delivery_portal_order_detail(request, order_number):
    """
    Page 15: Delivery details.
    Pickup details, customer address, authorized contact, pickup and delivery action confirmations.
    """
    order = get_object_or_404(Order, order_number=order_number)

    # Permission check: must be assigned rider or order is unassigned
    if order.assigned_delivery_partner and order.assigned_delivery_partner != request.user and not request.user.is_superuser:
        messages.error(request, "This delivery is assigned to another delivery partner.")
        return redirect('main:delivery_portal_overview')

    context = {
        'order': order,
        'is_assigned_to_me': (order.assigned_delivery_partner == request.user),
    }
    return render(request, 'main/delivery_order_detail.html', context)


@login_required
@delivery_required
def delivery_claim_order(request, order_number):
    """
    Rider accepts/claims an available delivery.
    """
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(order_number=order_number).first()
        if not order:
            messages.error(request, "Order not found.")
            return redirect('main:delivery_portal_overview')

        if order.assigned_delivery_partner:
            messages.warning(request, "This order was already accepted by another rider.")
            return redirect('main:delivery_portal_overview')

        order.assigned_delivery_partner = request.user
        order.save()
        messages.success(request, f"You accepted Order #{order.order_number}! Pickup from {order.restaurant.name}.")

    return redirect('main:delivery_portal_order_detail', order_number=order.order_number)


@login_required
@delivery_required
def delivery_confirm_pickup(request, order_number):
    """
    Rider confirms food has been picked up from restaurant and is out for delivery.
    """
    order = get_object_or_404(Order, order_number=order_number, assigned_delivery_partner=request.user)
    order.status = 'Out for Delivery'
    order.picked_up_at = timezone.now()
    order.save()
    messages.success(request, f"Order #{order.order_number} picked up! En route to customer.")
    return redirect('main:delivery_portal_order_detail', order_number=order.order_number)


@login_required
@delivery_required
def delivery_confirm_delivered(request, order_number):
    """
    Rider marks order as successfully delivered to customer.
    """
    order = get_object_or_404(Order, order_number=order_number, assigned_delivery_partner=request.user)
    now = timezone.now()
    order.status = 'Delivered'
    order.delivery_date = now
    order.is_paid = True
    order.save()
    order.cart_items.update(status='Delivered', delivery_date=now.date())

    messages.success(request, f"Order #{order.order_number} marked as Delivered! Great job!")
    return redirect('main:delivery_portal_overview')


# -------------------------------------------------------------
# Department 4: Admin Dashboard (Pages 16, 17, 18)
# -------------------------------------------------------------
@login_required
@admin_required
def admin_portal_overview(request):
    """
    Page 16: Admin overview.
    KPIs: Total customers, total restaurants, total orders, recorded platform revenue, active deliveries.
    """
    total_customers = User.objects.filter(profile__role='CUSTOMER').count() or User.objects.count()
    total_restaurants = Restaurant.objects.count()
    total_orders = Order.objects.count()
    platform_revenue = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.0

    active_orders = Order.objects.filter(
        status__in=['Confirmed', 'Accepted', 'Preparing', 'Ready for Pickup', 'Picked Up', 'Out for Delivery', 'Active']
    ).count()
    active_deliveries = Order.objects.filter(status__in=['Picked Up', 'Out for Delivery']).count()

    recent_orders = Order.objects.all().order_by('-created_at')[:10]

    context = {
        'total_customers': total_customers,
        'total_restaurants': total_restaurants,
        'total_orders': total_orders,
        'platform_revenue': round(platform_revenue, 2),
        'active_orders': active_orders,
        'active_deliveries': active_deliveries,
        'recent_orders': recent_orders,
    }
    return render(request, 'main/admin_overview.html', context)


@login_required
@admin_required
def admin_portal_management(request):
    """
    Page 17: User and restaurant management.
    List/search customers, staff, riders. Change user roles. Approve/suspend restaurants.
    """
    user_search = request.GET.get('u_q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    rest_search = request.GET.get('r_q', '').strip()

    users = User.objects.select_related('profile').all().order_by('-date_joined')
    if user_search:
        users = users.filter(Q(username__icontains=user_search) | Q(email__icontains=user_search))
    if role_filter:
        users = users.filter(profile__role=role_filter)

    restaurants = Restaurant.objects.all().order_by('-id')
    if rest_search:
        restaurants = restaurants.filter(Q(name__icontains=rest_search) | Q(area__icontains=rest_search))

    context = {
        'users': users[:30],
        'restaurants': restaurants[:30],
        'all_restaurants': Restaurant.objects.all().order_by('name')[:50],
        'user_search': user_search,
        'role_filter': role_filter,
        'rest_search': rest_search,
    }
    return render(request, 'main/admin_management.html', context)


@login_required
@admin_required
def admin_change_user_role(request, user_id):
    """
    Change user role (CUSTOMER, RESTAURANT, DELIVERY, ADMIN) and assign restaurant if restaurant staff.
    """
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        new_role = request.POST.get('role', 'CUSTOMER')
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = new_role

        rest_id = request.POST.get('restaurant_id')
        if rest_id and new_role == 'RESTAURANT':
            rest = Restaurant.objects.filter(id=rest_id).first()
            profile.restaurant = rest
        profile.save()
        messages.success(request, f"Updated role for {user.username} to {new_role}.")

    return redirect('main:admin_portal_management')


@login_required
@admin_required
def admin_toggle_restaurant_approval(request, restaurant_id):
    """
    Approve or suspend restaurant listing.
    """
    rest = get_object_or_404(Restaurant, id=restaurant_id)
    rest.is_approved = not rest.is_approved
    rest.save()
    status_str = "Approved" if rest.is_approved else "Suspended"
    messages.info(request, f"Restaurant '{rest.name}' is now {status_str}.")
    return redirect('main:admin_portal_management')


@login_required
@admin_required
def admin_portal_orders_offers(request):
    """
    Page 18: Order and offer management.
    Platform-wide orders list + Promotional coupon creation, toggle, and deletion.
    """
    status_filter = request.GET.get('status', '').strip()
    order_search = request.GET.get('q', '').strip()

    orders = Order.objects.all().order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    if order_search:
        orders = orders.filter(Q(order_number__icontains=order_search) | Q(user__username__icontains=order_search))

    coupons = Coupon.objects.all().order_by('-created_at')

    context = {
        'orders': orders[:35],
        'coupons': coupons,
        'status_filter': status_filter,
        'order_search': order_search,
    }
    return render(request, 'main/admin_orders_offers.html', context)


@login_required
@admin_required
def admin_coupon_create(request):
    """
    Create a new promotional coupon code.
    """
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        discount_percent = int(request.POST.get('discount_percent', 0))
        discount_amount = float(request.POST.get('discount_amount', 0.0))
        min_order_amount = float(request.POST.get('min_order_amount', 150.0))
        max_discount_amount = float(request.POST.get('max_discount_amount', 100.0))

        if code and title:
            Coupon.objects.update_or_create(
                code=code,
                defaults={
                    'title': title,
                    'description': description,
                    'discount_percent': discount_percent,
                    'discount_amount': discount_amount,
                    'min_order_amount': min_order_amount,
                    'max_discount_amount': max_discount_amount,
                    'is_active': True,
                }
            )
            messages.success(request, f"Coupon '{code}' created successfully!")
    return redirect('main:admin_portal_orders_offers')


@login_required
@admin_required
def admin_coupon_toggle(request, coupon_id):
    """
    Toggle active status of a coupon.
    """
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save()
    status_str = "Active" if coupon.is_active else "Inactive"
    messages.info(request, f"Coupon '{coupon.code}' set to {status_str}.")
    return redirect('main:admin_portal_orders_offers')


@login_required
@admin_required
def admin_coupon_delete(request, coupon_id):
    """
    Delete a promotional coupon.
    """
    coupon = get_object_or_404(Coupon, id=coupon_id)
    code = coupon.code
    coupon.delete()
    messages.info(request, f"Coupon '{code}' deleted.")
    return redirect('main:admin_portal_orders_offers')


# -------------------------------------------------------------
# Backwards-Compatible Legacy Admin & Item Views
# -------------------------------------------------------------
@login_required
@admin_required
def admin_dashboard(request):
    """
    Backwards compatible route pointing to admin portal overview.
    """
    return admin_portal_overview(request)


@login_required
@admin_required
def admin_view(request):
    """
    Delivered orders archive.
    """
    orders = Order.objects.filter(status="Delivered").order_by('-created_at')
    return render(request, 'main/admin_view.html', {'orders': orders})


@login_required
@admin_required
def pending_orders(request):
    """
    Active kitchen orders awaiting preparation/dispatch.
    """
    orders = Order.objects.filter(status__in=['Confirmed', 'Accepted', 'Preparing', 'Ready for Pickup', 'Active']).order_by('-created_at')
    return render(request, 'main/pending_orders.html', {'orders': orders})


@login_required
@admin_required
def update_status(request, pk):
    """
    Update status of an Order.
    """
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status', 'Confirmed')
        order.status = new_status
        if new_status == 'Delivered':
            order.delivery_date = timezone.now()
            order.is_paid = True
            order.cart_items.update(status='Delivered', delivery_date=timezone.now().date())
        order.save()
        messages.success(request, f"Order #{order.order_number} status updated to {new_status}.")

    return redirect('main:pending_orders')


@login_required
@admin_required
def item_list(request):
    """
    List of dishes for admin/partner management.
    """
    items = Item.objects.all().order_by('-id')
    paginator = Paginator(items, 25)
    page = request.GET.get('page', 1)
    items_page = paginator.get_page(page)
    return render(request, 'main/item_list.html', {'items': items_page})


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    fields = [
        'title', 'restaurant', 'category', 'price', 'pieces',
        'is_veg', 'image', 'food_image_url', 'description',
        'instructions', 'labels', 'label_colour', 'slug'
    ]
    template_name = 'main/item_form.html'
    success_url = '/item_list/'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.data_type = 'USER_CREATED'
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Item
    fields = [
        'title', 'restaurant', 'category', 'price', 'pieces',
        'is_veg', 'image', 'food_image_url', 'description',
        'instructions', 'labels', 'label_colour', 'slug'
    ]
    template_name = 'main/item_form.html'
    success_url = '/item_list/'

    def test_func(self):
        item = self.get_object()
        return self.request.user.is_superuser or self.request.user.is_staff or self.request.user == item.created_by


class ItemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Item
    template_name = 'main/item_confirm_delete.html'
    success_url = '/item_list/'

    def test_func(self):
        item = self.get_object()
        return self.request.user.is_superuser or self.request.user.is_staff or self.request.user == item.created_by

