from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLE_CHOICES = (
        ('CUSTOMER', 'Customer'),
        ('RESTAURANT', 'Restaurant Staff'),
        ('DELIVERY', 'Delivery Partner'),
        ('ADMIN', 'Platform Administrator'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER', db_index=True)
    restaurant = models.ForeignKey('main.Restaurant', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_profiles')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='Bengaluru, Karnataka')
    is_available = models.BooleanField(default=True)  # For delivery partners on duty
    vehicle_type = models.CharField(max_length=50, blank=True, default='Motorcycle')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_restaurant_staff(self):
        return self.role == 'RESTAURANT' or self.user.is_superuser or self.user.groups.filter(name='admin_owner').exists()

    @property
    def is_delivery_partner(self):
        return self.role == 'DELIVERY' or self.user.groups.filter(name='delivery_partner').exists()

    @property
    def is_admin(self):
        return self.role == 'ADMIN' or self.user.is_superuser or self.user.is_staff


class CustomerAddress(models.Model):
    ADDRESS_TYPES = (
        ('Home', 'Home'),
        ('Work', 'Work'),
        ('Other', 'Other'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_addresses')
    title = models.CharField(max_length=50, choices=ADDRESS_TYPES, default='Home')
    address_line = models.TextField()
    landmark = models.CharField(max_length=150, blank=True, default='')
    area = models.CharField(max_length=100, default='Koramangala')
    city = models.CharField(max_length=50, default='Bengaluru')
    pincode = models.CharField(max_length=10, default='560034')
    phone = models.CharField(max_length=20, blank=True, default='')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = 'Customer Address'
        verbose_name_plural = 'Customer Addresses'

    def __str__(self):
        return f"{self.title}: {self.address_line[:40]} ({self.area})"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Clear default flag on user's other addresses
            CustomerAddress.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'ADMIN' if instance.is_superuser else 'CUSTOMER'
        Profile.objects.get_or_create(user=instance, defaults={'role': role})
    else:
        Profile.objects.get_or_create(user=instance)

