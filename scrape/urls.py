from django.urls import path
from .views import ScrapeView, ScrapeDataDetailView, ScrapeNamshiView

urlpatterns = [
    path('', ScrapeView.as_view(), name='scrape'),
    path('detail/<uuid:id>/', ScrapeDataDetailView.as_view(), name='scrape-detail'),
    path('namshi/', ScrapeNamshiView.as_view(), name='scrape-namshi'),
]