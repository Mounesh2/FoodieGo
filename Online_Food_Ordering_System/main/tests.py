from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from main.models import Restaurant, Item, Order, CartItems, Reviews

class CustomerWorkflowIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='bengaluru_customer',
            password='Password123!',
            email='customer@foodiego.com'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin_boss',
            password='AdminPassword123!',
            email='admin@foodiego.com'
        )
        self.restaurant = Restaurant.objects.create(
            name='Meghana Biryani Demo',
            slug='meghana-biryani-demo-koramangala-101',
            area='Koramangala',
            city='Bengaluru',
            cuisine='Biryani',
            rating=4.6,
            rating_count=1200,
            average_cost_for_two=450.0,
            estimated_delivery_minutes=25,
            delivery_fee=0.0,
            is_open=True,
            data_type='SYNTHETIC_DEMO'
        )
        self.dish1 = Item.objects.create(
            restaurant=self.restaurant,
            title='Hyderabadi Chicken Biryani',
            slug='hyderabadi-chicken-biryani-101',
            category='Biryani',
            price=280.0,
            is_veg=False,
            rating=4.7,
            is_available=True,
            created_by=self.admin_user,
            data_type='SYNTHETIC_DEMO'
        )
        self.dish2 = Item.objects.create(
            restaurant=self.restaurant,
            title='Paneer Tikka Biryani',
            slug='paneer-tikka-biryani-102',
            category='Biryani',
            price=240.0,
            is_veg=True,
            rating=4.5,
            is_available=True,
            created_by=self.admin_user,
            data_type='SYNTHETIC_DEMO'
        )

    # 1. Homepage & Exploration Tests
    def test_homepage_renders_with_bengaluru_restaurants(self):
        response = self.client.get(reverse('main:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Meghana Biryani Demo')
        self.assertContains(response, 'Koramangala')
        self.assertContains(response, 'FoodieGo')

    def test_cuisine_and_area_filters(self):
        # Filter by cuisine
        res = self.client.get(reverse('main:home') + '?cuisine=Biryani')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Meghana Biryani Demo')

        # Filter by area
        res_area = self.client.get(reverse('main:home') + '?area=Koramangala')
        self.assertEqual(res_area.status_code, 200)
        self.assertContains(res_area, 'Koramangala')

    def test_restaurant_detail_view(self):
        url = reverse('main:restaurant_detail', kwargs={'slug': self.restaurant.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Meghana Biryani Demo')
        self.assertContains(response, 'Hyderabadi Chicken Biryani')
        self.assertContains(response, 'Paneer Tikka Biryani')

    def test_pure_veg_filter_on_restaurant_detail(self):
        url = reverse('main:restaurant_detail', kwargs={'slug': self.restaurant.slug}) + '?veg=true'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Paneer Tikka Biryani')
        self.assertNotContains(response, 'Hyderabadi Chicken Biryani')

    # 2. Dish Detail & Customer Review Tests
    def test_dish_detail_and_review_workflow(self):
        url = reverse('main:dishes', kwargs={'slug': self.dish1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.dish1.title)

        # Authenticated customer submits review
        self.client.login(username='bengaluru_customer', password='Password123!')
        rev_url = reverse('main:add_reviews')
        rev_resp = self.client.post(rev_url, {
            'rslug': self.dish1.slug,
            'rating': '5',
            'review': 'Super flavorful and authentic spices!'
        })
        self.assertEqual(rev_resp.status_code, 302)
        self.assertTrue(Reviews.objects.filter(item=self.dish1, user=self.user).exists())

    # 3. Cart & Quantity Update Tests
    def test_cart_add_and_quantity_increment(self):
        self.client.login(username='bengaluru_customer', password='Password123!')

        # Add dish1 to cart
        add_url = reverse('main:add-to-cart', kwargs={'slug': self.dish1.slug})
        res1 = self.client.get(add_url)
        self.assertEqual(res1.status_code, 302)

        cart_item = CartItems.objects.get(user=self.user, item=self.dish1, ordered=False)
        self.assertEqual(cart_item.quantity, 1)

        # Add dish1 AGAIN -> quantity must increment to 2, NOT create duplicate row
        self.client.get(add_url)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(CartItems.objects.filter(user=self.user, ordered=False).count(), 1)
        self.assertEqual(cart_item.subtotal, 560.0)

    def test_cart_quantity_controls(self):
        self.client.login(username='bengaluru_customer', password='Password123!')
        cart_item = CartItems.objects.create(
            user=self.user,
            item=self.dish1,
            ordered=False,
            quantity=2
        )

        # Increment quantity
        inc_url = reverse('main:update_cart_quantity', kwargs={'pk': cart_item.pk})
        self.client.post(inc_url, {'action': 'increase'})
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 3)

        # Decrement quantity
        self.client.post(inc_url, {'action': 'decrease'})
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 2)

        # Decrement until removed
        self.client.post(inc_url, {'action': 'decrease'})
        self.client.post(inc_url, {'action': 'decrease'})
        self.assertFalse(CartItems.objects.filter(pk=cart_item.pk).exists())

    # 4. Checkout & Order Creation Tests
    def test_complete_checkout_workflow(self):
        self.client.login(username='bengaluru_customer', password='Password123!')
        CartItems.objects.create(
            user=self.user,
            item=self.dish1,
            ordered=False,
            quantity=2  # 2 * 280 = 560
        )

        checkout_url = reverse('main:ordered')
        response = self.client.post(checkout_url, {
            'address': '#108, 4th Main, HSR Layout Sector 1, Bengaluru',
            'phone': '9876543210',
            'instructions': 'Leave with security guard',
            'payment_method': 'Cash on Delivery'
        })

        # Must redirect to order confirmation receipt
        self.assertEqual(response.status_code, 302)
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertTrue(order.order_number.startswith('FG-'))
        self.assertEqual(order.subtotal, 560.0)
        self.assertIn(order.status, ['Confirmed', 'Active'])
        self.assertEqual(order.delivery_fee, 0.0)  # Free delivery over 300

        # Active cart items must now be marked ordered
        active_items = CartItems.objects.filter(user=self.user, ordered=False)
        self.assertEqual(active_items.count(), 0)

        # Order history renders with placed order
        history_url = reverse('main:order_details')
        hist_resp = self.client.get(history_url)
        self.assertEqual(hist_resp.status_code, 200)
        self.assertContains(hist_resp, order.order_number)

    # 5. Admin Dashboard & Kitchen Order Status Update
    def test_admin_order_status_update(self):
        order = Order.objects.create(
            order_number='FG-TEST-999',
            user=self.user,
            restaurant=self.restaurant,
            subtotal=280.0,
            total_amount=294.0,
            status='Active'
        )

        # Non-admin user cannot access admin dashboard
        self.client.login(username='bengaluru_customer', password='Password123!')
        dash_res = self.client.get(reverse('main:admin_dashboard'))
        self.assertEqual(dash_res.status_code, 302)

        # Admin user updates status
        self.client.login(username='admin_boss', password='AdminPassword123!')
        dash_admin_res = self.client.get(reverse('main:admin_dashboard'))
        self.assertEqual(dash_admin_res.status_code, 200)

        update_url = reverse('main:update_status', kwargs={'pk': order.pk})
        update_resp = self.client.post(update_url, {'status': 'Delivered'})
        self.assertEqual(update_resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Delivered')
        self.assertTrue(order.is_paid)

    # 6. REST API & Swagger UI Documentation Tests
    def test_rest_api_restaurants_list(self):
        api_url = reverse('api-restaurant-list')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_rest_api_items_filter_by_veg(self):
        api_url = reverse('api-item-list') + '?is_veg=true'
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        for item in response.data['results']:
            self.assertTrue(item['is_veg'])

    def test_swagger_documentation_endpoint(self):
        swagger_url = reverse('swagger-ui')
        response = self.client.get(swagger_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'swagger')

    def test_openapi_schema_generation(self):
        schema_url = reverse('schema')
        response = self.client.get(schema_url)
        self.assertEqual(response.status_code, 200)

    # 7. Phase 2 Features: Validation & Isolation Tests
    def test_phone_validation_rejects_invalid_phone(self):
        self.client.login(username='bengaluru_customer', password='Password123!')
        CartItems.objects.create(
            user=self.user,
            item=self.dish1,
            ordered=False,
            quantity=1
        )
        checkout_url = reverse('main:ordered')
        # Submit invalid 4-digit phone
        resp = self.client.post(checkout_url, {
            'address': '#108, 4th Main, HSR Layout, Bengaluru',
            'phone': '1234',
            'payment_method': 'Cash on Delivery (DEMO)'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.endswith('/cart/') or resp.url.endswith('/checkout/'))
        # No order created
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_in_menu_search_filters_dishes(self):
        url = reverse('main:restaurant_detail', kwargs={'slug': self.restaurant.slug}) + '?search=Chicken'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hyderabadi Chicken Biryani')
        self.assertNotContains(response, 'Paneer Tikka Biryani')

    def test_user_order_isolation(self):
        # Create user2 with an order
        user2 = User.objects.create_user(username='other_customer', password='Password123!')
        Order.objects.create(
            order_number='FG-PRIVATE-999',
            user=user2,
            restaurant=self.restaurant,
            subtotal=200.0,
            total_amount=210.0,
            status='Active'
        )
        # Log in as user1
        self.client.login(username='bengaluru_customer', password='Password123!')
        resp = self.client.get(reverse('main:order_details'))
        self.assertEqual(resp.status_code, 200)
        # User 1 must NOT see user 2's private order
        self.assertNotContains(resp, 'FG-PRIVATE-999')


class FoodieGo22EndToEndTestSuite(TestCase):
    """
    Mandatory 22 End-to-End Verification Test Suite for FoodieGo 2.2
    Tests all 4 departments, connected lifecycle, role security, coupons, address management, and REST APIs.
    """
    def setUp(self):
        self.client = Client()

        # Seed Admin
        self.admin = User.objects.create_superuser(
            username='platform_admin',
            password='AdminPassword123!',
            email='admin@foodiego.com'
        )
        self.admin.profile.role = 'ADMIN'
        self.admin.profile.save()

        # Seed Restaurant A & Chef
        self.restaurant_a = Restaurant.objects.create(
            name='Meghana Foods HSR',
            slug='meghana-foods-hsr-201',
            area='HSR Layout',
            cuisine='Biryani',
            rating=4.8,
            average_cost_for_two=500.0,
            estimated_delivery_minutes=30,
            is_approved=True,
            is_open=True
        )
        self.chef_a = User.objects.create_user(
            username='chef_meghana',
            password='ChefPassword123!'
        )
        self.chef_a.profile.role = 'RESTAURANT'
        self.chef_a.profile.restaurant = self.restaurant_a
        self.chef_a.profile.save()

        # Seed Restaurant B
        self.restaurant_b = Restaurant.objects.create(
            name='Empire Restaurant Koramangala',
            slug='empire-restaurant-koramangala-202',
            area='Koramangala',
            cuisine='North Indian',
            rating=4.4,
            average_cost_for_two=400.0,
            estimated_delivery_minutes=25,
            is_approved=True,
            is_open=True
        )

        # Seed Dishes
        self.dish_biryani = Item.objects.create(
            restaurant=self.restaurant_a,
            title='Special Chicken Dum Biryani',
            slug='special-chicken-dum-biryani-201',
            category='Biryani',
            price=290.0,
            is_veg=False,
            is_available=True,
            created_by=self.chef_a
        )
        self.dish_paneer = Item.objects.create(
            restaurant=self.restaurant_a,
            title='Paneer Butter Masala',
            slug='paneer-butter-masala-201',
            category='Main Course',
            price=210.0,
            is_veg=True,
            is_available=True,
            created_by=self.chef_a
        )
        self.dish_empire = Item.objects.create(
            restaurant=self.restaurant_b,
            title='Empire Butter Chicken',
            slug='empire-butter-chicken-202',
            category='Main Course',
            price=280.0,
            is_veg=False,
            is_available=True
        )

        # Seed Delivery Rider
        self.rider = User.objects.create_user(
            username='rider_vikram',
            password='RiderPassword123!'
        )
        self.rider.profile.role = 'DELIVERY'
        self.rider.profile.vehicle_type = 'Ather 450X Electric'
        self.rider.profile.phone_number = '9876543210'
        self.rider.profile.save()

        # Seed Customer 1 & 2
        self.customer1 = User.objects.create_user(
            username='rohit_sharma',
            password='CustomerPassword123!'
        )
        self.customer1.profile.role = 'CUSTOMER'
        self.customer1.profile.phone_number = '9988776655'
        self.customer1.profile.save()

        self.customer2 = User.objects.create_user(
            username='virat_kohli',
            password='CustomerPassword123!'
        )
        self.customer2.profile.role = 'CUSTOMER'
        self.customer2.profile.save()

        # Seed Customer 1 Address
        from accounts.models import CustomerAddress
        self.addr1 = CustomerAddress.objects.create(
            user=self.customer1,
            title='Home',
            address_line='#402, Green Glen Layout, Bellandur',
            area='Bellandur',
            city='Bengaluru',
            pincode='560103',
            phone='9988776655',
            is_default=True
        )

        # Seed Active Coupon
        from main.models import Coupon
        self.coupon = Coupon.objects.create(
            code='SWIGGY50',
            title='50% Off Welcome Deal',
            discount_percent=50,
            min_order_amount=200.0,
            max_discount_amount=100.0,
            is_active=True
        )

    # 1. Customer Registration & Login
    def test_01_customer_signup_and_login(self):
        resp = self.client.post(reverse('accounts:signup'), {
            'username': 'new_user_blr',
            'email': 'new_user@foodiego.com',
            'first_name': 'New',
            'last_name': 'Customer',
            'password1': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username='new_user_blr').exists())

    # 2. Search Page & Case-Insensitive Matching
    def test_02_search_dishes_and_restaurants(self):
        resp = self.client.get(reverse('main:search') + '?q=biryani')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Special Chicken Dum Biryani')
        self.assertContains(resp, 'Meghana Foods HSR')

    # 3. Restaurant Details & Menu Inspection
    def test_03_restaurant_detail_menu(self):
        resp = self.client.get(reverse('main:restaurant_detail', kwargs={'slug': self.restaurant_a.slug}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Special Chicken Dum Biryani')
        self.assertContains(resp, 'Paneer Butter Masala')

    # 4 & 5. Add to Cart, Quantity Update, and Totals
    def test_04_cart_operations_and_calculations(self):
        self.client.login(username='rohit_sharma', password='CustomerPassword123!')
        
        # Add dish 1 (price 290)
        self.client.get(reverse('main:add-to-cart', kwargs={'slug': self.dish_biryani.slug}))
        # Add dish 2 (price 210)
        self.client.get(reverse('main:add-to-cart', kwargs={'slug': self.dish_paneer.slug}))

        ci1 = CartItems.objects.get(user=self.customer1, item=self.dish_biryani, ordered=False)
        self.assertEqual(ci1.quantity, 1)

        # Increase quantity of dish 1 to 2
        self.client.post(reverse('main:update_cart_quantity', kwargs={'pk': ci1.pk}) + '?action=increase')
        ci1.refresh_from_db()
        self.assertEqual(ci1.quantity, 2)

        # Verify Cart Page
        cart_resp = self.client.get(reverse('main:cart'))
        self.assertEqual(cart_resp.status_code, 200)
        # subtotal = 2*290 + 1*210 = 790
        self.assertContains(cart_resp, '790')

    # 6. Apply Valid & Invalid Coupons
    def test_05_coupon_application(self):
        self.client.login(username='rohit_sharma', password='CustomerPassword123!')
        CartItems.objects.create(user=self.customer1, item=self.dish_biryani, quantity=2, ordered=False)

        # Test Invalid Coupon
        inv_resp = self.client.post(reverse('main:apply_coupon'), {'coupon_code': 'FAKE999'})
        self.assertEqual(inv_resp.status_code, 302)
        session = self.client.session
        self.assertNotIn('coupon_id', session)

        # Test Valid Coupon SWIGGY50 (50% of 580 = 290, capped at max 100)
        val_resp = self.client.post(reverse('main:apply_coupon'), {'coupon_code': 'SWIGGY50'})
        self.assertEqual(val_resp.status_code, 302)
        session = self.client.session
        self.assertEqual(session.get('coupon_id'), self.coupon.id)

    # 7, 8, 9. Checkout & Order Item Snapshots Creation
    def test_06_checkout_creates_order_and_snapshots(self):
        self.client.login(username='rohit_sharma', password='CustomerPassword123!')
        CartItems.objects.create(user=self.customer1, item=self.dish_biryani, quantity=2, ordered=False)
        
        # Apply SWIGGY50 coupon
        self.client.post(reverse('main:apply_coupon'), {'coupon_code': 'SWIGGY50'})

        # Checkout post
        checkout_resp = self.client.post(reverse('main:ordered'), {
            'saved_address_id': self.addr1.id,
            'phone_number': '9988776655',
            'payment_method': 'Cash On Delivery'
        })
        self.assertEqual(checkout_resp.status_code, 302)

        order = Order.objects.filter(user=self.customer1).latest('created_at')
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'Confirmed')
        self.assertEqual(order.discount_amount, 100.0)

        # Check immutable historical snapshot
        snapshots = order.order_items.all()
        self.assertEqual(snapshots.count(), 1)
        snap = snapshots.first()
        self.assertEqual(snap.item_title, 'Special Chicken Dum Biryani')
        self.assertEqual(snap.item_price, 290.0)
        self.assertEqual(snap.quantity, 2)

        # Customer can view tracking
        track_resp = self.client.get(reverse('main:order_tracking', kwargs={'order_number': order.order_number}))
        self.assertEqual(track_resp.status_code, 200)
        self.assertContains(track_resp, order.order_number)

    # 10, 11. Restaurant Staff Order Acceptance & Prep
    def test_07_restaurant_staff_kitchen_workflow(self):
        order = Order.objects.create(
            order_number='FG-TEST-KITCHEN-1',
            user=self.customer1,
            restaurant=self.restaurant_a,
            subtotal=500.0,
            total_amount=525.0,
            status='Confirmed',
            delivery_address='Bengaluru'
        )
        self.client.login(username='chef_meghana', password='ChefPassword123!')

        # Chef accepts order
        accept_url = reverse('main:restaurant_update_order_status', kwargs={'order_number': order.order_number})
        resp = self.client.post(accept_url, {'action': 'accept'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'Accepted')
        self.assertIsNotNone(order.accepted_at)

        # Chef starts preparing
        self.client.post(accept_url, {'action': 'preparing'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'Preparing')

        # Chef marks ready for pickup
        self.client.post(accept_url, {'action': 'ready'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'Ready for Pickup')
        self.assertIsNotNone(order.ready_at)

    # 12, 13, 14. Delivery Partner Claim, Pickup & Complete
    def test_08_delivery_partner_lifecycle(self):
        order = Order.objects.create(
            order_number='FG-TEST-RIDER-1',
            user=self.customer1,
            restaurant=self.restaurant_a,
            subtotal=500.0,
            total_amount=525.0,
            status='Ready for Pickup',
            delivery_address='Bengaluru'
        )
        self.client.login(username='rider_vikram', password='RiderPassword123!')

        # Rider claims order
        claim_url = reverse('main:delivery_claim_order', kwargs={'order_number': order.order_number})
        self.client.post(claim_url)
        order.refresh_from_db()
        self.assertEqual(order.assigned_delivery_partner, self.rider)

        # Rider confirms pickup (Out for Delivery)
        pickup_url = reverse('main:delivery_confirm_pickup', kwargs={'order_number': order.order_number})
        self.client.post(pickup_url)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Out for Delivery')
        self.assertIsNotNone(order.picked_up_at)

        # Rider confirms delivered
        deliver_url = reverse('main:delivery_confirm_delivered', kwargs={'order_number': order.order_number})
        self.client.post(deliver_url)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Delivered')
        self.assertTrue(order.is_paid)
        self.assertIsNotNone(order.delivery_date)

    # 15, 16. Admin Inspection & Coupon Management
    def test_09_admin_portal_and_coupon_creation(self):
        self.client.login(username='platform_admin', password='AdminPassword123!')
        
        # View platform overview
        overview_resp = self.client.get(reverse('main:admin_portal_overview'))
        self.assertEqual(overview_resp.status_code, 200)

        # Create new promotional coupon
        create_url = reverse('main:admin_coupon_create')
        self.client.post(create_url, {
            'code': 'DIWALI2026',
            'title': 'Diwali Festival 30% Off',
            'discount_percent': 30,
            'discount_amount': 0,
            'min_order_amount': 250,
            'max_discount_amount': 150
        })
        from main.models import Coupon
        self.assertTrue(Coupon.objects.filter(code='DIWALI2026').exists())

    # 17. Security: Customer Order Isolation
    def test_10_customer_cannot_access_other_orders(self):
        order2 = Order.objects.create(
            order_number='FG-VIRAT-ORDER',
            user=self.customer2,
            restaurant=self.restaurant_a,
            total_amount=300.0,
            status='Confirmed'
        )
        self.client.login(username='rohit_sharma', password='CustomerPassword123!')
        resp = self.client.get(reverse('main:order_tracking', kwargs={'order_number': order2.order_number}))
        # Redirected with access denied
        self.assertEqual(resp.status_code, 302)

    # 18. Security: Chef cannot modify another restaurant's menu
    def test_11_chef_cannot_modify_other_restaurant(self):
        self.client.login(username='chef_meghana', password='ChefPassword123!')
        # Try to delete dish from restaurant B
        del_url = reverse('main:restaurant_dish_delete', kwargs={'pk': self.dish_empire.pk})
        resp = self.client.post(del_url)
        self.assertEqual(resp.status_code, 404)
        # Dish still exists
        self.assertTrue(Item.objects.filter(pk=self.dish_empire.pk).exists())

    # 19. Security: Delivery partner cannot modify unassigned deliveries
    def test_12_rider_cannot_confirm_unassigned_order(self):
        order = Order.objects.create(
            order_number='FG-UNASSIGNED',
            user=self.customer1,
            restaurant=self.restaurant_a,
            status='Ready for Pickup'
        )
        self.client.login(username='rider_vikram', password='RiderPassword123!')
        # Try to confirm pickup without claiming
        pickup_url = reverse('main:delivery_confirm_pickup', kwargs={'order_number': order.order_number})
        resp = self.client.post(pickup_url)
        self.assertEqual(resp.status_code, 404)

    # 20. Security: Non-admin cannot access admin portal
    def test_13_non_admin_cannot_access_admin_portal(self):
        self.client.login(username='rohit_sharma', password='CustomerPassword123!')
        resp = self.client.get(reverse('main:admin_portal_overview'))
        self.assertEqual(resp.status_code, 302)

    # 21. REST APIs & Address Management
    def test_14_saved_address_management(self):
        self.client.login(username='rohit_sharma', password='CustomerPassword123!')
        add_url = reverse('accounts:add_address')
        self.client.post(add_url, {
            'title': 'Office',
            'address_line': 'RMZ EcoWorld, Marathahalli-Sarjapur Outer Ring Road',
            'area': 'Bellandur',
            'city': 'Bengaluru',
            'pincode': '560103'
        })
        from accounts.models import CustomerAddress
        self.assertTrue(CustomerAddress.objects.filter(user=self.customer1, title='Office').exists())

    def test_15_rest_api_coupons(self):
        resp = self.client.get(reverse('api-coupon-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data['results']), 1)

    # 22. Razorpay Payment Gateway Tests
    def test_16_checkout_view_provides_razorpay_credentials(self):
        self.client.login(username='rohit_sharma', password='CustomerPassword123!')
        CartItems.objects.create(
            user=self.customer1,
            item=self.dish_biryani,
            ordered=False,
            quantity=1
        )
        resp = self.client.get(reverse('main:checkout'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('razorpay_key_id', resp.context)
        self.assertEqual(resp.context['razorpay_key_id'], 'rzp_test_TqzhtjQhQryWfB')
        self.assertIn('razorpay_order_id', resp.context)
        self.assertIn('razorpay_amount', resp.context)
        self.assertGreater(resp.context['razorpay_amount'], 0)

    def test_17_razorpay_checkout_order_submission(self):
        self.client.login(username='rohit_sharma', password='CustomerPassword123!')
        CartItems.objects.create(
            user=self.customer1,
            item=self.dish_biryani,
            ordered=False,
            quantity=2
        )
        checkout_url = reverse('main:ordered')
        resp = self.client.post(checkout_url, {
            'address': '#42, 5th Cross, HSR Layout Sector 2, Bengaluru',
            'phone': '9876543210',
            'instructions': 'Leave at door',
            'payment_method': 'Razorpay',
            'razorpay_payment_id': 'pay_test_SAMPLE12345',
            'razorpay_order_id': 'order_demo_SAMPLE12345',
            'razorpay_signature': 'sig_test_SAMPLE12345'
        })
        self.assertEqual(resp.status_code, 302)
        order = Order.objects.filter(user=self.customer1, payment_method='Razorpay').first()
        self.assertIsNotNone(order)
        self.assertTrue(order.is_paid)
        self.assertEqual(order.razorpay_payment_id, 'pay_test_SAMPLE12345')
        self.assertEqual(order.razorpay_order_id, 'order_demo_SAMPLE12345')

    def test_18_create_razorpay_order_ajax_endpoint(self):
        self.client.login(username='rohit_sharma', password='CustomerPassword123!')
        CartItems.objects.create(
            user=self.customer1,
            item=self.dish_biryani,
            ordered=False,
            quantity=1
        )
        resp = self.client.get(reverse('main:create_razorpay_order'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['key'], 'rzp_test_TqzhtjQhQryWfB')
        self.assertIn('order_id', data)
        self.assertIn('amount', data)
        self.assertEqual(data['currency'], 'INR')


