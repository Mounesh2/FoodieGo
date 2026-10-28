from django.contrib import admin
from .models import Restaurant, Item, Order, CartItems, Reviews

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'area', 'cuisine', 'rating', 'average_cost_for_two', 'is_open', 'data_type')
    list_filter = ('cuisine', 'area', 'is_open', 'data_type')
    search_fields = ('name', 'area', 'cuisine')
    prepopulated_fields = {'slug': ('name', 'area')}

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'restaurant', 'category', 'price', 'is_veg', 'rating', 'is_available', 'data_type')
    list_filter = ('category', 'is_veg', 'is_available', 'labels', 'data_type')
    search_fields = ('title', 'description', 'restaurant__name')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'restaurant', 'total_amount', 'status', 'payment_method', 'is_paid', 'razorpay_payment_id', 'created_at')
    list_filter = ('status', 'payment_method', 'is_paid', 'created_at')
    search_fields = ('order_number', 'user__username', 'delivery_address', 'razorpay_payment_id', 'razorpay_order_id')

@admin.register(CartItems)
class CartItemsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'item', 'quantity', 'ordered', 'order', 'status', 'ordered_date')
    list_filter = ('ordered', 'status', 'ordered_date')
    search_fields = ('user__username', 'item__title')

@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'rating', 'review', 'posted_on')
    list_filter = ('rating', 'posted_on')
    search_fields = ('user__username', 'item__title', 'review')
