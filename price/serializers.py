# price/serializers.py
from rest_framework import serializers
from .models import Product, Address , ExchangeRate
from rest_framework import serializers
from .models import ExchangeRate

class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ['aed_to_toman', 'shipping_cost', 'profit_percentage', 'per_kg_cost']

class NumberSerializer(serializers.Serializer):
    price = serializers.FloatField()

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id','city', 'province', 'address_detail' , 'postalcode']

class ProductSerializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        address = Address.objects.create(**address_data)
        product = Product.objects.create(address=address, **validated_data)
        return product