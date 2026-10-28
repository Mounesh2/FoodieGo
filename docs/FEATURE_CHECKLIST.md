# FoodieGo — Feature Verification & Page-by-Page Checklist

This checklist documents the verified status of every page, workflow, and access control boundary across all four departments in FoodieGo.

---

## 1. Customer Marketplace Department

| Feature / Page | URL Route | Access Control | Status | Verified Capabilities |
| :--- | :--- | :--- | :---: | :--- |
| **Home Page** | `/` | Public | **PASS** | Hero banner, neighborhood discovery chips, featured restaurants, cuisine pills, footer navigation. Responsive on desktop and mobile. |
| **Registration** | `/accounts/signup/` | Public | **PASS** | Username, email, password fields. Password confirmation and strength validation. Automatically sets role to `CUSTOMER`. |
| **Login & Logout** | `/accounts/login/`, `/accounts/logout/` | Public / Auth | **PASS** | Form validation with invalid credential feedback. Secure session establishment. Post-login redirect based on role. |
| **Restaurant Listing** | `/restaurants/` | Public | **PASS** | Paginated grid of 100 Bengaluru outlets. Filter by Pure Veg, minimum rating (4.0+), and neighborhood locality. |
| **Search & Filters** | `/search/` | Public | **PASS** | Instant multi-entity search matching dish names, restaurant titles, and cuisines across the entire 10,006 item catalog. |
| **Restaurant Details** | `/restaurant/<slug>/` | Public | **PASS** | Cover photo, cuisine tags, delivery estimate, rating stats, customer reviews list, and categorization of dishes. |
| **Menu Items** | `/restaurant/<slug>/`, `/dishes/<slug>/` | Public | **PASS** | Dish cards showing title, price, vegetarian icon, description, and high-resolution food image with fallback SVG protection. |
| **Shopping Cart** | `/cart/` | `@login_required` | **PASS** | Line items display, unit price, item subtotal, delivery fee calculation (free over ₹300), 5% tax amount, empty state message. |
| **Quantity Updates & Item Removal** | `/cart/update/<id>/`, `/remove-from-cart/<id>/` | `@login_required` | **PASS** | Increment/decrement buttons dynamically update quantities. Decrementing below 1 cleanly removes item from cart. |
| **Coupon Application** | `/coupon/apply/`, `/coupon/remove/` | `@login_required` | **PASS** | Validates coupon codes (`WELCOME50`, `BENGALURU100`), checks minimum order spend threshold, and deducts discount. |
| **Checkout** | `/checkout/` | `@login_required` | **PASS** | Phone validation (>=10 digits regex), saved address radio selector, manual address fallback input, bill summary display. |
| **Payment Selection** | `/checkout/` | `@login_required` | **PASS** | Radio toggle between **Razorpay Standard Checkout** and **Cash on Delivery**. AJAX order ID generation via `/checkout/razorpay/create/`. |
| **Order Confirmation** | `/order-success/<order_number>/` | `@login_required` | **PASS** | Order number display (`FG-YYYYMMDD-XXXX`), delivery address, payment mode, order item summary, and link to track order. |
| **Order History** | `/orders/` | `@login_required` | **PASS** | Historical list of user's past orders with status badges, dates, and one-click "Reorder" action that restocks active cart. |
| **Order Tracking** | `/order-tracking/<order_number>/` | `@login_required` | **PASS** | Real-time 5-stage progress indicator: `Order Received` &rarr; `Accepted & Preparing` &rarr; `Ready for Pickup` &rarr; `Out for Delivery` &rarr; `Delivered`. |
| **Customer Profile** | `/accounts/profile/` | `@login_required` | **PASS** | Personal details, email, contact phone, role indicator, and saved addresses overview. |
| **Address Management** | `/accounts/address/add/`, `/accounts/address/default/<id>/` | `@login_required` | **PASS** | Add tagged addresses (Home, Work, Other), delete addresses, and mark active default address. |

---

## 2. Restaurant Partner Hub Department

| Feature / Page | URL Route | Access Control | Status | Verified Capabilities |
| :--- | :--- | :--- | :---: | :--- |
| **Partner Login** | `/accounts/login/` | Public | **PASS** | Kitchen managers authenticate and are redirected directly to their portal dashboard. |
| **Kitchen Dashboard** | `/partner/dashboard/` | `@restaurant_required` | **PASS** | Outlet KPI cards: today's incoming ticket count, active preparing orders, and revenue summary. |
| **Restaurant Profile & Settings** | `/partner/settings/` | `@restaurant_required` | **PASS** | Outlet operating hours, delivery radius, preparation time estimate, and open/closed toggle switch. |
| **Menu Management** | `/partner/menu/` | `@restaurant_required` | **PASS** | Dish catalog list with price, category, vegetarian flag, and stock status for the partner's restaurant. |
| **Add Menu Item** | `/partner/menu/add/` | `@restaurant_required` | **PASS** | Form to create a new dish with title, price, category, vegetarian flag, and optional image. |
| **Edit Menu Item** | `/partner/menu/edit/<id>/` | `@restaurant_required` | **PASS** | Modify price, description, pieces, and discount details with form validation. |
| **Toggle Availability** | `/partner/menu/toggle/<id>/` | `@restaurant_required` | **PASS** | One-click instant toggle to switch dishes between "In Stock" and "Sold Out". |
| **Delete Menu Item** | `/partner/menu/delete/<id>/` | `@restaurant_required` | **PASS** | Confirmation modal preventing accidental menu dish deletion. |
| **Incoming Orders Queue** | `/partner/orders/` | `@restaurant_required` | **PASS** | Live ticket queue displaying customer name, contact phone, items, quantities, and order timestamp. |
| **Order Status Progression** | `/partner/orders/update/<order_number>/` | `@restaurant_required` | **PASS** | Controlled state machine: advances order from `Order Received` &rarr; `Accepted & Preparing` &rarr; `Ready for Pickup`. |
| **Operational Cancellation** | `/partner/orders/update/<order_number>/` | `@restaurant_required` | **PASS** | Allows rejecting/cancelling an order with mandatory operational reason recording. |

---

## 3. Delivery Partner Portal Department

| Feature / Page | URL Route | Access Control | Status | Verified Capabilities |
| :--- | :--- | :--- | :---: | :--- |
| **Rider Login** | `/accounts/login/` | Public | **PASS** | Delivery couriers log in and are routed to the rider dispatch portal. |
| **Rider Dashboard** | `/delivery/dashboard/` | `@delivery_required` | **PASS** | Overview of active assigned trip, trip completion counter, and available orders pool. |
| **Available Deliveries Pool** | `/delivery/dashboard/` | `@delivery_required` | **PASS** | Unassigned orders marked `Ready for Pickup` with restaurant pickup locality and customer drop address. |
| **Claim Delivery Run** | `/delivery/claim/<order_number>/` | `@delivery_required` | **PASS** | One-click claim assigning order to the rider; locks order so other riders cannot claim it. |
| **Order Pickup Checkpoint** | `/delivery/pickup/<order_number>/` | `@delivery_required` | **PASS** | Rider confirms arrival and food collection at kitchen; advances status to `Out for Delivery`. |
| **Order Drop Checkpoint** | `/delivery/deliver/<order_number>/` | `@delivery_required` | **PASS** | Rider confirms drop-off at customer location; marks order `Delivered` and records delivery timestamp. |
| **Earnings & History Ledger** | `/delivery/dashboard/` | `@delivery_required` | **PASS** | Automated calculation of delivery fees (flat ₹45 per completed order) with historical trip logs. |

---

## 4. Platform Administrator Operations Department

| Feature / Page | URL Route | Access Control | Status | Verified Capabilities |
| :--- | :--- | :--- | :---: | :--- |
| **Admin Login** | `/accounts/login/`, `/admin/` | Staff / Superuser | **PASS** | Superuser and admin authentication with access to both custom executive dashboard and Django admin. |
| **Executive KPI Dashboard** | `/admin-portal/` | `@admin_required` | **PASS** | Platform Gross Merchandise Value (GMV), total completed orders, registered customer counts, and restaurants count. |
| **User & Role Governance** | `/admin-portal/users-restaurants/` | `@admin_required` | **PASS** | List of registered users with role badges; ability to promote users to `RESTAURANT`, `DELIVERY`, or `ADMIN`. |
| **Restaurant Affiliation** | `/admin-portal/role/<id>/` | `@admin_required` | **PASS** | Link a restaurant partner user to their specific restaurant outlet. |
| **Restaurant Moderation** | `/admin-portal/restaurant/toggle/<id>/` | `@admin_required` | **PASS** | Instant one-click toggle to approve or suspend partner restaurant listings on the public marketplace. |
| **Orders Oversight** | `/admin-portal/orders-offers/` | `@admin_required` | **PASS** | Filterable table of all system orders across all restaurants and couriers. |
| **Promotional Coupon Engine** | `/admin-portal/coupon/create/`, `toggle/`, `delete/` | `@admin_required` | **PASS** | Create promo codes with percentage or flat deductions, set minimum spend amounts, and toggle campaign status. |
| **Django Native Admin** | `/admin/` | `is_staff` | **PASS** | Full relational database CRUD for all models (`User`, `Profile`, `CustomerAddress`, `Restaurant`, `Item`, `Order`, `OrderItem`, `Coupon`, `Review`). |

---

## 5. Verification Standards & Defect Report

- **Security Enforcement**: Unauthorized access attempts to any portal (`/partner/`, `/delivery/`, `/admin-portal/`) result in immediate redirect to `/accounts/login/` with an informational notice.
- **Empty States**: Cart, orders list, search results, and kitchen queues render clean empty state graphics and descriptive guidance when no records are present.
- **Responsive Layout**: Validated across viewport widths (desktop 1440px, tablet 768px, mobile 375px).
- **Missing Features / Known Gaps**:
  - Live push notifications: Currently relies on page reload; WebSockets (Django Channels) recommended for production.
  - GPS Tracking: Neighborhood centroid approximations used instead of real-time Google Maps telemetry.
