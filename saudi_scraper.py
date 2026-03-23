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

# --- إعدادات النظام الأساسية ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
DB_FILE = "published_links.txt"

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
        
        # البحث عن واتساب
        wa = re.search(r'(?:wa\.me|api\.whatsapp\.com/send\?phone=|whatsapp:)(\d+)', source)
        if wa: data["wa"] = f"https://wa.me/{wa.group(1)}"
        else:
            p = re.findall(r"(?:\+966|05)\d{8,10}", source)
            if p: data["wa"] = p[0]

        # روابط التواصل
        ig = re.search(r'instagram\.com/([a-zA-Z0-9._]+)', source)
        tk = re.search(r'tiktok\.com/@([a-zA-Z0-9._]+)', source)
        sn = re.search(r'snapchat\.com/add/([a-zA-Z0-9._]+)', source)
        
        if ig: data["ig"] = f"https://instagram.com/{ig.group(1)}"
        if tk: data["tk"] = f"https://tiktok.com/@{tk.group(1)}"
        if sn: data["sn"] = f"https://snapchat.com/add/{sn.group(1)}"
    except: pass
    finally: tmp.quit()
    return data

def run_automation():
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: published = f.read().splitlines()

    driver = setup_driver()
    wait = WebDriverWait(driver, 45)
    
    try:
        query = "متاجر إلكترونية جديدة الرياض"
        driver.get(f"https://www.google.com/maps/search/{query.replace(' ', '+')}?hl=ar")
        
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc")))
        time.sleep(7)
        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")

        for item in results[:10]:
            try:
                name = item.get_attribute("aria-label")
                driver.execute_script("arguments[0].click();", item)
                time.sleep(7)
                
                try:
                    site_url = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-item-id='authority']"))).get_attribute("href")
                except: continue

                if site_url in published: continue

                # تحليل العنوان والنشاط
                try: area = driver.find_element(By.CSS_SELECTOR, "[data-item-id='address']").text.split("،")[1].strip()
                except: area = "الرياض"
                try: cat = driver.find_element(By.CSS_SELECTOR, "button[class*='DkEaL']").text
                except: cat = "متجر إلكتروني"

                # --- المنطق الذكي لتحليل التقييمات وتنبيه "الأغبياء" ---
                try:
                    # محاولة العثور على عدد التقييمات
                    rev_element = driver.find_element(By.CLASS_NAME, "F7B63c")
                    rev_text = rev_element.text
                    status_alert = f"📊 حالة النشاط: {rev_text} (متجر قائم)"
                except:
                    # في حالة صفر تقييمات
                    status_alert = (
                        f"🚨 *فرصة ذهبية: صفر تقييمات* 🚨\n"
                        f"💡 _(تنبيه: هذا المتجر افتتح الآن ولم يصله أي منافس قبلك، بادر بالاتصال فوراً!)_"
                    )

                # الفحص العميق
                print(f"🔎 فحص روابط التواصل لـ: {name}")
                social = get_deep_social_info(site_url)

                msg = (
                    f"🌟 *تقرير رصد تجاري احترافي* 🌟\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🏢 *المتجر:* {name}\n"
                    f"🏷️ *النشاط:* #{cat.replace(' ', '_')}\n"
                    f"📍 *الحي:* {area}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{status_alert}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔗 *الموقع:* [اضغط للزيارة]({site_url})\n"
                    f"📞 *واتساب:* `{social['wa']}`\n"
                    f"📸 *إنستقرام:* {social['ig']}\n"
                    f"🎵 *تيك توك:* {social['tk']}\n"
                    f"👻 *سناب شات:* {social['sn']}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🗺️ *الخريطة:* [فتح الموقع](https://maps.google.com/{name.replace(' ', '+')})\n"
                    f"🕒 *توقيت الرصد:* {time.strftime('%H:%M')} | {time.strftime('%Y-%m-%d')}\n\n"
                    f"👤 _نظام الرصد الذكي - م. أديب_"
                )
                
                if send_to_telegram(msg):
                    with open(DB_FILE, "a") as f: f.write(site_url + "\n")
                    print(f"✅ تم النشر بنجاح: {name}")

            except: continue
    finally:
        driver.quit()
        print("🏁 اكتملت الجولة.")

if __name__ == "__main__":
    run_automation()
