import re
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- إعدادات النظام من جيت هوب ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
DB_FILE = "published_links.txt"

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    # تمويه متقدم لتبدو كمستخدم حقيقي
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # حذف أثر السيلينيوم من المتصفح لعدم كشف البوت
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHANNEL_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        res = requests.post(url, data=payload, timeout=10)
        return res.status_code == 200
    except:
        return False

def get_whatsapp_from_site(site_url):
    if not site_url or "google.com" in site_url:
        return "غير متوفر"
    
    temp_driver = setup_driver()
    whatsapp = "غير متوفر"
    try:
        temp_driver.get(site_url)
        time.sleep(12) # وقت إضافي لتحميل محتوى الموقع
        
        # البحث عن روابط الواتساب
        links = temp_driver.find_elements(By.XPATH, "//a[contains(@href, 'wa.me') or contains(@href, 'whatsapp')]")
        if links:
            whatsapp = links[0].get_attribute("href")
        else:
            # البحث عن أرقام الهواتف بنمط سعودي
            page_content = temp_driver.find_element(By.TAG_NAME, "body").text
            phones = re.findall(r"(?:\+966|05)\d{8,10}", page_content)
            if phones:
                whatsapp = phones[0]
    except:
        whatsapp = "فشل الفحص التلقائي"
    finally:
        temp_driver.quit()
    return whatsapp

def run_automation():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: pass

    with open(DB_FILE, "r") as f:
        published = f.read().splitlines()

    driver = setup_driver()
    wait = WebDriverWait(driver, 40)
    
    print("🌐 جاري الاتصال بنظام الخرائط...")
    
    try:
        # الدخول المباشر لنتائج البحث لتقليل كشف البوت
        search_query = "متاجر عطور في الرياض"
        encoded_query = search_query.replace(" ", "+")
        driver.get(f"https://www.google.com/maps/search/{encoded_query}?hl=ar")
        
        print("⏳ انتظار تحميل القائمة...")
        # ننتظر ظهور النتائج (العناصر التي تحمل كلاس hfpxzc)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc")))
        time.sleep(5)

        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        print(f"📊 تم رصد {len(results)} متجر.")

        for item in results[:10]: 
            try:
                name = item.get_attribute("aria-label")
                # استخدام جافا سكريبت للنقر لضمان الفتح في الخلفية
                driver.execute_script("arguments[0].click();", item)
                time.sleep(6)
                
                try:
                    # محاولة استخراج زر الموقع الإلكتروني
                    site_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-item-id='authority']")))
                    site_url = site_el.get_attribute("href")
                except:
                    continue

                if site_url in published:
                    print(f"⏭️ المتجر {name} مسجل مسبقاً.")
                    continue

                print(f"🔎 فحص معمق للموقع: {name}")
                contact = get_whatsapp_from_site(site_url)
                
                msg = (
                    f"🚀 *فرصة ذهبية جديدة* 🚀\n\n"
                    f"🏢 *اسم المتجر:* {name}\n"
                    f"🔗 *رابط الموقع:* [زيارة الموقع]({site_url})\n"
                    f"📞 *واتساب المالك:* `{contact}`\n\n"
                    f"👤 _تم الاستخراج بواسطة نظام أديب الذكي_"
                )
                
                if send_to_telegram(msg):
                    with open(DB_FILE, "a") as f:
                        f.write(site_url + "\n")
                    print(f"✅ تم الإرسال للقناة: {name}")

            except Exception as sub_e:
                print(f"⚠️ تخطي متجر بسبب بطء التحميل: {sub_e}")
                continue

    except Exception as e:
        print(f"❌ خطأ في النظام الأساسي: {e}")
    finally:
        driver.quit()
        print("🏁 انتهت الدورة الحالية بنجاح.")

if __name__ == "__main__":
    run_automation()
