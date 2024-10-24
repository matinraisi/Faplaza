from django.urls import path
from .views import ConvertPriceView, create_product , UpdateExchangeRateView,ProductListView,ProductDetailView ,GetExchangeRateView

urlpatterns = [
    path('price/convert/', ConvertPriceView.as_view(), name='convert-price'),
    path('create_product/', create_product, name='create_product'),
    path('exchange-rate/<int:pk>/', UpdateExchangeRateView.as_view(), name='update_exchange_rate'),
    path('rate/<int:pk>/', GetExchangeRateView.as_view(), name='GetExchangeRateView'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]
