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
# إعدادات النظام وقواعد البيانات
# ==========================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
DB_FILE = "published_links.txt"
CSV_FILE = "gulf_stores_database.csv"

# ==========================================
# بنك الأهداف (المدن والانشطة)
# ==========================================
GULF_CITIES = [
    "الرياض، السعودية", "جدة، السعودية", "الدمام، السعودية", "الخبر، السعودية",
    "دبي، الإمارات", "أبوظبي، الإمارات", "الشارقة، الإمارات",
    "مدينة الكويت، الكويت", "الدوحة، قطر", "المنامة، البحرين", "مسقط، عمان"
]

BUSINESS_TYPES = [
    "متاجر عطور جديدة", "متاجر ملابس إلكترونية", "متاجر هدايا وتغليف",
    "مطاعم سحابية Cloud Kitchen", "وكالات تسويق رقمي", "متاجر حلويات ومخابز",
    "شركات تقنية ناشئة", "متاجر عبايات", "متاجر إلكترونيات"
]

# ==========================================
# الدوال المساعدة (CSV، متصفح، تليجرام، سوشيال ميديا)
# ==========================================
def save_to_csv(data):
    """حفظ البيانات في ملف إكسل بترتيب احترافي ودعم كامل للعربية"""
    fieldnames = [
        "تاريخ الرصد", "المدينة", "اسم المتجر", "النشاط", "الحالة", 
        "رابط الواتساب", "إنستقرام", "تيك توك", "سناب شات", "الموقع الإلكتروني"
    ]
    file_exists = os.path.isfile(CSV_FILE)
    
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        
        # ترتيب البيانات لتتطابق مع العناوين بدقة
        writer.writerow({
            "تاريخ الرصد": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "المدينة": data.get("المدينة", ""),
            "اسم المتجر": data.get("الاسم", ""),
            "النشاط": data.get("النشاط", ""),
            "الحالة": data.get("الحالة", ""),
            "رابط الواتساب": data.get("واتساب", ""),
            "إنستقرام": data.get("إنستقرام", ""),
            "تيك توك": data.get("تيك توك", ""),
            "سناب شات": data.get("سناب", ""),
            "الموقع الإلكتروني": data.get("الموقع", "")
        })

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHANNEL_ID, 'text': message, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
    try:
        requests.post(url, data=payload, timeout=15)
        return True
    except: return False

def get_deep_social_info(site_url):
    """استخراج الواتساب والسوشيال ميديا من شفرة الموقع"""
    data = {"wa": "غير متوفر", "ig": "غير متوفر", "tk": "غير متوفر", "sn": "غير متوفر"}
    if not site_url or "google.com" in site_url: return data
    
    tmp = setup_driver()
    try:
        tmp.get(site_url)
        time.sleep(12)
        source = tmp.page_source
        
        wa = re.search(r'(?:wa\.me|api\.whatsapp\.com/send\?phone=|whatsapp:)(\d+)', source)
        if wa: data["wa"] = f"https://wa.me/{wa.group(1)}"
        else:
            p = re.findall(r"(?:\+966|05|\+971|\+965|\+974|\+973|\+968)\d{7,10}", source)
            if p: data["wa"] = p[0]

        ig = re.search(r'instagram\.com/([a-zA-Z0-9._]+)', source)
        tk = re.search(r'tiktok\.com/@([a-zA-Z0-9._]+)', source)
        sn = re.search(r'snapchat\.com/add/([a-zA-Z0-9._]+)', source)
        
        if ig: data["ig"] = f"https://instagram.com/{ig.group(1)}"
        if tk: data["tk"] = f"https://tiktok.com/@{tk.group(1)}"
        if sn: data["sn"] = f"https://snapchat.com/add/{sn.group(1)}"
    except: pass
    finally: tmp.quit()
    return data

# ==========================================
# المحرك الأساسي (The Core Engine)
# ==========================================
def run_automation():
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: published = f.read().splitlines()

    # اختيار عشوائي ذكي لمنع التكرار وتجنب الحظر
    target_city = random.choice(GULF_CITIES)
    target_business = random.choice(BUSINESS_TYPES)
    search_query = f"{target_business} في {target_city}"
    
    print(f"🌍 جاري مسح الهدف: {search_query}")
    
    driver = setup_driver()
    wait = WebDriverWait(driver, 45)
    
    try:
        driver.get(f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}?hl=ar")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc")))
        time.sleep(8)
        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")

        # نكتفي بـ 5 نتائج في كل دورة تشغيل لضمان جودة الاستخراج وتجنب الحظر
        for item in results[:5]: 
            try:
                name = item.get_attribute("aria-label")
                driver.execute_script("arguments[0].click();", item)
                time.sleep(7)
                
                try:
                    site_url = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-item-id='authority']"))).get_attribute("href")
                except: continue

                if site_url in published: continue

                # استخراج النشاط
                try: cat = driver.find_element(By.CSS_SELECTOR, "button[class*='DkEaL']").text
                except: cat = target_business.split(" ")[1] # استخراج الكلمة الثانية كنشاط تقريبي
                
                # تحليل التقييمات وتنبيه الافتتاح الحديث
                is_super_new = False
                try:
                    revs = driver.find_element(By.CLASS_NAME, "F7B63c").text
                    status_text = f"متجر قائم ({revs})"
                    alert_msg = f"📊 *حالة النشاط:* {status_text}"
                except:
                    status_text = "جديد (0 تقييمات)"
                    alert_msg = (
                        f"🚨 *فرصة نادرة: صفر تقييمات* 🚨\n"
                        f"💡 _(هذا المتجر افتتح الآن ولم يصله منافسوك، تواصل معه فوراً!)_"
                    )
                    is_super_new = True

                print(f"🔎 فحص الروابط العميقة لمتجر: {name}")
                social = get_deep_social_info(site_url)

                # 1. حفظ البيانات في ملف الإكسل المرتب
                store_data = {
                    "الاسم": name,
                    "النشاط": cat,
                    "المدينة": target_city,
                    "الحالة": status_text,
                    "الموقع": site_url,
                    "واتساب": social['wa'],
                    "إنستقرام": social['ig'],
                    "تيك توك": social['tk'],
                    "سناب": social['sn']
                }
                save_to_csv(store_data)

                # 2. إرسال التقرير اللحظي لقناة التليجرام
                msg = (
                    f"🌍 *رصد تجاري خليجي جديد* 🌍\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🏢 *المتجر:* {name}\n"
                    f"📍 *الموقع:* {target_city}\n"
                    f"🏷️ *التصنيف:* #{cat.replace(' ', '_').replace('،', '')}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{alert_msg}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔗 *الموقع:* [اضغط لزيارة المتجر]({site_url})\n"
                    f"📞 *واتساب:* `{social['wa']}`\n"
                    f"📸 *إنستقرام:* {social['ig']}\n"
                    f"🎵 *تيك توك:* {social['tk']}\n"
                    f"👻 *سناب شات:* {social['sn']}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🗺️ *الخريطة:* [فتح في جوجل ماب](https://maps.google.com/{name.replace(' ', '+')})\n"
                    f"🕒 *التوقيت:* {datetime.now().strftime('%Y-%m-%d | %H:%M')}\n\n"
                    f"👤 _نظام رادار الخليج - أديب_"
                )
                
                if send_to_telegram(msg):
                    with open(DB_FILE, "a") as f: f.write(site_url + "\n")
                    print(f"✅ تم صيد المتجر بنجاح: {name}")

            except Exception as e:
                print(f"⚠️ تخطي نتيجة بسبب خطأ: {e}")
                continue
    finally:
        driver.quit()
        print("🏁 اكتملت جولة المسح الخليجي.")

if __name__ == "__main__":
    run_automation()
