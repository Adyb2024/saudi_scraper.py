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
# 🌍 بنك الأهداف (المدن والأنشطة)
# ==========================================
GULF_CITIES = [
    "الرياض، السعودية", "جدة، السعودية", "الدمام، السعودية", "الخبر، السعودية",
    "دبي، الإمارات", "أبوظبي، الإمارات", "الشارقة، الإمارات",
    "مدينة الكويت، الكويت", "الدوحة، قطر", "المنامة، البحرين", "مسقط، عمان"
]

BUSINESS_TYPES = [
    "متاجر عطور", "متاجر ملابس", "متاجر هدايا وتغليف",
    "مطاعم سحابية", "وكالات تسويق رقمي", "متاجر حلويات ومخابز",
    "شركات تقنية ناشئة", "متاجر عبايات", "متاجر إلكترونيات"
]

# ==========================================
# 🛠️ أدوات التحليل والذكاء الرقمي
# ==========================================

def get_domain_age(site_url):
    """استخراج تاريخ تسجيل الدومين من السجلات العالمية"""
    try:
        domain = re.search(r'https?://([^/]+)', site_url).group(1)
        # استخدام بروتوكول RDAP لجلب بيانات التسجيل
        res = requests.get(f"https://rdap.org/domain/{domain}", timeout=5).json()
        for event in res.get("events", []):
            if event.get("eventAction") == "registration":
                return event.get("eventDate").split("T")[0]
        return "2026 (حديث)"
    except: return "قيد الفحص"

def detect_platform(html_source):
    """كشف المنصة المشغلة للموقع (سلة، زد، إلخ) عبر تحليل الكود المصدري"""
    html_source = html_source.lower()
    if "salla.sa" in html_source or "salla-cdn" in html_source: return "سلة (Salla)"
    if "zid.store" in html_source or "zid-assets" in html_source: return "زد (Zid)"
    if "shopify.com" in html_source: return "شوبيفاي (Shopify)"
    if "wp-content" in html_source: return "ووردبريس (WordPress)"
    return "برمجة خاصة / أخرى"

def send_to_telegram(message):
    """إرسال التقرير النهائي لقناة تليجرام"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHANNEL_ID,
        'text': message,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': True # لمنع ظهور معاينة الروابط وتخريب تنسيق الرسالة
    }
    try:
        r = requests.post(url, data=payload, timeout=15)
        return r.status_code == 200
    except: return False

def save_to_csv(data):
    """حفظ البيانات في ملف إكسل مرتب يدعم اللغة العربية"""
    fieldnames = ["تاريخ الرصد", "المدينة", "المتجر", "النشاط", "المنصة", "عمر الدومين", "الحالة", "واتساب", "إنستقرام", "تيك توك", "سناب", "الموقع"]
    file_exists = os.path.isfile(CSV_FILE)
    # استخدام utf-8-sig لضمان ظهور الحروف العربية بشكل صحيح في الإكسل
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists: writer.writeheader()
        writer.writerow(data)

def setup_driver():
    """إعداد متصفح كروم للعمل في بيئة جيت هوب (Headless Mode)"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # تشغيل بدون واجهة رسومية
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # استخدام User-Agent حقيقي لتجنب كشف البوت من قبل جوجل
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ==========================================
# 🚀 المحرك الأساسي المطور (Robust Version)
# ==========================================

def run_automation():
    # 1. تجهيز الذاكرة (قاعدة البيانات المحلية) لمنع نشر التكرار
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: published = f.read().splitlines()

    # 2. اختيار هدف عشوائي ذكي للدورة الحالية
    target_city = random.choice(GULF_CITIES)
    target_business = random.choice(BUSINESS_TYPES)
    search_query = f"{target_business} في {target_city}"
    
    print(f"🌍 جاري بدء مهمة الرصد للمنطقة المستهدفة: {search_query}")
    
    driver = setup_driver()
    # وقت انتظار افتراضي كافٍ لبيئة GitHub Actions الأبطأ قليلاً
    wait = WebDriverWait(driver, 40) 
    
    try:
        # 3. الوصول لخرائط جوجل مع وقت انتظار للتحميل الكامل
        driver.get(f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}?hl=ar")
        time.sleep(15) 
        
        # 4. استخراج قائمة بأسماء المتاجر فقط (Names) لتجنب الـ Stale Elements
        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        print(f"✅ تم العثور على {len(results)} متجر محتمل.")

        # تخزين الأسماء في قائمة ثابتة
        stores_names = []
        for item in results[:10]: # نأخذ أول 10 محاولات كعينة
            try:
                stores_names.append(item.get_attribute("aria-label"))
            except: continue

        count = 0
        # 5. حلقة فحص دفاعية تعتمد على اسم المتجر لإعادة البحث عنه وتجاوز تحديث الصفحة
        for store_name in stores_names:
            if count >= 5: break # نكتفي بخمسة متاجر جديدة في كل دورة لضمان جودة البيانات

            try:
                print(f"🔎 جاري فحص المتجر الحالي: {store_name}")
                
                # --- [الخطوة الدفاعية الأهم] ---
                # إعادة البحث عن المتجر باستخدامه اسمه لتجاوز أي تحديث مفاجئ للصفحة
                current_item_selector = f"v[aria-label='{store_name}']"
                try:
                    # ننتظر حتى يصبح قابلاً للضغط
                    current_item = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, current_item_selector)))
                    driver.execute_script("arguments[0].click();", current_item)
                    time.sleep(8) # وقت كافٍ لتحميل تفاصيل المتجر بالكامل
                except:
                    print(f"⏩ تخطي {store_name}: تعذر الضغط عليه (غالباً لم يعد موجوداً في القائمة المحدثة).")
                    continue
                # -------------------------------

                # استخراج رابط الموقع الإلكتروني
                try:
                    site_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-item-id='authority']")))
                    site_url = site_element.get_attribute("href")
                except:
                    print(f"⏩ تخطي {store_name}: لا يوجد موقع إلكتروني للتحليل السيبراني العميق.")
                    continue

                # منع التكرار بناءً على الرابط قبل تضييع الوقت في فحص الموقع
                if site_url in published:
                    print(f"⏩ تخطي {store_name}: مكرر ومسجل مسبقاً في قاعدة البيانات.")
                    continue

                # 6. التحليل العميق للموقع (Deep Inspection)
                # فتح الموقع في نافذة جديدة
                main_window = driver.current_window_handle
                driver.execute_script(f"window.open('{site_url}');")
                time.sleep(12) # GitHub Actions أبطأ قليلاً، نحتاج وقتاً للتحميل
                driver.switch_to.window(driver.window_handles[-1])
                
                # التحليل السيبراني للموقع
                full_html = driver.page_source
                platform_info = detect_platform(full_html)
                domain_birthday = get_domain_age(site_url)
                
                # استخراج أرقام التواصل وروابط السوشيال ميديا (Regex)
                wa_match = re.search(r'(?:wa\.me|whatsapp\.com/send\?phone=|api\.whatsapp\.com/send\?phone=)(\d+)', full_html)
                ig_match = re.search(r'instagram\.com/([a-zA-Z0-9._]+)', full_html)
                tk_match = re.search(r'tiktok\.com/@([a-zA-Z0-9._]+)', full_html)
                sn_match = re.search(r'snapchat\.com/add/([a-zA-Z0-9._]+)', full_html)

                driver.close() # إغلاق نافذة الموقع والعودة للخرائط
                driver.switch_to.window(main_window)

                # 7. تحليل حالة التقييمات في جوجل ماب
                try: 
                    reviews_count = driver.find_element(By.CLASS_NAME, "F7B63c").text
                    current_status = f"قائم ({reviews_count})"
                    is_new_brand = False
                except: 
                    current_status = "حديث (0 تقييم)"
                    is_new_brand = True

                # 8. تنظيم البيانات للحفظ في ملف CSV
                data_row = {
                    "تاريخ الرصد": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "المدينة": target_city,
                    "المتجر": store_name,
                    "النشاط": target_business,
                    "المنصة": platform_info,
                    "عمر الدومين": domain_birthday,
                    "الحالة": current_status,
                    "واتساب": f"https://wa.me/{wa_match.group(1)}" if wa_match else "غير متوفر",
                    "إنستقرام": f"https://instagram.com/{ig_match.group(1)}" if ig_match else "غير متوفر",
                    "تيك توك": f"https://tiktok.com/@{tk_match.group(1)}" if tk_match else "غير متوفر",
                    "سناب": f"https://snapchat.com/add/{sn_match.group(1)}" if sn_match else "غير متوفر",
                    "الموقع": site_url
                }
                
                save_to_csv(data_row)

                # 9. صياغة الرسالة النهائية للقناة (البرستيج المؤسسي وبدون اسمك)
                alert_text = "🚨 *فرصة ذهبية: افتتاح حديث* 🚨" if is_new_brand else "📊 *حالة النشاط:* متجر قائم"
                
                msg = (
                    f"🛰️ *تم رصد متجر جديد الآن!* 🛰️\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🏢 *المتجر:* {store_name}\n"
                    f"📍 *الموقع:* {target_city}\n"
                    f"🏷️ *النشاط:* #{target_business.replace(' ', '_')}\n"
                    f"🛠️ *المنصة:* {platform_info}\n"
                    f"📅 *تأسيس الدومين:* `{domain_birthday}`\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{alert_text}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔍 *كيف تحققنا؟*\n"
                    f"تم فحص سجلات **WHOIS** العالمية وتحليل الكود المصدري للموقع لضمان دقة البيانات.\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📞 [تواصل عبر الواتساب]({data_row['واتساب']})\n"
                    f"📸 [حساب الإنستقرام]({data_row['إنستقرام']})\n"
                    f"🔗 [رابط المتجر الإلكتروني]({site_url})\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🛰️ *رادار متاجر الخليج الذكي* 🛰️\n"
                    f"🤖 _نظام رصد آلي مستقل بالذكاء الاصطناعي_"
                )
                
                # إرسال الرسالة وتسجيل الرابط في قاعدة البيانات لمنع التكرار
                if send_to_telegram(msg):
                    with open(DB_FILE, "a") as f: f.write(site_url + "\n")
                    print(f"✅ تم الإرسال بنجاح للمشتركين: {store_name}")
                    count += 1
                
            except Exception as e:
                print(f"⚠️ خطأ غير متوقع أثناء فحص متجر: {e}")
                # التأكد من العودة للنافذة الرئيسية دائماً في حال حدوث خطأ
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                continue
    finally:
        driver.quit()
        print("🏁 اكتملت مهمة الرصد الدورية.")

if __name__ == "__main__":
    run_automation()
