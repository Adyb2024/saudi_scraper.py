import random
import re
import time
import os
import requests
import json
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# ⚙️ إعدادات النظام 2.5 (GitHub Secrets)
# ==========================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DB_FILE = "published_links.txt"

# إعداد المحرك (استخدام أقوى نسخة متاحة للتنفيذ)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro') # Pro لمعالجة أعمق وتفكير منطقي أدق

# ==========================================
# 🧠 محرك الاستدلال الذكي 2.5 (AI Engine)
# ==========================================

def ai_verify_v25(html_content, store_name):
    """
    تحليل "جينات" الموقع لتحديد ما إذا كان افتتاح اليوم فعلاً.
    """
    prompt = f"""
    بصفتك نظام الرادار 2.5 الفائق، حلل الكود المصدري لمتجر ({store_name}).
    
    المهمة:
    1. هل المتجر "وُلد اليوم"؟ ابحث عن وسوم السجلات، رسائل الترحيب بالافتتاح، أو غياب التقييمات والأرشفة.
    2. استخرج رقم الواتساب (تأكد من رمز الدولة).
    3. حدد نوع المنصة (سلة، زد، إلخ).
    
    المعايير الصارمة:
    - إذا كان المتجر قديماً أو براند مشهور (مثل زارا، ناييكي، إلخ) -> REJECT.
    - إذا كان افتتاحاً حقيقياً وحصرياً لليوم -> CONFIRMED.
    
    أجب بتنسيق JSON حصرياً:
    {{
      "status": "CONFIRMED/REJECT",
      "platform": "المنصة",
      "whatsapp": "الرقم",
      "logic": "برهان الذكاء الاصطناعي على حداثة المتجر"
    }}
    
    محتوى الكود:
    {html_content[:10000]}
    """
    try:
        response = model.generate_content(prompt)
        clean_res = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_res)
    except:
        return {"status": "REJECT"}

# ==========================================
# 🚀 محرك الرصد الميداني (The Scraper 2.5)
# ==========================================

def run_automation_v25():
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: published = f.read().splitlines()

    city = random.choice(["الرياض", "جدة", "دبي", "الدوحة", "الكويت"])
    business = random.choice(["متاجر عطور", "متاجر عبايات", "متاجر ملابس", "متاجر إلكترونيات"])
    
    print(f"🛰️ رادار 2.5 ينطلق في: {business} - {city}")
    driver = setup_driver()
    
    try:
        driver.get(f"https://www.google.com/maps/search/{business}+في+{city}?hl=ar")
        time.sleep(15) # وقت كافٍ لفتح الخرائط
        
        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        
        processed = 0
        for el in elements[:15]:
            if processed >= 5: break
            try:
                name = el.get_attribute("aria-label")
                
                # النقر المباشر (تجاوز الأخطاء التقنية)
                driver.execute_script("arguments[0].click();", el)
                time.sleep(10)
                
                try:
                    site_url = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']").get_attribute("href")
                except: continue

                if site_url in published: continue

                # الفحص العميق عبر رادار 2.5
                driver.execute_script(f"window.open('{site_url}');")
                time.sleep(15)
                driver.switch_to.window(driver.window_handles[-1])
                
                analysis = ai_verify_v25(driver.page_source, name)
                
                if analysis.get("status") == "CONFIRMED":
                    wa_number = analysis.get("whatsapp", "")
                    wa_link = f"https://wa.me/{wa_number}" if wa_number else "غير متوفر"
                    
                    msg = (
                        f"🛰️ *رصد ذكي: إصدار الرادار 2.5* 🛰️\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🏢 *المتجر:* {name}\n"
                        f"📍 *الموقع:* {city}\n"
                        f"🛠️ *المنصة:* {analysis.get('platform')}\n"
                        f"🔬 *برهان AI:* {analysis.get('logic')}\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📞 [تواصل عبر الواتساب]({wa_link})\n"
                        f"🔗 [رابط المتجر]({site_url})\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"⚠️ *ملاحظة:* تم التحقق عبر بروتوكول 2.5 الذكي.\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🛰️ *رادار متاجر الخليج الذكي* 🛰️"
                    )
                    
                    if send_telegram(msg):
                        with open(DB_FILE, "a") as f: f.write(site_url + "\n")
                        print(f"✅ تم تأكيد الهدف: {name}")
                        processed += 1
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except: continue
    finally:
        driver.quit()

# [بقية الدوال المساعدة: setup_driver, send_telegram]
