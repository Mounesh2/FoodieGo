# FoodieGo — Online Food Ordering System

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0-success.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.x-646cff.svg)](https://vitejs.dev/)
[![DRF](https://img.shields.io/badge/DRF-3.15%2B-red.svg)](https://www.django-rest-framework.org/)
[![OpenAPI 3.0](https://img.shields.io/badge/OpenAPI-3.0%20Swagger-orange.svg)](http://127.0.0.1:8000/api/docs/)
[![Razorpay](https://img.shields.io/badge/Payment-Razorpay%20Test%20Mode-blueviolet.svg)](https://razorpay.com/)
[![Automated Tests](https://img.shields.io/badge/Automated%20Tests-34%20Passed%20(100%25)-brightgreen.svg)](docs/FEATURE_CHECKLIST.md)

---

## 1. Project Overview

**FoodieGo** is an enterprise-grade, full-stack online food ordering and multi-department fulfillment web platform inspired by hyper-local food delivery services such as Swiggy and Zomato. The application supports an authentic culinary catalog of **100 Bengaluru restaurants** and **10,006 menu items** across 8 major localities.

The platform is designed with a **decoupled architecture**:
- A modern **React + Vite Single-Page Application (SPA)** with real-time role switching, rich UI animations, dynamic cart management, and seamless API communication.
- A robust **Django 6.0 & Django REST Framework (DRF)** backend powering secure Role-Based Access Control (RBAC), transactional order processing, Razorpay test mode payment verification, and automated OpenAPI 3.0 documentation.
- Dual compatibility with native **Django server-rendered templates** alongside the React SPA, operating concurrently against a single authoritative database.

---

## 2. Website & Documentation Links

> [!IMPORTANT]
> **Server Dependency Notice**: The following links function **only when the corresponding local development servers are actively running**. Ensure the backend server (`python manage.py runserver 127.0.0.1:8000`) and/or frontend server (`npm run dev`) are started before clicking these links.

| Interface / Service | Local Development URL | Description |
| :--- | :--- | :--- |
| **React Frontend SPA** | [http://localhost:5173/](http://localhost:5173/) | Modern React + Vite application with live role switcher for technical interview demonstrations |
| **Django Website** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | Full-featured server-rendered web application with all 4 department portals |
| **Swagger API Documentation** | [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/) | Interactive OpenAPI 3.0 Swagger UI for live API testing (`Try it out`) |
| **ReDoc API Documentation** | [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/) | Clean, structured technical API documentation |
| **Django Admin** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) | Native Django administrative interface for raw database management |

---

## 3. Interview Demo Accounts

For technical interviews and demonstrations, a repeatable setup command configures dedicated development-only accounts with the minimum required role permissions.

### Demo Credentials Matrix

| Role | Username | Local Dev Password | Purpose & Features to Demonstrate |
| :--- | :--- | :--- | :--- |
| **Customer** | `demo_customer` | `FoodieGo@Customer2026!` | **Marketplace Experience**: Browse 100 restaurants across 8 Bengaluru zones, live dish search, veg/rating filters, add items to cart, apply promo coupons (`WELCOME50`), checkout via COD or Razorpay test mode, and track live 5-stage order progression. |
| **Restaurant Partner** | `demo_partner` | `FoodieGo@Partner2026!` | **Kitchen Control Center**: Linked to *Coastal Cafe 010*. View live incoming ticket queue, sequentially advance preparation statuses (`Accepted` &rarr; `Preparing` &rarr; `Ready for Pickup`), and toggle menu dish availability (in-stock vs. sold-out). |
| **Delivery Partner** | `demo_rider` | `FoodieGo@Rider2026!` | **Rider Dispatch & Logistics**: View unassigned order pool, claim available delivery runs, confirm kitchen pickup (`Out for Delivery`), confirm customer drop-off (`Delivered`), and review flat ₹45/trip earnings. |
| **Administrator** | `demo_admin` | `FoodieGo@Admin2026!` | **Operations & Governance**: Real-time platform KPI analytics (GMV, volume, counts), user role assignment, restaurant approval / suspension toggling, promotional coupon creation, and Django Admin access. |

### How to Create or Reset Demo Accounts

Run the custom idempotent Django management command from the project root:

```powershell
python manage.py setup_test_accounts
```

> [!NOTE]
> **Pre-Verification Confirmation**: This command has been executed and verified against the live database. All four accounts have been tested via Django's authentication system (`authenticate(username, password)`) with a **100% verified pass rate**. The command is safe to re-run at any time — it updates existing accounts without duplicating records or corrupting unrelated data.

---

## 4. System Architecture

FoodieGo cleanly separates concerns between client presentation, REST APIs, business logic, and transactional data storage:

```
                            ┌─────────────────────────────────────────┐
                            │        React + Vite Frontend SPA        │
                            │        http://localhost:5173/           │
                            │  (Role Switcher, Cart, Dynamic Filters) │
                            └────────────────────┬────────────────────┘
                                                 │
                                 JSON REST APIs / Session & CSRF
                                 (CORS Enabled with Credentials)
                                                 │
                            ┌────────────────────▼────────────────────┐
                            │         Django 6.0 Core Backend         │
                            │         http://127.0.0.1:8000/          │
                            │   (REST Framework + Template Engine)    │
                            └──────────┬───────────────────┬──────────┘
                                       │                   │
                ┌──────────────────────┴──────┐     ┌──────┴──────────────────────┐
                │          accounts           │     │            main             │
                │  Authentication, Profiles,  │     │  Catalog, Cart, Portals,    │
                │  RBAC Decorators, Addresses │     │  Orders, Razorpay & APIs    │
                └──────────────┬──────────────┘     └──────────────┬──────────────┘
                               │                                   │
                               └─────────────────┬─────────────────┘
                                                 │
                                     Django ORM / QuerySet Layer
                                                 │
                            ┌────────────────────▼────────────────────┐
                            │       Authoritative Database (SQLite)   │
                            │     100 Restaurants, 10,006 Menu Items  │
                            └─────────────────────────────────────────┘
```

### Technology Stack Details

| Layer | Technologies | Role & Implementation |
| :--- | :--- | :--- |
| **Frontend SPA** | React 18, Vite 6, Vanilla CSS3 | Client-side reactive interface with reverse proxy to `:8000`, live role switcher, and dynamic cart state |
| **Backend Core** | Python 3.13, Django 6.0 | Batteries-included web framework with secure ORM, session handling, and authentication |
| **REST APIs** | Django REST Framework 3.15+ | Model serializers, ViewSets, API views, and CORS middleware (`django-cors-headers`) |
| **API Schema** | `drf-spectacular` 0.28+ | Auto-generated OpenAPI 3.0 schema with interactive Swagger UI and ReDoc |
| **Payments** | Razorpay Python SDK 1.4+ | Razorpay Standard Checkout (`checkout.js`) with HMAC-SHA256 signature verification & test sandbox simulator |
| **Database** | SQLite3 (Dev) / PostgreSQL (Prod) | Relational database containing 100 restaurants, 10,006 menu items, and relational order snapshots |
| **Styling & Assets** | Custom CSS Design System, Bootstrap 4.6 | Clean responsive styling (`foodiego.css`) with infinite-loop-safe brand SVG fallbacks |
| **Testing** | Django Standard Test Runner | 34 automated unit and integration tests (100% pass rate) |

---

## 5. Startup Instructions

### Prerequisites
- **Python**: Version 3.11, 3.12, or 3.13 installed
- **Node.js**: Version 18+ and `npm` installed
- **Git**: Installed and configured

### Step 1: Clone and Set Up Virtual Environment

```powershell
# Clone the repository
git clone https://github.com/Mounesh2/FoodieGo.git
cd FoodieGo

# Create and activate virtual environment (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# (For macOS / Linux: source .venv/bin/activate)
```

### Step 2: Install Backend Dependencies & Configure Environment

```powershell
# Install required Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create environment configuration
copy .env.example .env

# Verify database and run system check
python manage.py check
python manage.py migrate

# Initialize or reset interview test accounts
python manage.py setup_test_accounts
```

### Step 3: Start the Backend Server

```powershell
# Start Django backend on http://127.0.0.1:8000
python manage.py runserver 127.0.0.1:8000
```

### Step 4: Start the Frontend Application (New Terminal Window)

```powershell
# Open a new terminal and navigate to frontend
cd frontend

# Install Node dependencies (first time only)
npm install

# Start Vite development server
npm run dev
# The React SPA will open at http://localhost:5173/
```

To verify the production frontend build:
```powershell
cd frontend
npm run build
```

---

## 6. Project Directory Layout

```text
FoodieGo/
├── frontend/                                   # React + Vite Single-Page Application
│   ├── src/
│   │   ├── App.jsx                             # Multi-department view & Role Switcher
│   │   ├── api.js                              # REST API client with CSRF & session handling
│   │   ├── index.css                           # Modern CSS design system
│   │   └── main.jsx
│   ├── dist/                                   # Production build output
│   ├── index.html
│   ├── vite.config.js                          # Reverse proxy configuration to Django :8000
│   ├── package.json
│   ├── .env.example
│   └── .gitignore
│
├── backend/ -> Online_Food_Ordering_System/    # Authoritative Django project directory
│   ├── Foods_Ordering/                         # Django settings, root URLs, WSGI
│   ├── accounts/                               # Custom User, Profile (RBAC), Address models
│   ├── main/                                   # Restaurant, Item, Cart, Order models & views
│   │   ├── api_views.py                        # Django REST Framework ViewSets & Auth APIs
│   │   ├── api_urls.py                         # REST API routes & Swagger registration
│   │   ├── serializers.py                      # Model serializers
│   │   ├── management/commands/
│   │   │   └── setup_test_accounts.py          # Demo accounts setup command
│   │   └── tests.py                            # 34 integration & regression tests
│   ├── media/                                  # Uploaded restaurant and food photos
│   ├── data/                                   # Bengaluru restaurant & menu CSV datasets
│   ├── db.sqlite3                              # Authoritative database (100 rests, 10,006 items)
│   ├── manage.py
│   └── requirements.txt
│
├── docs/                                       # Technical Interview Documentation
│   ├── README.md                               # Comprehensive system documentation
│   ├── INTERVIEW_GUIDE.md                      # 10-minute demonstration script & talking points
│   ├── TEST_ACCOUNTS.md                        # Test credentials & role permissions guide
│   └── FEATURE_CHECKLIST.md                    # Page-by-page verification checklist
│
├── db_backups/                                 # Safe pre-modification database archives (git-ignored)
├── _backup_foodiego_v1/                        # Original V1 backup (kept strictly untouched)
├── manage.py                                   # Root launcher forwarding to backend
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md                                   # Root platform documentation
```

---

## 7. Departmental Portals & Workflows

### 1. Customer Marketplace
- **Discovery**: Filter restaurants across 8 Bengaluru zones (Koramangala, Indiranagar, HSR Layout, Whitefield, Jayanagar, BTM Layout, JP Nagar, Peenya).
- **Cart & Pricing**: Live recalculation of subtotal, delivery fee, packaging fee, and taxes.
- **Discounts**: Promotional coupon application (`WELCOME50`, `BENGALURU100`) with minimum-order validation.
- **Dual Payment**:
  - **Razorpay Standard Checkout**: Automated order creation, modal popup, HMAC-SHA256 signature verification, and sandbox simulation fallback.
  - **Cash on Delivery (COD)**: One-click submission for pay-on-arrival orders.
- **Order Tracking**: 5-stage visual progression bar (`Order Received` &rarr; `Accepted & Preparing` &rarr; `Ready for Pickup` &rarr; `Out for Delivery` &rarr; `Delivered`).

### 2. Restaurant Partner Hub (`/partner/`)
- Protected by `@restaurant_required` decorator.
- **Live Kitchen Queue**: Real-time incoming order tickets for the manager's assigned restaurant.
- **Status Advancement**: Sequentially transition orders from `Accepted` &rarr; `Preparing` &rarr; `Ready for Pickup`.
- **Menu Management**: One-click toggling of menu items between in-stock and sold-out.

### 3. Delivery Partner Portal (`/delivery/`)
- Protected by `@delivery_required` decorator.
- **Available Orders Pool**: Claim unassigned orders ready for pickup.
- **Delivery Workflow**: Two-phase verification — Confirm Pickup at Restaurant (`Out for Delivery`) and Confirm Drop at Customer (`Delivered`).
- **Earnings Tracking**: Automated flat ₹45 rate credited per completed trip.

### 4. Platform Administrator Operations (`/admin-portal/` and `/admin/`)
- Protected by `@admin_required` decorator.
- **Executive KPIs**: Real-time Gross Merchandise Value (GMV), order volume, customer count, and restaurant count.
- **Governance**: User role assignment (`CUSTOMER`, `RESTAURANT`, `DELIVERY`, `ADMIN`), restaurant listing approval toggles, and promotional coupon management.

---

## 8. Automated Testing & Quality Assurance

Run the automated test suite:
```powershell
python manage.py test
```

### Test Suite Summary:
- **Total Test Cases**: 34
- **Pass Rate**: 100% (34 passed, 0 failures, 0 errors)
- **Key Test Areas**:
  - Role-Based Access Control and decorator security (`@restaurant_required`, `@delivery_required`, `@admin_required`).
  - Cart calculation, coupon discount validation, and minimum-spend rules.
  - Checkout form validation (phone number verification, address selection).
  - Razorpay order ID generation, signature validation, and sandbox fallback.
  - Multi-stage order progression and delivery earnings calculation.
  - DRF REST API serializers and OpenAPI schema generation.

---

## 9. Security & Production Considerations

- **Credential Isolation**: All sensitive keys (`DJANGO_SECRET_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`) are isolated in `.env` files and excluded from Git version control via `.gitignore`.
- **Protection**: Native Django CSRF token enforcement across all state-changing POST requests.
- **Production Checklist**:
  1. Set `DJANGO_DEBUG=False` in `.env`.
  2. Configure `DJANGO_ALLOWED_HOSTS` to your production domain.
  3. Migrate from SQLite to managed PostgreSQL.
  4. Enable HTTPS enforcement (`SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`).
  5. Upgrade real-time order tracking from HTTP polling to WebSockets (Django Channels + Redis).
