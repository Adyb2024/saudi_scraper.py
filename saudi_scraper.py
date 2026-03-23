import random
import re
import time
import os
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# ⚙️ الإعدادات (GitHub Secrets)
# ==========================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
DB_FILE = "published_links.txt"

# قائمة الماركات العالمية المستبعدة (لحماية جودة المحتوى)
EXCLUDED_BRANDS = ["zara", "h&m", "nike", "adidas", "ikea", "lc waikiki", "centerpoint", "max", "splash"]

# ==========================================
# 🛠️ أدوات التنظيف والذكاء الرقمي
# ==========================================

def clean_url(url):
    """تنظيف روابط جوجل واستخراج الموقع المباشر"""
    if "google.com/url?" in url:
        try:
            parsed = urlparse(url)
            return parse_qs(parsed.query).get('q', [url])[0]
        except: return url
    return url

def get_platform(html):
    """كشف منصة المتجر"""
    html = html.lower()
    if "salla.sa" in html: return "سلة (Salla)"
    if "zid.store" in html: return "زد (Zid)"
    if "shopify" in html: return "شوبيفاي (Shopify)"
    if "wp-content" in html: return "ووردبريس (WordPress)"
    return "برمجة خاصة"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHANNEL_ID, 'text': msg, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
    try: return requests.post(url, data=payload, timeout=10).status_code == 200
    except: return False

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ==========================================
# 🚀 محرك الرصد (The Tactical Engine)
# ==========================================

def run_automation():
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: published = f.read().splitlines()

    city = random.choice(["الرياض", "جدة", "دبي", "الدوحة", "الكويت"])
    business = random.choice(["متاجر عطور", "متاجر عبايات", "متاجر ملابس", "متاجر هدايا"])
    
    print(f"🌍 جاري المسح: {business} في {city}")
    driver = setup_driver()
    wait = WebDriverWait(driver, 35)

    try:
        driver.get(f"https://www.google.com/maps/search/{business}+في+{city}?hl=ar")
        time.sleep(10)
        
        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for el in elements[:8]:
            try:
                name = el.get_attribute("aria-label")
                # فلترة الماركات العالمية
                if any(brand in name.lower() for brand in EXCLUDED_BRANDS): continue

                driver.execute_script("arguments[0].click();", el)
                time.sleep(6)
                
                try:
                    raw_url = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']").get_attribute("href")
                    site_url = clean_url(raw_url)
                except: continue

                if site_url in published: continue

                # فحص الموقع في نافذة جديدة
                driver.execute_script(f"window.open('{site_url}');")
                time.sleep(10)
                driver.switch_to.window(driver.window_handles[-1])
                
                source = driver.page_source
                platform = get_platform(source)
                wa = re.search(r'(?:wa\.me/|whatsapp\.com/send\?phone=|api\.whatsapp\.com/send\?phone=)(\d{9,15})', source)
                
                wa_link = f"https://wa.me/{wa.group(1)}" if wa else "غير متوفر"
                
                msg = (
                    f"🛰️ *تم رصد متجر جديد الآن!* 🛰️\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🏢 *المتجر:* {name}\n"
                    f"📍 *الموقع:* {city}\n"
                    f"🛠️ *المنصة:* {platform}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📞 [تواصل عبر الواتساب]({wa_link})\n"
                    f"🔗 [رابط المتجر]({site_url})\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🛰️ *رادار متاجر الخليج الذكي* 🛰️"
                )

                if send_telegram(msg):
                    with open(DB_FILE, "a") as f: f.write(site_url + "\n")
                    print(f"✅ رصد بنجاح: {name}")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except: continue
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
