from django.core.management.base import BaseCommand
from main.models import Restaurant, Item
from main.image_catalog import get_curated_food_image, get_curated_restaurant_cover

class Command(BaseCommand):
    help = 'Updates existing restaurant cover images and dish images in FoodieGo with curated, authentic food photography.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== FoodieGo 2.1 Food & Restaurant Image Updater ==="))

        # 1. Update Restaurants with curated storefront/dining images
        restaurants = Restaurant.objects.all()
        updated_rests = 0
        for rest in restaurants:
            new_cover = get_curated_restaurant_cover(rest.cuisine, rest.name, rest.demo_id or rest.id)
            if rest.image_url != new_cover:
                rest.image_url = new_cover
                rest.save(update_fields=['image_url'])
                updated_rests += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully updated {updated_rests} of {restaurants.count()} restaurant cover images."
        ))

        # 2. Update Items with curated dish-specific images (e.g. Masala Dosa -> Dosa photo, Biryani -> Biryani photo)
        items = Item.objects.all()
        total_items = items.count()
        self.stdout.write(f"Analyzing and updating {total_items} menu dishes with curated images...")

        updated_items = 0
        batch_size = 500
        items_to_update = []

        for item in items:
            curated_img = get_curated_food_image(item.title, item.category, item.is_veg)
            if item.food_image_url != curated_img:
                item.food_image_url = curated_img
                items_to_update.append(item)
                updated_items += 1

            if len(items_to_update) >= batch_size:
                Item.objects.bulk_update(items_to_update, ['food_image_url'], batch_size=batch_size)
                self.stdout.write(f"  Processed {updated_items} dishes...")
                items_to_update = []

        if items_to_update:
            Item.objects.bulk_update(items_to_update, ['food_image_url'], batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS(
            f"Completed! Accurately mapped and updated {updated_items} dishes with dish-specific photography."
        ))
