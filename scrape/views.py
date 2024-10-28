from decimal import Decimal
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import json
from .models import ScrapeData
from price.models import ExchangeRate
from .serializers import ScrapeDataSerializer
from selenium.common.exceptions import (NoSuchElementException as NSEE, TimeoutException as TOE, 
                                         NoSuchWindowException as NSWE, InvalidArgumentException as IAE, WebDriverException,StaleElementReferenceException as SERE,)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import time

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
            # دریافت نرخ ارز
            exchange_rate = ExchangeRate.objects.first()
            if exchange_rate is None:
                return Response({'error': 'Exchange rate not set'}, status=status.HTTP_400_BAD_REQUEST)

            # محاسبه قیمت تبدیل‌شده و هزینه‌ها
            price = Decimal(response_data.get('results', {}).get('price', '0.0'))
            converted_price = price * exchange_rate.aed_to_toman
            additional_cost = converted_price * Decimal('0.25')
            shipping_cost = exchange_rate.shipping_cost
            total_cost = converted_price + additional_cost + shipping_cost
        except Exception as e:
            return Response({'error': f'Error processing data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # تبدیل داده‌ها به فرمت مشابه با خروجی Namshi
        result = {
            'id': str(scrape_data.id),
            'price': str(price),
            'images': response_data.get('results', {}).get('images', []),
            'title': response_data.get('results', {}).get('title', ''),
            'color': response_data.get('results', {}).get('color', []),
            'styles': response_data.get('results', {}).get('styles', []),
            'sizes': response_data.get('results', {}).get('sizes', []),
            'Flavor': response_data.get('results', {}).get('Flavor', []),
            'available': response_data.get('results', {}).get('available'),
            'converted_price': str(converted_price),
            'additional_cost': str(additional_cost),
            'shipping_cost': str(shipping_cost),
            'total_cost': str(total_cost)
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
                # Fetch the exchange rate
                exchange_rate = ExchangeRate.objects.first()
                if exchange_rate is None:
                    return Response({'error': 'Exchange rate not set'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate the converted price and additional costs
                price = Decimal(data.get('price', '0.0').replace('د.إ.', '').strip())
                converted_price = price * exchange_rate.aed_to_toman
                additional_cost = converted_price * Decimal('0.25')
                shipping_cost = exchange_rate.shipping_cost
                total_cost = converted_price + additional_cost + shipping_cost
            except Exception as e:
                return Response({'error': f'Error processing data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            # Save scraped data
            scrape_data, created = ScrapeData.objects.update_or_create(
                url=url,
                defaults={
                    'color': data.get('color_source', []),
                    'size': data.get('size', []),
                    'style': [],  # Not used for Namshi
                    'flavor': [],  # Not used for Namshi
                    'response_data': json.dumps(data)  # Save data as JSON
                }
            )

            # Prepare the result
            result = {
                'id': scrape_data.id,
                'images': data.get('picture', []),
                'title': data.get('name', ''),
                'color': data.get('color_source', []),
                'styles': [],  # Not used for Namshi
                'sizes': data.get('size', []),
                'flavor': [],  # Not used for Namshi
                'available': None,  # Not provided by Namshi
                'weight': 'Not Found',
                'converted_price': str(converted_price),
                'additional_cost': str(additional_cost),
                'shipping_cost': str(shipping_cost),
                'total_cost': str(total_cost)
            }

            return Response({'results': result}, status=status.HTTP_200_OK)
        except (TOE, SERE, WebDriverException) as e:
            return Response({'error': f'Web scraping error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': f'Unexpected error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def namshi(url):
    driver = None

    def driver_init(retry_count=3):
        nonlocal driver
        options = Options()
        options.add_argument("--headless")
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1366x768')
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-popup-blocking")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        for attempt in range(retry_count):
            try:
                driver = webdriver.Chrome(options=options)
                driver.set_page_load_timeout(90)  # Increase timeout
                driver.get(url)
                end = driver.find_element(By.XPATH, '/html/body/section/section/section/div[2]/div[1]/div/div/div[1]')
                actions = ActionChains(driver)
                actions.scroll_to_element(end).perform()
                break
            except (TOE, WebDriverException) as e:
                if driver:
                    driver.quit()
                if attempt < retry_count - 1:
                    time.sleep(5)  # Wait before retrying
                    continue
                raise Exception(f"Error initializing the driver: {str(e)}")
        return driver

    def products():
        try:
            brand = driver.find_element(By.CLASS_NAME, 'ProductConversion_brand__Y76P_').text.strip()
            name = driver.find_element(By.XPATH, '/html/body/section/section/section/section/div/div[2]/section[1]/section[1]/div/div[1]/h1').text.strip()
            price = driver.find_element(By.XPATH, '/html/body/section/section/section/section/div/div[2]/section[1]/section[1]/section/div[1]/section/span/span[2]').text.replace('\n', ' ')

            size_div = driver.find_elements(By.XPATH, '/html/body/section/section/section/section/div/div[2]/section[1]/div[1]/div[2]/div')
            size = [_.text.strip() for size1 in size_div for _ in size1.find_elements(By.CLASS_NAME, 'SizePills_size_variant__4qpXf')]

            color = []
            color_page = []
            try:
                color_big_div = driver.find_elements(By.CLASS_NAME, 'ProductConversion_groupImages__4tRb8')
                for m in color_big_div:
                    color_mid_div = m.find_elements(By.TAG_NAME, 'img')
                    color.extend([color1.get_property("src") for color1 in color_mid_div])
                pag = [page.get_property('href') for pg in color_big_div for page in pg.find_elements(By.TAG_NAME, 'a')]
                color_page.extend(pag)
            except NSEE:
                pass

            picture = []
            picture_div = driver.find_elements(By.CLASS_NAME, 'ImageGallery_container__cNIDV')
            for pic1 in picture_div:
                pic2 = pic1.find_elements(By.TAG_NAME, 'img')
                picture.extend([pic3.get_property('src') for pic3 in pic2])

            return {
                'brand': brand,
                'name': name,
                'price': price,
                'size': size,
                'color_source': color,
                'color_pages': color_page,
                'picture': picture,
            }

        except (NSEE, TOE, SERE, Exception) as e:
            raise Exception(f"An error occurred while scraping product data: {str(e)}")

    driver_init()
    try:
        return products()
    finally:
        if driver:
            driver.quit()
            
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
            'converted_price': str(converted_price),
            'additional_cost': str(additional_cost),
            'shipping_cost': str(shipping_cost),
            'total_cost': str(total_cost)
        }

        return Response({'results': result}, status=status.HTTP_200_OK)