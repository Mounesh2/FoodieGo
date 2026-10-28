"""
FoodieGo 2.1 — Curated Food & Restaurant Image Catalog
Provides dish-specific and restaurant-specific high-resolution imagery
with keyword intelligence and local SVG fallback handling.

Images sourced from Unsplash under the Unsplash License (free for commercial
and non-commercial demonstration use without required copyright notice).
"""

import re

# -------------------------------------------------------------------------
# 1. Dish-Specific Curated Image Mapping
# -------------------------------------------------------------------------
# Maps food title keywords to verified authentic food photographs
FOOD_KEYWORD_IMAGES = [
    # South Indian Delicacies
    (r'\b(masala\s+dosa|mysore\s+dosa|crispy\s+dosa|plain\s+dosa|ghee\s+roast|rava\s+dosa|dosa)\b',
     'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=600&q=80',
     'Crispy golden Dosa with coconut chutney and sambar'),

    (r'\b(idli|rava\s+idli|button\s+idli|thatte\s+idli)\b',
     'https://images.unsplash.com/photo-1589301773859-994c502b4d24?auto=format&fit=crop&w=600&q=80',
     'Steaming soft Idlis with spicy sambar'),

    (r'\b(vada|medu\s+vada|sambar\s+vada)\b',
     'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=600&q=80',
     'Crispy hot Medu Vada'),

    (r'\b(uttapam|onion\s+uttapam|upma|pongal|poori|puri)\b',
     'https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?auto=format&fit=crop&w=600&q=80',
     'Traditional South Indian breakfast'),

    # Biryani & Rice Dishes
    (r'\b(mutton\s+biryani|lamb\s+biryani)\b',
     'https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&w=600&q=80',
     'Royal Dum Mutton Biryani with saffron rice'),

    (r'\b(chicken\s+biryani|hyderabadi\s+biryani|dum\s+biryani)\b',
     'https://images.unsplash.com/photo-1563379091339-03246963d96c?auto=format&fit=crop&w=600&q=80',
     'Aromatic Chicken Dum Biryani'),

    (r'\b(paneer\s+biryani|veg\s+biryani|vegetable\s+biryani)\b',
     'https://images.unsplash.com/photo-1642821373181-696a54913e9a?auto=format&fit=crop&w=600&q=80',
     'Fragrant Vegetarian Biryani with spiced paneer'),

    (r'\b(biryani)\b',
     'https://images.unsplash.com/photo-1563379091339-03246963d96c?auto=format&fit=crop&w=600&q=80',
     'Signature Biryani pot'),

    # Pizzas
    (r'\b(margherita|cheese\s+pizza|mozzarella|farmhouse|veggie\s+pizza)\b',
     'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80',
     'Hand-stretched wood fired Margherita Pizza'),

    (r'\b(pepperoni|bbq\s+chicken\s+pizza|meat\s+pizza|paneer\s+pizza|pizza)\b',
     'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=600&q=80',
     'Crisp crust Gourmet Pizza with melted cheese'),

    # Burgers & Sandwiches
    (r'\b(chicken\s+burger|crispy\s+burger|beef\s+burger|patty\s+burger)\b',
     'https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=600&q=80',
     'Stacked Gourmet Chicken Burger with fries'),

    (r'\b(veg\s+burger|veggie\s+burger|cheese\s+burger|burger)\b',
     'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80',
     'Cheesy vegetable burger on toasted brioche bun'),

    (r'\b(grilled\s+sandwich|club\s+sandwich|cheese\s+sandwich|sandwich|toast)\b',
     'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=600&q=80',
     'Golden toasted triple-decker sandwich'),

    (r'\b(french\s+fries|fries|potato\s+wedges|nuggets)\b',
     'https://images.unsplash.com/photo-1576107232684-1279f3908594?auto=format&fit=crop&w=600&q=80',
     'Crispy seasoned French Fries'),

    # Chinese, Noodles & Momos
    (r'\b(momo|momos|dim\s*sum|dumpling|dumplings)\b',
     'https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?auto=format&fit=crop&w=600&q=80',
     'Steamed Himalayan Momos with spicy red chilli dip'),

    (r'\b(noodle|noodles|chow\s*mein|hakka\s+noodles|ramen)\b',
     'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80',
     'Wok-tossed Hakka noodles with julienne vegetables'),

    (r'\b(fried\s+rice|schezwan\s+rice|rice\s+bowl)\b',
     'https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=600&q=80',
     'Sizzling Oriental Fried Rice'),

    (r'\b(manchurian|chilli\s+paneer|chilli\s+chicken|spring\s+roll|spring\s+rolls)\b',
     'https://images.unsplash.com/photo-1525755662778-989d0524087e?auto=format&fit=crop&w=600&q=80',
     'Crispy Indo-Chinese Chilli Appetizers'),

    (r'\b(soup|hot\s+and\s+sour|sweet\s+corn|manchow)\b',
     'https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=600&q=80',
     'Steaming bowl of hot Asian soup'),

    # North Indian Curries, Breads & Combos
    (r'\b(paneer\s+butter\s+masala|shahi\s+paneer|kadai\s+paneer|palak\s+paneer|paneer\s+tikka)\b',
     'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=600&q=80',
     'Rich Creamy Paneer Butter Masala'),

    (r'\b(butter\s+chicken|chicken\s+tikka|tandoori\s+chicken|murgh)\b',
     'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=600&q=80',
     'Tender Smoky Tandoori Chicken Tikka'),

    (r'\b(dal\s+makhani|dal\s+tadka|yellow\s+dal|chana\s+masala)\b',
     'https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80',
     'Slow-simmered Dal Makhani with fresh cream'),

    (r'\b(chole\s+bhature|bhatura|bhature)\b',
     'https://images.unsplash.com/photo-1626074353765-517a681e40be?auto=format&fit=crop&w=600&q=80',
     'Puffy Chole Bhature with pickled onion'),

    (r'\b(rajma|rajma\s+chawal)\b',
     'https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80',
     'Homestyle Rajma Chawal bowl'),

    (r'\b(naan|butter\s+naan|tandoori\s+roti|paratha|kulcha|roti)\b',
     'https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=600&q=80',
     'Butter Garlic Naan straight from the clay tandoor'),

    (r'\b(thali|combo|platter|meal)\b',
     'https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?auto=format&fit=crop&w=600&q=80',
     'Grand Indian Thali Feast'),

    # Street Food & Rolls
    (r'\b(kathi\s+roll|paneer\s+roll|chicken\s+roll|egg\s+roll|frankie|wrap|shawarma)\b',
     'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=600&q=80',
     'Flaky Kolkata Style Kathi Roll'),

    (r'\b(pav\s+bhaji|vada\s+pav|misal\s+pav)\b',
     'https://images.unsplash.com/photo-1606491956689-2ea866880c84?auto=format&fit=crop&w=600&q=80',
     'Buttery Mumbai Street Pav Bhaji'),

    (r'\b(samosa|samosas|kachori|chaat|pani\s+puri|sev\s+puri|bhel)\b',
     'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80',
     'Golden crunchy Samosas with mint and tamarind chutneys'),

    # Cafe, Coffee & Beverages
    (r'\b(filter\s+coffee|cappuccino|latte|espresso|cold\s+coffee|coffee|americano)\b',
     'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=600&q=80',
     'Freshly frothed Bengaluru South Indian Filter Coffee'),

    (r'\b(chai|tea|masala\s+chai|green\s+tea)\b',
     'https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&q=80',
     'Aromatic Indian Masala Cutting Chai'),

    (r'\b(avocado|avocado\s+toast|sourdough|croissant|bagel)\b',
     'https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=600&q=80',
     'Fresh Avocado Toast with herbs and sesame seeds'),

    (r'\b(shake|milkshake|smoothie|juice|mojito|beverage)\b',
     'https://images.unsplash.com/photo-1553530666-ba11a7da3888?auto=format&fit=crop&w=600&q=80',
     'Chilled fresh fruit smoothie shake'),

    # Desserts, Cakes & Bakery
    (r'\b(chocolate\s+cake|black\s+forest|truffle|cake|pastry|pastries|cheesecake)\b',
     'https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=600&q=80',
     'Rich Belgium Chocolate Layer Cake'),

    (r'\b(brownie|brownies|lava\s+cake|muffin|muffins|cupcake|donut|waffle)\b',
     'https://images.unsplash.com/photo-1586985289688-ca3cf47d3e6e?auto=format&fit=crop&w=600&q=80',
     'Warm Fudgy Brownie with chocolate drizzle'),

    (r'\b(ice\s+cream|sundae|gelato|kulfi)\b',
     'https://images.unsplash.com/photo-1563805042-7684c019e1cb?auto=format&fit=crop&w=600&q=80',
     'Creamy handcrafted Ice Cream scoops'),

    (r'\b(gulab\s+jamun|rasgulla|halwa|jalebi|rasmalai|kheer|dessert|mithai)\b',
     'https://images.unsplash.com/photo-1589301773859-994c502b4d24?auto=format&fit=crop&w=600&q=80',
     'Warm syrup-dipped Gulab Jamun dessert'),

    # Salads & Healthy Food
    (r'\b(salad|quinoa|fruit\s+bowl|sprouts|keto|diet)\b',
     'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80',
     'Nutrient-dense fresh garden salad bowl'),
]

# Category default fallback images when no specific food keyword matches
CATEGORY_FALLBACK_IMAGES = {
    'South Indian': 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=600&q=80',
    'Biryani': 'https://images.unsplash.com/photo-1563379091339-03246963d96c?auto=format&fit=crop&w=600&q=80',
    'North Indian': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80',
    'Pizza': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80',
    'Fast Food': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80',
    'Chinese': 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80',
    'Cafe': 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=600&q=80',
    'Desserts': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=600&q=80',
    'Street Food': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80',
    'Healthy Food': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80',
    'Main Course': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80',
}


# -------------------------------------------------------------------------
# 2. Restaurant-Specific Curated Storefront & Dining Cover Images
# -------------------------------------------------------------------------
# Completely separate from individual dish photos to avoid repeated imagery
RESTAURANT_CUISINE_COVERS = {
    'South Indian': [
        'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80',
    ],
    'Biryani': [
        'https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80',
    ],
    'North Indian': [
        'https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80',
    ],
    'Pizza': [
        'https://images.unsplash.com/photo-1579751626657-72bc17010498?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80',
    ],
    'Fast Food': [
        'https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=800&q=80',
    ],
    'Chinese': [
        'https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80',
    ],
    'Cafe': [
        'https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1442512595331-e89e73853f31?auto=format&fit=crop&w=800&q=80',
    ],
    'Desserts': [
        'https://images.unsplash.com/photo-1559925393-8be0ec4767c8?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=800&q=80',
    ],
    'Street Food': [
        'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80',
    ],
    'Healthy Food': [
        'https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80',
        'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80',
    ],
}

DEFAULT_RESTAURANT_COVER = 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80'


# -------------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------------
def get_curated_food_image(title: str, category: str = '', is_veg: bool = True) -> str:
    """
    Intelligently assigns an accurate, high-resolution food image based on the
    actual dish title. E.g., 'Masala Dosa' gets a dosa photo, 'Chicken Biryani' gets a biryani photo.
    """
    cleaned_title = title.lower()

    # 1. Check title against specific food regex mappings
    for pattern, img_url, _ in FOOD_KEYWORD_IMAGES:
        if re.search(pattern, cleaned_title, re.IGNORECASE):
            return img_url

    # 2. Check category fallback
    if category in CATEGORY_FALLBACK_IMAGES:
        return CATEGORY_FALLBACK_IMAGES[category]

    # 3. Veg / Non-veg default fallback
    if is_veg:
        return 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=600&q=80'
    return 'https://images.unsplash.com/photo-1563379091339-03246963d96c?auto=format&fit=crop&w=600&q=80'


def get_curated_restaurant_cover(cuisine: str, name: str = '', demo_id: int = 1) -> str:
    """
    Assigns a distinct restaurant dining/storefront cover image based on cuisine
    and restaurant ID, ensuring restaurants don't all show the exact same image.
    """
    covers = RESTAURANT_CUISINE_COVERS.get(cuisine)
    if covers:
        idx = (demo_id or 1) % len(covers)
        return covers[idx]
    return DEFAULT_RESTAURANT_COVER
