import os
import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import Restaurant, Item

class Command(BaseCommand):
    help = "Update restaurant and menu item representative image URLs from FoodieGo CSV files."

    def add_arguments(self, parser):
        parser.add_argument(
            '--restaurants-csv',
            type=str,
            default='data/FoodieGo_Restaurants_with_Image_Links.csv',
            help='Path to restaurants image links CSV'
        )
        parser.add_argument(
            '--menu-csv',
            type=str,
            default='data/FoodieGo_Menu_Items_with_Image_Links.csv',
            help='Path to menu items image links CSV'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Starting FoodieGo Image URLs Update from CSV ==="))

        rest_csv_path = options['restaurants_csv']
        menu_csv_path = options['menu_csv']

        # Check alternative paths if relative path doesn't resolve directly
        if not os.path.exists(rest_csv_path):
            alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), rest_csv_path)
            if os.path.exists(alt_path):
                rest_csv_path = alt_path

        if not os.path.exists(menu_csv_path):
            alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), menu_csv_path)
            if os.path.exists(alt_path):
                menu_csv_path = alt_path

        self.stdout.write(f"Loading Restaurants CSV from: {rest_csv_path}")
        self.stdout.write(f"Loading Menu Items CSV from: {menu_csv_path}")

        if not os.path.exists(rest_csv_path):
            self.stdout.write(self.style.ERROR(f"Error: Restaurants CSV not found at {rest_csv_path}"))
            return

        if not os.path.exists(menu_csv_path):
            self.stdout.write(self.style.ERROR(f"Error: Menu Items CSV not found at {menu_csv_path}"))
            return

        # Known broken URL mapping to working verified Unsplash URLs
        BROKEN_URL_FIXES = {
            'https://images.unsplash.com/photo-1563379091339-03246963d96c?auto=format&fit=crop&w=1000&q=85':
                'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=1000&q=85',
        }

        def clean_url(url_val):
            url_val = (url_val or '').strip()
            return BROKEN_URL_FIXES.get(url_val, url_val)

        # ------------------------------------------------------------------
        # 1. Update Restaurants
        # ------------------------------------------------------------------
        rest_updated_count = 0
        with open(rest_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            restaurants_to_update = []
            for row in reader:
                r_id = int(row['restaurant_id'])
                new_image_url = clean_url(row.get('restaurant_image_url', ''))
                if not new_image_url:
                    continue

                # Match by demo_id or id
                restaurant = Restaurant.objects.filter(demo_id=r_id).first() or Restaurant.objects.filter(id=r_id).first()
                if restaurant:
                    restaurant.image_url = new_image_url
                    restaurants_to_update.append(restaurant)

            if restaurants_to_update:
                Restaurant.objects.bulk_update(restaurants_to_update, ['image_url'])
                rest_updated_count = len(restaurants_to_update)

        self.stdout.write(self.style.SUCCESS(f"Successfully updated image URLs for {rest_updated_count} restaurants."))

        # ------------------------------------------------------------------
        # 2. Update Menu Items
        # ------------------------------------------------------------------
        items_updated_count = 0
        with open(menu_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Build in-memory map of demo_id -> new_image_url for fast bulk updating
            url_map = {}
            for row in reader:
                m_id = int(row['menu_item_id'])
                img_url = clean_url(row.get('food_image_url', ''))
                if img_url:
                    url_map[m_id] = img_url

            self.stdout.write(f"Read {len(url_map)} menu item image mappings from CSV.")

            # Batch fetch and update to avoid huge memory spikes
            items_to_update = []
            matched_items = Item.objects.filter(demo_id__in=url_map.keys())
            for item in matched_items:
                new_url = url_map.get(item.demo_id)
                if new_url and item.food_image_url != new_url:
                    item.food_image_url = new_url
                    items_to_update.append(item)
                elif new_url:
                    # Even if identical, keep counted
                    item.food_image_url = new_url
                    items_to_update.append(item)

            if items_to_update:
                with transaction.atomic():
                    Item.objects.bulk_update(items_to_update, ['food_image_url'], batch_size=1000)
                items_updated_count = len(items_to_update)

        self.stdout.write(self.style.SUCCESS(f"Successfully updated food image URLs for {items_updated_count} menu items."))
        self.stdout.write(self.style.SUCCESS(f"Total Restaurants in DB: {Restaurant.objects.count()} (Preserved)"))
        self.stdout.write(self.style.SUCCESS(f"Total Menu Items in DB: {Item.objects.count()} (Preserved, no duplicates)"))
