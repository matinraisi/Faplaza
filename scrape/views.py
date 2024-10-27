from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import json
from .models import ScrapeData
from price.models import ExchangeRate
from playwright.sync_api import sync_playwright
from selenium.common.exceptions import (NoSuchElementException as NSEE, TimeoutException as TOE, 
                                         NoSuchWindowException as NSWE, InvalidArgumentException as IAE, WebDriverException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
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
            response = requests.post('http://188.165.62.242:5049/scrape', json={
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
    driver = None

    def driver_init():
        nonlocal driver
        options = Options()
        options.add_argument("--headless")
        options.add_argument('--enable-gpu')  # Enable GPU for better rendering
        options.add_argument('--no-sandbox')  # Required for certain environments (optional)
        # options.add_argument("--disable-gpu")
        # options.add_argument("start-maximized")
        # options.add_argument("disable-infobars")
        # options.add_argument("--disable-extensions")
        # options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-popup-blocking")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(60)
            driver.get(url)
            print('Finding End ...')
            end = driver.find_element(By.XPATH, '/html/body/section/section/section/div[2]/div[1]/div/div/div[1]')
            actions = ActionChains(driver)
            actions.scroll_to_element(end).perform()
        except (TOE, WebDriverException) as e:
            print(f"Error initializing the driver: {e}")
            if driver:
                driver.quit()
            raise
        return driver

    def products():
        try:
            print('Locating Brand ...')
            brand = driver.find_element(By.CLASS_NAME, 'ProductConversion_brand__Y76P_').text.strip()
            print('Locating Name ...')
            name = driver.find_element(By.XPATH, '/html/body/section/section/section/section/div/div[2]/section[1]/section[1]/div/div[1]/h1').text.strip()
            print('Locating Price ...')
            price = driver.find_element(By.XPATH, '/html/body/section/section/section/section/div/div[2]/section[1]/section[1]/section/div[1]/section/span/span[2]').text.replace('\n', ' ')

            print('Finding Size_Div ...')
            size_div = driver.find_elements(By.XPATH, '/html/body/section/section/section/section/div/div[2]/section[1]/div[1]/div[2]/div')
            print('Locating Sizes ...')
            size = [_.text.strip() for size1 in size_div for _ in size1.find_elements(By.CLASS_NAME, 'SizePills_size_variant__4qpXf')]

            color = []
            color_page = []
            try:
                print('Locating Color_Big_Div ...')
                color_big_div = driver.find_elements(By.CLASS_NAME, 'ProductConversion_groupImages__4tRb8')
                print('Locating Colors ...')
                for m in color_big_div:
                    color_mid_div = m.find_elements(By.TAG_NAME, 'img')
                    color.extend([color1.get_property("src") for color1 in color_mid_div])
                print('Locating Page_colors ...')
                pag = [page.get_property('href') for pg in color_big_div for page in pg.find_elements(By.TAG_NAME, 'a')]
                color_page.extend(pag)
            except NSEE:
                pass

            picture = []
            print('Locating Pictures ...')
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

        except (NSEE, NSWE, TOE, Exception) as e:
            print(f"An unexpected error occurred: {e}")
            raise

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
            'aed_to_toman': str(converted_price),
            'profit_percentage': str(additional_cost),
            'shipping_cost': str(shipping_cost),
            'per_kg_cost': str(total_cost)
        }

        return Response({'results': result}, status=status.HTTP_200_OK)
