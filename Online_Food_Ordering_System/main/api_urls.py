from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)
from .api_views import (
    RestaurantViewSet,
    ItemViewSet,
    CartViewSet,
    OrderViewSet,
    CustomerAddressViewSet,
    CouponViewSet,
    csrf_token_view,
    auth_me_view,
    auth_login_view,
    auth_logout_view,
    auth_signup_view,
    partner_orders_api,
    partner_update_order_status_api,
    delivery_orders_api,
    delivery_claim_order_api,
    delivery_update_status_api,
    admin_kpis_api
)

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='api-restaurant')
router.register(r'items', ItemViewSet, basename='api-item')
router.register(r'cart', CartViewSet, basename='api-cart')
router.register(r'orders', OrderViewSet, basename='api-order')
router.register(r'addresses', CustomerAddressViewSet, basename='api-address')
router.register(r'coupons', CouponViewSet, basename='api-coupon')

urlpatterns = [
    # OpenAPI 3 Schema & Swagger UI
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication Endpoints
    path('auth/csrf/', csrf_token_view, name='api-auth-csrf'),
    path('auth/me/', auth_me_view, name='api-auth-me'),
    path('auth/login/', auth_login_view, name='api-auth-login'),
    path('auth/logout/', auth_logout_view, name='api-auth-logout'),
    path('auth/signup/', auth_signup_view, name='api-auth-signup'),

    # Departmental Endpoints
    path('partner/orders/', partner_orders_api, name='api-partner-orders'),
    path('partner/orders/<str:order_number>/status/', partner_update_order_status_api, name='api-partner-order-status'),
    path('delivery/orders/', delivery_orders_api, name='api-delivery-orders'),
    path('delivery/claim/<str:order_number>/', delivery_claim_order_api, name='api-delivery-claim'),
    path('delivery/status/<str:order_number>/', delivery_update_status_api, name='api-delivery-status'),
    path('admin/kpis/', admin_kpis_api, name='api-admin-kpis'),

    # ViewSet Routers
    path('', include(router.urls)),
]
