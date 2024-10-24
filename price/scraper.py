# price/scraper.py

import time
import random
from playwright.sync_api import sync_playwright, Page
from amazoncaptcha import AmazonCaptcha

def UA_header():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        # Add more user agents as needed
    ]
    headers_list = [
        {'Accept-Language': 'en-US,en;q=0.9', 'Accept-Encoding': 'gzip, deflate, br', 'Connection': 'keep-alive', 'DNT': '1', 'Upgrade-Insecure-Requests': '1'},
        {'Accept-Language': 'en-US,en;q=0.8,en;q=0.6', 'Accept-Encoding': 'gzip, deflate', 'Connection': 'keep-alive', 'DNT': '1', 'Upgrade-Insecure-Requests': '1'},
        # Add more headers as needed
    ]
    return user_agents[random.randint(0, len(user_agents) - 1)], headers_list[random.randint(0, len(headers_list) - 1)]

def Captcha_solver(image_url: str) -> str:
    cap = AmazonCaptcha.fromlink(image_url)
    return AmazonCaptcha.solve(cap)

def url_check(url: str) -> bool:
    splitted_url = url.split('/')
    return splitted_url[2].split('.')[-1] == 'ae'

def link_fetch(page: Page, options):
    ava = None
    try:
        title = page.locator('#title').inner_text()
    except:
        time.sleep(5)
        image = page.locator('body > div > div.a-row.a-spacing-double-large > div.a-section > div > div > form > div.a-row.a-spacing-large > div > div > div.a-row.a-text-center > img').get_attribute('src')
        cap_text = Captcha_solver(image)
        page.locator('#captchacharacters').fill(cap_text)
        page.locator('body > div > div.a-row.a-spacing-double-large > div.a-section > div > div > form > div.a-section.a-spacing-extra-large > div > span > span > button').click()
        return link_fetch(page, options)
    
    # Process the page to fetch data
    # ...

    data = {
        'price': '0',  # Replace with actual price
        'images': [],   # Replace with actual images
        'title': title,
        'color': [],    # Replace with actual colors
        'styles': [],   # Replace with actual styles
        'sizes': [],    # Replace with actual sizes
        'Flavor': [],   # Replace with actual flavors
        'avalibale': ava
    }
    return data

def scrape_amazon(link):
    if not url_check(link.url):
        return False
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        user_agent, headers = UA_header()
        context = browser.new_context(user_agent=user_agent, extra_http_headers=headers)
        page = context.new_page()
        page.goto(link.url)
        return link_fetch(page, link)
