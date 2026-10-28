from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from accounts.models import Profile, CustomerAddress
from main.models import Restaurant, Coupon, Order, CartItems, OrderItem
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = "Seeds demo roles, default coupons, and customer addresses for FoodieGo 2.2"

    def handle(self, *args, **options):
        self.stdout.write("Seeding FoodieGo 2.2 roles and initial demo records...")

        # 1. Ensure Groups exist
        admin_group, _ = Group.objects.get_or_create(name='admin_owner')
        delivery_group, _ = Group.objects.get_or_create(name='delivery_partner')
        customer_group, _ = Group.objects.get_or_create(name='customer')

        # 2. Demo Customer: bengaluru_customer
        customer_user, created = User.objects.get_or_create(
            username='bengaluru_customer',
            defaults={'email': 'customer@foodiego.com', 'first_name': 'Aarav', 'last_name': 'Sharma'}
        )
        if created:
            customer_user.set_password('Password123!')
            customer_user.save()
        customer_user.groups.add(customer_group)
        cust_profile, _ = Profile.objects.get_or_create(user=customer_user)
        cust_profile.role = 'CUSTOMER'
        cust_profile.phone_number = '9876543210'
        cust_profile.address = '#108, 4th Main, 7th Cross, HSR Layout Sector 1, Bengaluru'
        cust_profile.save()

        # Seed saved addresses for customer
        CustomerAddress.objects.get_or_create(
            user=customer_user,
            title='Home',
            defaults={
                'address_line': '#108, 4th Main, 7th Cross, HSR Layout Sector 1',
                'landmark': 'Near Agara Lake',
                'area': 'HSR Layout',
                'city': 'Bengaluru',
                'pincode': '560102',
                'phone': '9876543210',
                'is_default': True
            }
        )
        CustomerAddress.objects.get_or_create(
            user=customer_user,
            title='Work',
            defaults={
                'address_line': 'Embassy TechVillage, Tower 2B, 3rd Floor, Bellandur Outer Ring Road',
                'landmark': 'Near Cessna Business Park',
                'area': 'Koramangala',
                'city': 'Bengaluru',
                'pincode': '560103',
                'phone': '9876543210',
                'is_default': False
            }
        )

        # 3. Demo Restaurant: pick first restaurant or Meghana Biryani
        demo_rest = Restaurant.objects.filter(name__icontains='Meghana').first()
        if not demo_rest:
            demo_rest = Restaurant.objects.first()

        restaurant_user, created = User.objects.get_or_create(
            username='restaurant_chef',
            defaults={'email': 'chef@restaurant.com', 'first_name': 'Vikram', 'last_name': 'Reddy'}
        )
        if created:
            restaurant_user.set_password('Password123!')
            restaurant_user.save()
        restaurant_user.groups.add(admin_group)
        rest_profile, _ = Profile.objects.get_or_create(user=restaurant_user)
        rest_profile.role = 'RESTAURANT'
        rest_profile.restaurant = demo_rest
        rest_profile.phone_number = '9845012345'
        rest_profile.save()

        if demo_rest:
            demo_rest.owner = restaurant_user
            demo_rest.opening_time = '10:30 AM'
            demo_rest.closing_time = '11:00 PM'
            demo_rest.contact_phone = '+91 80 4110 5555'
            demo_rest.address_details = f"{demo_rest.name}, 100ft Road, {demo_rest.area}, Bengaluru, Karnataka 560034"
            demo_rest.save()

        # 4. Demo Delivery Partner: delivery_rider
        delivery_user, created = User.objects.get_or_create(
            username='delivery_rider',
            defaults={'email': 'rider@foodiego.com', 'first_name': 'Karthik', 'last_name': 'Gowda'}
        )
        if created:
            delivery_user.set_password('Password123!')
            delivery_user.save()
        delivery_user.groups.add(delivery_group)
        deliv_profile, _ = Profile.objects.get_or_create(user=delivery_user)
        deliv_profile.role = 'DELIVERY'
        deliv_profile.phone_number = '9876543211'
        deliv_profile.vehicle_type = 'Ather 450X Electric'
        deliv_profile.is_available = True
        deliv_profile.save()

        # 5. Demo Admin: admin
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            adm_profile, _ = Profile.objects.get_or_create(user=admin_user)
            adm_profile.role = 'ADMIN'
            adm_profile.save()

        # 6. Seed Coupons & Offers
        coupons = [
            {
                'code': 'SWIGGY50',
                'title': '50% Welcome Discount',
                'description': '50% off on your favorite dishes up to ₹100',
                'discount_percent': 50,
                'min_order_amount': 200.0,
                'max_discount_amount': 100.0,
            },
            {
                'code': 'FOODIEGO20',
                'title': '20% Flat Discount',
                'description': 'Enjoy 20% off on orders above ₹250',
                'discount_percent': 20,
                'min_order_amount': 250.0,
                'max_discount_amount': 120.0,
            },
            {
                'code': 'BENGALURU100',
                'title': 'Flat ₹100 Off Bengaluru Mega Feast',
                'description': 'Get ₹100 flat discount on orders above ₹400',
                'discount_percent': 0,
                'discount_amount': 100.0,
                'min_order_amount': 400.0,
                'max_discount_amount': 100.0,
            },
            {
                'code': 'WELCOME50',
                'title': 'First Bite Welcome Offer',
                'description': '50% discount up to ₹75 on orders above ₹150',
                'discount_percent': 50,
                'min_order_amount': 150.0,
                'max_discount_amount': 75.0,
            },
        ]

        now = timezone.now()
        for cdata in coupons:
            Coupon.objects.update_or_create(
                code=cdata['code'],
                defaults={
                    'title': cdata['title'],
                    'description': cdata['description'],
                    'discount_percent': cdata.get('discount_percent', 0),
                    'discount_amount': cdata.get('discount_amount', 0.0),
                    'min_order_amount': cdata['min_order_amount'],
                    'max_discount_amount': cdata['max_discount_amount'],
                    'valid_from': now - timedelta(days=1),
                    'valid_to': now + timedelta(days=365),
                    'is_active': True,
                }
            )

        # 7. Convert existing Order CartItems to OrderItems if missing
        for ord_obj in Order.objects.all():
            if not ord_obj.order_items.exists():
                for ci in ord_obj.cart_items.all():
                    OrderItem.objects.create(
                        order=ord_obj,
                        item=ci.item,
                        item_title=ci.item.title if ci.item else "Delicious Dish",
                        item_price=ci.item.price if ci.item else 200.0,
                        quantity=ci.quantity,
                        subtotal=ci.subtotal,
                        is_veg=ci.item.is_veg if ci.item else True,
                        food_image_url=ci.item.get_display_image if ci.item else ""
                    )

        self.stdout.write(self.style.SUCCESS("Successfully seeded FoodieGo 2.2 demo roles, coupons, and historical snapshots!"))
