import random
import re
import time
import os
import requests
import csv
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# ⚙️ إعدادات النظام
# ==========================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
DB_FILE = "published_links.txt"

# ==========================================
# 🛠️ وظائف التنظيف والتحليل الذكي
# ==========================================

def clean_google_url(url):
    """تنظيف روابط جوجل المعقدة واستخراج الرابط الحقيقي للمتجر"""
    if "google.com/url?" in url:
        parsed_url = urlparse(url)
        captured_url = parse_qs(parsed_url.query).get('q', [None])[0]
        return captured_url if captured_url else url
    return url

def get_domain_age(site_url):
    try:
        domain = re.search(r'https?://([^/]+)', site_url).group(1)
        res = requests.get(f"https://rdap.org/domain/{domain}", timeout=5).json()
        for event in res.get("events", []):
            if event.get("eventAction") == "registration":
                return event.get("eventDate").split("T")[0]
        return "2026 (حديث)"
    except: return "قيد الفحص"

def detect_platform(html_source):
    html_source = html_source.lower()
    if any(x in html_source for x in ["salla.sa", "salla-cdn"]): return "سلة (Salla)"
    if any(x in html_source for x in ["zid.store", "zid-assets"]): return "زد (Zid)"
    if "shopify.com" in html_source: return "شوبيفاي (Shopify)"
    if "wp-content" in html_source: return "ووردبريس (WordPress)"
    return "برمجة خاصة / أخرى"

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHANNEL_ID, 'text': message, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
    try:
        r = requests.post(url, data=payload, timeout=15)
        return r.status_code == 200
    except: return False

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ==========================================
# 🚀 المحرك الأساسي (The Final Professional Version)
# ==========================================

def run_automation():
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: published = f.read().splitlines()

    target_city = random.choice(["الرياض، السعودية", "جدة، السعودية", "الدمام، السعودية", "دبي، الإمارات", "الدوحة، قطر"])
    target_business = random.choice(["متاجر عطور", "متاجر ملابس", "متاجر عبايات", "متاجر إلكترونيات"])
    
    print(f"🌍 جاري بدء الرصد: {target_business} في {target_city}")
    driver = setup_driver()
    wait = WebDriverWait(driver, 40)
    
    try:
        driver.get(f"https://www.google.com/maps/search/{target_business} في {target_city}?hl=ar")
        time.sleep(12)
        
        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        stores_names = [el.get_attribute("aria-label") for el in elements[:10] if el.get_attribute("aria-label")]

        count = 0
        for name in stores_names:
            if count >= 5: break
            try:
                # البحث عن العنصر والضغط عليه
                el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"a[aria-label='{name}']")))
                driver.execute_script("arguments[0].click();", el)
                time.sleep(7)
                
                try:
                    site_element = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']")
                    raw_url = site_element.get_attribute("href")
                    site_url = clean_google_url(raw_url) # تنظيف الرابط فوراً
                except: continue

                if site_url in published: continue

                # فحص الموقع بعمق
                driver.execute_script(f"window.open('{site_url}');")
                time.sleep(10)
                driver.switch_to.window(driver.window_handles[-1])
                
                html = driver.page_source
                platform = detect_platform(html)
                age = get_domain_age(site_url)
                
                # استخراج رقم الواتساب بدقة
                wa_match = re.search(r'(?:wa\.me/|whatsapp\.com/send\?phone=|api\.whatsapp\.com/send\?phone=)(\d{10,15})', html)
                wa_number = wa_match.group(1) if wa_match else ""
                wa_link = f"https://wa.me/{wa_number}" if wa_number else "غير متوفر"

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                # صياغة الرسالة النهائية
                msg = (
                    f"🛰️ *تم رصد متجر جديد الآن!* 🛰️\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🏢 *المتجر:* {name}\n"
                    f"📍 *الموقع:* {target_city}\n"
                    f"🛠️ *المنصة:* {platform}\n"
                    f"📅 *تأسيس الدومين:* `{age}`\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📞 [تواصل عبر الواتساب]({wa_link})\n"
                    f"🔗 [رابط المتجر الإلكتروني]({site_url})\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🛰️ *رادار متاجر الخليج الذكي* 🛰️"
                )
                
                if send_to_telegram(msg):
                    with open(DB_FILE, "a") as f: f.write(site_url + "\n")
                    print(f"✅ تم الإرسال بنجاح: {name}")
                    count += 1
            except: continue
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
