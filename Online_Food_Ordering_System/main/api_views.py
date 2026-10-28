import uuid
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import Restaurant, Item, Order, CartItems, Reviews
from .serializers import (
    RestaurantSerializer,
    RestaurantDetailSerializer,
    ItemSerializer,
    CartItemSerializer,
    OrderSerializer,
    ReviewSerializer
)

class RestaurantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to list and retrieve Bengaluru restaurants.
    Supports searching and filtering by cuisine, area, and open status.
    """
    queryset = Restaurant.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'cuisine', 'area', 'city']
    ordering_fields = ['rating', 'estimated_delivery_minutes', 'average_cost_for_two']
    ordering = ['-rating']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RestaurantDetailSerializer
        return RestaurantSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        cuisine = self.request.query_params.get('cuisine')
        area = self.request.query_params.get('area')
        is_open = self.request.query_params.get('is_open')
        min_rating = self.request.query_params.get('min_rating')

        if cuisine:
            qs = qs.filter(cuisine__iexact=cuisine)
        if area:
            qs = qs.filter(area__iexact=area)
        if is_open is not None:
            qs = qs.filter(is_open=(is_open.lower() == 'true'))
        if min_rating:
            try:
                qs = qs.filter(rating__gte=float(min_rating))
            except ValueError:
                pass
        return qs

class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to browse Bengaluru food items.
    Supports filtering by vegetarian flag, restaurant ID, category, and keyword search.
    """
    queryset = Item.objects.filter(is_available=True)
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category', 'instructions']
    ordering_fields = ['price', 'rating', 'title']
    ordering = ['-rating']

    def get_queryset(self):
        qs = super().get_queryset()
        restaurant_id = self.request.query_params.get('restaurant_id')
        category = self.request.query_params.get('category')
        is_veg = self.request.query_params.get('is_veg')
        max_price = self.request.query_params.get('max_price')

        if restaurant_id:
            qs = qs.filter(restaurant_id=restaurant_id)
        if category:
            qs = qs.filter(category__iexact=category)
        if is_veg is not None:
            qs = qs.filter(is_veg=(is_veg.lower() == 'true'))
        if max_price:
            try:
                qs = qs.filter(price__lte=float(max_price))
            except ValueError:
                pass
        return qs

class CartViewSet(viewsets.ModelViewSet):
    """
    API endpoint to view, add, modify, and delete active cart items for the authenticated user.
    """
    queryset = CartItems.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItems.objects.filter(user=self.request.user, ordered=False).select_related('item', 'item__restaurant')

    def create(self, request, *args, **kwargs):
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))

        if not item_id:
            return Response({'error': 'item_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = Item.objects.get(pk=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItems.objects.get_or_create(
            user=request.user,
            item=item,
            ordered=False,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        cart_item = self.get_object()
        action_type = request.data.get('action')  # 'increase' or 'decrease'
        
        if action_type == 'increase':
            cart_item.quantity += 1
            cart_item.save()
        elif action_type == 'decrease':
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                cart_item.delete()
                return Response({'status': 'Item removed from cart'}, status=status.HTTP_200_OK)
            cart_item.save()
        else:
            return Response({'error': 'Invalid action. Use "increase" or "decrease"'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(cart_item).data)

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint to view user orders and execute checkout.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('cart_items', 'cart_items__item')

    def create(self, request, *args, **kwargs):
        cart_items = CartItems.objects.filter(user=request.user, ordered=False)
        if not cart_items.exists():
            return Response({'error': 'Your cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        delivery_address = request.data.get('delivery_address', 'Bengaluru, Karnataka')
        contact_phone = request.data.get('contact_phone', '')
        instructions = request.data.get('order_instructions', '')
        payment_method = request.data.get('payment_method', 'Cash on Delivery')

        subtotal = sum(ci.quantity * ci.item.price for ci in cart_items)
        delivery_fee = 35.0 if subtotal < 300 else 0.0
        tax_amount = round(subtotal * 0.05, 2)
        total_amount = round(subtotal + delivery_fee + tax_amount, 2)

        first_item = cart_items.first()
        restaurant = first_item.item.restaurant if first_item and first_item.item else None

        order_number = f"FG-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        order = Order.objects.create(
            order_number=order_number,
            user=request.user,
            restaurant=restaurant,
            delivery_address=delivery_address,
            contact_phone=contact_phone,
            order_instructions=instructions,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            tax_amount=tax_amount,
            total_amount=total_amount,
            payment_method=payment_method,
            status='Active'
        )

        cart_items.update(
            order=order,
            ordered=True,
            ordered_date=timezone.now().date(),
            status='Active'
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomerAddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for customer delivery addresses.
    """
    from accounts.models import CustomerAddress
    from .serializers import CustomerAddressSerializer
    queryset = CustomerAddress.objects.all()
    serializer_class = CustomerAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from accounts.models import CustomerAddress
        return CustomerAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for active promotional coupons.
    """
    from .models import Coupon
    from .serializers import CouponSerializer
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = CouponSerializer
    permission_classes = [permissions.AllowAny]


# ==============================================================================
# Authentication & Departmental API Endpoints (For Decoupled Frontend)
# ==============================================================================
from rest_framework.decorators import api_view, permission_classes as perm_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from accounts.models import Profile

@extend_schema(description="Returns CSRF token and sets the CSRF cookie for SPA clients.", responses={200: OpenApiTypes.OBJECT})
@api_view(['GET'])
@perm_decorator([permissions.AllowAny])
def csrf_token_view(request):
    """Returns CSRF token and sets the CSRF cookie for SPA clients."""
    token = get_token(request)
    return Response({'csrfToken': token})


@extend_schema(description="Returns the current authenticated user's profile and departmental role.", responses={200: OpenApiTypes.OBJECT})
@api_view(['GET'])
@perm_decorator([permissions.AllowAny])
def auth_me_view(request):
    """Returns the current authenticated user's profile and departmental role."""
    if not request.user.is_authenticated:
        return Response({'authenticated': False, 'role': 'GUEST'})

    profile = getattr(request.user, 'profile', None)
    role = getattr(profile, 'role', 'CUSTOMER') if profile else ('ADMIN' if request.user.is_superuser else 'CUSTOMER')
    restaurant_id = profile.restaurant.id if profile and profile.restaurant else None
    restaurant_name = profile.restaurant.name if profile and profile.restaurant else None

    return Response({
        'authenticated': True,
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'role': role,
        'restaurant_id': restaurant_id,
        'restaurant_name': restaurant_name,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
    })


@extend_schema(description="Authenticates user credentials and establishes a session for SPA clients.", responses={200: OpenApiTypes.OBJECT})
@api_view(['POST'])
@perm_decorator([permissions.AllowAny])
def auth_login_view(request):
    """Authenticates user credentials and establishes a session for SPA clients."""
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Support login via email or username
    user = authenticate(request, username=username, password=password)
    if not user:
        user_by_email = User.objects.filter(email__iexact=username).first()
        if user_by_email:
            user = authenticate(request, username=user_by_email.username, password=password)

    if user:
        login(request, user)
        profile = getattr(user, 'profile', None)
        role = getattr(profile, 'role', 'CUSTOMER') if profile else ('ADMIN' if user.is_superuser else 'CUSTOMER')
        return Response({
            'success': True,
            'message': 'Logged in successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': role,
                'restaurant_id': profile.restaurant.id if profile and profile.restaurant else None,
                'restaurant_name': profile.restaurant.name if profile and profile.restaurant else None,
            }
        })
    return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(description="Terminates the active session.", responses={200: OpenApiTypes.OBJECT})
@api_view(['POST'])
@perm_decorator([permissions.IsAuthenticated])
def auth_logout_view(request):
    """Terminates the active session."""
    logout(request)
    return Response({'success': True, 'message': 'Logged out successfully.'})


@extend_schema(description="Registers a new customer account.", responses={201: OpenApiTypes.OBJECT})
@api_view(['POST'])
@perm_decorator([permissions.AllowAny])
def auth_signup_view(request):
    """Registers a new customer account."""
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username is already taken.'}, status=status.HTTP_400_BAD_REQUEST)

    if email and User.objects.filter(email=email).exists():
        return Response({'error': 'Email is already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    Profile.objects.update_or_create(user=user, defaults={'role': 'CUSTOMER'})
    login(request, user)

    return Response({
        'success': True,
        'message': 'Account created successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': 'CUSTOMER'
        }
    }, status=status.HTTP_201_CREATED)


# --- Department 2: Restaurant Partner API ---
@extend_schema(description="Returns incoming orders for the logged-in restaurant partner's outlet.", responses={200: OpenApiTypes.OBJECT})
@api_view(['GET'])
@perm_decorator([permissions.IsAuthenticated])
def partner_orders_api(request):
    """Returns incoming orders for the logged-in restaurant partner's outlet."""
    profile = getattr(request.user, 'profile', None)
    if not (request.user.is_superuser or (profile and profile.role == 'RESTAURANT')):
        return Response({'error': 'Access denied: Restaurant partner role required.'}, status=status.HTTP_403_FORBIDDEN)

    rest = profile.restaurant if profile and profile.restaurant else Restaurant.objects.first()
    if not rest:
        return Response({'orders': [], 'restaurant': None})

    orders = Order.objects.filter(restaurant=rest).order_by('-created_at')[:50]
    serializer = OrderSerializer(orders, many=True)
    return Response({
        'restaurant': {'id': rest.id, 'name': rest.name, 'area': rest.area, 'is_open': rest.is_open},
        'orders': serializer.data
    })


@extend_schema(description="Updates preparation status for an order belonging to the partner's restaurant.", responses={200: OpenApiTypes.OBJECT})
@api_view(['POST'])
@perm_decorator([permissions.IsAuthenticated])
def partner_update_order_status_api(request, order_number):
    """Updates preparation status for an order belonging to the partner's restaurant."""
    profile = getattr(request.user, 'profile', None)
    if not (request.user.is_superuser or (profile and profile.role == 'RESTAURANT')):
        return Response({'error': 'Access denied: Restaurant partner role required.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    valid_statuses = ['Order Received', 'Accepted & Preparing', 'Ready for Pickup', 'Cancelled']
    if new_status not in valid_statuses:
        return Response({'error': f'Invalid status. Allowed: {valid_statuses}'}, status=status.HTTP_400_BAD_REQUEST)

    order.status = new_status
    if new_status == 'Accepted & Preparing' and not order.accepted_at:
        order.accepted_at = timezone.now()
    elif new_status == 'Ready for Pickup' and not order.ready_at:
        order.ready_at = timezone.now()
    elif new_status == 'Cancelled':
        order.cancellation_reason = request.data.get('reason', 'Cancelled by kitchen partner')
    order.save()

    return Response({'success': True, 'order_number': order.order_number, 'status': order.status})


# --- Department 3: Delivery Partner API ---
@extend_schema(description="Returns available orders and active assigned deliveries for the rider.", responses={200: OpenApiTypes.OBJECT})
@api_view(['GET'])
@perm_decorator([permissions.IsAuthenticated])
def delivery_orders_api(request):
    """Returns available orders and active assigned deliveries for the rider."""
    profile = getattr(request.user, 'profile', None)
    if not (request.user.is_superuser or (profile and profile.role == 'DELIVERY')):
        return Response({'error': 'Access denied: Delivery partner role required.'}, status=status.HTTP_403_FORBIDDEN)

    available_orders = Order.objects.filter(
        status__in=['Ready for Pickup', 'Accepted & Preparing', 'Active'],
        assigned_delivery_partner__isnull=True
    ).order_by('-created_at')[:20]

    assigned_orders = Order.objects.filter(
        assigned_delivery_partner=request.user
    ).exclude(status__in=['Delivered', 'Cancelled']).order_by('-created_at')

    completed_count = Order.objects.filter(
        assigned_delivery_partner=request.user,
        status='Delivered'
    ).count()

    return Response({
        'available': OrderSerializer(available_orders, many=True).data,
        'assigned': OrderSerializer(assigned_orders, many=True).data,
        'completed_deliveries_count': completed_count,
        'estimated_earnings_inr': completed_count * 45
    })


@extend_schema(description="Assigns an unassigned order to the calling delivery partner.", responses={200: OpenApiTypes.OBJECT})
@api_view(['POST'])
@perm_decorator([permissions.IsAuthenticated])
def delivery_claim_order_api(request, order_number):
    """Assigns an unassigned order to the calling delivery partner."""
    profile = getattr(request.user, 'profile', None)
    if not (request.user.is_superuser or (profile and profile.role == 'DELIVERY')):
        return Response({'error': 'Access denied: Delivery partner role required.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

    if order.assigned_delivery_partner and order.assigned_delivery_partner != request.user:
        return Response({'error': 'Order already assigned to another courier.'}, status=status.HTTP_400_BAD_REQUEST)

    order.assigned_delivery_partner = request.user
    order.status = 'Ready for Pickup'
    order.save()

    return Response({'success': True, 'order_number': order.order_number, 'status': order.status})


@extend_schema(description="Updates delivery run checkpoint (pickup -> deliver).", responses={200: OpenApiTypes.OBJECT})
@api_view(['POST'])
@perm_decorator([permissions.IsAuthenticated])
def delivery_update_status_api(request, order_number):
    """Updates delivery run checkpoint (pickup -> deliver)."""
    profile = getattr(request.user, 'profile', None)
    if not (request.user.is_superuser or (profile and profile.role == 'DELIVERY')):
        return Response({'error': 'Access denied: Delivery partner role required.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    if new_status == 'Out for Delivery':
        order.status = 'Out for Delivery'
        order.picked_up_at = timezone.now()
    elif new_status == 'Delivered':
        order.status = 'Delivered'
        order.delivered_at = timezone.now()
        order.is_paid = True
    else:
        return Response({'error': 'Invalid status. Use "Out for Delivery" or "Delivered"'}, status=status.HTTP_400_BAD_REQUEST)

    order.save()
    return Response({'success': True, 'order_number': order.order_number, 'status': order.status})


# --- Department 4: Platform Administrator API ---
@extend_schema(description="Returns platform executive statistics (GMV, order volume, partners count).", responses={200: OpenApiTypes.OBJECT})
@api_view(['GET'])
@perm_decorator([permissions.IsAuthenticated])
def admin_kpis_api(request):
    """Returns platform executive statistics (GMV, order volume, partners count)."""
    if not (request.user.is_staff or request.user.is_superuser):
        profile = getattr(request.user, 'profile', None)
        if not (profile and profile.role == 'ADMIN'):
            return Response({'error': 'Access denied: Platform Administrator role required.'}, status=status.HTTP_403_FORBIDDEN)

    from django.db.models import Sum
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='Delivered').count()
    total_gmv = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.0
    total_restaurants = Restaurant.objects.count()
    total_users = User.objects.count()

    recent_orders = Order.objects.order_by('-created_at')[:10]

    return Response({
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'total_gmv_inr': round(total_gmv, 2),
        'total_restaurants': total_restaurants,
        'total_users': total_users,
        'recent_orders': OrderSerializer(recent_orders, many=True).data
    })

