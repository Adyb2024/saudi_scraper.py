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
# 🛰️ بروتوكول الرادار 2.5 (الإصدار الشامل)
# ==========================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DB_FILE = "published_links.txt"

genai.configure(api_key=GEMINI_API_KEY)
# تنفيذ أمرك الصريح بالمسمى الذي طلبته
model = genai.GenerativeModel('gemini-2.5-flash') 

def ai_verify_v25(html_content, store_name):
    """تحليل شامل للافتتاح وروابط التواصل الاجتماعي"""
    prompt = f"""
    بصفتك نظام الرادار 2.5، حلل الكود لمتجر ({store_name}).
    المهمة: هل هذا المتجر 'وُلد اليوم'؟ 
    المطلوب استخراج البيانات التالية بدقة:
    1. الحالة (CONFIRMED/REJECT).
    2. المنصة (سلة، زد، إلخ).
    3. رقم الواتساب.
    4. روابط التواصل (تيك توك، سناب شات، إنستقرام) إذا وجدت.
    
    أجب بتنسيق JSON حصرياً:
    {{
      "status": "CONFIRMED/REJECT",
      "platform": "المنصة",
      "whatsapp": "الرقم",
      "social": {{"tiktok": "رابط", "snapchat": "رابط", "instagram": "رابط"}},
      "logic": "برهان الحداثة"
    }}
    
    الكود: {html_content[:10000]}
    """
    try:
        response = model.generate_content(prompt)
        clean_res = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_res)
        return data
    except Exception as e:
        print(f"⚠️ خطأ في المحرك 2.5: {e}")
        return {"status": "REJECT"}

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def run_automation():
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: published = f.read().splitlines()

    city = random.choice(["الرياض", "جدة", "دبي", "الدوحة", "الكويت"])
    business = random.choice(["متاجر عطور", "متاجر عبايات", "متاجر ملابس", "متاجر تقنية"])
    
    print(f"🛰️ رادار 2.5 (الشامل) ينطلق بمحرك Gemini 2.5 Flash في: {city}")
    driver = setup_driver()

    try:
        driver.get(f"https://www.google.com/maps/search/{business}+في+{city}")
        time.sleep(15)
        
        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        count = 0
        for el in elements[:15]:
            if count >= 5: break
            try:
                name = el.get_attribute("aria-label")
                driver.execute_script("arguments[0].click();", el)
                time.sleep(10)
                
                site_url = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']").get_attribute("href")
                if site_url in published: continue

                driver.execute_script(f"window.open('{site_url}');")
                time.sleep(12)
                driver.switch_to.window(driver.window_handles[-1])
                
                analysis = ai_verify_v25(driver.page_source, name)
                
                if analysis.get("status") == "CONFIRMED":
                    social = analysis.get("social", {})
                    social_text = ""
                    if social.get("tiktok"): social_text += f"📱 [تيك توك]({social['tiktok']})\n"
                    if social.get("snapchat"): social_text += f"👻 [سناب شات]({social['snapchat']})\n"
                    if social.get("instagram"): social_text += f"📸 [إنستقرام]({social['instagram']})\n"

                    msg = (
                        f"🛰️ *رصد ذكي: نظام الرادار 2.5* 🛰️\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🏢 *المتجر:* {name}\n"
                        f"📍 *الموقع:* {city}\n"
                        f"🛠️ *المنصة:* {analysis.get('platform')}\n"
                        f"🔬 *البرهان:* {analysis.get('logic')}\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📞 [تواصل واتساب](https://wa.me/{analysis.get('whatsapp')})\n"
                        f"{social_text}"
                        f"🔗 [رابط المتجر]({site_url})\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🛰️ *رادار متاجر الخليج الذكي* 🛰️"
                    )
                    
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                  data={'chat_id': CHANNEL_ID, 'text': msg, 'parse_mode': 'Markdown', 'disable_web_page_preview': True})
                    
                    with open(DB_FILE, "a") as f: f.write(site_url + "\n")
                    count += 1
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except: continue
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
