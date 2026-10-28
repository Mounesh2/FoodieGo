FoodieGo 2.0 — Bengaluru Food Delivery Demo Dataset

FILES
- foodiego_all_in_one_10000_demo.csv: 10,000 menu-item rows with restaurant, location, price, rating, delivery, veg status, offer, and image URL/path fields.
- bengaluru_restaurants_100_demo.csv: 100 restaurant records.
- bengaluru_menu_items_10000_demo.csv: 10,000 menu item records with restaurant IDs.

IMPORTANT DATA QUALITY / ETHICS
- These are SYNTHETIC DEMONSTRATION RECORDS, not verified real restaurants or current Swiggy data.
- Restaurant names, ratings, rating counts, prices, delivery estimates, opening flags, offers, and coordinates are generated for demonstration.
- The latitude/longitude values are approximate points around Bengaluru area centroids and must not be presented as verified business addresses.
- Image URLs point to general food-photo images hosted by Unsplash and may need verification or replacement. They are not guaranteed to depict the exact listed dish.
- image_filename_placeholder values are intended as local image path placeholders; the image files are not included in this dataset ZIP.
- Check the applicable image license/terms before redistribution or commercial use.
- Do not use this dataset to claim real-world ratings, current prices, restaurant availability, or live delivery times.

Suggested use
1. Place the CSV file in your Django project's data/ directory.
2. Ask Antigravity to inspect the columns and build a repeatable Django management command to import records.
3. Use restaurant_id as the relation key between restaurant and menu item data.
4. Keep data_type=SYNTHETIC_DEMO visible in development/admin documentation.
