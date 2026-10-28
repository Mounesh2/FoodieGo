import React, { useState, useEffect } from 'react';
import {
  Utensils,
  ShoppingBag,
  Search,
  Star,
  Clock,
  MapPin,
  CheckCircle,
  Truck,
  ChefHat,
  ShieldCheck,
  X,
  Plus,
  Minus,
  ArrowRight,
  TrendingUp,
  PackageCheck
} from 'lucide-react';
import {
  fetchRestaurants,
  fetchRestaurantDetail,
  fetchCart,
  addToCart,
  updateCartItem,
  removeCartItem,
  fetchCoupons,
  placeOrder,
  fetchOrders,
  getCurrentUser,
  loginUser,
  logoutUser,
  fetchPartnerOrders,
  updatePartnerOrderStatus,
  fetchDeliveryOrders,
  claimDeliveryOrder,
  updateDeliveryStatus,
  fetchAdminKpis
} from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('marketplace'); // 'marketplace', 'kitchen', 'rider', 'admin'
  const [currentUser, setCurrentUser] = useState({ authenticated: false, role: 'GUEST' });
  const [restaurants, setRestaurants] = useState([]);
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [selectedArea, setSelectedArea] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [cart, setCart] = useState([]);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [activeOrder, setActiveOrder] = useState(null);
  const [userOrders, setUserOrders] = useState([]);

  // Form states
  const [checkoutAddress, setCheckoutAddress] = useState('#102, Green Glen Layout, Bellandur, Bengaluru');
  const [checkoutPhone, setCheckoutPhone] = useState('9876543213');
  const [paymentMethod, setPaymentMethod] = useState('Razorpay'); // 'Razorpay' or 'Cash on Delivery'
  const [appliedCoupon, setAppliedCoupon] = useState(null);
  const [couponCode, setCouponCode] = useState('');
  const [coupons, setCoupons] = useState([]);
  const [statusMessage, setStatusMessage] = useState('');

  // Departmental states
  const [partnerData, setPartnerData] = useState({ orders: [], restaurant: null });
  const [deliveryData, setDeliveryData] = useState({ available: [], assigned: [], completed_deliveries_count: 0, estimated_earnings_inr: 0 });
  const [adminKpis, setAdminKpis] = useState(null);

  // Initialize
  useEffect(() => {
    initApp();
  }, []);

  const initApp = async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
      loadRestaurants();
      loadCart();
      const cpns = await fetchCoupons();
      setCoupons(cpns);
    } catch (e) {
      console.error('Init error:', e);
    }
  };

  const loadRestaurants = async (area = selectedArea, q = searchQuery) => {
    try {
      const params = {};
      if (area && area !== 'All') params.area = area;
      if (q) params.search = q;
      const data = await fetchRestaurants(params);
      setRestaurants(data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCart = async () => {
    try {
      const data = await fetchCart();
      setCart(data);
    } catch (e) {
      console.log('Cart fetch notice:', e);
    }
  };

  const handleQuickLogin = async (roleName, username, password) => {
    try {
      setStatusMessage(`Authenticating as ${roleName} (${username})...`);
      const res = await loginUser(username, password);
      if (res.success) {
        setCurrentUser(res.user);
        setStatusMessage(`Logged in successfully as ${roleName}!`);
        setTimeout(() => setStatusMessage(''), 3000);
        if (roleName === 'Restaurant') {
          setActiveTab('kitchen');
          loadPartnerPortal();
        } else if (roleName === 'Delivery') {
          setActiveTab('rider');
          loadDeliveryPortal();
        } else if (roleName === 'Admin') {
          setActiveTab('admin');
          loadAdminPortal();
        } else {
          setActiveTab('marketplace');
          loadCart();
        }
      }
    } catch (err) {
      setStatusMessage(`Login failed: ${err.response?.data?.error || err.message}`);
      setTimeout(() => setStatusMessage(''), 4000);
    }
  };

  const loadPartnerPortal = async () => {
    try {
      const data = await fetchPartnerOrders();
      setPartnerData(data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadDeliveryPortal = async () => {
    try {
      const data = await fetchDeliveryOrders();
      setDeliveryData(data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadAdminPortal = async () => {
    try {
      const data = await fetchAdminKpis();
      setAdminKpis(data);
    } catch (e) {
      console.error(e);
    }
  };

  // Cart math
  const cartSubtotal = cart.reduce((acc, ci) => acc + (ci.quantity * (ci.item?.price || 0)), 0);
  const deliveryFee = cartSubtotal >= 300 || cartSubtotal === 0 ? 0 : 35;
  const taxAmount = Math.round(cartSubtotal * 0.05 * 100) / 100;
  const discountAmount = appliedCoupon ? Math.min(appliedCoupon.discount_amount || (cartSubtotal * (appliedCoupon.discount_percent / 100)), cartSubtotal) : 0;
  const grandTotal = Math.max(0, Math.round((cartSubtotal + deliveryFee + taxAmount - discountAmount) * 100) / 100);

  const handleAddToCart = async (dish) => {
    try {
      await addToCart(dish.id, 1);
      await loadCart();
      setStatusMessage(`Added "${dish.title}" to cart!`);
      setTimeout(() => setStatusMessage(''), 2500);
    } catch (e) {
      alert('Please log in as Customer to add items to cart.');
    }
  };

  const handleUpdateQty = async (cartItemId, action) => {
    await updateCartItem(cartItemId, action);
    loadCart();
  };

  const handleApplyCoupon = () => {
    const found = coupons.find(c => c.code.toUpperCase() === couponCode.trim().toUpperCase());
    if (found) {
      if (cartSubtotal < found.min_order_amount) {
        alert(`Minimum order of ₹${found.min_order_amount} required for ${found.code}`);
        return;
      }
      setAppliedCoupon(found);
      setStatusMessage(`Coupon ${found.code} applied!`);
      setTimeout(() => setStatusMessage(''), 2500);
    } else {
      alert('Invalid coupon code. Try WELCOME50');
    }
  };

  const handlePlaceOrder = async () => {
    if (!checkoutPhone || checkoutPhone.length < 10) {
      alert('Please provide a valid 10-digit phone number.');
      return;
    }

    try {
      const orderPayload = {
        delivery_address: checkoutAddress,
        contact_phone: checkoutPhone,
        payment_method: paymentMethod,
        order_instructions: 'Handle with care'
      };
      const res = await placeOrder(orderPayload);
      setActiveOrder(res);
      setIsCheckoutOpen(false);
      setIsCartOpen(false);
      loadCart();
      setStatusMessage(`Order #${res.order_number} confirmed!`);
    } catch (e) {
      alert('Order placement failed: ' + (e.response?.data?.error || e.message));
    }
  };

  const areas = ['All', 'Koramangala', 'Indiranagar', 'HSR Layout', 'Whitefield', 'Jayanagar', 'BTM Layout', 'JP Nagar'];

  return (
    <div>
      {/* Sticky Header */}
      <header className="header">
        <div className="brand" onClick={() => { setSelectedRestaurant(null); setActiveTab('marketplace'); }}>
          <Utensils size={24} />
          <span>FoodieGo</span>
          <span style={{ fontSize: '0.75rem', background: '#fef3c7', color: '#b45309', padding: '2px 8px', borderRadius: '6px', fontWeight: 700 }}>
            Bengaluru
          </span>
        </div>

        {/* Department Switcher Tabs */}
        <div style={{ display: 'flex', gap: '0.4rem', background: '#f1f5f9', padding: '4px', borderRadius: '12px' }}>
          <button
            className={`btn btn-sm ${activeTab === 'marketplace' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('marketplace')}
          >
            Customer
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'kitchen' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setActiveTab('kitchen'); loadPartnerPortal(); }}
          >
            Kitchen Hub
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'rider' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setActiveTab('rider'); loadDeliveryPortal(); }}
          >
            Rider Portal
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'admin' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setActiveTab('admin'); loadAdminPortal(); }}
          >
            Admin
          </button>
        </div>

        {/* Right side: Role badge & Cart */}
        <div className="nav-links">
          {currentUser.authenticated ? (
            <span className={`role-badge ${currentUser.role?.toLowerCase()}`}>
              {currentUser.username} ({currentUser.role})
            </span>
          ) : (
            <span className="role-badge" style={{ background: '#e2e8f0', color: '#475569' }}>
              Guest
            </span>
          )}

          <button className="btn btn-secondary" onClick={() => setIsCartOpen(true)} style={{ position: 'relative' }}>
            <ShoppingBag size={18} />
            <span>Cart</span>
            {cart.length > 0 && (
              <span style={{ position: 'absolute', top: -5, right: -5, background: 'var(--primary)', color: 'white', borderRadius: '50%', width: 20, height: 20, fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                {cart.reduce((a, b) => a + b.quantity, 0)}
              </span>
            )}
          </button>
        </div>
      </header>

      {/* Quick Demo Role Switcher Toolbar (Interview Ready) */}
      <div style={{ background: '#1e293b', color: '#94a3b8', padding: '0.45rem 1.5rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#f8fafc', fontWeight: 700 }}>Interview Quick Switcher:</span>
          <span>Click to switch demo role instantly:</span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => handleQuickLogin('Customer', 'demo_customer', 'FoodieGo@Customer2026!')}
            style={{ background: '#3b82f6', color: 'white', border: 'none', padding: '3px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
          >
            Demo Customer
          </button>
          <button
            onClick={() => handleQuickLogin('Restaurant', 'demo_partner', 'FoodieGo@Partner2026!')}
            style={{ background: '#f59e0b', color: 'white', border: 'none', padding: '3px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
          >
            Demo Kitchen
          </button>
          <button
            onClick={() => handleQuickLogin('Delivery', 'demo_rider', 'FoodieGo@Rider2026!')}
            style={{ background: '#10b981', color: 'white', border: 'none', padding: '3px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
          >
            Demo Rider
          </button>
          <button
            onClick={() => handleQuickLogin('Admin', 'demo_admin', 'FoodieGo@Admin2026!')}
            style={{ background: '#ec4899', color: 'white', border: 'none', padding: '3px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
          >
            Demo Admin
          </button>
        </div>
      </div>

      {statusMessage && (
        <div style={{ background: '#ecfdf5', color: '#065f46', borderBottom: '1px solid #a7f3d0', padding: '0.6rem 1.5rem', textAlign: 'center', fontSize: '0.85rem', fontWeight: 600 }}>
          {statusMessage}
        </div>
      )}

      {/* Main Content Area */}
      <main className="container">
        {/* TAB 1: CUSTOMER MARKETPLACE */}
        {activeTab === 'marketplace' && (
          <div>
            {!selectedRestaurant ? (
              <>
                {/* Hero Banner */}
                <div className="hero-banner">
                  <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>
                    Bengaluru's Best Food, Delivered Fast.
                  </h1>
                  <p style={{ opacity: 0.9, maxWidth: '600px' }}>
                    Order from 100 curated restaurants and 10,006 authentic dishes across Bengaluru's favorite dining hubs.
                  </p>

                  <div className="search-box">
                    <Search size={20} color="#94a3b8" />
                    <input
                      type="text"
                      placeholder="Search restaurants, cuisines (Biryani, Dosa, Burgers)..."
                      value={searchQuery}
                      onChange={(e) => {
                        setSearchQuery(e.target.value);
                        loadRestaurants(selectedArea, e.target.value);
                      }}
                    />
                  </div>
                </div>

                {/* Area Filters */}
                <div className="filters-bar">
                  {areas.map((area) => (
                    <button
                      key={area}
                      className={`filter-pill ${selectedArea === area ? 'active' : ''}`}
                      onClick={() => {
                        setSelectedArea(area);
                        loadRestaurants(area, searchQuery);
                      }}
                    >
                      {area}
                    </button>
                  ))}
                </div>

                {/* Restaurants Grid */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                    {selectedArea === 'All' ? 'All Bengaluru Restaurants' : `Restaurants in ${selectedArea}`} ({restaurants.length})
                  </h2>
                </div>

                <div className="grid">
                  {restaurants.map((rest) => (
                    <div key={rest.id} className="card" onClick={async () => {
                      const detail = await fetchRestaurantDetail(rest.id);
                      setSelectedRestaurant(detail);
                    }} style={{ cursor: 'pointer' }}>
                      <div className="card-img-wrapper">
                        <img
                          src={rest.display_image || rest.image_url}
                          alt={rest.name}
                          className="card-img"
                          onError={(e) => { e.target.src = 'http://127.0.0.1:8000/static/images/fallback_restaurant.svg'; }}
                        />
                      </div>
                      <div className="card-body">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.25rem' }}>
                          <h3 className="card-title">{rest.name}</h3>
                          <span className="rating-badge">
                            <Star size={12} fill="white" /> {rest.rating || '4.2'}
                          </span>
                        </div>
                        <div className="card-meta">
                          <span>{rest.cuisine}</span>
                          <span>•</span>
                          <span><MapPin size={12} style={{ display: 'inline' }} /> {rest.area}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '0.5rem', borderTop: '1px solid var(--border)', fontSize: '0.85rem' }}>
                          <span style={{ color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                            <Clock size={14} /> {rest.estimated_delivery_minutes || 30} mins
                          </span>
                          <span style={{ fontWeight: 600 }}>₹{rest.average_cost_for_two || 400} for two</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              /* Restaurant Detail & Menu View */
              <div>
                <button className="btn btn-secondary btn-sm" onClick={() => setSelectedRestaurant(null)} style={{ marginBottom: '1rem' }}>
                  ← Back to Restaurants
                </button>

                <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                      <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>{selectedRestaurant.name}</h1>
                      <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                        {selectedRestaurant.cuisine} • {selectedRestaurant.area}, {selectedRestaurant.city}
                      </p>
                      <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem' }}>
                        <span className="rating-badge">
                          <Star size={12} fill="white" /> {selectedRestaurant.rating} ({selectedRestaurant.rating_count || 120}+ ratings)
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Clock size={14} /> {selectedRestaurant.estimated_delivery_minutes} mins delivery
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <h2 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '1rem' }}>
                  Menu Dishes ({selectedRestaurant.menu_items?.length || 0})
                </h2>

                <div className="grid">
                  {selectedRestaurant.menu_items?.map((dish) => (
                    <div key={dish.id} className="card">
                      <div className="card-img-wrapper" style={{ height: '140px' }}>
                        <img
                          src={dish.display_image || dish.food_image_url}
                          alt={dish.title}
                          className="card-img"
                          onError={(e) => { e.target.src = 'http://127.0.0.1:8000/static/images/fallback_food.svg'; }}
                        />
                      </div>
                      <div className="card-body">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                          <span className={`veg-icon ${dish.is_veg ? '' : 'non-veg'}`}>
                            <span className={`veg-dot ${dish.is_veg ? '' : 'non-veg'}`} />
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 600 }}>{dish.category}</span>
                        </div>
                        <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.5rem' }}>{dish.title}</h4>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
                          <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--dark)' }}>
                            ₹{dish.price}
                          </span>
                          <button className="btn btn-primary btn-sm" onClick={() => handleAddToCart(dish)}>
                            <Plus size={14} /> Add
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: RESTAURANT PARTNER HUB */}
        {activeTab === 'kitchen' && (
          <div>
            <div className="hero-banner" style={{ background: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <ChefHat size={32} />
                <div>
                  <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Restaurant Partner Kitchen Display</h1>
                  <p style={{ opacity: 0.9 }}>
                    Active Kitchen: {partnerData.restaurant?.name || 'Assigned Outlet'} ({partnerData.restaurant?.area || 'Bengaluru'})
                  </p>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 800 }}>Incoming Order Tickets ({partnerData.orders?.length || 0})</h2>
              <button className="btn btn-secondary btn-sm" onClick={loadPartnerPortal}>
                Refresh Tickets
              </button>
            </div>

            {partnerData.orders?.length === 0 ? (
              <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--muted)' }}>
                No active orders in the queue right now. Place an order from the Customer tab!
              </div>
            ) : (
              <div className="grid">
                {partnerData.orders?.map((ord) => (
                  <div key={ord.id} className="card" style={{ borderLeft: '4px solid #f59e0b', padding: '1.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 800, color: 'var(--dark)' }}>#{ord.order_number}</span>
                      <span className="role-badge" style={{ background: '#fef3c7', color: '#b45309' }}>{ord.status}</span>
                    </div>
                    <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.75rem' }}>
                      Customer: {ord.username} • Phone: {ord.contact_phone || 'N/A'}
                    </p>
                    <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.75rem', marginBottom: '1rem', fontSize: '0.85rem' }}>
                      <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Items:</div>
                      {ord.order_items?.map((oi, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>{oi.quantity}x {oi.item_title}</span>
                          <span>₹{oi.subtotal}</span>
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
                      <span style={{ fontWeight: 800 }}>Total: ₹{ord.total_amount}</span>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        {ord.status === 'Active' || ord.status === 'Order Received' ? (
                          <button className="btn btn-primary btn-sm" onClick={async () => {
                            await updatePartnerOrderStatus(ord.order_number, 'Accepted & Preparing');
                            loadPartnerPortal();
                          }}>
                            Accept & Cook
                          </button>
                        ) : ord.status === 'Accepted & Preparing' ? (
                          <button className="btn btn-primary btn-sm" style={{ background: '#10b981' }} onClick={async () => {
                            await updatePartnerOrderStatus(ord.order_number, 'Ready for Pickup');
                            loadPartnerPortal();
                          }}>
                            Mark Ready
                          </button>
                        ) : (
                          <span style={{ fontSize: '0.8rem', color: '#059669', fontWeight: 600 }}>Ready / Dispatched</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: DELIVERY PARTNER PORTAL */}
        {activeTab === 'rider' && (
          <div>
            <div className="hero-banner" style={{ background: 'linear-gradient(135deg, #059669 0%, #047857 100%)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Truck size={32} />
                <div>
                  <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Delivery Courier Dispatch Hub</h1>
                  <p style={{ opacity: 0.9 }}>
                    Completed Trips: {deliveryData.completed_deliveries_count} | Estimated Earnings: ₹{deliveryData.estimated_earnings_inr} (₹45/drop)
                  </p>
                </div>
              </div>
            </div>

            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '1rem' }}>Active Deliveries Claimed By You</h2>
            {deliveryData.assigned?.length === 0 ? (
              <p style={{ color: 'var(--muted)', marginBottom: '2rem' }}>You have no active runs right now.</p>
            ) : (
              <div className="grid" style={{ marginBottom: '2rem' }}>
                {deliveryData.assigned?.map((ord) => (
                  <div key={ord.id} className="card" style={{ borderLeft: '4px solid #10b981', padding: '1.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 800 }}>#{ord.order_number}</span>
                      <span className="role-badge delivery">{ord.status}</span>
                    </div>
                    <p style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                      <strong>Drop Address:</strong> {ord.delivery_address}
                    </p>
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                      {ord.status !== 'Out for Delivery' ? (
                        <button className="btn btn-primary btn-sm" onClick={async () => {
                          await updateDeliveryStatus(ord.order_number, 'Out for Delivery');
                          loadDeliveryPortal();
                        }}>
                          Confirm Pickup (Start Run)
                        </button>
                      ) : (
                        <button className="btn btn-primary btn-sm" style={{ background: '#059669' }} onClick={async () => {
                          await updateDeliveryStatus(ord.order_number, 'Delivered');
                          loadDeliveryPortal();
                        }}>
                          Confirm Delivered (₹45)
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '1rem' }}>
              Available Orders For Pickup ({deliveryData.available?.length || 0})
            </h2>
            <div className="grid">
              {deliveryData.available?.map((ord) => (
                <div key={ord.id} className="card" style={{ padding: '1.25rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 800 }}>#{ord.order_number}</span>
                    <span className="rating-badge" style={{ background: '#3b82f6' }}>₹45 Earning</span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>
                    <strong>Delivery To:</strong> {ord.delivery_address}
                  </p>
                  <button className="btn btn-secondary btn-sm" style={{ marginTop: 'auto' }} onClick={async () => {
                    await claimDeliveryOrder(ord.order_number);
                    loadDeliveryPortal();
                  }}>
                    Claim Delivery Run
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: PLATFORM ADMINISTRATOR */}
        {activeTab === 'admin' && (
          <div>
            <div className="hero-banner" style={{ background: 'linear-gradient(135deg, #db2777 0%, #be185d 100%)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <ShieldCheck size={32} />
                <div>
                  <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Platform Executive Dashboard</h1>
                  <p style={{ opacity: 0.9 }}>
                    Executive KPIs, Gross Merchandise Value, and platform-wide order oversight.
                  </p>
                </div>
              </div>
            </div>

            {adminKpis && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                <div className="card" style={{ padding: '1.25rem' }}>
                  <span style={{ color: 'var(--muted)', fontSize: '0.85rem', fontWeight: 600 }}>Total GMV</span>
                  <span style={{ fontSize: '1.75rem', fontWeight: 800, color: '#059669' }}>₹{adminKpis.total_gmv_inr}</span>
                </div>
                <div className="card" style={{ padding: '1.25rem' }}>
                  <span style={{ color: 'var(--muted)', fontSize: '0.85rem', fontWeight: 600 }}>Total Orders</span>
                  <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>{adminKpis.total_orders}</span>
                </div>
                <div className="card" style={{ padding: '1.25rem' }}>
                  <span style={{ color: 'var(--muted)', fontSize: '0.85rem', fontWeight: 600 }}>Partner Restaurants</span>
                  <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>{adminKpis.total_restaurants}</span>
                </div>
                <div className="card" style={{ padding: '1.25rem' }}>
                  <span style={{ color: 'var(--muted)', fontSize: '0.85rem', fontWeight: 600 }}>Registered Users</span>
                  <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>{adminKpis.total_users}</span>
                </div>
              </div>
            )}

            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '1rem' }}>Recent Platform Orders</h2>
            <div className="card" style={{ padding: '1rem', overflowX: 'auto' }}>
              <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--border)' }}>
                    <th style={{ padding: '0.5rem' }}>Order #</th>
                    <th style={{ padding: '0.5rem' }}>Customer</th>
                    <th style={{ padding: '0.5rem' }}>Total</th>
                    <th style={{ padding: '0.5rem' }}>Payment</th>
                    <th style={{ padding: '0.5rem' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {adminKpis?.recent_orders?.map((ord) => (
                    <tr key={ord.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '0.5rem', fontWeight: 600 }}>#{ord.order_number}</td>
                      <td style={{ padding: '0.5rem' }}>{ord.username}</td>
                      <td style={{ padding: '0.5rem' }}>₹{ord.total_amount}</td>
                      <td style={{ padding: '0.5rem' }}>{ord.payment_method}</td>
                      <td style={{ padding: '0.5rem' }}>
                        <span className="role-badge customer">{ord.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Cart Modal */}
      {isCartOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Your Shopping Cart</h2>
              <button onClick={() => setIsCartOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            {cart.length === 0 ? (
              <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '2rem 0' }}>Your cart is empty.</p>
            ) : (
              <div>
                <div style={{ maxHeight: '250px', overflowY: 'auto', marginBottom: '1rem' }}>
                  {cart.map((ci) => (
                    <div key={ci.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.6rem 0', borderBottom: '1px solid var(--border)' }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{ci.item?.title}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>₹{ci.item?.price} each</div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <button className="btn btn-secondary btn-sm" onClick={() => handleUpdateQty(ci.id, 'decrease')}><Minus size={12} /></button>
                        <span style={{ fontWeight: 700 }}>{ci.quantity}</span>
                        <button className="btn btn-secondary btn-sm" onClick={() => handleUpdateQty(ci.id, 'increase')}><Plus size={12} /></button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Coupon Code Input */}
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                  <input
                    type="text"
                    placeholder="Enter Coupon (e.g. WELCOME50)"
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value)}
                    style={{ flex: 1, padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)' }}
                  />
                  <button className="btn btn-secondary btn-sm" onClick={handleApplyCoupon}>Apply</button>
                </div>

                {/* Bill Breakdown */}
                <div style={{ fontSize: '0.85rem', color: 'var(--slate)', marginBottom: '1.25rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span>Item Total</span>
                    <span>₹{cartSubtotal}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span>Delivery Fee (Free over ₹300)</span>
                    <span>₹{deliveryFee}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span>Govt Taxes (5%)</span>
                    <span>₹{taxAmount}</span>
                  </div>
                  {appliedCoupon && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', color: '#059669', fontWeight: 600 }}>
                      <span>Discount ({appliedCoupon.code})</span>
                      <span>-₹{discountAmount}</span>
                    </div>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '0.5rem', borderTop: '2px solid var(--border)', fontSize: '1rem', fontWeight: 800 }}>
                    <span>To Pay</span>
                    <span>₹{grandTotal}</span>
                  </div>
                </div>

                <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => { setIsCartOpen(false); setIsCheckoutOpen(true); }}>
                  Proceed to Checkout <ArrowRight size={16} />
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Checkout Modal */}
      {isCheckoutOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Complete Your Order</h2>
              <button onClick={() => setIsCheckoutOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', marginBottom: '0.25rem' }}>Delivery Address</label>
              <textarea
                rows={2}
                value={checkoutAddress}
                onChange={(e) => setCheckoutAddress(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '0.85rem' }}
              />
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', marginBottom: '0.25rem' }}>Phone Number (10 Digits)</label>
              <input
                type="text"
                value={checkoutPhone}
                onChange={(e) => setCheckoutPhone(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '0.85rem' }}
              />
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>Payment Method</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  type="button"
                  className={`btn btn-sm ${paymentMethod === 'Razorpay' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setPaymentMethod('Razorpay')}
                  style={{ flex: 1 }}
                >
                  Razorpay (Test)
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${paymentMethod === 'Cash on Delivery' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setPaymentMethod('Cash on Delivery')}
                  style={{ flex: 1 }}
                >
                  Cash on Delivery
                </button>
              </div>
            </div>

            <div style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px', marginBottom: '1.25rem', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700 }}>
                <span>Final Payable:</span>
                <span>₹{grandTotal}</span>
              </div>
            </div>

            <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={handlePlaceOrder}>
              Confirm & Pay ₹{grandTotal}
            </button>
          </div>
        </div>
      )}

      {/* Live Order Tracking Modal */}
      {activeOrder && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '600px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Live Order Tracking</h2>
              <button onClick={() => setActiveOrder(null)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ background: '#ecfdf5', padding: '0.75rem 1rem', borderRadius: '8px', color: '#065f46', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle size={20} />
              <div>
                <strong>Order Placed Successfully!</strong>
                <div style={{ fontSize: '0.8rem' }}>Order Number: #{activeOrder.order_number}</div>
              </div>
            </div>

            {/* 5-Stage Timeline */}
            <div className="tracker-steps">
              <div className="tracker-step completed">
                <div className="tracker-dot">✓</div>
                <span>Order Placed</span>
              </div>
              <div className="tracker-step active">
                <div className="tracker-dot">2</div>
                <span>Accepted</span>
              </div>
              <div className="tracker-step">
                <div className="tracker-dot">3</div>
                <span>Cooking</span>
              </div>
              <div className="tracker-step">
                <div className="tracker-dot">4</div>
                <span>On the Way</span>
              </div>
              <div className="tracker-step">
                <div className="tracker-dot">5</div>
                <span>Delivered</span>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', fontSize: '0.85rem' }}>
              <p><strong>Delivery Address:</strong> {activeOrder.delivery_address}</p>
              <p><strong>Payment Mode:</strong> {activeOrder.payment_method}</p>
              <p><strong>Estimated Arrival:</strong> 30 - 35 mins</p>
            </div>

            <button className="btn btn-primary" style={{ width: '100%', marginTop: '1rem', justifyContent: 'center' }} onClick={() => setActiveOrder(null)}>
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
