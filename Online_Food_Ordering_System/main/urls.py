from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    # -------------------------------------------------------------
    # Department 1: Customer Website (Pages 1 - 9)
    # -------------------------------------------------------------
    # Page 1: Home
    path('', views.home, name='home'),
    
    # Page 2: Search
    path('search/', views.search_view, name='search'),
    
    # Page 3: Restaurant listing
    path('restaurants/', views.restaurants_list_view, name='restaurants'),
    path('menu/', views.MenuListView.as_view(), name='menu_list'),
    
    # Page 4: Restaurant details & reviews
    path('restaurant/<slug:slug>/', views.restaurant_detail, name='restaurant_detail'),
    path('dishes/<slug:slug>/', views.menuDetail, name='dishes'),
    path('postReview', views.add_reviews, name='add_reviews'),

    # Page 5: Cart
    path('cart/', views.get_cart_items, name='cart'),
    path('add-to-cart/<slug:slug>/', views.add_to_cart, name='add-to-cart'),
    path('cart/update/<int:pk>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove-from-cart/<int:pk>/', views.CartDeleteView.as_view(), name='remove-from-cart'),
    path('coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('coupon/remove/', views.remove_coupon, name='remove_coupon'),

    # Page 6: Checkout
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/razorpay/create/', views.create_razorpay_order, name='create_razorpay_order'),
    path('ordered/', views.order_item, name='ordered'),
    path('order-success/<str:order_number>/', views.order_success, name='order_success'),

    # Page 7: Order tracking
    path('order-tracking/<str:order_number>/', views.order_tracking_view, name='order_tracking'),

    # Page 8: My orders
    path('orders/', views.order_details, name='orders'),
    path('order_details/', views.order_details, name='order_details'),
    path('orders/reorder/<str:order_number>/', views.reorder_order, name='reorder_order'),
    path('orders/cancel/<str:order_number>/', views.cancel_order, name='cancel_order'),

    # -------------------------------------------------------------
    # Department 2: Restaurant Dashboard (Pages 10 - 13)
    # -------------------------------------------------------------
    # Page 10: Restaurant overview
    path('partner/dashboard/', views.restaurant_portal_overview, name='restaurant_portal_overview'),

    # Page 11: Order management
    path('partner/orders/', views.restaurant_portal_orders, name='restaurant_portal_orders'),
    path('partner/orders/update/<str:order_number>/', views.restaurant_update_order_status, name='restaurant_update_order_status'),

    # Page 12: Menu management
    path('partner/menu/', views.restaurant_portal_menu, name='restaurant_portal_menu'),
    path('partner/menu/add/', views.restaurant_dish_create, name='restaurant_dish_create'),
    path('partner/menu/edit/<int:pk>/', views.restaurant_dish_edit, name='restaurant_dish_edit'),
    path('partner/menu/toggle/<int:pk>/', views.restaurant_dish_toggle_availability, name='restaurant_dish_toggle_availability'),
    path('partner/menu/delete/<int:pk>/', views.restaurant_dish_delete, name='restaurant_dish_delete'),

    # Page 13: Restaurant settings
    path('partner/settings/', views.restaurant_portal_settings, name='restaurant_portal_settings'),

    # -------------------------------------------------------------
    # Department 3: Delivery Dashboard (Pages 14 - 15)
    # -------------------------------------------------------------
    # Page 14: Delivery overview
    path('delivery/dashboard/', views.delivery_portal_overview, name='delivery_portal_overview'),

    # Page 15: Delivery details
    path('delivery/order/<str:order_number>/', views.delivery_portal_order_detail, name='delivery_portal_order_detail'),
    path('delivery/claim/<str:order_number>/', views.delivery_claim_order, name='delivery_claim_order'),
    path('delivery/pickup/<str:order_number>/', views.delivery_confirm_pickup, name='delivery_confirm_pickup'),
    path('delivery/deliver/<str:order_number>/', views.delivery_confirm_delivered, name='delivery_confirm_delivered'),

    # -------------------------------------------------------------
    # Department 4: Admin Dashboard (Pages 16 - 18)
    # -------------------------------------------------------------
    # Page 16: Admin overview
    path('admin-portal/', views.admin_portal_overview, name='admin_portal_overview'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Page 17: User and restaurant management
    path('admin-portal/users-restaurants/', views.admin_portal_management, name='admin_portal_management'),
    path('admin-portal/role/<int:user_id>/', views.admin_change_user_role, name='admin_change_user_role'),
    path('admin-portal/restaurant/toggle/<int:restaurant_id>/', views.admin_toggle_restaurant_approval, name='admin_toggle_restaurant_approval'),

    # Page 18: Order and offer management
    path('admin-portal/orders-offers/', views.admin_portal_orders_offers, name='admin_portal_orders_offers'),
    path('admin-portal/coupon/create/', views.admin_coupon_create, name='admin_coupon_create'),
    path('admin-portal/coupon/toggle/<int:coupon_id>/', views.admin_coupon_toggle, name='admin_coupon_toggle'),
    path('admin-portal/coupon/delete/<int:coupon_id>/', views.admin_coupon_delete, name='admin_coupon_delete'),

    # Legacy views
    path('admin_view/', views.admin_view, name='admin_view'),
    path('pending_orders/', views.pending_orders, name='pending_orders'),
    path('update_status/<int:pk>/', views.update_status, name='update_status'),
    path('item_list/', views.item_list, name='item_list'),
    path('item/new/', views.ItemCreateView.as_view(), name='item-create'),
    path('item-update/<slug:slug>/', views.ItemUpdateView.as_view(), name='item-update'),
    path('item-delete/<slug:slug>/', views.ItemDeleteView.as_view(), name='item-delete'),
]
