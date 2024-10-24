# price/models.py

from django.db import models
from django.utils import timezone
class ExchangeRate(models.Model):
    aed_to_toman = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    profit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=25.00)  # درصد سود
    per_kg_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # هزینه برای هر کیلوگرم

    def __str__(self):
        return f'{self.aed_to_toman} Toman per AED, Shipping Cost: {self.shipping_cost} Toman, Profit: {self.profit_percentage}%'

class Address(models.Model):
    city = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    postalcode = models.CharField(max_length=255)
    address_detail = models.TextField()

    def __str__(self):
        return f'{self.city}, {self.province} - {self.address_detail}'

from django.db import models
from django.utils import timezone

class Product(models.Model):
    STATUS_CHOICES = [
        ('Processing', 'Processing'),
        ('Confirmed', 'Confirmed'),
        ('Failed', 'Failed'),
    ]

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    national_code = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=255)
    address = models.OneToOneField(Address, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    product_image = models.CharField(max_length=255)
    product_link = models.TextField()
    price_in_dirhams = models.DecimalField(max_digits=10, decimal_places=2)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=255)
    color = models.CharField(max_length=255)
    flavor = models.CharField(max_length=255)
    product_count = models.IntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Failed')

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.product_name}'
