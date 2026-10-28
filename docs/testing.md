# FoodieGo — Quality Assurance & Testing Guide

## Test Suite Overview
FoodieGo includes automated test suites covering customer workflows, role-based authorization, cart and pricing calculations, order fulfillment, and REST API endpoints.

## Running Tests

### 1. Execute the Full Automated Test Suite:
```bash
python manage.py test main
```
This runs 34 comprehensive test cases validating:
- Customer browsing and restaurant search
- Cart calculations, discount coupons, and checkout
- Immutable Order and OrderItem creation
- Kitchen partner status transitions (Accepted -> Preparing -> Ready)
- Delivery partner assignment and completion lifecycle
- Role-based security decorators preventing unauthorized horizontal and vertical access
- REST API serialization and OpenAPI Swagger schema generation

### 2. Run System Integrity & Configuration Checks:
```bash
python manage.py check
```

### 3. Key Manual Verification Steps:
1. **Customer Order Journey**:
   - Register a new account at `/accounts/signup/`.
   - Browse `/restaurants/` and filter by "Pure Veg".
   - Search for dishes via `/search/?q=biryani`.
   - Add items to cart and verify dynamic subtotal at `/cart/`.
   - Complete checkout at `/checkout/` with delivery address and contact phone number.
   - Verify live tracking at `/order/<order_number>/track/`.
2. **Kitchen Order Processing**:
   - Log in as kitchen partner.
   - Visit `/partner/orders/` and advance order status.
3. **Delivery Rider Fulfillment**:
   - Log in as delivery partner.
   - Visit `/delivery/` and complete assigned delivery runs.
4. **API Documentation**:
   - Visit `/api/docs/` in the browser to interact with live endpoints.
