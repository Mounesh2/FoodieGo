# FoodieGo — Technical Interview Demonstration Guide

This guide provides a structured, 10-minute presentation plan for demonstrating the FoodieGo platform during a technical interview.

---

## 1. Quick Architecture Talking Points (2 Minutes)

When introducing the project, highlight the following architectural decisions:

1. **Decoupled Full-Stack Architecture**:
   - Built with **Python 3.13** and **Django 6.0** providing robust ORM modeling, transactional database integrity, and security against OWASP top 10 vulnerabilities (CSRF, SQL Injection, XSS).
   - Cleanly decoupled REST APIs built with **Django REST Framework (DRF)** and automated **OpenAPI 3.0 / Swagger UI** documentation via `drf-spectacular`.
   - Dual frontend support: An interactive **React + Vite** single-page application communicating via CORS and REST endpoints, backed by established, SEO-friendly server-rendered Django templates.

2. **Enterprise Role-Based Access Control (RBAC)**:
   - Four distinct departments: Customer Marketplace, Restaurant Kitchen Hub, Delivery Courier Portal, and Platform Administrator Operations.
   - Enforced server-side with custom Python decorators (`@restaurant_required`, `@delivery_required`, `@admin_required`) and object-level ownership checks (`restaurant=rest`, `assigned_delivery_partner=request.user`).

3. **Data Integrity & Scale**:
   - Curated dataset featuring **100 authentic Bengaluru restaurants** across 8 key localities (Koramangala, Indiranagar, HSR Layout, Whitefield, Jayanagar, BTM Layout, JP Nagar, Peenya) and **10,006 menu items**.
   - Immutable `OrderItem` historical snapshots preserving exact item titles, prices, and imagery at the moment of order placement.
   - Category-curated culinary photography with infinite-loop-safe brand SVG fallbacks.

4. **Production-Ready Payment Architecture**:
   - Dual-mode checkout supporting both **Razorpay Standard Checkout** (`checkout.js` + Python SDK) with SHA256 HMAC signature verification and **Cash on Delivery**.
   - Graceful sandbox payment simulation fallback allowing 100% reliable interview demonstration regardless of external gateway test server outages.

---

## 2. Step-by-Step Live Demonstration Script (6 Minutes)

### Step 1: Customer Discovery & Cart (1.5 Minutes)
1. Open the Customer Marketplace at [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (or [http://localhost:5173/](http://localhost:5173/)).
2. Filter restaurants by neighborhood (e.g., select **HSR Layout** or **Koramangala**).
3. Search for dishes (e.g., type `Biryani` or `Paneer`).
4. Click into a restaurant and view the menu dish listings with vegetarian indicators.
5. Add 2 dishes to the cart.
6. Open `/cart/`:
   - Demonstrate quantity increment/decrement (+/-) and dynamic subtotal recalculation.
   - Apply coupon `WELCOME50` and point out the discount calculation.
7. Click **Proceed to Checkout**.

### Step 2: Dynamic Checkout & Razorpay Payment (1.5 Minutes)
1. On the checkout page (`/checkout/`), show that the user can choose a saved tagged address (`#102, Green Glen Layout, Bellandur`) or enter a custom address.
2. Select **Razorpay** payment method.
3. Click **Proceed to Pay**:
   - Point out the invocation of `/checkout/razorpay/create/` which dynamically generates an authorized order ID.
   - Show the official Razorpay Checkout modal or test sandbox simulator.
   - Complete the test transaction.
4. The system validates the transaction signature and redirects to the order confirmation page (`/order-success/<order_number>/`).
5. Open `/order-tracking/<order_number>/` and point out the 5-stage progression timeline at **Stage 1: Order Received**.

### Step 3: Kitchen Processing — Restaurant Partner Hub (1 Minute)
1. In another private/incognito window (or using the React toolbar), log in as **`demo_partner`** (`FoodieGo@Partner2026!`).
2. Navigate to `/partner/orders/`:
   - Point out the newly created customer ticket appearing in the live queue.
   - Click **Accept Order** &rarr; advances status to `Accepted & Preparing`.
   - Click **Mark Ready for Pickup** &rarr; order is ready for courier dispatch.
3. Show the **Menu Management** tab (`/partner/menu/`) and demonstrate the 1-click **Toggle Availability** button to mark an item in-stock or sold-out.

### Step 4: Dispatch & Delivery — Delivery Partner Portal (1 Minute)
1. Log in as **`demo_rider`** (`FoodieGo@Rider2026!`).
2. Navigate to `/delivery/dashboard/`:
   - Point out the order appearing in the **Available Orders** pool.
   - Click **Claim Delivery** to take ownership of the trip.
3. Click **Confirm Pickup** at restaurant &rarr; status updates to `Out for Delivery`.
4. Click **Confirm Delivered** &rarr; status advances to `Delivered`.
5. Point out the rider earnings ledger incrementing by ₹45.

### Step 5: Customer Real-Time Tracking & Admin Overview (1 Minute)
1. Switch back to the Customer order tracking page (`/order-tracking/<order_number>/`):
   - Show the progress bar now sitting at **Stage 5: Delivered**.
2. Log in as **`demo_admin`** (`FoodieGo@Admin2026!`) and open `/admin-portal/`:
   - Point out the updated **Gross Merchandise Value (GMV)** and order count reflecting the completed delivery.
   - Show the **User & Restaurant Governance** section where restaurant approvals can be toggled with one click.
3. Open [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/) and show the interactive Swagger UI OpenAPI 3.0 documentation.

---

## 3. Potential Interview Questions & Answers

### Q1: How is authorization enforced between the four departments?
> **Answer**: We enforce authorization server-side through custom Python view decorators (`@restaurant_required`, `@delivery_required`, `@admin_required`) defined in `main/decorators.py`. These decorators inspect `request.user.profile.role` and ensure that even if an unauthorized user types a URL directly, they are redirected to `/accounts/login/`. Additionally, object-level filtering is applied so restaurant managers only see tickets where `restaurant=request.user.profile.restaurant`, and couriers only view their own assigned deliveries.

### Q2: How does the payment architecture handle security and webhook / signature validation?
> **Answer**: Payment credentials (`RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`) are strictly kept in environment variables (`.env`) and excluded from Git. When an order is placed, the backend initializes the order with Razorpay via an authenticated server-side API call. Upon client payment completion, the callback endpoint (`/ordered/`) recalculates the expected HMAC-SHA256 signature using the secret key and compares it against `razorpay_signature` before marking `is_paid=True`. No raw card numbers or CVVs ever touch our database.

### Q3: Why did you separate OrderItems into an immutable snapshot model?
> **Answer**: In food ordering systems, menu items frequently change prices or go out of stock. If historical orders referenced the live `Item` record directly, any price change would retroactively alter the financial reporting of historical completed orders. By snapshotting item titles, unit prices, and quantities into `OrderItem` at checkout time, we ensure referential and accounting immutability.

### Q4: How is the decoupled architecture organized?
> **Answer**: The application provides a clean separation of concerns. The backend exposes standard REST endpoints adhering to REST principles (using ViewSets, Serializers, and OpenAPI 3.0 schemas), secured with CORS headers and CSRF tokens. The frontend is a standalone React + Vite SPA that consumes these endpoints via an Axios client configured with credentials. At the same time, the Django server-side templates remain intact, giving interviewers the flexibility to evaluate both modern SPA and traditional SSR paradigms.

### Q5: What would you prioritize before deploying to production?
> **Answer**: 
> 1. Migrate the database from SQLite to a managed PostgreSQL cluster with connection pooling.
> 2. Set `DEBUG=False`, configure strict `ALLOWED_HOSTS`, and enable HTTPS security headers (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`).
> 3. Implement Redis and Django Channels to push real-time order status updates over WebSockets instead of relying on HTTP polling.
> 4. Connect real SMS (Twilio) and transactional email (SendGrid) notifications.
> 5. Integrate Google Maps / Mapbox SDK for live rider GPS telemetry.
