import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile, CustomerAddress
from main.models import Restaurant


class Command(BaseCommand):
    help = 'Safely creates or updates development-only interview test accounts for all 4 roles.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== FoodieGo Development Test Accounts Setup ==='))

        # Passwords sourced from environment variables with secure dev defaults
        admin_pass = os.environ.get('DEMO_ADMIN_PASSWORD', 'FoodieGo@Admin2026!')
        partner_pass = os.environ.get('DEMO_PARTNER_PASSWORD', 'FoodieGo@Partner2026!')
        rider_pass = os.environ.get('DEMO_RIDER_PASSWORD', 'FoodieGo@Rider2026!')
        customer_pass = os.environ.get('DEMO_CUSTOMER_PASSWORD', 'FoodieGo@Customer2026!')

        # 1. Platform Administrator
        admin_user, created_admin = User.objects.get_or_create(
            username='demo_admin',
            defaults={
                'email': 'admin@foodiego.local',
                'first_name': 'Demo',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password(admin_pass)
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        Profile.objects.update_or_create(
            user=admin_user,
            defaults={'role': 'ADMIN', 'phone_number': '9876543210'}
        )
        status_admin = 'Created' if created_admin else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'[{status_admin}] Administrator: username="demo_admin", email="admin@foodiego.local"'))

        # 2. Restaurant Partner (Meghana Foods or first restaurant)
        partner_rest = Restaurant.objects.filter(name__icontains='Meghana').first() or Restaurant.objects.first()
        partner_user, created_partner = User.objects.get_or_create(
            username='demo_partner',
            defaults={
                'email': 'partner@foodiego.local',
                'first_name': 'Suresh',
                'last_name': 'KitchenManager',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        partner_user.set_password(partner_pass)
        partner_user.is_staff = False
        partner_user.is_superuser = False
        partner_user.save()
        Profile.objects.update_or_create(
            user=partner_user,
            defaults={
                'role': 'RESTAURANT',
                'restaurant': partner_rest,
                'phone_number': '9876543211',
                'address': f'{partner_rest.name if partner_rest else "Restaurant"}, {partner_rest.area if partner_rest else "Bengaluru"}'
            }
        )
        status_partner = 'Created' if created_partner else 'Updated'
        rest_name = partner_rest.name if partner_rest else "None"
        self.stdout.write(self.style.SUCCESS(f'[{status_partner}] Restaurant Partner: username="demo_partner", outlet="{rest_name}"'))

        # 3. Delivery Partner
        rider_user, created_rider = User.objects.get_or_create(
            username='demo_rider',
            defaults={
                'email': 'rider@foodiego.local',
                'first_name': 'Kiran',
                'last_name': 'Courier',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        rider_user.set_password(rider_pass)
        rider_user.is_staff = False
        rider_user.is_superuser = False
        rider_user.save()
        Profile.objects.update_or_create(
            user=rider_user,
            defaults={
                'role': 'DELIVERY',
                'is_available': True,
                'phone_number': '9876543212',
                'address': 'HSR Layout Sector 2, Bengaluru'
            }
        )
        status_rider = 'Created' if created_rider else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'[{status_rider}] Delivery Partner: username="demo_rider", email="rider@foodiego.local"'))

        # 4. Customer
        customer_user, created_customer = User.objects.get_or_create(
            username='demo_customer',
            defaults={
                'email': 'customer@foodiego.local',
                'first_name': 'Ananya',
                'last_name': 'Sharma',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        customer_user.set_password(customer_pass)
        customer_user.is_staff = False
        customer_user.is_superuser = False
        customer_user.save()
        Profile.objects.update_or_create(
            user=customer_user,
            defaults={
                'role': 'CUSTOMER',
                'phone_number': '9876543213',
                'address': '#102, Green Glen Layout, Bellandur, Bengaluru'
            }
        )
        CustomerAddress.objects.update_or_create(
            user=customer_user,
            title='Home',
            defaults={
                'address_line': '#102, 3rd Floor, Green Glen Layout, Bellandur',
                'landmark': 'Opposite Cloudnine Hospital',
                'area': 'Bellandur',
                'city': 'Bengaluru',
                'pincode': '560103',
                'phone': '9876543213',
                'is_default': True
            }
        )
        status_customer = 'Created' if created_customer else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'[{status_customer}] Customer: username="demo_customer", email="customer@foodiego.local"'))

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Test Accounts Summary Table ==='))
        table_output = """
+--------------------+----------------+---------------------------+-----------------------+--------------------------------------+
| Role               | Username       | Email                     | Default Dev Password  | Portal URL                           |
+--------------------+----------------+---------------------------+-----------------------+--------------------------------------+
| Customer           | demo_customer  | customer@foodiego.local   | FoodieGo@Customer2026!| http://127.0.0.1:8000/               |
| Restaurant Partner | demo_partner   | partner@foodiego.local    | FoodieGo@Partner2026! | http://127.0.0.1:8000/partner/       |
| Delivery Partner   | demo_rider     | rider@foodiego.local      | FoodieGo@Rider2026!   | http://127.0.0.1:8000/delivery/      |
| Administrator      | demo_admin     | admin@foodiego.local      | FoodieGo@Admin2026!   | http://127.0.0.1:8000/admin-portal/  |
+--------------------+----------------+---------------------------+-----------------------+--------------------------------------+
"""
        self.stdout.write(table_output)
        self.stdout.write(self.style.NOTICE('NOTE: These credentials are intended strictly for local technical interview demonstrations.'))
