import random
import re
import time
import os
import requests
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# ⚙️ إعدادات النظام (GitHub Secrets)
# ==========================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
DB_FILE = "published_links.txt"
CSV_FILE = "gulf_intelligence_database.csv"

# ==========================================
# 🌍 بنك الأهداف
# ==========================================
GULF_CITIES = ["الرياض، السعودية", "جدة، السعودية", "دبي، الإمارات", "الدوحة، قطر", "مدينة الكويت، الكويت"]
BUSINESS_TYPES = ["متاجر عطور", "متاجر ملابس", "متاجر عبايات", "متاجر إلكترونيات"]

# ==========================================
# 🛠️ أدوات التحليل
# ==========================================

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
    if "salla.sa" in html_source or "salla-cdn" in html_source: return "سلة (Salla)"
    if "zid.store" in html_source or "zid-assets" in html_source: return "زد (Zid)"
    if "shopify.com" in html_source: return "شوبيفاي (Shopify)"
    if "wp-content" in html_source: return "ووردبريس (WordPress)"
    return "برمجة خاصة"

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
# 🚀 المحرك الأساسي (The Final Bulletproof Engine)
# ==========================================

def run_automation():
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: published = f.read().splitlines()

    target_city = random.choice(GULF_CITIES)
    target_business = random.choice(BUSINESS_TYPES)
    search_query = f"{target_business} في {target_city}"
    
    print(f"🌍 جاري بدء مهمة الرصد: {search_query}")
    driver = setup_driver()
    wait = WebDriverWait(driver, 40)
    
    try:
        driver.get(f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}?hl=ar")
        time.sleep(12)
        
        # استخراج أسماء المتاجر أولاً لتجنب Stale Element
        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        stores_names = [el.get_attribute("aria-label") for el in elements[:10] if el.get_attribute("aria-label")]
        print(f"✅ تم العثور على {len(stores_names)} نتيجة محتملة.")

        count = 0
        for name in stores_names:
            if count >= 5: break
            try:
                print(f"🔎 فحص المتجر: {name}")
                # محاولة الضغط مع إعادة المحاولة إذا كان العنصر "Stale"
                for retry in range(3):
                    try:
                        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"a[aria-label='{name}']")))
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                        time.sleep(2)
                        driver.execute_script("arguments[0].click();", el)
                        break
                    except:
                        time.sleep(2)
                
                time.sleep(6)
                try:
                    site_element = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']")
                    site_url = site_element.get_attribute("href")
                except:
                    print(f"⏩ تخطي {name}: لا يوجد موقع.")
                    continue

                if site_url in published: continue

                # التحليل العميق
                main_window = driver.current_window_handle
                driver.execute_script(f"window.open('{site_url}');")
                time.sleep(10)
                driver.switch_to.window(driver.window_handles[-1])
                
                html = driver.page_source
                platform = detect_platform(html)
                age = get_domain_age(site_url)
                wa = re.search(r'(?:wa\.me|whatsapp\.com/send\?phone=|api\.whatsapp\.com/send\?phone=)(\d+)', html)
                
                driver.close()
                driver.switch_to.window(main_window)

                # صياغة الرسالة
                msg = (
                    f"🛰️ *تم رصد متجر جديد الآن!* 🛰️\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🏢 *المتجر:* {name}\n"
                    f"📍 *الموقع:* {target_city}\n"
                    f"🛠️ *المنصة:* {platform}\n"
                    f"📅 *تأسيس الدومين:* `{age}`\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📞 [تواصل عبر الواتساب](https://wa.me/{wa.group(1) if wa else ''})\n"
                    f"🔗 [رابط المتجر]({site_url})\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🛰️ *رادار متاجر الخليج الذكي* 🛰️"
                )
                
                if send_to_telegram(msg):
                    with open(DB_FILE, "a") as f: f.write(site_url + "\n")
                    print(f"✅ تم الإرسال: {name}")
                    count += 1
            except Exception as e:
                print(f"⚠️ خطأ أثناء فحص {name}")
                continue
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
