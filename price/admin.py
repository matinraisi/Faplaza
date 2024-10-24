# price/admin.py

from django.contrib import admin
from .models import ExchangeRate , Product

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('aed_to_toman', 'shipping_cost')
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'first_name' , 'address')
