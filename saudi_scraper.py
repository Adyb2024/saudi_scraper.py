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
# 🛠️ أدوات التحليل والذكاء
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
    return "برمجة خاصة / أخرى"

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHANNEL_ID, 'text': message, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
    try:
        r = requests.post(url, data=payload, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ خطأ في إرسال تليجرام: {e}")
        return False

def save_to_csv(data):
    fieldnames = ["تاريخ الرصد", "المدينة", "المتجر", "النشاط", "المنصة", "عمر الدومين", "الحالة", "واتساب", "إنستقرام", "تيك توك", "سناب", "الموقع"]
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists: writer.writeheader()
        writer.writerow(data)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ==========================================
# 🚀 المحرك الأساسي (The Engine)
# ==========================================

def run_automation():
    # التأكد من وجود الملفات
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: published = f.read().splitlines()

    GULF_CITIES = ["الرياض، السعودية", "جدة، السعودية", "دبي، الإمارات", "الكويت", "الدوحة، قطر"]
    BUSINESS_TYPES = ["متاجر عطور", "متاجر ملابس", "متاجر هدايا", "مطاعم سحابية"]

    target_city = random.choice(GULF_CITIES)
    target_business = random.choice(BUSINESS_TYPES)
    search_query = f"{target_business} في {target_city}"
    
    print(f"🌍 جاري البحث عن: {search_query}")
    
    driver = setup_driver()
    wait = WebDriverWait(driver, 30)
    
    try:
        driver.get(f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}?hl=ar")
        time.sleep(10)
        
        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        print(f"✅ تم العثور على {len(results)} متجر محتمل")

        count = 0
        for item in results:
            if count >= 5: break # نكتفي بـ 5 متاجر جديدة في كل دورة
            
            try:
                name = item.get_attribute("aria-label")
                driver.execute_script("arguments[0].click();", item)
                time.sleep(5)
                
                try:
                    site_element = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']")
                    site_url = site_element.get_attribute("href")
                except:
                    print(f"⏩ تخطي {name}: لا يوجد موقع إلكتروني")
                    continue

                if site_url in published:
                    print(f"⏩ تخطي {name}: تم نشره مسبقاً")
                    continue

                print(f"🕵️ تحليل استخباراتي عميق لـ: {name}")
                
                # فتح الموقع في نافذة جديدة
                main_window = driver.current_window_handle
                driver.execute_script(f"window.open('{site_url}');")
                time.sleep(8)
                driver.switch_to.window(driver.window_handles[-1])
                
                html = driver.page_source
                platform = detect_platform(html)
                creation_date = get_domain_age(site_url)
                
                # استخراج السوشيال ميديا (Regex محسن)
                wa = re.search(r'(?:wa\.me|whatsapp\.com/send\?phone=|api\.whatsapp\.com/send\?phone=)(\d+)', html)
                ig = re.search(r'instagram\.com/([a-zA-Z0-9._]+)', html)
                tk = re.search(r'tiktok\.com/@([a-zA-Z0-9._]+)', html)
                sn = re.search(r'snapchat\.com/add/([a-zA-Z0-9._]+)', html)

                driver.close() # إغلاق نافذة الموقع
                driver.switch_to.window(main_window) # العودة للخرائط

                # تحليل التقييمات
                try: 
                    revs = driver.find_element(By.CLASS_NAME, "F7B63c").text
                    status = f"قائم ({revs})"
                    is_new = False
                except: 
                    status = "حديث (0 تقييم)"
                    is_new = True

                data_row = {
                    "تاريخ الرصد": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "المدينة": target_city, "المتجر": name, "النشاط": target_business,
                    "المنصة": platform, "عمر الدومين": creation_date, "الحالة": status,
                    "واتساب": f"https://wa.me/{wa.group(1)}" if wa else "غير متوفر",
                    "إنستقرام": f"https://instagram.com/{ig.group(1)}" if ig else "غير متوفر",
                    "تيك توك": f"https://tiktok.com/@{tk.group(1)}" if tk else "غير متوفر",
                    "سناب": f"https://snapchat.com/add/{sn.group(1)}" if sn else "غير متوفر",
                    "الموقع": site_url
                }
                
                save_to_csv(data_row)

                alert = "🚨 *فرصة ذهبية: افتتاح حديث* 🚨" if is_new else "📊 *حالة النشاط:* متجر قائم"
                
                msg = (
                    f"🌟 *رصد استخباراتي للمتاجر* 🌟\n"
                    f"🏢 *المتجر:* {name}\n"
                    f"📍 *الموقع:* {target_city}\n"
                    f"🛠️ *المنصة:* {platform}\n"
                    f"📅 *تأسيس الدومين:* `{creation_date}`\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{alert}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔍 *كيف تحققنا؟*\n"
                    f"تم فحص سجلات **WHOIS** العالمية وتحليل الكود المصدري للموقع لضمان دقة البيانات.\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📞 *واتساب:* `{data_row['واتساب']}`\n"
                    f"📸 *إنستقرام:* {data_row['إنستقرام']}\n"
                    f"🔗 [رابط المتجر]({site_url})\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"👤 _نظام رادار الخليج - م. أديب_"
                )
                
                if send_to_telegram(msg):
                    with open(DB_FILE, "a") as f: f.write(site_url + "\n")
                    print(f"✅ تم الإرسال بنجاح: {name}")
                    count += 1
                
            except Exception as e:
                print(f"⚠️ خطأ أثناء فحص متجر: {e}")
                # التأكد من العودة للنافذة الرئيسية في حال حدوث خطأ
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                continue
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
