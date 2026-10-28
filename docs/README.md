# FoodieGo — Project Architecture & Setup Guide

## 1. Executive Summary
FoodieGo is an enterprise-grade full-stack food delivery application modeled after Swiggy and Zomato. The platform is designed with a decoupled architecture featuring:
- **Backend**: Python 3.13 / Django 6.0 REST API with Role-Based Access Control (RBAC), Razorpay payment processing, and OpenAPI 3.0 interactive documentation.
- **Frontend**: Modern React + Vite Single Page Application (SPA) offering dedicated interfaces for Customers, Restaurant Kitchen Managers, Delivery Couriers, and Platform Administrators, alongside the established Django server-rendered templates.
- **Database**: Relational catalog populated with 100 authentic Bengaluru restaurants and 10,006 dishes across 8 localities.

---

## 2. Technology Stack & Decoupled Architecture

```
                                  ┌───────────────────────────────────────────────┐
                                  │               Client Interfaces               │
                                  │  • React + Vite SPA (http://localhost:5173)   │
                                  │  • Django HTML5 Web (http://127.0.0.1:8000)   │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                        JSON REST API / Session & CSRF
                                                         │
                                  ┌──────────────────────▼────────────────────────┐
                                  │            Django Core Application            │
                                  │      (CORS Headers, Session Auth, RBAC)       │
                                  └──────────┬────────────────────────┬───────────┘
                                             │                        │
                      ┌──────────────────────┴──────┐  ┌──────────────┴──────────────┐
                      │          accounts           │  │            main             │
                      │  Authentication, Profiles,  │  │  Catalog, Cart, Portals,    │
                      │  RBAC Decorators, Addresses │  │  Orders, Razorpay & APIs    │
                      └──────────────┬──────────────┘  └──────────────┬──────────────┘
                                     │                                │
                                     └────────────────┬───────────────┘
                                                      │
                                         Django ORM / SQLite Database
                                                      │
                                  ┌───────────────────▼───────────────────────────┐
                                  │         Shared Relational Database            │
                                  │    100 Restaurants, 10,006 Menu Items         │
                                  └───────────────────────────────────────────────┘
```

### Frontend Architecture (`frontend/`):
- **Framework**: React 18, Vite 5.
- **State Management & Networking**: Axios with CSRF injection and session cookie credentials (`withCredentials: true`).
- **Styling**: Vanilla CSS design system with CSS custom tokens (`index.css`), responsive layouts, and Lucide React icons.
- **Portals Implemented**:
  1. *Customer Marketplace*: Locality filtering, instant search, menu dish browsing, dynamic cart bill breakdown, coupon discount engine, checkout form with Cash on Delivery and Razorpay test simulation, and 5-stage live order tracking.
  2. *Kitchen Partner Hub*: Real-time incoming order tickets, order status progression (`Accepted` &rarr; `Preparing` &rarr; `Ready for Pickup`), and menu availability.
  3. *Delivery Partner Portal*: Available order claiming pool, active delivery runs, pickup/delivery checkpoints, and automated earnings ledger (₹45/drop).
  4. *Platform Administrator*: Executive KPI metrics (Total GMV, Orders Count, Partner Count) and order management table.
  5. *Interview Demonstration Toolbar*: One-click instant role switcher to demonstrate any of the 4 roles without manual logout/login friction.

### Backend Architecture (`backend/`):
- **Framework**: Django 6.0, Django REST Framework 3.15+.
- **API Documentation**: OpenAPI 3.0 and interactive Swagger UI via `drf-spectacular` at `/api/docs/`.
- **CORS Support**: `django-cors-headers` configured for `http://localhost:5173` and `http://127.0.0.1:5173`.
- **Payment Gateway**: Integrated Razorpay Python SDK and Standard Checkout (`checkout.js`).

---

## 3. Database Design & Relational Schema

```
┌────────────────────────┐             1:1             ┌────────────────────────┐
│       auth.User        ├─────────────────────────────┤    accounts.Profile    │
│  (Django Native Auth)  │                             │  role: CUSTOMER/etc.   │
└───────────┬────────────┘                             └───────────┬────────────┘
            │                                                      │
            │ 1:N                                                  │ 0..1 (Manager)
            ▼                                                      ▼
┌────────────────────────┐                             ┌────────────────────────┐
│accounts.CustomerAddress │                             │    main.Restaurant     │
│  is_default: Boolean   │                             │  100 Bengaluru Outlets │
└────────────────────────┘                             └───────────┬────────────┘
            ▲                                                      │
            │ 1:N                                                  │ 1:N
            │                                                      ▼
┌───────────┴────────────┐                             ┌────────────────────────┐
│       main.Order       │                             │       main.Item        │
│  order_number: string  │                             │  10,006 Menu Dishes    │
│  status: 5 Stages      │                             └───────────┬────────────┘
│  payment_method: COD/RZ│                                         │
└───────────┬────────────┘                                         │ 1:N
            │                                                      ▼
            │ 1:N                                      ┌────────────────────────┐
            ▼                                          │     main.CartItems     │
┌────────────────────────┐                             │  quantity: integer     │
│     main.OrderItem     │                             └────────────────────────┘
│  Snapshot of Title,    │
│  Price, Quantity       │
└────────────────────────┘
```

- **Order Immutability**: Historical order lines are stored in `OrderItem` as fixed snapshots preserving the exact item title, price, and image at the time of purchase, preventing price skew if a merchant updates their menu later.
- **Catalog Breadth**: 100 restaurants across 8 Bengaluru neighborhoods (Koramangala, Indiranagar, HSR Layout, Whitefield, Jayanagar, BTM Layout, JP Nagar, Peenya) with 10,006 dishes.

---

## 4. Key API Endpoints

| Endpoint | Method | Role / Auth | Description |
| :--- | :--- | :--- | :--- |
| `/api/auth/csrf/` | GET | Public | Sets CSRF cookie and returns token |
| `/api/auth/me/` | GET | Public | Returns current authenticated user & role |
| `/api/auth/login/` | POST | Public | Authenticates credentials and starts session |
| `/api/auth/logout/` | POST | Authenticated | Terminates active session |
| `/api/auth/signup/` | POST | Public | Registers a new Customer account |
| `/api/restaurants/` | GET | Public | Lists restaurants with cuisine & area filters |
| `/api/restaurants/<id>/` | GET | Public | Retrieves restaurant details and menu items |
| `/api/items/` | GET | Public | Browse dishes with vegetarian and price filters |
| `/api/cart/` | GET/POST | Authenticated | Shopping cart view and item addition |
| `/api/cart/<id>/update_quantity/` | POST | Authenticated | Increment or decrement cart item quantity |
| `/api/orders/` | GET/POST | Authenticated | View orders and place checkout orders |
| `/api/partner/orders/` | GET | RESTAURANT | Kitchen live incoming order tickets queue |
| `/api/partner/orders/<order_number>/status/` | POST | RESTAURANT | Advance preparation status |
| `/api/delivery/orders/` | GET | DELIVERY | Available and active courier assignments |
| `/api/delivery/claim/<order_number>/` | POST | DELIVERY | Claim an available order for delivery |
| `/api/delivery/status/<order_number>/` | POST | DELIVERY | Update checkpoint (Pickup &rarr; Delivered) |
| `/api/admin/kpis/` | GET | ADMIN | Executive metrics (GMV, volume, users) |
| `/api/docs/` | GET | Public | Interactive Swagger UI API documentation |

---

## 5. How to Run the Project Locally

### Terminal 1: Backend (Django REST API & Templates)
```powershell
# Navigate to repository root
cd Online_Food_Ordering_System

# Activate Virtual Environment
.\.venv\Scripts\Activate.ps1

# Run system integrity check
python manage.py check

# Seed/Update Interview Test Accounts
python manage.py setup_test_accounts

# Start Django Development Server
python manage.py runserver 127.0.0.1:8000
```

### Terminal 2: Frontend (React + Vite Single Page Application)
```powershell
# Navigate to frontend folder
cd Online_Food_Ordering_System\frontend

# Install dependencies (first time only)
npm install

# Start Vite dev server
npm run dev
```

---

## 6. Accessing the Application

- **React + Vite Frontend**: [http://localhost:5173/](http://localhost:5173/)
- **Django Template Website**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger REST API Documentation**: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Platform Admin Dashboard**: [http://127.0.0.1:8000/admin-portal/](http://127.0.0.1:8000/admin-portal/)
- **Native Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 7. Known Limitations & Production Roadmap
- **Development Database**: SQLite is utilized for zero-configuration local execution; configure PostgreSQL with connection pooling (e.g., PgBouncer) for production concurrency.
- **GPS Telemetry**: Distance and delivery estimates use neighborhood locality centroid coordinates; live GPS tracking requires integrating Google Maps or Mapbox APIs.
- **Push Updates**: Live status updates use HTTP polling / page updates; production roadmap includes Redis and Django Channels for WebSocket push notifications.
