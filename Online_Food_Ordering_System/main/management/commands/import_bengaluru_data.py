import csv
import os
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.conf import settings
from main.models import Restaurant, Item
from main.image_catalog import get_curated_food_image, get_curated_restaurant_cover

class Command(BaseCommand):
    help = 'Imports synthetic Bengaluru restaurant and menu item demonstration datasets into FoodieGo 2.0'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush-demo',
            action='store_true',
            help='Removes existing SYNTHETIC_DEMO records before re-importing (preserves user data)',
        )
        parser.add_argument(
            '--restaurants-csv',
            type=str,
            default=None,
            help='Custom path to bengaluru_restaurants_100_demo.csv'
        )
        parser.add_argument(
            '--menu-csv',
            type=str,
            default=None,
            help='Custom path to bengaluru_menu_items_10000_demo.csv'
        )
        parser.add_argument(
            '--limit-items',
            type=int,
            default=None,
            help='Limit the number of menu items imported (for quick test runs)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== FoodieGo 2.0 Dataset Importer ==="))
        self.stdout.write("Note: This dataset contains SYNTHETIC DEMONSTRATION RECORDS.")
        self.stdout.write("Ratings, delivery times and coordinates are generated demonstration values.\n")

        base_dir = settings.BASE_DIR
        data_dir = os.path.join(base_dir, 'data')

        rest_path = options['restaurants_csv'] or os.path.join(data_dir, 'bengaluru_restaurants_100_demo.csv')
        menu_path = options['menu_csv'] or os.path.join(data_dir, 'bengaluru_menu_items_10000_demo.csv')

        if not os.path.exists(rest_path):
            # Try workspace root fallback
            rest_path_alt = os.path.join(os.path.dirname(base_dir), 'FoodieGo_Bengaluru_Demo_Dataset', 'bengaluru_restaurants_100_demo.csv')
            if os.path.exists(rest_path_alt):
                rest_path = rest_path_alt

        if not os.path.exists(menu_path):
            menu_path_alt = os.path.join(os.path.dirname(base_dir), 'FoodieGo_Bengaluru_Demo_Dataset', 'bengaluru_menu_items_10000_demo.csv')
            if os.path.exists(menu_path_alt):
                menu_path = menu_path_alt

        if not os.path.exists(rest_path):
            self.stderr.write(self.style.ERROR(f"Restaurants CSV not found at: {rest_path}"))
            return

        if not os.path.exists(menu_path):
            self.stderr.write(self.style.ERROR(f"Menu items CSV not found at: {menu_path}"))
            return

        # Handle --flush-demo
        if options['flush_demo']:
            self.stdout.write("Flushing existing SYNTHETIC_DEMO records...")
            deleted_items = Item.objects.filter(data_type='SYNTHETIC_DEMO').delete()[0]
            deleted_rests = Restaurant.objects.filter(data_type='SYNTHETIC_DEMO').delete()[0]
            self.stdout.write(f"Removed {deleted_items} demo items and {deleted_rests} demo restaurants.")

        # Ensure demo admin user exists for created_by attribution
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()

        # Step 1: Import Restaurants
        self.stdout.write(f"Importing restaurants from: {rest_path}...")
        created_restaurants = 0
        updated_restaurants = 0
        restaurant_map = {}  # demo_id -> Restaurant instance

        with open(rest_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # Normalize field names
            for row in reader:
                clean_row = {k.strip().lstrip('\ufeff'): v.strip() for k, v in row.items() if k}
                try:
                    demo_id = int(clean_row['restaurant_id'])
                except (ValueError, KeyError):
                    continue

                name = clean_row.get('restaurant_name', f'Restaurant {demo_id}')
                area = clean_row.get('area', 'Bengaluru')
                slug_candidate = slugify(f"{name}-{area}-{demo_id}")[:240]

                defaults = {
                    'name': name,
                    'slug': slug_candidate,
                    'area': area,
                    'city': clean_row.get('city', 'Bengaluru'),
                    'state': clean_row.get('state', 'Karnataka'),
                    'cuisine': clean_row.get('cuisine', 'Multi-Cuisine'),
                    'rating': float(clean_row.get('rating') or 4.0),
                    'rating_count': int(clean_row.get('rating_count') or 0),
                    'average_cost_for_two': float(clean_row.get('average_cost_for_two_inr') or 300),
                    'estimated_delivery_minutes': int(clean_row.get('estimated_delivery_minutes') or 30),
                    'delivery_fee': float(clean_row.get('delivery_fee_inr') or 0),
                    'latitude': float(clean_row['latitude']) if clean_row.get('latitude') else None,
                    'longitude': float(clean_row['longitude']) if clean_row.get('longitude') else None,
                    'is_open': clean_row.get('is_open_demo', 'True').lower() == 'true',
                    'image_url': get_curated_restaurant_cover(clean_row.get('cuisine', 'Multi-Cuisine'), name, demo_id),
                    'data_type': 'SYNTHETIC_DEMO',
                }

                restaurant_obj, created = Restaurant.objects.update_or_create(
                    demo_id=demo_id,
                    defaults=defaults
                )
                if created:
                    created_restaurants += 1
                else:
                    updated_restaurants += 1

                restaurant_map[demo_id] = restaurant_obj

        self.stdout.write(self.style.SUCCESS(
            f"Restaurants processed: {created_restaurants} created, {updated_restaurants} updated. Total: {len(restaurant_map)}"
        ))

        # Step 2: Import Menu Items
        self.stdout.write(f"Importing menu items from: {menu_path}...")
        existing_demo_ids = set(Item.objects.filter(demo_id__isnull=False).values_list('demo_id', flat=True))
        items_to_create = []
        batch_size = 1000
        total_processed = 0
        limit = options.get('limit_items')

        with open(menu_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                clean_row = {k.strip().lstrip('\ufeff'): v.strip() for k, v in row.items() if k}
                try:
                    demo_id = int(clean_row['menu_item_id'])
                    rest_demo_id = int(clean_row['restaurant_id'])
                except (ValueError, KeyError):
                    continue

                # Skip if already exists to prevent duplicate rows
                if demo_id in existing_demo_ids:
                    continue

                restaurant = restaurant_map.get(rest_demo_id)
                food_name = clean_row.get('food_name', f'Dish {demo_id}')
                category = clean_row.get('category', 'Main Course')
                price = float(clean_row.get('price_inr') or 150)
                is_veg = clean_row.get('is_veg', 'True').lower() == 'true'
                rating = float(clean_row.get('rating') or 4.0)
                is_available = clean_row.get('is_available_demo', 'True').lower() == 'true'
                discount = int(float(clean_row.get('discount_percent_demo') or 0))
                food_img = get_curated_food_image(food_name, category, is_veg)
                offer = clean_row.get('offer_label_demo', '')
                slug_dish = slugify(f"{food_name}-{demo_id}")[:240]

                item = Item(
                    demo_id=demo_id,
                    restaurant=restaurant,
                    title=food_name,
                    category=category,
                    price=price,
                    pieces=1,
                    instructions=clean_row.get('cuisine', 'Available'),
                    description=f"{category} freshly prepared at {clean_row.get('restaurant_name', 'our kitchen')}.",
                    labels='Best Selling Foods' if rating >= 4.5 else ('New Food' if is_veg else ''),
                    label_colour='success' if is_veg else 'danger',
                    slug=slug_dish,
                    created_by=admin_user,
                    is_veg=is_veg,
                    rating=rating,
                    is_available=is_available,
                    discount_percent=discount,
                    food_image_url=food_img,
                    offer_label=offer,
                    data_type='SYNTHETIC_DEMO'
                )
                items_to_create.append(item)
                existing_demo_ids.add(demo_id)
                total_processed += 1

                if len(items_to_create) >= batch_size:
                    Item.objects.bulk_create(items_to_create)
                    self.stdout.write(f"  Inserted {total_processed} items...")
                    items_to_create = []

                if limit and total_processed >= limit:
                    self.stdout.write(f"Reached item limit: {limit}")
                    break

            if items_to_create:
                Item.objects.bulk_create(items_to_create)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully finished importing {total_processed} menu items!"
        ))
        self.stdout.write(self.style.SUCCESS("Demo dataset import completed without altering user records."))
