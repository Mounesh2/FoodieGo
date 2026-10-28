import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper to get CSRF cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Request interceptor to inject CSRF token
api.interceptors.request.use((config) => {
  const csrfToken = getCookie('csrftoken');
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});

export const fetchCsrfToken = async () => {
  try {
    const res = await api.get('/auth/csrf/');
    return res.data.csrfToken;
  } catch (err) {
    console.error('CSRF fetch error', err);
    return null;
  }
};

export const getCurrentUser = async () => {
  try {
    const res = await api.get('/auth/me/');
    return res.data;
  } catch {
    return { authenticated: false, role: 'GUEST' };
  }
};

export const loginUser = async (username, password) => {
  await fetchCsrfToken();
  const res = await api.post('/auth/login/', { username, password });
  return res.data;
};

export const logoutUser = async () => {
  const res = await api.post('/auth/logout/');
  return res.data;
};

export const fetchRestaurants = async (params = {}) => {
  const res = await api.get('/restaurants/', { params });
  return res.data.results || res.data;
};

export const fetchRestaurantDetail = async (id) => {
  const res = await api.get(`/restaurants/${id}/`);
  return res.data;
};

export const fetchDishes = async (params = {}) => {
  const res = await api.get('/items/', { params });
  return res.data.results || res.data;
};

export const fetchCart = async () => {
  const res = await api.get('/cart/');
  return res.data.results || res.data;
};

export const addToCart = async (itemId, quantity = 1) => {
  const res = await api.post('/cart/', { item_id: itemId, quantity });
  return res.data;
};

export const updateCartItem = async (cartItemId, action) => {
  const res = await api.post(`/cart/${cartItemId}/update_quantity/`, { action });
  return res.data;
};

export const removeCartItem = async (cartItemId) => {
  const res = await api.delete(`/cart/${cartItemId}/`);
  return res.data;
};

export const fetchCoupons = async () => {
  const res = await api.get('/coupons/');
  return res.data.results || res.data;
};

export const placeOrder = async (orderData) => {
  const res = await api.post('/orders/', orderData);
  return res.data;
};

export const fetchOrders = async () => {
  const res = await api.get('/orders/');
  return res.data.results || res.data;
};

export const fetchPartnerOrders = async () => {
  const res = await api.get('/partner/orders/');
  return res.data;
};

export const updatePartnerOrderStatus = async (orderNumber, status) => {
  const res = await api.post(`/partner/orders/${orderNumber}/status/`, { status });
  return res.data;
};

export const fetchDeliveryOrders = async () => {
  const res = await api.get('/delivery/orders/');
  return res.data;
};

export const claimDeliveryOrder = async (orderNumber) => {
  const res = await api.post(`/delivery/claim/${orderNumber}/`);
  return res.data;
};

export const updateDeliveryStatus = async (orderNumber, status) => {
  const res = await api.post(`/delivery/status/${orderNumber}/`, { status });
  return res.data;
};

export const fetchAdminKpis = async () => {
  const res = await api.get('/admin/kpis/');
  return res.data;
};

export default api;
