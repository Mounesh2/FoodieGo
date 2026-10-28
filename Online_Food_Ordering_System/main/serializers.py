from rest_framework import serializers
from .models import Restaurant, Item, Order, OrderItem, Coupon, CartItems, Reviews
from accounts.models import CustomerAddress

class ItemSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    display_image = serializers.CharField(source='get_display_image', read_only=True)

    class Meta:
        model = Item
        fields = [
            'id',
            'demo_id',
            'restaurant',
            'restaurant_name',
            'title',
            'category',
            'price',
            'pieces',
            'is_veg',
            'rating',
            'is_available',
            'discount_percent',
            'food_image_url',
            'display_image',
            'offer_label',
            'slug',
            'description',
            'data_type'
        ]

class RestaurantSerializer(serializers.ModelSerializer):
    display_image = serializers.CharField(source='get_display_image', read_only=True)
    menu_items_count = serializers.IntegerField(source='menu_items.count', read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            'id',
            'demo_id',
            'name',
            'slug',
            'area',
            'city',
            'state',
            'cuisine',
            'rating',
            'rating_count',
            'average_cost_for_two',
            'estimated_delivery_minutes',
            'delivery_fee',
            'latitude',
            'longitude',
            'is_open',
            'image_url',
            'display_image',
            'menu_items_count',
            'data_type'
        ]

from drf_spectacular.utils import extend_schema_field

class RestaurantDetailSerializer(RestaurantSerializer):
    menu_items = serializers.SerializerMethodField()

    class Meta(RestaurantSerializer.Meta):
        fields = RestaurantSerializer.Meta.fields + ['menu_items']

    @extend_schema_field(ItemSerializer(many=True))
    def get_menu_items(self, obj):
        items = obj.menu_items.filter(is_available=True)[:50]
        return ItemSerializer(items, many=True).data

class CartItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(), source='item', write_only=True
    )
    subtotal = serializers.FloatField(read_only=True)

    class Meta:
        model = CartItems
        fields = [
            'id',
            'item',
            'item_id',
            'quantity',
            'subtotal',
            'ordered',
            'status',
            'ordered_date'
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'item_title', 'item_price', 'quantity', 'subtotal', 'is_veg', 'food_image_url']

class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        from accounts.models import CustomerAddress
        model = CustomerAddress
        fields = ['id', 'title', 'address_line', 'landmark', 'area', 'city', 'pincode', 'phone', 'is_default']

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import Coupon
        model = Coupon
        fields = ['id', 'code', 'title', 'description', 'discount_percent', 'discount_amount', 'min_order_amount', 'max_discount_amount', 'is_active', 'usage_count']

class OrderSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cart_items', many=True, read_only=True)
    order_items = OrderItemSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'username',
            'restaurant',
            'delivery_address',
            'contact_phone',
            'order_instructions',
            'subtotal',
            'delivery_fee',
            'tax_amount',
            'discount_amount',
            'total_amount',
            'status',
            'payment_method',
            'is_paid',
            'created_at',
            'items',
            'order_items'
        ]

class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Reviews
        fields = ['id', 'username', 'item', 'review', 'rating', 'posted_on']
