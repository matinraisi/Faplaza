from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import json
from .models import ScrapeData
from price.models import ExchangeRate
from selenium.common.exceptions import (NoSuchElementException as NSEE, TimeoutException as TOE, 
                                         NoSuchWindowException as NSWE, WebDriverException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from playwright.sync_api import sync_playwright

class ScrapeView(APIView):

    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        color = request.data.get('color')
        size = request.data.get('size')
        style = request.data.get('style')
        flavor = request.data.get('Flavor')

        # بررسی اینکه تمام فیلدها وجود دارند
        if not all([url, color, size, style, flavor]):
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # ارسال درخواست به API خارجی
            response = requests.post('http://185.80.196.109:5049/scrape', json={
                "url": url,
                "color": color,
                "size": size,
                "style": style,
                "Flavor": flavor
            })
            response.raise_for_status()  # بررسی وضعیت پاسخ
            response_data = response.json()  # تجزیه داده‌ها به فرمت JSON
        except requests.exceptions.RequestException as e:
            return Response({'error': f'Request failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON response from the server.'}, status=status.HTTP_400_BAD_REQUEST)

        # ذخیره یا بروزرسانی داده‌ها در مدل
        scrape_data, created = ScrapeData.objects.update_or_create(
            url=url,
            defaults={
                'color': color,
                'size': size,
                'style': style,
                'flavor': flavor,
                'response_data': json.dumps(response_data)  # ذخیره داده‌ها به صورت JSON
            }
        )

        try:
            # دریافت نرخ ارز و دیگر مقادیر
            exchange_rate = ExchangeRate.objects.first()
            if exchange_rate is None:
                return Response({'error': 'Exchange rate not set'}, status=status.HTTP_400_BAD_REQUEST)

            # فقط مقادیر ثبت‌شده در مدل ExchangeRate را باز می‌گردانیم
            converted_price = exchange_rate.aed_to_toman
            additional_cost = exchange_rate.profit_percentage
            shipping_cost = exchange_rate.shipping_cost
            per_kg_cost = exchange_rate.per_kg_cost
        except Exception as e:
            return Response({'error': f'Error processing data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # تبدیل داده‌ها به فرمت خروجی
        result = {
            'id': str(scrape_data.id),
            'price': response_data.get('results', {}).get('price', 'Unknown'),  # قیمت اولیه
            'images': response_data.get('results', {}).get('images', []),
            'title': response_data.get('results', {}).get('title', ''),
            'color': response_data.get('results', {}).get('color', []),
            'styles': response_data.get('results', {}).get('styles', []),
            'sizes': response_data.get('results', {}).get('sizes', []),
            'Flavor': response_data.get('results', {}).get('Flavor', []),
            'available': response_data.get('results', {}).get('available'),
            'weight': response_data.get('results', {}).get('weight', 'Unknown'),  # اضافه کردن وزن
            # مقادیر ذخیره‌شده در مدل
            'aed_to_toman': str(converted_price),
            'profit_percentage': str(additional_cost),
            'shipping_cost': str(shipping_cost),
            'per_kg_cost': str(per_kg_cost),
        }

        return Response({'results': result}, status=status.HTTP_200_OK)

class ScrapeNamshiView(APIView):
    def post(self, request, *args, **kwargs):
        url = request.data.get('url')

        if not url:
            return Response({'error': 'URL is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = namshi(url)
            if not data:
                return Response({'error': 'Failed to retrieve data from Namshi.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # دریافت نرخ ارز
                exchange_rate = ExchangeRate.objects.first()
                if exchange_rate is None:
                    return Response({'error': 'Exchange rate not set'}, status=status.HTTP_400_BAD_REQUEST)

                # محاسبه قیمت تبدیل‌شده و هزینه‌ها
                price = Decimal(data.get('price', '0.0').replace('د.إ.', '').strip())
                # converted_price = price * exchange_rate.aed_to_toman
                # additional_cost = converted_price * Decimal('0.25')
                # shipping_cost = exchange_rate.shipping_cost
                # total_cost = converted_price + additional_cost + shipping_cost
                converted_price = exchange_rate.aed_to_toman
                additional_cost = exchange_rate.profit_percentage
                shipping_cost = exchange_rate.shipping_cost
                per_kg_cost = exchange_rate.per_kg_cost
            except Exception as e:
                return Response({'error': f'Error processing data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            scrape_data, created = ScrapeData.objects.update_or_create(
                url=url,
                defaults={
                    'color': data.get('color_source', []),
                    'size': data.get('size', []),
                    'style': [],  # این بخش برای Namshi استفاده نمی‌شود
                    'flavor': [],  # این بخش برای Namshi استفاده نمی‌شود
                    'response_data': json.dumps(data)  # ذخیره داده‌ها به صورت JSON
                }
            )

            result = {
                'id': scrape_data.id,
                'images': data.get('picture', []),
                'title': data.get('name', ''),
                'color': data.get('color_source', []),
                'styles': [],  # این بخش برای Namshi استفاده نمی‌شود
                'sizes': data.get('size', []),
                'flavor': [],  # این بخش برای Namshi استفاده نمی‌شود
                'available': None,  # این اطلاعات از Namshi دریافت نمی‌شود
                'weight': 'Not Found',
                'price' : data.get('price',''),
                'aed_to_toman': str(converted_price),
                'profit_percentage': str(additional_cost),
                'shipping_cost': str(shipping_cost),
                'per_kg_cost': str(per_kg_cost),
            }

            return Response({'results': result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def namshi(url):
    def products(browser):
        page = browser.new_page()
        page.set_default_timeout(60000)  # Set timeout to 60 seconds

        try:
            page.goto(url)
            page.wait_for_selector('h1')  # Wait for the title to ensure the page has loaded
            
            brand = page.query_selector('.ProductConversion_brand__Y76P_').inner_text().strip()
            name = page.query_selector('h1').inner_text().strip()
            price = page.query_selector('section span span:nth-child(2)').inner_text().replace('\n', ' ')

            size_elements = page.query_selector_all('.SizePills_size_variant__4qpXf')
            size = [size.inner_text().strip() for size in size_elements]

            color = []
            color_page = []
            color_elements = page.query_selector_all('.ProductConversion_groupImages__4tRb8 img')
            color.extend([color_elem.get_attribute('src') for color_elem in color_elements])

            picture_elements = page.query_selector_all('.ImageGallery_container__cNIDV img')
            picture = [pic_elem.get_attribute('src') for pic_elem in picture_elements]

            return {
                'brand': brand,
                'name': name,
                'price': price,
                'size': size,
                'color_source': color,
                'picture': picture,
            }

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
        finally:
            page.close()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Launch headless browser
        try:
            return products(browser)
        finally:
            browser.close()

class ScrapeDataDetailView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            instance = ScrapeData.objects.get(id=kwargs.get('id'))
        except ScrapeData.DoesNotExist:
            return Response({'error': 'ScrapeData not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        # اطمینان از اینکه response_data به دیکشنری تبدیل شده است
        try:
            response_data = json.loads(instance.response_data)
        except (TypeError, json.JSONDecodeError) as e:
            return Response({'error': 'Invalid JSON data: ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            exchange_rate = ExchangeRate.objects.first()
            if exchange_rate is None:
                return Response({'error': 'Exchange rate not set'}, status=status.HTTP_400_BAD_REQUEST)

            price = Decimal(response_data.get('price', '0.0'))
            converted_price = price * exchange_rate.aed_to_toman
            additional_cost = converted_price * Decimal('0.25')
            shipping_cost = exchange_rate.shipping_cost
            total_cost = converted_price + additional_cost + shipping_cost
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        result = {
            'id': instance.id,
            'price': response_data.get('price'),
            'images': response_data.get('images'),
            'title': response_data.get('title'),
            'color': response_data.get('color'),
            'styles': response_data.get('styles'),
            'sizes': response_data.get('sizes'),
            'flavor': response_data.get('flavor'),
            'available': response_data.get('available'),
            'aed_to_toman': str(converted_price),
            'profit_percentage': str(additional_cost),
            'shipping_cost': str(shipping_cost),
            'per_kg_cost': str(total_cost)
        }

        return Response({'results': result}, status=status.HTTP_200_OK)
