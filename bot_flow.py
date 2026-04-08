import asyncio
import json
import os
import sys
import pyperclip
import base64
from datetime import datetime
from playwright.async_api import async_playwright

# ตั้งค่าแก้ปัญหา path ถ้าไม่รันจาก root
sys.path.append(os.path.dirname(os.path.abspath(__name__)))
from core.schema import VideoPlan

STATE_FILE = "output/bot_state.json"

def update_state(status, message, progress=0, current_scene=0, total_scenes=0, screenshot_path=None):
    # อ่านค่าเดิมมาผสมกับค่าใหม่เพื่อไม่ให้โดนทับหมดถ้าไม่ได้ส่งมาครบ
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except:
        state = {}
        
    state.update({
        "status": status,
        "message": message,
        "progress": progress,
        "current_scene": current_scene,
        "total_scenes": total_scenes,
        "last_updated": datetime.now().isoformat()
    })
    
    if screenshot_path:
        state["screenshot_path"] = screenshot_path
        
    if "user_action" not in state:
        state["user_action"] = "none"

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)
        
async def snapshot(page):
    screenshot_path = "output/latest_screenshot.jpg"
    try:
        await page.screenshot(path=screenshot_path, type="jpeg", quality=40)
        return screenshot_path
    except:
        return None

async def wait_for_user_action(page, prompt_message, progress=0, current_scene=0, total_scenes=0):
    print(f"⏳ {prompt_message} (รอคำสั่งจากมือถือ)")
    while True:
        ss_path = await snapshot(page)
        update_state("waiting", prompt_message, progress, current_scene, total_scenes, screenshot_path=ss_path)
        
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                if state.get("user_action") == "continue":
                    state["user_action"] = "none"
                    with open(STATE_FILE, "w", encoding="utf-8") as fw:
                        json.dump(state, fw, ensure_ascii=False, indent=4)
                    break
                elif state.get("user_action") == "stop":
                    print("🛑 ผู้ใช้สั่งหยุดบอท")
                    sys.exit(0)
        except:
            pass
            
        await asyncio.sleep(2)


async def run_bot():
    print("🤖 กำลังเปิด Playwright Bot สำหรับ Google Labs Flow...")
    update_state("starting", "กำลังเปิดบอท...")
    
    # 1. โหลดข้อมูลแผนจากแอป (ถ้ามี)
    plan_path = "output/latest_plan.json"
    if not os.path.exists(plan_path):
        print(f"❌ ไม่พบไฟล์ {plan_path} \nกรุณาไปกดปุ่ม 'วิเคราะห์ด้วย AI' ในแอป (app.py) ก่อนเพื่อให้ระบบสร้างไฟล์แผนงานครับ")
        return
        
    with open(plan_path, "r", encoding="utf-8") as f:
        video_plan_data = json.load(f)
        video_plan = VideoPlan(**video_plan_data)
        
    image_input_path = "assets/input/app_uploaded_product_0.jpg"
    
    # 2. เริ่มต้น Playwright แบบ Persistent เพื่อให้จำ Login Google ไว้
    # โฟลเดอร์ที่ใช้เก็บ Cookies (ถ้าแบนๆให้ใช้ browser แบบไม่ Headless จะได้แก้ captcha ได้)
    user_data_dir = os.path.abspath("venv/playwright_chrome_profile")
    
    async with async_playwright() as p:
        print("🌐 กำลังเปิดเบราว์เซอร์ Chrome...")
        # เราใช้ Channel chrome เพื่อให้ใช้ Chrome ตัวเต็มในเครื่อง (จะช่วยหลบกัปช่า Google ได้ระดับนึง)
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False, # ต้องเห็นหน้าจอ
            channel="chrome", # ใช้ Google Chrome ในเครื่อง
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            no_viewport=True
        )
        
        page = await browser.new_page()
        print("🔗 เข้าสู่เว็บไซต์ Google Labs Flow...")
        await page.goto("https://labs.google/fx/tools/flow", timeout=60000)
        
        print("\n⏳ 1) กรุณาล็อกอิน Google ด้วยตนเอง (ถ้าเพิ่งเปิดบอทครั้งแรก)")
        print("⏳ 2) เตรียมตัวในเว็บให้เห็นหน้าตาเครื่องมือ Flowise")
        await wait_for_user_action(page, "ล็อกอินให้เสร็จ แล้วกดยืนยันด้านล่างเพื่อเริ่มบอท", 10, 0, len(video_plan.scenes))
        
        # js snippet สำหรับทะลวงดึงรูปที่ AI เพิ่งเจนเสร็จ
        get_last_image_js = """
        async () => {
            let resultUrl = null;
            let imgs = Array.from(document.querySelectorAll('img')).filter(i => i.width > 200 && i.height > 200);
            if(imgs.length > 0) {
                let lastImg = imgs[imgs.length - 1];
                if(lastImg.src.startsWith('data:')){
                    resultUrl = lastImg.src;
                } else if (lastImg.src.startsWith('blob:') || lastImg.src.startsWith('http')) {
                    try {
                        let response = await fetch(lastImg.src);
                        let blob = await response.blob();
                        resultUrl = await new Promise((resolve, reject) => {
                            let reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.onerror = reject;
                            reader.readAsDataURL(blob);
                        });
                    } catch(e) {}
                }
            }
            if (!resultUrl) {
                let canvases = Array.from(document.querySelectorAll('canvas')).filter(c => c.width > 200 && c.height > 200);
                if (canvases.length > 0) {
                    resultUrl = canvases[canvases.length - 1].toDataURL();
                }
            }
            return resultUrl;
        }
        """

        print("\n==================================")
        print("🚀 เริ่มลุยเจนรูปและวิดีโอ (Scene by Scene)")
        print("==================================")

        for scene in video_plan.scenes:
            print(f"\n▶️ [Scene {scene.scene_number}]")
            
            # -------------------------------------------------------------
            # Step 1: เจนรูปภาพ (Image)
            # -------------------------------------------------------------
            print("🔹 Copy Image Prompt:")
            print("-" * 40)
            print(scene.image_prompt)
            print("-" * 40)
            
            try: pyperclip.copy(scene.image_prompt)
            except: pass
            
            update_state("running", f"กำลังกรอกข้อมูล Image ให้ซีน {scene.scene_number} / {len(video_plan.scenes)}", 20, scene.scene_number, len(video_plan.scenes), screenshot_path=await snapshot(page))
            
            if scene.scene_number == 1:
                await page.wait_for_timeout(3000)
                
            try: await page.get_by_text("New project", exact=True).first.click(timeout=3000)
            except: pass
            
            try: await page.get_by_text("image", exact=True).first.click(timeout=3000)
            except: pass
            
            try: await page.get_by_text("9:16", exact=True).first.click(timeout=3000)
            except: pass
            
            try: await page.get_by_text("X1", exact=True).first.click(timeout=3000)
            except: pass
            
            try: await page.get_by_text("nano banana pro", exact=True).first.click(timeout=3000)
            except: pass
            
            try: await page.locator("input[type='file']").first.set_input_files(image_input_path, timeout=3000) 
            except: pass
            
            try:
                textarea = page.locator("textarea").first
                await textarea.fill("", timeout=3000)
                await textarea.fill(scene.image_prompt, timeout=3000)
                await page.get_by_text("Generate", exact=True).first.click(timeout=3000)
                print(f"✅ บอทกด Generate รูปภาพซีน {scene.scene_number}")
            except Exception as e:
                print(f"⚠️ บอทพยายามป้อน Prompt อัตโนมัติแต่ไม่สำเร็จ: {e}")
                
            print("⏳ บอทกำลังรอ AI สร้างรูปภาพ (รอประมาณ 35 วินาที)...")
            update_state("waiting", f"รอเจนรูปซีน {scene.scene_number} เสร็จ บอทกำลังพยายามดึงรูป...", 30, scene.scene_number, len(video_plan.scenes))
            await page.wait_for_timeout(35000)
            
            # --- Auto Extract Image ---
            generated_img_path = f"assets/input/generated_scene_{scene.scene_number}.jpg"
            print("📸 กำลังดึงรูปล่าสุดจากจออัตโนมัติ (แทบลากรูป)...")
            data_url = await page.evaluate(get_last_image_js)
            if data_url and "," in data_url:
                try:
                    header, encoded = data_url.split(",", 1)
                    with open(generated_img_path, "wb") as f:
                        f.write(base64.b64decode(encoded))
                    print(f"✅ บอทดึงรูปล่าสุดสำเร็จ! ถือว่าแนบไว้เตรียมทำวิดีโอแล้ว")
                except Exception as e:
                    print(f"⚠️ แปลงรูปภาพล้มเหลว: {e}")
            else:
                print("⚠️ บอทหารูปล่าสุดไม่เจอ (ทำไว้เผื่อต้องลากเอง)")
            
            await page.wait_for_timeout(2000)
            
            # -------------------------------------------------------------
            # Step 2: เจนวิดีโอ (Video)
            # -------------------------------------------------------------
            print("\n🔹 Copy Video Prompt:")
            print("-" * 40)
            print(scene.video_prompt)
            print("-" * 40)
            
            try: pyperclip.copy(scene.video_prompt)
            except: pass
            
            update_state("running", f"กำลังกรอกข้อมูล Video ให้ซีน {scene.scene_number} / {len(video_plan.scenes)}", 60, scene.scene_number, len(video_plan.scenes), screenshot_path=await snapshot(page))
            
            try: await page.get_by_text("video", exact=True).first.click(timeout=3000)
            except: pass
            
            try: await page.get_by_text("frames", exact=True).first.click(timeout=3000)
            except: pass
            
            try: await page.get_by_text("9:16", exact=True).first.click(timeout=3000)
            except: pass
            
            try: await page.get_by_text("X1", exact=True).first.click(timeout=3000)
            except: pass
            
            try: await page.get_by_text("veo3.1 -fast [lower priority]", exact=True).first.click(timeout=3000)
            except: 
                try: await page.get_by_text("veo3.1 -fast").first.click(timeout=3000)
                except: pass
            
            if os.path.exists(generated_img_path):
                try: 
                    await page.locator("input[type='file']").first.set_input_files(generated_img_path, timeout=3000) 
                    print("✅ บอทนำรูปที่เจนเมื่อสักครู่ อัปโหลดกลับไปทำวิดีโอให้แล้ว!")
                except: 
                    print("⚠️ บอทอัปรูปลงช่องรับไฟล์ไม่ได้")
            
            try:
                textarea = page.locator("textarea").first
                await textarea.fill("", timeout=3000)
                await textarea.fill(scene.video_prompt, timeout=3000)
                
                try: await page.get_by_text("Generate", exact=True).first.click(timeout=3000)
                except: 
                    try: await page.get_by_text("Start").first.click(timeout=3000)
                    except: pass
                    
                print(f"✅ บอทกดสั่งเจนวิดีโอซีน {scene.scene_number} แล้ว!")
            except Exception as e:
                print(f"⚠️ บอทหาช่องกรอก Prompt Video ไม่เจอ: {e}")
            
            print("⏳ บอทกำลังรอ AI สร้างวิดีโอ (ประมาณ 70 วินาที)...")
            update_state("waiting", f"รอเจนวิดีโอซีน {scene.scene_number}... (จะทำต่ออัตโนมัติ)", 80, scene.scene_number, len(video_plan.scenes))
            await page.wait_for_timeout(70000)
            
            print(f"✅ จบกระบวนการ ซีน {scene.scene_number}")
            
        print("\n🎉 ทำงานเสร็จสิ้นทั้งหมดแล้ว ดาวน์โหลดเข้า CapCut ต่อได้เลย!")
        update_state("finished", "เสร็จสิ้นทุกกระบวนการ! ประกอบคลิปใน CapCut ต่อได้เลย 🚀", 100, len(video_plan.scenes), len(video_plan.scenes), screenshot_path=await snapshot(page))
        await asyncio.sleep(10)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
