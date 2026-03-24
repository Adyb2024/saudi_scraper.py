import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import random
import time
import os
import requests
import json
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ==========================================
# 🛰️ رادار 2.5 الشامل - بمحرك Gemini 2.5 Flash
# ==========================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DB_FILE = "published_links.txt"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

def ai_verify_v25(html_content, store_name):
    prompt = f"""
    بصفتك نظام الرادار 2.5، حلل المتجر ({store_name}).
    المطلوب: هل الافتتاح جديد (CONFIRMED/REJECT)؟
    استخرج: المنصة، رقم الواتساب، وروابط (تيك توك، سناب شات، إنستقرام).
    أجب بتنسيق JSON فقط.
    الكود: {html_content[:10000]}
    """
    try:
        response = model.generate_content(prompt)
        clean_res = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_res)
    except:
        return {"status": "REJECT"}

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def run_automation():
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: published = f.read().splitlines()

    city = random.choice(["الرياض", "جدة", "دبي", "الكويت"])
    business = random.choice(["متاجر عطور", "متاجر ملابس", "متاجر تقنية"])
    
    print(f"🛰️ الرادار ينطلق في: {city}")
    driver = setup_driver()

    try:
        driver.get(f"https://www.google.com/maps/search/{business}+في+{city}")
        time.sleep(15)
        
        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        count = 0
        for el in elements[:10]:
            if count >= 5: break
            try:
                name = el.get_attribute("aria-label")
                driver.execute_script("arguments[0].click();", el)
                time.sleep(10)
                
                site_url = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']").get_attribute("href")
                if site_url in published: continue

                driver.execute_script(f"window.open('{site_url}');")
                time.sleep(10)
                driver.switch_to.window(driver.window_handles[-1])
                
                analysis = ai_verify_v25(driver.page_source, name)
                
                if analysis.get("status") == "CONFIRMED":
                    social = analysis.get("social", {})
                    s_links = []
                    if social.get("tiktok"): s_links.append(f"📱 [تيك توك]({social['tiktok']})")
                    if social.get("snapchat"): s_links.append(f"👻 [سناب شات]({social['snapchat']})")
                    if social.get("instagram"): s_links.append(f"📸 [إنستقرام]({social['instagram']})")
                    
                    msg = (
                        f"🛰️ *رصد ذكي: نظام الرادار 2.5* 🛰️\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🏢 *المتجر:* {name}\n"
                        f"🛠️ *المنصة:* {analysis.get('platform')}\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📞 [تواصل واتساب](https://wa.me/{analysis.get('whatsapp')})\n"
                        f"{chr(10).join(s_links)}\n"
                        f"🔗 [رابط المتجر المباشر]({site_url})\n"
                        f"━━━━━━━━━━━━━━━"
                    )
                    
                    # إرسال الرسالة وطباعة النتيجة للتحقق
                    res = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                  data={'chat_id': CHANNEL_ID, 'text': msg, 'parse_mode': 'Markdown', 'disable_web_page_preview': True})
                    
                    print(f"📡 نتيجة إرسال تليجرام لـ {name}: {res.status_code} - {res.text}")
                    
                    if res.status_code == 200:
                        with open(DB_FILE, "a") as f: f.write(site_url + "\n")
                        count += 1
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except: continue
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
