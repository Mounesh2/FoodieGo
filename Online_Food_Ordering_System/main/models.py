from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django.utils import timezone
from django.contrib.auth.models import User

class Restaurant(models.Model):
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_restaurants')
    demo_id = models.IntegerField(unique=True, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True)
    area = models.CharField(max_length=150, db_index=True)
    city = models.CharField(max_length=100, default='Bengaluru')
    state = models.CharField(max_length=100, default='Karnataka')
    cuisine = models.CharField(max_length=150, db_index=True)
    rating = models.FloatField(default=4.0)
    rating_count = models.IntegerField(default=0)
    average_cost_for_two = models.FloatField(default=300.0)
    estimated_delivery_minutes = models.IntegerField(default=30)
    delivery_fee = models.FloatField(default=0.0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_open = models.BooleanField(default=True)
    opening_time = models.CharField(max_length=20, default='08:00 AM')
    closing_time = models.CharField(max_length=20, default='11:00 PM')
    contact_phone = models.CharField(max_length=30, blank=True, default='+91 80 2345 6789')
    address_details = models.TextField(blank=True, default='')
    is_approved = models.BooleanField(default=True)
    image_url = models.URLField(max_length=500, blank=True, default='')
    image = models.ImageField(upload_to='restaurant_images/', blank=True, null=True)
    data_type = models.CharField(max_length=50, default='SYNTHETIC_DEMO')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-rating', 'name']
        verbose_name = 'Restaurant'
        verbose_name_plural = 'Restaurants'

    def __str__(self):
        return f"{self.name} ({self.area})"

    def get_absolute_url(self):
        return reverse("main:restaurant_detail", kwargs={'slug': self.slug})

    @property
    def get_display_image(self):
        if self.image_url and self.image_url.strip():
            return self.image_url
        if self.image and hasattr(self.image, 'url'):
            try:
                return self.image.url
            except Exception:
                pass
        return '/static/images/fallback_restaurant.svg'

    @property
    def get_image_url(self):
        return self.get_display_image


class Item(models.Model):
    LABELS = (
        ('Best Selling Foods', 'Best Selling Foods'),
        ('New Food', 'New Food'),
        ('Spicy Foods🔥', 'Spicy Foods🔥'),
    )   

    LABEL_COLOUR = (
        ('danger', 'danger'),
        ('success', 'success'),
        ('primary', 'primary'),
        ('info', 'info'),
        ('warning', 'warning'),
    )

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    price = models.FloatField()
    pieces = models.IntegerField(default=6)
    instructions = models.CharField(max_length=250, default="Available")
    image = models.ImageField(default='default.png', upload_to='images/', blank=True)
    labels = models.CharField(max_length=50, choices=LABELS, blank=True)
    label_colour = models.CharField(max_length=20, choices=LABEL_COLOUR, blank=True)
    slug = models.SlugField(max_length=250, default="foods")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Bengaluru Demo Dataset extension fields
    category = models.CharField(max_length=100, default='Main Course', blank=True, db_index=True)
    is_veg = models.BooleanField(default=True)
    rating = models.FloatField(default=4.0)
    is_available = models.BooleanField(default=True)
    discount_percent = models.IntegerField(default=0)
    food_image_url = models.URLField(max_length=500, blank=True, default='')
    offer_label = models.CharField(max_length=100, blank=True, default='')
    demo_id = models.IntegerField(unique=True, null=True, blank=True, db_index=True)
    data_type = models.CharField(max_length=50, default='USER_CREATED')

    class Meta:
        ordering = ['-rating', 'title']
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("main:dishes", kwargs={'slug': self.slug})
    
    def get_add_to_cart_url(self):
        return reverse("main:add-to-cart", kwargs={'slug': self.slug})

    def get_item_delete_url(self):
        return reverse("main:item-delete", kwargs={'slug': self.slug})

    def get_update_item_url(self):
        return reverse("main:item-update", kwargs={'slug': self.slug})

    @property
    def get_display_image(self):
        if self.food_image_url and self.food_image_url.strip():
            return self.food_image_url
        if self.image and hasattr(self.image, 'url'):
            try:
                return self.image.url
            except Exception:
                pass
        return '/static/images/fallback_food.svg'

    @property
    def get_image_url(self):
        return self.get_display_image


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    discount_percent = models.IntegerField(default=20)
    discount_amount = models.FloatField(default=0.0)  # Flat discount if percent is 0
    min_order_amount = models.FloatField(default=200.0)
    max_discount_amount = models.FloatField(default=100.0)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Coupon / Promotional Offer'
        verbose_name_plural = 'Coupons & Promotional Offers'

    def __str__(self):
        return f"{self.code} - {self.title}"

    def is_valid_for(self, subtotal):
        if not self.is_active:
            return False, "This coupon is no longer active."
        now = timezone.now()
        if self.valid_to and now > self.valid_to:
            return False, "This coupon has expired."
        if now < self.valid_from:
            return False, "This coupon is not yet active."
        if subtotal < self.min_order_amount:
            return False, f"Minimum order value of ₹{self.min_order_amount:.0f} required for {self.code}."
        return True, "Valid coupon"

    def calculate_discount(self, subtotal):
        valid, _ = self.is_valid_for(subtotal)
        if not valid:
            return 0.0
        if self.discount_percent > 0:
            disc = (subtotal * self.discount_percent) / 100.0
            return round(min(disc, self.max_discount_amount), 2)
        return round(min(self.discount_amount, subtotal), 2)


class Order(models.Model):
    ORDER_STATUS = (
        ('Confirmed', 'Confirmed'),
        ('Accepted', 'Accepted'),
        ('Preparing', 'Preparing'),
        ('Ready for Pickup', 'Ready for Pickup'),
        ('Picked Up', 'Picked Up'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Active', 'Active'),  # For backwards compatibility with initial orders
    )
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    assigned_delivery_partner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_deliveries')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_orders')
    discount_amount = models.FloatField(default=0.0)
    delivery_address = models.TextField(default='Bengaluru, Karnataka')
    contact_phone = models.CharField(max_length=30, blank=True, default='')
    order_instructions = models.CharField(max_length=255, blank=True, default='')
    subtotal = models.FloatField(default=0.0)
    delivery_fee = models.FloatField(default=0.0)
    tax_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    status = models.CharField(max_length=30, choices=ORDER_STATUS, default='Confirmed', db_index=True)
    payment_method = models.CharField(max_length=50, default='Cash on Delivery (DEMO)')
    is_paid = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    rejection_reason = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    accepted_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"Order #{self.order_number} ({self.user.username}) - {self.status}"

    @property
    def can_be_cancelled(self):
        # Customer can cancel only if still in 'Confirmed' or 'Active' state before restaurant starts preparing
        return self.status in ['Confirmed', 'Active']


class OrderItem(models.Model):
    """
    Immutable historical snapshot of items ordered.
    Ensures later price/dish edits on restaurant menu never alter past receipts.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='historical_order_items')
    item_title = models.CharField(max_length=200)
    item_price = models.FloatField()
    quantity = models.IntegerField(default=1)
    subtotal = models.FloatField()
    is_veg = models.BooleanField(default=True)
    food_image_url = models.URLField(max_length=500, blank=True, default='')

    class Meta:
        verbose_name = 'Order Line Item Snapshot'
        verbose_name_plural = 'Order Line Item Snapshots'

    def __str__(self):
        return f"{self.quantity}x {self.item_title} (Order #{self.order.order_number})"


class Reviews(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    rslug = models.SlugField(max_length=250)
    review = models.TextField()
    rating = models.IntegerField(default=5)
    posted_on = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'

    def __str__(self):
        return f"{self.user.username} on {self.item.title}: {self.review[:30]}"


class CartItems(models.Model):
    ORDER_STATUS = (
        ('Active', 'Active'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_items')
    ordered = models.BooleanField(default=False)
    quantity = models.IntegerField(default=1)
    ordered_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='Active')
    delivery_date = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f"{self.quantity}x {self.item.title} ({self.user.username})"
    
    def get_remove_from_cart_url(self):
        return reverse("main:remove-from-cart", kwargs={'pk': self.pk})

    def update_status_url(self):
        return reverse("main:update_status", kwargs={'pk': self.pk})

    @property
    def subtotal(self):
        return round(self.quantity * self.item.price, 2)
