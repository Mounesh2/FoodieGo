# FoodieGo — Local Development Test Accounts

This document provides credentials and verification workflows for local development and technical interview demonstrations.

> [!IMPORTANT]
> These credentials are generated strictly for local technical evaluations and testing environments. They are initialized via `python manage.py setup_test_accounts` and are never hard-coded into production settings or exposed in public deployments.

---

## 1. Test Accounts Directory

| Role | Username | Email | Development Password | Primary Portal URL |
| :--- | :--- | :--- | :--- | :--- |
| **Customer** | `demo_customer` | `customer@foodiego.local` | `FoodieGo@Customer2026!` | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) |
| **Restaurant Partner** | `demo_partner` | `partner@foodiego.local` | `FoodieGo@Partner2026!` | [http://127.0.0.1:8000/partner/dashboard/](http://127.0.0.1:8000/partner/dashboard/) |
| **Delivery Partner** | `demo_rider` | `rider@foodiego.local` | `FoodieGo@Rider2026!` | [http://127.0.0.1:8000/delivery/dashboard/](http://127.0.0.1:8000/delivery/dashboard/) |
| **Administrator** | `demo_admin` | `admin@foodiego.local` | `FoodieGo@Admin2026!` | [http://127.0.0.1:8000/admin-portal/](http://127.0.0.1:8000/admin-portal/) |

---

## 2. Role Features & Demonstration Capabilities

### Account 1: Customer (`demo_customer`)
- **Login URL**: [http://127.0.0.1:8000/accounts/login/](http://127.0.0.1:8000/accounts/login/) (or via React SPA top bar)
- **Features to Demonstrate**:
  1. **Restaurant Discovery**: Browse 100 Bengaluru outlets with live search and neighborhood filters (Koramangala, Indiranagar, HSR Layout, etc.).
  2. **Dietary Filtering**: Toggle "Pure Veg" dishes and 4.0+ rated restaurants.
  3. **Shopping Cart**: Add dishes, dynamically increment/decrement item quantities, and observe subtotal recalculation.
  4. **Coupon Engine**: Apply promotional code `WELCOME50` or `BENGALURU100` and observe instant bill deduction.
  5. **Dynamic Checkout**: Select between pre-configured saved address (`#102, Green Glen Layout, Bellandur`) or custom address.
  6. **Payment Options**: Choose between **Razorpay Standard Checkout** (test mode modal) and **Cash on Delivery**.
  7. **Live 5-Stage Order Tracking**: Watch the order timeline progress from `Order Received` to `Delivered`.
  8. **Order History**: Review previous orders at `/orders/` and test 1-click reorder functionality.

### Account 2: Restaurant Partner (`demo_partner`)
- **Login URL**: [http://127.0.0.1:8000/accounts/login/](http://127.0.0.1:8000/accounts/login/)
- **Assigned Outlet**: Coastal Cafe 010 (or first partner restaurant)
- **Portal URL**: [http://127.0.0.1:8000/partner/dashboard/](http://127.0.0.1:8000/partner/dashboard/)
- **Features to Demonstrate**:
  1. **Kitchen Live Queue**: View incoming ticket orders specifically belonging to the partner's restaurant.
  2. **Order Progression**: Advance order status sequentially: `Accepted` &rarr; `Preparing` &rarr; `Ready for Pickup`.
  3. **Menu Stock Management**: Add dishes, edit pricing, and toggle in-stock / sold-out availability with a single click.
  4. **Kitchen Settings**: Update estimated cooking time, delivery radius, and store open/closed status.

### Account 3: Delivery Partner (`demo_rider`)
- **Login URL**: [http://127.0.0.1:8000/accounts/login/](http://127.0.0.1:8000/accounts/login/)
- **Portal URL**: [http://127.0.0.1:8000/delivery/dashboard/](http://127.0.0.1:8000/delivery/dashboard/)
- **Features to Demonstrate**:
  1. **Available Trips Pool**: View unassigned orders marked `Ready for Pickup`.
  2. **Trip Claiming**: Claim an order, locking it to the rider's active schedule.
  3. **Route Checkpoints**:
     - Confirm pickup at restaurant &rarr; advances order to `Out for Delivery`.
     - Confirm drop at customer address &rarr; advances order to `Delivered`.
  4. **Earnings Ledger**: View completed trip counters and earnings calculation (flat ₹45 per completed delivery).

### Account 4: Platform Administrator (`demo_admin`)
- **Login URL**: [http://127.0.0.1:8000/accounts/login/](http://127.0.0.1:8000/accounts/login/)
- **Portals**:
  - Custom Admin Portal: [http://127.0.0.1:8000/admin-portal/](http://127.0.0.1:8000/admin-portal/)
  - Django Native Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Features to Demonstrate**:
  1. **Executive KPI Analytics**: Gross Merchandise Value (GMV), total order volume, and registered user counts.
  2. **Role Governance**: Change any user's role (`CUSTOMER`, `RESTAURANT`, `DELIVERY`, `ADMIN`) or outlet affiliation.
  3. **Restaurant Approval Controls**: Approve or suspend partner listings on the public marketplace.
  4. **Coupon Campaign Management**: Create, activate, or deactivate promotional discount campaigns.

---

## 3. Account Reset & Idempotency Instructions

To reset, re-seed, or ensure all 4 accounts exist with their standard default passwords, run the management command from the project root:

```powershell
python manage.py setup_test_accounts
```

### Custom Password Overrides:
You can define custom local passwords via environment variables before running the command:
```powershell
$env:DEMO_ADMIN_PASSWORD="YourCustomAdminPassword123!"
$env:DEMO_PARTNER_PASSWORD="YourCustomPartnerPassword123!"
$env:DEMO_RIDER_PASSWORD="YourCustomRiderPassword123!"
$env:DEMO_CUSTOMER_PASSWORD="YourCustomCustomerPassword123!"
python manage.py setup_test_accounts
```

The command is strictly idempotent: it updates passwords and roles for the demo accounts without deleting database records or affecting unrelated user accounts.
