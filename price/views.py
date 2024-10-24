# price/views.py
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import NumberSerializer
from .models import ExchangeRate
from decimal import Decimal
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProductSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ExchangeRate , Product
from .serializers import ExchangeRateSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ExchangeRate
from .serializers import ExchangeRateSerializer

class GetExchangeRateView(generics.RetrieveAPIView):
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [AllowAny] 
class UpdateExchangeRateView(generics.UpdateAPIView):
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)  # Partial=True برای اینکه همه فیلدها اجباری نباشند
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ConvertPriceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # بررسی اینکه ورودی به صورت مستقیم عدد باشد
        if isinstance(request.data, int) or isinstance(request.data, float):
            data = {'price': request.data}
        elif 'price' in request.data:
            data = {'price': request.data['price']}
        else:
            return Response({'error': 'Invalid input'}, status=status.HTTP_400_BAD_REQUEST)
        
        # خواندن نرخ تبدیل، هزینه کشتی، درصد سود و هزینه هر کیلوگرم از دیتابیس
        exchange_rate = ExchangeRate.objects.first()
        if exchange_rate is None:
            return Response({'error': 'Exchange rate is not set'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = NumberSerializer(data=data)
        if serializer.is_valid():
            price = Decimal(serializer.validated_data['price'])
            
            # تبدیل قیمت
            converted_price = price * exchange_rate.aed_to_toman
            
            # محاسبه هزینه سود (بر اساس درصد سود)
            additional_cost = converted_price * (exchange_rate.profit_percentage / 100)
            
            # اگر وزن کالا در درخواست ارسال شده باشد، محاسبه هزینه حمل‌ونقل بر اساس وزن
            weight = Decimal(request.data.get('weight', 1))  # در صورتی که وزن ارسال نشده باشد، به‌صورت پیش‌فرض ۱ کیلوگرم در نظر می‌گیریم
            shipping_cost = exchange_rate.per_kg_cost * weight
            
            # محاسبه کل هزینه
            total_cost = converted_price + additional_cost + shipping_cost
            
            return Response({
                'converted_price': converted_price,
                'additional_cost': additional_cost,
                'shipping_cost': shipping_cost,
                'total_cost': total_cost
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_product(request):
    if request.method == 'POST':
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class ProductListView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
