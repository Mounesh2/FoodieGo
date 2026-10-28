# FoodieGo — Platform Architecture & System Design

## 1. Architectural Overview
FoodieGo is built as a monolithic Django full-stack web application with a shared relational database (SQLite in development, PostgreSQL ready for production) and integrated REST APIs powered by Django REST Framework (DRF) and `drf-spectacular` (OpenAPI 3.0 / Swagger UI).

```
                        ┌───────────────────────────────┐
                        │      Client Web / Mobile      │
                        │    (Responsive HTML5 + CSS)   │
                        └───────────────┬───────────────┘
                                        │
                         HTTP Requests / REST API calls
                                        │
                        ┌───────────────▼───────────────┐
                        │     Django Web Application    │
                        │   (Session Auth / DRF Tokens) │
                        └───────┬───────────────┬───────┘
                                │               │
          ┌─────────────────────┴──────┐ ┌──────┴────────────────────┐
          │         accounts           │ │           main            │
          │  User Models & Profiles    │ │  Catalog, Cart, Orders,   │
          │  Role Decorators, Auth     │ │  Portals, REST Endpoints  │
          └─────────────┬──────────────┘ └──────┬────────────────────┘
                        │                       │
                        └───────────────┬───────┘
                                        │
                        ┌───────────────▼───────────────┐
                        │    Shared Relational Database │
                        │    (100 Rests, 10,006 Dishes) │
                        └───────────────────────────────┘
```

## 2. Department Design & Role-Based Access Control (RBAC)
FoodieGo implements strict role-based access control across four functional departments:

| Department | Role Name | Required Permissions | Primary Views / URLs |
| :--- | :--- | :--- | :--- |
| **Customer** | `CUSTOMER` | Authenticated user (`login_required`) | `/` (Explore), `/restaurants/`, `/restaurant/<slug>/`, `/cart/`, `/checkout/`, `/orders/`, `/accounts/profile/` |
| **Restaurant Partner** | `RESTAURANT` | `@restaurant_required` decorator | `/partner/` (Overview), `/partner/orders/` (Order Lifecycle), `/partner/menu/` (Menu Management), `/partner/settings/` |
| **Delivery Partner** | `DELIVERY` | `@delivery_required` decorator | `/delivery/` (Rider Hub), `/delivery/order/<id>/` (Pickup/Delivery Actions) |
| **Administrator** | `ADMIN` | `@admin_required` or `is_staff` / `is_superuser` | `/admin-portal/` (Executive KPIs), `/admin-portal/orders/`, `/admin-portal/management/`, `/admin/` (Django Admin) |

### Role Decorators (`main/decorators.py`):
- `restaurant_required`: Ensures `request.user.profile.role == 'RESTAURANT'` or user is a superuser. Redirects unauthorized users to `/accounts/login/`.
- `delivery_required`: Ensures `request.user.profile.role == 'DELIVERY'` or user is a superuser.
- `admin_required`: Ensures `request.user.profile.role == 'ADMIN'`, `is_staff`, or `is_superuser`.

## 3. Core Database Models & Relationships
- **User & Profile** (`accounts.models`): One-to-One with Django's `User`. Stores `role`, `phone_number`, `address`, `restaurant` foreign key, and `is_available` flag.
- **CustomerAddress** (`accounts.models`): ForeignKey to `User`. Supports multiple tagged delivery addresses with `is_default` flag.
- **Restaurant** (`main.models`): Master entity with `name`, `slug`, `cuisine`, `area`, `city`, `rating`, `estimated_delivery_minutes`, `image_url`, and `is_open`.
- **Item** (`main.models`): Menu dish linked via ForeignKey to `Restaurant`. Has `title`, `slug`, `price`, `food_image_url`, `is_veg`, `category`, and `is_available`.
- **CartItems** (`main.models`): Active user shopping session line item linked to `User` and `Item`. Includes `quantity` and `ordered` boolean flag.
- **Order** (`main.models`): Fulfillment transaction with unique `order_number`, linked to `User` (customer), `assigned_delivery_partner` (User), `delivery_address`, `total_amount`, and `status`.
- **OrderItem** (`main.models`): Immutable historical line item snapshot storing dish title, unit price, quantity, and food image at the exact time of order placement.
- **Coupon** (`main.models`): Promotional discount rules with minimum order threshold and expiry controls.
