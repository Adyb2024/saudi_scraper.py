import re
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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
    # تمويه السيرفر لكي لا يتم حظره
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHANNEL_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        res = requests.post(url, data=payload)
        return res.status_code == 200
    except:
        return False

def get_whatsapp_from_site(site_url):
    """دالة فحص المواقع لاستخراج أرقام التواصل"""
    if not site_url or "google.com" in site_url:
        return "غير متوفر"
    
    temp_driver = setup_driver()
    whatsapp = "غير متوفر"
    try:
        temp_driver.get(site_url)
        time.sleep(8) # انتظار المواقع الثقيلة
        
        # البحث عن روابط واتساب مباشرة
        links = temp_driver.find_elements(By.XPATH, "//a[contains(@href, 'wa.me') or contains(@href, 'whatsapp')]")
        if links:
            whatsapp = links[0].get_attribute("href")
        else:
            # البحث عن أنماط الأرقام السعودية في نصوص الموقع
            page_content = temp_driver.find_element(By.TAG_NAME, "body").text
            phones = re.findall(r"(?:\+966|05)\d{8,10}", page_content)
            if phones:
                whatsapp = phones[0]
    except:
        whatsapp = "تعذر الفحص"
    finally:
        temp_driver.quit()
    return whatsapp

def run_automation():
    # التأكد من وجود ملف قاعدة البيانات
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: pass

    with open(DB_FILE, "r") as f:
        published = f.read().splitlines()

    driver = setup_driver()
    print("🌐 بدء الاتصال بخرائط جوجل...")
    
    try:
        driver.get("http://googleusercontent.com/maps.google.com/3")
        time.sleep(5)
        
        search_query = "متاجر إلكترونية في الرياض"
        search_box = driver.find_element(By.ID, "searchboxinput")
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.ENTER)
        time.sleep(10)

        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        print(f"📊 تم العثور على {len(results)} نتيجة أولية.")

        for item in results[:8]: # فحص أفضل 8 نتائج لتجنب استهلاك وقت جيت هوب
            try:
                name = item.get_attribute("aria-label")
                item.click()
                time.sleep(5)
                
                # محاولة استخراج رابط الموقع
                try:
                    site_el = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']")
                    site_url = site_el.get_attribute("href")
                except:
                    continue

                if site_url in published:
                    print(f"⏭️ المتجر {name} منشؤ مسبقاً.")
                    continue

                print(f"🔎 جاري فحص متجر: {name}")
                contact_info = get_whatsapp_from_site(site_url)
                
                # تنسيق الرسالة الاحترافية للقناة
                msg = (
                    f"🚀 *فرصة تجارية جديدة تم رصدها*\n\n"
                    f"🏠 *المتجر:* {name}\n"
                    f"🔗 *الموقع:* [اضغط هنا للزيارة]({site_url})\n"
                    f"📞 *التواصل:* `{contact_info}`\n\n"
                    f"🤖 _تم الاستخراج بواسطة نظام أديب الذكي_"
                )
                
                if send_to_telegram(msg):
                    with open(DB_FILE, "a") as f:
                        f.write(site_url + "\n")
                    print(f"✅ تم النشر: {name}")

            except Exception as e:
                print(f"⚠️ خطأ بسيط في معالجة متجر: {e}")
                continue

    finally:
        driver.quit()
        print("🏁 اكتملت المهمة بنجاح.")

if __name__ == "__main__":
    run_automation()
