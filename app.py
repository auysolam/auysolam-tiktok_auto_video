import streamlit as st
import os
import asyncio
from PIL import Image
import json

# นำเข้าฟังก์ชันจากระบบที่เราเขียนไว้
from core.schema import VideoPlan

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="TikTok Auto Video Generator", page_icon="🎬", layout="wide")

# ฉีด Custom CSS เพื่อปรับแต่ง UI ให้สวยงามล้ำสมัยระดับพรีเมียม และรองรับมือถือขั้นสุด (Mobile-First UI)
st.markdown("""
<style>
    /* ฟอนต์ภาษาไทยเพื่อความอ่านง่ายและทันสมัย */
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Prompt', sans-serif !important;
    }
    
    /* ซ่อน Header และ Footer พื้นฐานของ Streamlit เพื่อให้ดูคล้าย Native App มากขึ้น */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* พื้นหลังแบบ Dark/Glassmorphism เบาๆ ให้ดูล้ำลึก */
    .stApp {
        background-color: #0f1115;
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(20, 30, 48, 0.4), transparent 50%),
            radial-gradient(circle at 85% 30%, rgba(255, 0, 80, 0.1), transparent 50%),
            radial-gradient(circle at 50% -20%, rgba(0, 242, 254, 0.15), transparent 50%);
    }

    /* ปรับแต่งปุ่มให้ดูโดดเด่น เด้ง และน่าสัมผัส */
    .stButton > button {
        background: linear-gradient(135deg, #ff0050 0%, #00f2fe 100%);
        color: white !important;
        border-radius: 999px; /* ปรับให้กลมมนคล้ายปุ่ม iOS/Android ยุคใหม่ */
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1.05rem;
        letter-spacing: 0.5px;
        box-shadow: 0 8px 20px rgba(255, 0, 80, 0.25);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 12px 25px rgba(0, 242, 254, 0.35) !important;
    }
    .stButton > button:active {
        transform: translateY(1px) scale(0.98);
        box-shadow: 0 4px 10px rgba(255, 0, 80, 0.2) !important;
    }

    /* กล่องข้อมูล (Inputs, Selectbox, Uploader, Text Area) ให้ดูแพงคล้าย Glassmorphism */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        background-color: rgba(30, 30, 35, 0.6) !important;
        backdrop-filter: blur(12px);
        padding: 0.6rem 1rem !important;
        font-size: 16px !important; /* บังคับ 16px ป้องกันระบบ iOS ซูมหน้าจออัตโนมัติเวลากดพิมพ์! */
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.2) !important;
        color: white !important;
        transition: border-color 0.3s ease;
    }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus, .stTextArea>div>div>textarea:focus {
        border-color: #00f2fe !important;
        box-shadow: 0 0 0 1px rgba(0, 242, 254, 0.5) !important;
    }

    /* Expander Cards (การ์ดหัวข้อแบบลอยขึ้นมา) */
    div[data-testid="stExpander"] {
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 16px !important;
        background-color: rgba(22, 22, 28, 0.6) !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.25) !important;
        margin-bottom: 1rem !important;
        overflow: hidden;
    }
    .streamlit-expanderHeader {
        background-color: transparent !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        padding: 16px 20px !important;
    }
    div[data-testid="stExpanderDetails"] {
        padding: 1.2rem 1rem !important;
        background-color: rgba(10, 10, 15, 0.3) !important;
        border-top: 1px solid rgba(255,255,255,0.03);
    }

    /* ปรับ File Uploader ดีไซน์ล้ำๆ โดดเด่นท่วงท่า */
    .stFileUploader>div>div {
        border-radius: 20px !important;
        background-color: rgba(40,40,45,0.3) !important;
        border: 2px dashed rgba(255, 0, 80, 0.5) !important;
        padding: 2rem !important;
        transition: all 0.3s ease;
    }
    .stFileUploader>div>div:hover {
        border-color: rgba(0, 242, 254, 0.8) !important;
        background-color: rgba(40,40,45,0.6) !important;
        transform: scale(1.02);
    }

    /* กรอบข้อความแจ้งเตือนต่างๆ ให้ออกมาเหมือน Info Cards (Info/Warning/Error/Success) */
    div[data-testid="stAlert"] {
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15) !important;
        background-color: rgba(30, 30, 35, 0.5) !important;
        backdrop-filter: blur(6px);
        padding: 1rem !important;
    }

    /* พื้นที่แสดงผลซอร์สโค้ด (st.code) ให้โค้งมนและสวยงาม */
    div[data-testid="stCodeBlock"] {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    /* 📱 จัดการเฉพาะหน้าจอมือถือ (Mobile Perfect Fit UX) */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 4rem !important;
        }
        
        /* ปรับหัวข้อใหญ่สุดให้เป็น Gradient ไล่สีสวยๆ สไตล์ TikTok */
        h1 {
            font-size: 1.8rem !important;
            text-align: left;
            background: linear-gradient(135deg, #ff0050 0%, #00f2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem !important;
            line-height: 1.3 !important;
            font-weight: 700 !important;
        }
        
        /* ปรับระดับหัวรองให้มีเส้นขีดล่างเพิ่มคลาส */
        h2 {
            font-size: 1.3rem !important;
            margin-top: 1.5rem !important;
            padding-bottom: 0.5rem !important;
            border-bottom: 2px solid rgba(255, 255, 255, 0.08);
            color: #ececec !important;
        }
        
        h3 {
            font-size: 1.15rem !important;
            color: #d8d8d8 !important;
        }

        /* ขยายระยะสัมผัส (Touch Target) ของตัวเลือก Checkbox/Radio ให้กดง่ายในมือถือ */
        .stCheckbox>label>div[data-testid="stMarkdownContainer"]>p, 
        .stRadio>label>div[data-testid="stMarkdownContainer"]>p {
            font-size: 1.1rem !important;
            padding: 10px 0;
            line-height: 1.4;
        }

        /* ปุ่มต่างๆ ให้นูนและกดง่ายเต็มความกว้างจอ (Full Width) */
        .stButton > button {
            width: 100% !important;
            padding: 1rem !important;
            font-size: 1.15rem !important;
            margin-top: 0.5rem;
        }

        /* Tab เลือกซีนวิดีโอ (Tabs) ขยายใหญ่เป็นปุ่มเมนูให้แตะง่ายๆ */
        button[data-baseweb="tab"] {
            font-size: 1.1rem !important;
            padding: 1rem 1.2rem !important;
            margin-right: 0.5rem !important;
            background-color: rgba(30,30,40,0.6) !important;
            border-radius: 12px 12px 0 0 !important;
            border-bottom: 2px solid transparent !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background-color: rgba(255, 0, 80, 0.15) !important;
            border-bottom: 2px solid #ff0050 !important;
            color: white !important;
            font-weight: 600 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# สร้าง session state เก็บผลลัพธ์วิเคราะห์
if 'product_info' not in st.session_state:
    st.session_state.product_info = None
if 'video_plan_json' not in st.session_state:
    st.session_state.video_plan_json = None
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = {}

st.title("🎬 TikTok Auto Video Generator (Affiliate SaaS)")
st.markdown("อัปโหลดรูปสินค้า 1 รูป แล้วระบบจะคิดสคริปต์ พากย์เสียง และสร้างคลิปวิดีโอปักตะกร้าให้คุณอัตโนมัติ")

# สร้างโฟลเดอร์สำหรับเก็บของ
os.makedirs("assets/input", exist_ok=True)
os.makedirs("output", exist_ok=True)

# ส่วนตั้งค่าโหมดและ API Key 
with st.sidebar:
    st.header("⚙️ การตั้งค่าระบบ")
    st.markdown("**⚙️ โหมดการทำงาน:** 👨‍💻 แมนนวล (ปรุง Prompt ให้ไปก๊อปวาง)")
    st.success("🟢 โหมดแมนนวลทำงานอิสระ 100%\\n(อัปโหลดรูป ฝาก Prompt ให้ AI และนำผลลัพธ์ที่ได้มาก๊อปวางทีละขั้นตอน)")

# ส่วนอัปโหลดภาพสินค้า
uploaded_files = st.file_uploader("📸 อัปโหลดรูปภาพสินค้าของคุณทั้งหมด (รับได้ 1-4 ภาพ) (JPG, PNG, WEBP)", type=['jpg', 'jpeg', 'png', 'webp'], accept_multiple_files=True)

if uploaded_files:
    if len(uploaded_files) > 4:
        st.error("⚠️ กรุณาอัปโหลดรูปภาพไม่เกิน 4 รูปครับ เพื่อให้ระบบทำงานได้อย่างรวดเร็วและไม่โหลดหนักเกินไป")
    else:
        st.write(f"พบภาพทั้งหมด {len(uploaded_files)} ภาพ")
        # รองรับ Mobile Layout 
        num_cols = min(2, len(uploaded_files))
        cols = st.columns(num_cols) 
        image_paths = []
        
        for i, file in enumerate(uploaded_files):
            image = Image.open(file)
            cols[i % num_cols].image(image, use_container_width=True)
            image_path = f"assets/input/app_uploaded_product_{i}.jpg"
            rgb_im = image.convert('RGB')
            rgb_im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
            rgb_im.save(image_path, format="JPEG", quality=95)
            image_paths.append(image_path)
            
        st.markdown("---")
        
        # ถือว่ามีข้อมูลเริ่มต้นเลยเพื่อปลดล็อคขั้นตอนถัดไปในโหมดแมนนวล
        if not st.session_state.product_info:
            st.session_state.product_info = "(ระบบจะให้คุณส่งรูปให้ Gemini วิเคราะห์สินค้าช่วยสำหรับโหมดแมนนวล)"

        # แสดงส่วนตั้งค่าวิดีโอทันทีที่อัปโหลด (ถ้าเป็นแมนนวล) หรือเมื่อวิเคราะห์เสร็จ (ถ้าเป็นออโต้)
        if st.session_state.product_info:
            st.markdown("---")
            st.subheader("⚙️ 2. ปรับแต่งตัวละครและเนื้อเรื่องสำหรับถ่ายทำ")
            
            with st.expander("👤 2.1 - 2.4 ตั้งค่าตัวละครหลัก", expanded=True):
                product_only_mode = st.checkbox("📦 โหมดโชว์เฉพาะสินค้า (ไม่เอาคน/เน้นมุมกล้อง)", value=False)
                fashion_mode = st.checkbox("👗 โหมดแฟชั่นเสื้อผ้า (เน้นตัวละครสวมใส่)", value=False, disabled=product_only_mode)
                
                no_voiceover = False
                if product_only_mode or fashion_mode:
                    no_voiceover = st.checkbox("🚫 ไม่เอาบทพูด (เน้นดนตรีประกอบอย่างเดียว)", value=False)

                char_options = [
                    "สาวไทย (วัยรุ่น)", "หนุ่มไทย (วัยรุ่น)", "สาวไทย (วัยทำงาน)", "หนุ่มไทย (วัยทำงาน)",
                    "นางแบบอินเตอร์", "นายแบบอินเตอร์", "คุณแม่ (แม่และเด็ก)", "แม่บ้าน", "พ่อบ้าน", 
                    "แม่ค้า", "พ่อค้า", "ช่างซ่อม/ช่างเทคนิค", "พนักงานออฟฟิศ", "นักเรียน/นักศึกษา", 
                    "อินฟลูเอนเซอร์/ครีเอเตอร์", "ไรเดอร์/พนักงานส่งของ", "เชฟ/คนทำอาหาร", 
                    "ผู้หญิงทั่วไป", "ผู้ชายทั่วไป", "เด็กเล็ก", "คนแก่", "ครอบครัวพ่อแม่ลูก", 
                    "คู่รัก", "สุนัข", "แมว", "อื่นๆ"
                ]

                if fashion_mode:
                    fashion_item_type = st.selectbox("👗 2.1.2 ประเภทสินค้าแฟชั่น", ["เสื้อ (Tops)", "กางเกง/กระโปรง (Bottoms)", "ชุดเดรส/ชุดเซท (Dress/Sets)", "กระเป๋า (Bags)", "รองเท้า (Shoes)", "หมวก/เครื่องประดับ (Accessories)", "อื่นๆ"])
                else:
                    fashion_item_type = ""
                char_type = st.selectbox("👤 2.1 เลือกตัวละครหลัก", char_options, index=0, disabled=product_only_mode)
                if char_type == "อื่นๆ":
                    char_type = st.text_input("ระบุตัวละครอื่นๆ:", disabled=product_only_mode)
                    
                is_thai_char = st.checkbox("🇹🇭 บังคับตัวละครหน้าตาคนไทย (Thai Nationality)", value=True, disabled=product_only_mode)
                    
                no_char_mode = product_only_mode
                
                if no_char_mode:
                    char_type = "ไม่มีตัวละคร"
                elif is_thai_char and "ไทย" not in char_type:
                    char_type = f"{char_type} (หน้าตาคนไทย เอเชีย)"

                char_style = st.selectbox("🎨 2.2 สไตล์ภาพตัวละคร (Art Style)", ["คนจริงสวยงาม (Realistic)", "การ์ตูน 2D (Anime/Cartoon)", "อวตาร 3D (Pixar/3D Avatar)"], disabled=no_char_mode)
                char_skin = st.selectbox("🎨 2.3 สีผิวตัวละคร", ["ผิวขาว/สว่าง", "ผิวแทน/น้ำผึ้ง", "ผิวคล้ำเข้ม", "ไม่ระบุ (ให้ AI เลือกเอง)"], disabled=no_char_mode)
                char_traits = st.multiselect("✨ 2.4 บุคลิกภาพและรูปร่าง (เลือกได้หลายข้อ)", 
                    ["สวยน่ารัก", "เซ็กซี่เย้ายวน", "หน้าอกใหญ่", "หุ่นนายแบบ/นางแบบ", "หล่อเท่สมาร์ท", "แต่งตัวภูมิฐานดูแพง", "ตลกขบขัน", "ร่าเริงสดใส", "ลึกลับน่าค้นหา"],
                    disabled=no_char_mode
                )
                
            with st.expander("🖼️ 2.4 ฉากหลังและบรรยากาศ", expanded=True):
                char_bg = st.selectbox("🏞️ 2.4 ฉากหลัง (Background)", ["ไม่ระบุ (อิสระตามเนื้อเรื่อง)", "ธรรมชาติป่าไม้ 🌳", "ทะเล/ชายหาด 🌊", "ภูเขา ⛰️", "ในเมือง/ตึกชิคๆ 🏙️"])
                
            with st.expander("🎙️ 2.5 - 2.7 เสียงและซาวด์เอฟเฟกต์", expanded=True):
                use_sfx = st.radio("🔊 2.5 ใส่ซาวด์เอฟเฟกต์ (Sound Effects) ในสคริปต์?", [
                    "ใส่ซาวด์ (เน้นลูกเล่นตื่นเต้น)", 
                    "ไม่ใส่ซาวด์ (เน้นพากย์เสียงอย่างเดียว)",
                    "ไม่ใส่ซาวด์ ไม่พากย์เสียง (เน้นดิบๆ เรียลๆ ภาพไม่กระตุกตามเสียง)"
                ])
                
                if "ไม่พากย์เสียง" in use_sfx:
                    no_voiceover = True
                    
                voice_type = st.selectbox("🎙️ 2.6 เสียงผู้พากย์ (Voice Type)", ["ไม่ระบุ (สุ่มให้เหมาะสม)", "ผู้หญิง", "ผู้ชาย", "เด็ก", "คนแก่", "หุ่นยนต์/AI", "สัตว์ (เช่น หมา/แมวบรรยาย)"], disabled=no_voiceover)
                voice_emotion = st.selectbox("🎭 2.7 อารมณ์ในการพากย์ (Emotion)", ["ไม่ระบุ (สุ่มให้เหมาะสม)", "ตื่นเต้นเร้าใจ (Energetic)", "ตลกขบขัน/กวนๆ (Funny)", "จริงจัง/น่าเชื่อถือ (Professional)", "กระซิบ/น่าค้นหา (ASMR)", "ดราม่า/ซึ้งกินใจ", "สดใส/อ้อนๆ น่ารัก"], disabled=no_voiceover)
    
            traits_str = ", ".join(char_traits) if char_traits else "ทั่วไป"
            no_bgm = "ไม่ใส่ซาวด์" in use_sfx
            sfx_flag = not no_bgm
            
            if no_voiceover and no_bgm:
                sfx_prompt = "ห้ามใส่ Sound Effects, ห้ามใส่ BGM และห้ามพากย์เสียงใดๆ ลงในสคริปต์เด็ดขาด (No voiceover, No SFX) เพื่อให้วิดีโอออกมาภาพนิ่งดิบๆ เรียลๆ ไม่ขยับตามเสียง"
            else:
                sfx_prompt = "ให้ใส่เสียง Sound Effects หรือ BGM กวนๆ ตลกๆ หรือตื่นเต้น แทรกในวงเล็บของ script ด้วย เช่น [เสียงตู้ม] หรือ [เสียงหัวเราะ]" if sfx_flag else "ห้ามใส่ Sound Effects ลงในบทพูด ให้ใช้เสียงพากย์ล้วนๆ"

    
            st.markdown("---")
            st.subheader("⚙️ 3. โครงสร้างวิดีโอ (Video Structure)")
            
            with st.expander("🎞️ ตั้งค่าจำนวนฉากและเวลา", expanded=True):
                num_scenes = st.number_input("🎞️ 3.1 จำนวนฉากทั้งหมด (Scenes)", min_value=1, max_value=10, value=3)
                scene_duration = st.number_input("⏱️ 3.2 ความยาว/ฉาก (วินาที)", min_value=3, max_value=30, value=8)
                product_scene_count = st.number_input("📦 3.3 โชว์สินค้าเน้นๆ (ฉาก)", min_value=0, max_value=num_scenes, value=1)
    
            # ปุ่มกดสร้างวิดีโอ (Step 4)
            st.markdown("---")
            st.subheader("📜 4. สร้าง Master Prompt สำหรับนำไปคุยกับ Gemini Advanced บนเว็บ")
            if st.button("🚀 4.1 คลิกเพื่อสร้างคำสั่ง Prompt อัตโนมัติ", use_container_width=True):
                    
                    script_instruction = '3. คิดบทพากย์ (script) ที่ดึงดูด น่าสนใจ เป็นเรื่องราวเนื้อหาต่อเนื่องกันแบบเนียนๆ ตั้งแต่ซีนแรกจนถึงซีนสุดท้าย (ห้ามตัดจบดื้อๆ) และสอดคล้องกับ "เสียงผู้พากย์" และ "อารมณ์น้ำเสียง" อย่างเคร่งครัด'
                    video_voice_instruction = f'- **ความเนียนระดับ Extend:** บังคับสั่งให้เสียงและภาพต่อกันเนียนที่สุดตั้งแต่ซีน 1 ยันซีนสุดท้าย ใส่คำสั่งว่า "Continuous seamless extension from previous scene, EXACTLY the same character, same environment. Include synchronized voiceover narration in {voice_type} voice with {voice_emotion} tone, EXACTLY the same voice identity across all clips"'
                    
                    if no_char_mode:
                        char_rule = f"- เป็นวิดีโอโชว์สินค้าเพียวๆ ไม่มีคนหรือสัตว์ในภาพเลย (100% Product B-Roll)\n- เน้นดนตรีประกอบน่าตื่นเต้น ตัดต่อเร้าใจ\n"
                        scene_rule = f"2. ทุกซีนต้องเป็นภาพเจาะสินค้า (Product Shot) หรือภาพบรรยากาศสินค้า (Product in Environment) ห้ามวาดมนุษย์หรือตัวละครประหลาดลงในภาพเด็ดขาด\n   - บังคับการเขียน Video Prompt ให้ใช้เทคนิคกล้องหวือหวา (เช่น Dynamic zoom in, Orbit around product, Dolly in, Cinematic pan) เหมือนถ่ายทำโฆษณาสินค้าไฮเอนด์"
                        if no_voiceover:
                            char_rule += "- **ย้ำ: ไม่ต้องคิดบทพูด (Voiceover) เด็ดขาด**\n"
                            if no_bgm:
                                script_instruction = '3. **ห้ามแต่งบทพูดและซาวด์เด็ดขาด** ให้ปล่อยฟิลด์ script ว่างไว้'
                                video_voice_instruction = '- **ข้อบังคับเรื่องเสียง:** กำชับไว้ใน Video Prompt เสมอว่า "NO voiceover, NO dialogue, NO background music, perfectly silent, RAW footage"'
                            else:
                                script_instruction = '3. **ห้ามแต่งบทพูดเด็ดขาด (No Voiceover)** ให้ปล่อยฟิลด์ script ว่างไว้ หรือเขียนเพียงแค่ "[ดนตรีบรรเลงเร้าใจ]"'
                                video_voice_instruction = '- **ข้อบังคับเรื่องเสียง:** กำชับไว้ใน Video Prompt เสมอว่า "NO voiceover, NO dialogue, ONLY energetic background music and cinematic sound effects"'
                    elif fashion_mode:
                        # แยกประเภทสินค้าเพื่อกำหนดฉากเจาะจง
                        if "เสื้อ" in fashion_item_type:
                            focus_target = "เสื้อ (Tops)"
                            pan_target = "แพนครึ่งตัวเห็นด้านบน ที่สวมใส่เสื้อ"
                        elif "กางเกง" in fashion_item_type or "กระโปรง" in fashion_item_type:
                            focus_target = "กางเกง หรือ กระโปรง (Bottoms)"
                            pan_target = "แพนครึ่งตัวเห็นท่อนล่าง ที่สวมใส่กางเกง/กระโปรง"
                        elif "กระเป๋า" in fashion_item_type:
                            focus_target = "กระเป๋า (Bags)"
                            pan_target = "โฟกัสที่กระเป๋าที่ตัวละครถือหรือสะพายอยู่"
                        elif "รองเท้า" in fashion_item_type:
                            focus_target = "รองเท้า (Shoes)"
                            pan_target = "โฟกัสที่รองเท้าที่ตัวละครสวมใส่อยู่"
                        elif "หมวก" in fashion_item_type or "เครื่อง" in fashion_item_type:
                            focus_target = "หมวก หรือ เครื่องประดับ (Accessories)"
                            pan_target = "โฟกัสที่หมวก/เครื่องประดับที่ตัวละครสวมใส่อยู่"
                        else:
                            focus_target = "ตัวสินค้า (Product)"
                            pan_target = "แพนกล้องโฟกัสที่ตัวสินค้าขณะสวมใส่"

                        char_rule = f"- โหมดแฟชั่น (ประเภทสินค้า: {fashion_item_type}): เน้นการถ่ายทอดรูปทรงและดีไซน์ของสินค้า ให้บรรยากาศดูเรียลๆ เหมือนใช้มือถือถ่ายเอง\n- ตัวละครหลัก: {char_type}\n- สีผิว: {char_skin}\n- บุคลิกภาพ/รูปร่าง: {traits_str}\n- **กฎความแม่นยำของสินค้า 100% (CRITICAL MATCH):** AI ฝั่งวาดภาพ(Imagen) จะไม่เห็นภาพอ้างอิงของคุณ ดังนั้นคุณ(Gemini) **ต้องทำหน้าที่เป็นตาให้มัน** หน้าที่ของคุณคือ **วิเคราะห์ลวดลายกราฟิก, สี, ลายพิมพ์, และตัวหนังสือบนสินค้า (เช่น เสื้อลายสงกรานต์มีตัวการ์ตูนอะไรบ้าง มีอักษรอะไร)** แล้วเขียนบรรยายรายละเอียดเหล่านั้นอย่างถี่ยิบที่สุดเป็นภาษาอังกฤษ ลงใน `image_prompt` ทุกซีน! ห้ามเขียนแค่กว้างๆ ว่า 'wearing the exact same shirt' เด็ดขาด!\n"
                        
                        scene_rule = f"""2. การจัดลำดับภาพแต่ละซีน (สำคัญมาก บังคับใช้ตามนี้):
   - ซีนช็อตที่ 1: บังคับดีไซน์ภาพให้เจาะจง **โฟกัสที่ {focus_target} เต็มๆ** เพื่อเปิดคลิป
   - ซีนช็อตที่ 2: เน้นภาพเต็มตัว (Full body shot) ตัวละครเดินอย่างเป็นธรรมชาติ
   - ซีนช็อตที่ 3: เน้นตัวละครโพสท่าชิคๆ อย่างเป็นธรรมชาติ (Natural posing)
   - ซีนช็อตที่ 4: **{pan_target}** อย่างชัดเจน
   (หากมีมากกว่า 4 ซีน ให้สลับหมุนเวียนให้เป็นธรรมชาติ)"""
                        
                        fashion_motion_instruction = f'\n   - **ท่าทางการเคลื่อนไหวภาพ:** บังคับให้สร้างแอนิเมชันความเร็วปกติ ขยับแบบมนุษย์ทั่วไป "Natural everyday human movement, completely normal real-time speed, NO slow-mo, absolutely NO visual effects, RAW authentic smartphone footage, deep depth of field, NO bokeh"'
                        
                        if no_voiceover:
                            char_rule += "- **ย้ำ: ไม่ต้องคิดบทพูด (Voiceover) เด็ดขาด**\n"
                            if no_bgm:
                                script_instruction = '3. **ห้ามแต่งบทพูดและซาวด์เด็ดขาด** ให้ปล่อยฟิลด์ script ว่างไว้'
                                video_voice_instruction = '- **ข้อบังคับเรื่องเสียง:** กำชับไว้ใน Video Prompt เสมอว่า "NO voiceover, NO dialogue, NO background music, perfectly silent, RAW footage"' + fashion_motion_instruction
                            else:
                                script_instruction = '3. **ห้ามแต่งบทพูดเด็ดขาด (No Voiceover)** ให้ปล่อยฟิลด์ script ว่างไว้ หรือเขียนเพียงแค่ "[ดนตรีบรรเลงเร้าใจ]"'
                                video_voice_instruction = '- **ข้อบังคับเรื่องเสียง:** กำชับไว้ใน Video Prompt เสมอว่า "NO voiceover, NO dialogue, ONLY energetic background music and cinematic sound effects"' + fashion_motion_instruction
                        else:
                            video_voice_instruction += fashion_motion_instruction
                    else:
                        char_rule = f"- ตัวละครหลัก: {char_type}\n- สีผิว: {char_skin}\n- บุคลิกภาพ/รูปร่าง: {traits_str}\n- **กฎความแม่นยำของสินค้า 100% (CRITICAL MATCH):** AI ฝั่งวาดภาพจะไม่เห็นภาพอ้างอิงของคุณ ดังนั้นคุณต้องทำหน้าที่เป็นตาให้มัน โดยวิเคราะห์ลวดลายกราฟิก, สี, ลายพิมพ์, ฉลากแบรนด์ และตัวหนังสือบนสินค้า แล้วเขียนบรรยายรายละเอียดเหล่านั้นอย่างถี่ยิบเป็นภาษาอังกฤษ ลงใน `image_prompt` ทุกซีน! ห้ามเขียนแค่กว้างๆ เด็ดขาด\n"
                        scene_rule = f"2. ต้องมีฉากที่เจาะจงนำเสนอ \"ตัวสินค้าชัดๆ (Product Shot)\" จำนวน {product_scene_count} ซีน ส่วนซีนที่เหลือให้เป็น \"ฉากเล่าเรื่อง/ไลฟ์สไตล์ (Story/Lifestyle)\" ที่มีตัวละครหลัก"
                        if no_voiceover and no_bgm: # Edge case general mode without voice and bgm
                            script_instruction = '3. **ห้ามแต่งบทพูดและซาวด์เด็ดขาด** ให้ปล่อยฟิลด์ script ว่างไว้'
                            video_voice_instruction = '- **ข้อบังคับเรื่องเสียง:** กำชับไว้ใน Video Prompt เสมอว่า "NO voiceover, NO dialogue, NO background music, perfectly silent, RAW footage"'

                    if no_char_mode or "คนจริง" in char_style:
                        image_style_instruction = '   - **สไตล์ภาพถ่ายสุดเรียล:** ให้ใส่คำว่า "Ultra-realistic raw smartphone photo, deep depth of field, everything in absolute focus, NO bokeh, completely sharp background, NO blurry background, authentic daily life snapshot" เสมอ เพื่อให้ภาพดูเรียลที่สุดเหมือนคนใช้มือถือถ่ายจริงๆ และ "ห้ามทำหน้าชัดหลังเบลอเด็ดขาด"'
                        video_style_instruction = '   - **สไตล์เรียลๆ ห้ามเบลอฉากหลัง:** บังคับเพิ่ม "Ultra-realistic raw smartphone footage, authentic daily life snapshot, UGC style, extreme deep depth of field, everything in absolute focus, NO bokeh, completely sharp background, NO blurry background" เสมอ'
                    elif "การ์ตูน 2D" in char_style:
                        image_style_instruction = '   - **สไตล์ภาพการ์ตูน 2D:** ให้กำหนดสไตล์ภาพเป็น "High quality 2D Anime style, vibrant colors, flat shading, Ghibli style background, completely sharp focus, NO bokeh" และ "ห้ามทำหน้าชัดหลังเบลอเด็ดขาด"'
                        video_style_instruction = '   - **สไตล์วิดีโอการ์ตูน 2D:** บังคับเพิ่ม "High quality 2D Anime animation, vibrant colors, flat shading, Ghibli style, extremely sharp focus, NO bokeh, completely sharp background, NO blurry background" เสมอ'
                    else: # อวตาร 3D
                        image_style_instruction = '   - **สไตล์ภาพอวตาร 3D:** ให้กำหนดสไตล์ภาพเป็น "High quality 3D Pixar style, cute 3D character, vibrant lighting, highly detailed 3D render, completely sharp focus, NO bokeh" และ "ห้ามทำหน้าชัดหลังเบลอเด็ดขาด"'
                        video_style_instruction = '   - **สไตล์วิดีโออวตาร 3D:** บังคับเพิ่ม "High quality 3D Pixar style animation, highly detailed 3D render, extremely sharp focus, NO bokeh, completely sharp background, NO blurry background" เสมอ'

                    master_prompt = f"""คุณคือผู้เชี่ยวชาญด้านการทำวิดีโอสั้น (TikTok/Reels) สำหรับ Affiliate Marketing หรือขายของออนไลน์
งานของคุณคือวิเคราะห์ 'ภาพสินค้า' ที่ฉันแนบมานี้ และสร้างแผนการทำวิดีโอ (Video Plan) จำนวน {num_scenes} ซีน

ข้อกำหนดของตัวละครและเนื้อเรื่อง:
- ข้อมูลสินค้าเริ่มต้น: {st.session_state.product_info}
{char_rule}- สถานที่/ฉากหลัง (Background): {char_bg}
- ซาวด์เอฟเฟกต์: {sfx_prompt}
- เสียงผู้พากย์ (Voice Type): {voice_type}
- อารมณ์น้ำเสียง (Emotion): {voice_emotion}

กติกาการจัดทำ:
1. ต้องสร้างซีนให้ได้จำนวน {num_scenes} ซีน เป๊ะๆ
{scene_rule}
{script_instruction}
4. เขียนบทพากย์ให้สามารถพูดจบได้ภายใน {scene_duration} วินาทีต่อซีน 
5. เขียน image_prompt เป็นภาษาอังกฤษ เพื่อใช้ **เจนภาพนิ่งด้วย Gemini (Imagen 3)**
   - **สำคัญมาก (การตั้งชื่อไฟล์):** บังคับให้คุณขึ้นต้นประโยคแรกของ `image_prompt` ทุกซีนด้วยคำว่า "Scene_1_", "Scene_2_", "Scene_3_" ... ตามลำดับซีนเสมอ (เช่น "Scene_1_ Vertical 9:16 aspect ratio...") เพื่อให้เวลาที่ฉันกดดาวน์โหลดรูปภาพที่คุณวาด ชื่อไฟล์จะได้ไม่ซ้ำกันและง่ายต่อการอัปโหลด
   - บังคับให้ใส่: "Vertical 9:16 aspect ratio, NO text overlays, NO typography, ONLY one single distinct scene, NO 4-panel grid, NO split screen"
   - **กฎการแยกภาพ (No Grid/Collage):** ห้ามให้ AI เจนภาพ 4 ซีนรวมอยู่ในรูปเดียว (กากบาท/ตาราง 4 ช่อง) อย่างเด็ดขาด! บังคับเขียนสั่งท้าย prompt ว่า "Single full frame, absolutely NO multi-panel collage"
   - **กฎการล็อกเป้าตัวละครและสถานที่ (CRITICAL: 100% UNIFIED SCENE & CHARACTER):** คุณต้องสร้างข้อความอธิบายตัวละคร ชุด และสถานที่ ที่ละเอียดมาก (MASTER_APPEARANCE_AND_ENVIRONMENT_PROMPT) ขึ้นมา 1 ชุดตายตัว และ **"คุณต้อง COPY และ PASTE ข้อความชุดนี้ใส่เป็นคำขึ้นต้นใน `image_prompt` ของทุกๆ ซีนแบบห้ามตัวอักษรเพี้ยนแม้แต่คำเดียวเด็ดขาด"** (ห้ามสลับสถานที่ ห้ามสลับชุด ห้ามเปลี่ยนทรงผม เรื่องราวทั้งหมดต้องเกิดใน 'สถานที่เดียวกัน' และ 'เวลาต่อเนื่องกัน' ทั้งคลิป)
   - **การขยับท่าทาง (Action):** เมื่อคุณวางข้อความ Master Prompt แล้ว ตอนท้ายของแต่ละซีนค่อยเขียนเปลี่ยนเฉพาะ "ท่าทางการโพส การกระทำ และ มุมกล้อง (Camera Angle/Action/Pose)" ให้ร้อยเรียงกันเป็นเรื่องราวเดียวตั้งแต่ซีนแรกจนซีนสุดท้ายเสมือนการถ่ายวิดีโอต่อเนื่อง (Single Location)
   - **กฎความสมส่วนหน้าตาและสินค้า:** ให้สั่งย้ำคำว่า "Realistic anatomical proportions, product size is naturally scaled, EXACTLY the same person identity and exact same environment across all scenes" เพื่อให้ขนาดสินค้าไม่ผิดเพี้ยน
{image_style_instruction}
   - **กฎการเก็บรายละเอียดด้านหลังสินค้า:** เนื่องจาก AI มักจะวาดด้านหลังเสื้อผ้า (เช่น เสื้อยืด) ออกมาเพี้ยน หากมีการแพนกล้องให้เห็นด้านหลัง ให้คุณวาดลวดลายด้านหลัง **"ให้เหมือนกับด้านหน้าเป๊ะๆ"** (Mirror the exact front design/pattern to the back) ห้ามมโนสร้างลวดลายใหม่ขึ้นมาเอง หรือถ้าหลีกเลี่ยงได้ให้เน้นถ่ายแต่ด้านหน้า (Front view only) เป็นหลัก
   - บรรยายแสงเงา บรรยากาศ มุมกล้อง (Lighting, Mood, Camera angle) ให้สวยงามสมจริง ห้ามสั่งให้วาดป้ายราคา/ข้อความ
6. เขียน video_prompt เป็นภาษาอังกฤษ สำหรับ **เจนวนิเมชัน+เสียง บน Google Labs Flow**
{video_style_instruction}
   - **กฎการพาแพนกล้อง (มุมด้านหลัง):** หากไม่มีความจำเป็น ให้หลีกเลี่ยงการเขียน Prompt สั่งแพนกล้องไปข้างหลัง ให้เน้นขยับกล้องเฉพาะด้านหน้า (Front view only) แต่ถ้าจำเป็นต้องเห็นด้านหลัง บังคับเขียนคำสั่งเพิ่มว่า "Back design is exactly identical to the front pattern" เพื่อไม่ให้ AI มโนลวดลายประหลาดๆ ขึ้นมาเอง
   - **ความต่อเนื่องแบบ Extend เนียนๆ:** ตั้งแต่ซีน 2 เป็นต้นไป ให้บังคับสั่ง "Continuous seamless extension from the exact previous frame, exact same subject, exact same environment, no cuts, perfectly smooth transition"
   - การขยับ: เน้นสั่งเฉพาะ 'Camera motion' และ 'Subject motion' รวบกับ "NO text overlays" อย่างกระชับ พร้อมทั้งบังคับเขียนคำสั่งให้วิดีโอความเร็วปกติ (Normal speed, NO slow-motion), ไม่ต้องมีเอฟเฟคต์แต่งเติมใดๆ (NO digital effects) จัดแสงให้ออกมาเหมือนครีเอเตอร์รีวิวสินค้าเอง (Natural daily lighting, Creator POV, UGC style) และ "ห้ามจัดแสงสีระดับ Studio สวยเกินจริงเด็ดขาด!" (Strictly NO studio lighting)
   {video_voice_instruction}
7. **Task 1 (ข้อมูล JSON อย่างเดียว):** เนื่องจากข้อจำกัดของระบบแชท ให้ส่งโครงสร้างบทวิเคราะห์ทั้งหมดมาเป็นโค้ด JSON อย่างเดียวโดยยึดตามโครงสร้างที่กำหนด (ไม่ต้องพยายามสร้างภาพกราฟิก)
8. **คำสั่งสำคัญเรื่องการตลาด:** หน้าที่ของคุณคือการเป็น Content Creator และนักการตลาดเชี่ยวชาญด้าน Affiliate Marketing บน TikTok โปรดดูภาพสินค้าที่ฉันแนบมานี้ และวิเคราะห์จุดขายเพื่อร่างข้อความโพสต์ใส่ลงใน `tiktok_post_data` ดังนี้
   - Product Details: เขียนสรรพคุณจุดเด่นชัดเจนของสินค้า (3-4 บรรทัด)
   - Overlay Text: ข้อความพาดหัวฮุคคนดู สำหรับแปะไว้บนคลิปวิดีโอ (สั้นๆ กระชับ ไม่เกิน 10 คำ) ตามแต่ละซีนของวิดีโอ
   - Link Title: ชื่อปุ่มตะกร้าสีเหลืองที่ดึงดูดใจให้นิ้วลั่น (สั้นๆ เช่น ราคา "โปรไฟไหม้🔥 จิ้มเลย")
   - Post Caption: แคปชั่นใต้โพสต์สไตล์ TikTok เน้นภาษาเป็นกันเอง กระตุ้นให้อยากซื้อทันที
   - Hashtags: แฮชแท็กที่เกี่ยวข้องและเป็นกระแส (5-8 แท็ก)

ขอให้ตอบกลับด้วยรูปแบบ JSON ตามโครงสร้างด้านล่างนี้เพียงอย่างเดียว:
{VideoPlan.model_json_schema()}"""
                    st.info("ขั้นตอนการทำ: 1) ถ่ายรูปสินค้าอัปโหลดขึ้นเว็บ Gemini 2) ก๊อปปี้คลิปบอร์ดข้อความกล่องดำด้านล่างเพื่อส่งให้มันคิดบทเป็น JSON")
                    st.link_button("🌐 คลิกเปิดหน้าต่างเว็บ Gemini Advanced ตรงนี้", "https://gemini.google.com/app", use_container_width=True)
                    st.code(master_prompt, language="text")
                    
                    st.warning("💡 **คำแนะนำเพิ่มเติม:** เนื่องจากบางบัญชีของ Gemini ไม่รองรับการวาดรูปภาพ หรือติดปัญหาด้าน Policy หลังจากที่คุณได้โค้ด JSON ด้านล่างแล้ว **ให้คุณนำ `image_prompt` ของแต่ละซีน ไปเจนรูปในโปรแกรมฟรี เช่น Google ImageFX, Microsoft Designer หรือ Midjourney แทนครับ**")
                
            st.markdown("---")
            st.subheader("📥 4.5 วางผลลัพธ์จาก Gemini ลงที่นี่")
            default_json = st.session_state.get('demo_pasted_json', '')
            pasted_json = st.text_area("เมื่อหน้าเว็บ Gemini พิมพ์บทให้เสร็จ ให้ก๊อปปี้ 'โค้ด JSON' ทั้งหมด นำมาประเคนไว้ในช่องนี้ครับ:", value=default_json, height=150)
            if st.button("✅ ประมวลผลตารางสคริปต์ (Render Storyboard)", use_container_width=True):
                if pasted_json.strip():
                    try:
                        # ล้างโค้ด Markdown block ออกเผื่อผู้ใช้ก๊อปมาติด ```json 
                        cleaned_json = pasted_json.replace("```json", "").replace("```", "").strip()
                        video_plan = VideoPlan.model_validate_json(cleaned_json)
                        st.session_state.video_plan_json = cleaned_json
                        st.session_state.generated_images = {}
                        st.success(f"✅ ประมวลผลโค้ดแยกช็อตสำเร็จ! (สินค้า: {video_plan.product_name})")
                    except Exception as e:
                        st.error(f"❌ รูปแบบ JSON ไม่ถูกต้อง กรุณาเช็คว่าก๊อปปี้โค้ดมาครบทุกบรรทัดตั้งแต่ปีกกาเปิดยันปิดหรือไม่ (รายละเอียด: {e})")
                else:
                    st.warning("⚠️ กรุณาวางโค้ด JSON ก่อนกดปุ่มครับ")

        # ส่วนที่ดึงตารางและขั้นตอนหลังจากโหลด JSON ยัดเข้า session_state เรียบร้อย
        if st.session_state.video_plan_json:
            try:
                video_plan = VideoPlan.model_validate_json(st.session_state.video_plan_json)
                
                # โชว์แท็บจัดกลุ่มตามซีน
                st.markdown("---")
                st.subheader("📋 5. แผนการทำวิดีโอรายฉาก (Storyboard & Prompts)")
                st.info("แตะขวา/ซ้าย ที่แท็บเพื่อดูรายละเอียดและอัปโหลดวิดีโอทีละซีน👇")
                st.markdown("*(ก๊อปปี้ Image Prompt แยกไปเจนภาพในเว็บด้านล่างนี้ได้เลย)*")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.link_button("🖼️ สร้างรูปภาพด้วย Gemini", "https://gemini.google.com/app", use_container_width=True)
                with col_btn2:
                    st.link_button("🎥 สร้างฟุตเทจด้วย Labs Flow", "https://labs.google/fx/tools/flow", use_container_width=True)

                os.makedirs("assets/video", exist_ok=True)
                os.makedirs("assets/audio", exist_ok=True)

                # สร้างคำสั่ง Image Prompt แบบรวมทุกซีน
                st.markdown("---")
                with st.expander("✨ เจนภาพทุกซีนพร้อมกันในคำสั่งเดียว (Combined Image Prompt)", expanded=False):
                    st.write("ก๊อปปี้คำสั่งด้านล่างไปวางใน AI Image Generator (เช่น Gemini, ChatGPT) เพื่อให้วาดรูปให้ครบทุกซีนในครั้งเดียว")
                    st.warning("⚠️ **ปัญหาที่พบบ่อย (AI ขี้เกียจ):** หาก Gemini วาดให้แค่รูปเดียวแล้วหยุด ให้พิมพ์ด่า AI ไปว่า **'ยังวาดไม่ครบ วาดซีนที่เหลือต่อให้จบเดี๋ยวนี้'** หรือใช้วิธีก๊อปปี้ไปวางทีละรูปครับ")
                    
                    # รูปแบบ Text Prompt
                    combined_text = f"🚨 คำสั่งระดับสูงสุด: คุณต้องสร้างรูปภาพแยกกันทั้งหมด {len(video_plan.scenes)} รูป ตาม Prompt ด้านล่างนี้ให้ครบทุก Scene ในการตอบกลับครั้งเดียว! ห้ามวาดรวมกัน และห้ามข้าม Scene ใด Scene หนึ่งไปเด็ดขาด! (CRITICAL MANDATORY: Generate {len(video_plan.scenes)} INDIVIDUAL images consecutively. DO NOT stop until you generate all {len(video_plan.scenes)} images.)\n\n"
                    for scene in video_plan.scenes:
                        combined_text += f"--- [รูปภาพที่ {scene.scene_number}] ---\n{scene.image_prompt}\n\n"
                    
                    # รูปแบบ JSON กรณีใช้กับ Tool อื่นๆ
                    combined_json = json.dumps([{"scene": s.scene_number, "image_prompt": s.image_prompt} for s in video_plan.scenes], indent=2, ensure_ascii=False)
                    
                    t1, t2 = st.tabs(["📝 แบบข้อความ (เอาไปวางใน Gemini/ChatGPT)", "⚙️ แบบรหัส JSON (เอาไปใช้กับ Automation Tools)"])
                    with t1:
                        st.code(combined_text, language="text")
                    with t2:
                        st.code(combined_json, language="json")
                

                # ใช้ระบบ Tabs เป็นมิตรกับมือถือและลดการไถจอ
                scene_tabs = st.tabs([f"🎬 ซีน {scene.scene_number}" for scene in video_plan.scenes])
                
                for i, scene in enumerate(video_plan.scenes):
                    with scene_tabs[i]:
                        st.markdown(f"**⏱️ เวลา:** {scene.timecode_start} - {scene.timecode_end}")
                        st.markdown(f"**🗣️ บทพากย์/เสียง:** {scene.script}")
                        
                        st.markdown("---")
                        st.write("🖼️ **1. นำพรอมต์นี้ไปสร้างรูป (Image Prompt):**")
                        st.code(scene.image_prompt, language="text")
                        
                        st.markdown("---")
                        st.write("🎥 **2. นำรูปภาพและพรอมต์นี้ไปทำภาพเคลื่อนไหว:**")
                        st.code(f"{scene.video_prompt}\\n(Voiceover: {scene.script})", language="text")
                        
            except Exception as e:
                st.error(f"ข้อผิดพลาดระหว่างแสดงผลสคริปต์: {e}")
                
        st.markdown("---")
        st.subheader("📝 6. ข้อมูลสำหรับโพสต์ TikTok (Caption & Hashtags)")
        st.write("ระบบจะดึงข้อมูลแคปชั่นและแฮชแท็กมาให้โดยอัตโนมัติ จากโค้ด JSON ที่คุณวางในขั้นตอนที่ 4.5")
        
        if st.session_state.video_plan_json:
            try:
                import json
                video_plan_data = json.loads(st.session_state.video_plan_json)
                post_data = video_plan_data.get('tiktok_post_data')
                
                if post_data:
                    st.info("**📌 รายละเอียดสินค้า**")
                    st.code(post_data.get('product_details', ''), language="text")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success("**💬 ข้อความพาดหัวคลิป (Overlay Text)**")
                        st.code(post_data.get('overlay_text', ''), language="text")
                        
                        st.warning("**🛒 ชื่อปุ่มตะกร้า/ลิงก์**")
                        st.code(post_data.get('link_title', ''), language="text")
                    with col2:
                        st.info("**📝 แคปชั่นโพสต์ขาย (Caption)**")
                        st.code(post_data.get('post_caption', ''), language="text")
                        
                        st.write("**#️⃣ แฮชแท็ก**")
                        st.code(post_data.get('hashtags', ''), language="text")
                else:
                    st.warning("⚠️ ไม่พบข้อมูลแคปชั่นและแฮชแท็กในโค้ด JSON กรุณากลับไปเช็ค Gemini หรือลองกดสร้างโค้ดใหม่อีกครั้งครับ")
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาดในการวิเคราะห์ข้อมูลแคปชั่น: {e}")
        else:
            st.info("👈 เมื่อคุณนำโค้ด JSON วางในข้อ 4.5 เสร็จแล้ว ข้อมูลโพสต์ทั้งหมดจะเด้งขึ้นมาตรงนี้ทันทีครับ!")
