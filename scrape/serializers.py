from rest_framework import serializers
from .models import ScrapeData
from decimal import Decimal, ROUND_HALF_UP
from price.models import ExchangeRate

class ScrapeDataSerializer(serializers.ModelSerializer):
    converted_price = serializers.SerializerMethodField()
    additional_cost = serializers.SerializerMethodField()
    shipping_cost = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = ScrapeData
        fields = '__all__'

    def get_exchange_rate(self):
        # دریافت نرخ تبادل به صورت هم‌زمان
        return ExchangeRate.objects.first()

    def get_converted_price(self, obj):
        try:
            exchange_rate = self.get_exchange_rate()
            if exchange_rate is None:
                return None
            
            price = Decimal(obj.response_data.get('results', {}).get('price', '0.0'))
            converted_price = price * exchange_rate.aed_to_toman
            precision = Decimal('0.01')
            converted_price = converted_price.quantize(precision, rounding=ROUND_HALF_UP)
            return str(converted_price)
        except Exception as e:
            return None

    def get_additional_cost(self, obj):
        try:
            converted_price = Decimal(self.get_converted_price(obj) or '0.0')
            additional_cost = converted_price * Decimal('0.25')
            precision = Decimal('0.01')
            additional_cost = additional_cost.quantize(precision, rounding=ROUND_HALF_UP)
            return str(additional_cost)
        except Exception as e:
            return None

    def get_shipping_cost(self, obj):
        try:
            exchange_rate = self.get_exchange_rate()
            if exchange_rate is None:
                return None
            shipping_cost = Decimal(exchange_rate.shipping_cost)
            precision = Decimal('0.01')
            shipping_cost = shipping_cost.quantize(precision, rounding=ROUND_HALF_UP)
            return str(shipping_cost)
        except Exception as e:
            return None

    def get_total_cost(self, obj):
        try:
            converted_price = Decimal(self.get_converted_price(obj) or '0.0')
            additional_cost = Decimal(self.get_additional_cost(obj) or '0.0')
            shipping_cost = Decimal(self.get_shipping_cost(obj) or '0.0')
            total_cost = converted_price + additional_cost + shipping_cost
            precision = Decimal('0.01')
            total_cost = total_cost.quantize(precision, rounding=ROUND_HALF_UP)
            return str(total_cost)
        except Exception as e:
            return None
