# FoodieGo Dataset Documentation

## Overview
This directory contains the representative dataset used by FoodieGo for Bengaluru restaurant and menu item cataloging.

## Data Files
- `FoodieGo_Restaurants_with_Image_Links.csv`: 100 curated restaurant profiles across key Bengaluru localities (Koramangala, Indiranagar, HSR Layout, Whitefield, Jayanagar, BTM Layout, JP Nagar, Peenya, etc.), including cuisines, ratings, delivery times, and representative restaurant cover photos.
- `FoodieGo_Menu_Items_with_Image_Links.csv`: 10,000 menu items across various cuisines (Biryani, Dosa, North Indian, Chinese, Burgers, Pizza, Desserts, Beverages), linked by `restaurant_id` with vegetarian status, pricing, and category food photography.
- `FoodieGo_Image_Links_Added.xlsx`: Source multi-sheet spreadsheet containing restaurants, dishes, and image mapping metadata.
- `bengaluru_restaurants_100_demo.csv` & `bengaluru_menu_items_10000_demo.csv`: Baseline catalog files.

## Dataset Provenance & Ethics
- **Representative Data**: The restaurant names, dishes, pricing, ratings, and locations are synthetic, structured data generated for educational, demonstration, and portfolio purposes. They do not represent real-world commercial entities or live Swiggy partner contracts.
- **Imagery**: Photographs are curated, high-resolution food category imagery from Unsplash under the Unsplash License. They represent general culinary categories and dish styles rather than proprietary photographs of physical kitchen locations.

## Import & Update Commands
To sync or refresh image URLs from the CSV files into the database:
```bash
python manage.py update_images_from_csv
```
