from django.contrib import admin
from .models import ScrapeData

# Register your models here.

@admin.register(ScrapeData)
class ScrapeDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
