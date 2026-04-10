import streamlit as st
import os
import asyncio
from PIL import Image
import json
import google.generativeai as genai

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
    
    /* ซ่อน Header และ Footer พื้นฐานของ Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* พื้นหลังแบบ Dark Theme เรียบหรู สะอาดตา (พรีเมียมแบบ Flat) */
    .stApp {
        background-color: #121212;
    }

    /* ปรับแต่งปุ่มให้ดูโดดเด่นแต่เรียบง่าย ไม่เรืองแสง */
    .stButton > button {
        background-color: #333333;
        color: white !important;
        border-radius: 8px; /* โค้งมนกำลังดี */
        border: 1px solid #444444;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-size: 1.05rem;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #4a4a4a;
        border-color: #666666;
    }
    .stButton > button:active {
        background-color: #2a2a2a;
        transform: translateY(1px);
    }
    
    /* เน้นปุ่มหลัก (Primary Button) ให้เป็นสีหลักของแอป เช่น ชมพู TikTok หม่นๆ เพื่อความมินิมอล */
    button[kind="primary"] {
        background-color: #e62e5c !important;
        border-color: #e62e5c !important;
    }
    button[kind="primary"]:hover {
        background-color: #d12250 !important;
    }

    /* กล่องข้อมูล (Inputs, Selectbox, Uploader, Text Area) เรียบหรูไม่เรืองแสง */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px !important;
        border: 1px solid #333333 !important;
        background-color: #1e1e1e !important;
        padding: 0.6rem 1rem !important;
        font-size: 16px !important; /* บังคับ 16px ป้องกันระบบ iOS ซูมหน้าจออัตโนมัติเวลากดพิมพ์! */
        color: white !important;
        transition: border-color 0.2s ease;
    }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus, .stTextArea>div>div>textarea:focus {
        border-color: #888888 !important;
        box-shadow: none !important;
    }

    /* Expander Cards (การ์ดหัวข้อแบบลอยขึ้นมาแบบ Clean) */
    div[data-testid="stExpander"] {
        border: 1px solid #2a2a2a !important;
        border-radius: 12px !important;
        background-color: #181818 !important;
        margin-bottom: 1rem !important;
        overflow: hidden;
    }
    .streamlit-expanderHeader {
        background-color: transparent !important;
        font-weight: 500 !important;
        font-size: 1.1rem !important;
        padding: 16px 20px !important;
    }
    div[data-testid="stExpanderDetails"] {
        padding: 1.2rem 1rem !important;
        background-color: #121212 !important;
        border-top: 1px solid #2a2a2a;
    }

    /* ปรับ File Uploader ดีไซน์มินิมอล */
    .stFileUploader>div>div {
        border-radius: 12px !important;
        background-color: #1a1a1a !important;
        border: 1px dashed #555555 !important;
        padding: 2rem !important;
        transition: all 0.2s ease;
    }
    .stFileUploader>div>div:hover {
        border-color: #888888 !important;
        background-color: #222222 !important;
    }

    /* กรอบข้อความแจ้งเตือนต่างๆ */
    div[data-testid="stAlert"] {
        border-radius: 8px !important;
        border: 1px solid #333333 !important;
        background-color: #1e1e1e !important;
        padding: 1rem !important;
    }

    /* พื้นที่แสดงผลซอร์สโค้ด (st.code) ให้โค้งมนและสวยงาม */
    div[data-testid="stCodeBlock"] {
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid #2a2a2a !important;
        background-color: #1e1e1e !important;
    }

    /* 📱 จัดการเฉพาะหน้าจอมือถือ (Mobile Perfect Fit UX) */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 4rem !important;
        }
        
        /* ปรับหัวข้อใหญ่สุด เรียบง่าย ไม่มลทิน */
        h1 {
            font-size: 1.8rem !important;
            text-align: left;
            margin-bottom: 0.5rem !important;
            line-height: 1.3 !important;
            font-weight: 600 !important;
        }
        
        /* ปรับระดับหัวรอง */
        h2 {
            font-size: 1.3rem !important;
            margin-top: 1.5rem !important;
            padding-bottom: 0.5rem !important;
            border-bottom: 1px solid #2a2a2a;
        }
        
        h3 {
            font-size: 1.15rem !important;
        }

        /* ขยายระยะสัมผัส (Touch Target) ของตัวเลือก Checkbox/Radio ให้กดง่ายในมือถือ */
        .stCheckbox>label>div[data-testid="stMarkdownContainer"]>p, 
        .stRadio>label>div[data-testid="stMarkdownContainer"]>p {
            font-size: 1.1rem !important;
            padding: 10px 0;
            line-height: 1.4;
        }

        /* ปุ่มต่างๆ ให้กดง่ายเต็มความกว้างจอ (Full Width) */
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
            background-color: #1e1e1e !important;
            border-radius: 8px 8px 0 0 !important;
            border-bottom: 2px solid transparent !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background-color: #2a2a2a !important;
            border-bottom: 2px solid #e62e5c !important;
            color: white !important;
            font-weight: 500 !important;
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

# ส่วนตั้งค่าโหมดและ API Key เปิดให้กรอกบนหน้าจอ (และรองรับ Environment Variable ด้วย)
st.markdown("### ⚙️ การตั้งค่าระบบ")
api_key = st.text_input("🔑 ใส่ Gemini API Key", value=os.environ.get("GEMINI_API_KEY", ""), type="password", help="รับ API Key ได้ฟรีที่ Google AI Studio")

if api_key:
    genai.configure(api_key=api_key)
    st.success("✅ เชื่อมต่อ API Key แล้ว")
else:
    st.warning("⚠️ กรุณาใส่ API Key ด้านบนก่อนเริ่มใช้งาน")
st.subheader("📸 1. เริ่มต้นใหม่: อัปโหลดรูปภาพสินค้า")

# ส่วนอัปโหลดภาพสินค้า
uploaded_file = st.file_uploader("📸 อัปโหลดรูปภาพสินค้า (หน้าตรง เห็นชัดเจน)", type=['png', 'jpg', 'jpeg', 'webp'])

if uploaded_file:
    if True:
        # แปลงและลดขนาดภาพ ป้องกัน Token ล้น และบีบอัดเป็น RGB
        img = Image.open(uploaded_file)
        rgb_im = img.convert('RGB')
        rgb_im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
        
        # Save for Gemini
        image_path = "assets/input/sample_product.jpg"
        rgb_im.save(image_path, format="JPEG", quality=95)
        
        col_img1, col_img2 = st.columns([1, 2])
        col_img1.image(img, caption="ตัวอย่างรูปภาพต้นฉบับ", use_container_width=True)
        
        # เราใช้แค่ภาพเดียวสำหรับวิเคราะห์ ส่งใส่ list ไว้เหมือนเดิมให้โค้ดข้างล่างทำงานต่อได้
        image_paths = [image_path]
        
        st.markdown("---")
        
        if not st.session_state.product_info:
            st.session_state.product_info = "(ระบบจะให้คุณส่งรูปให้ Gemini วิเคราะห์สินค้าช่วย)"

        # แสดงส่วนตั้งค่าวิดีโอทันทีที่อัปโหลด (ถ้าเป็นแมนนวล) หรือเมื่อวิเคราะห์เสร็จ (ถ้าเป็นออโต้)
        if st.session_state.product_info:
            st.markdown("---")
            st.subheader("⚙️ 2. ปรับแต่งตัวละครและเนื้อเรื่องสำหรับถ่ายทำ")
            
            with st.expander("👤 2.1 - 2.4 ตั้งค่าตัวละครหลัก", expanded=True):
                product_only_mode = st.checkbox("📦 โหมดโชว์เฉพาะสินค้า (ไม่เอาคน/เน้นมุมกล้อง)", value=False)
                fashion_mode = st.checkbox("👗 โหมดแฟชั่นเสื้อผ้า (เน้นตัวละครสวมใส่)", value=False, disabled=product_only_mode)
                seller_mode = st.checkbox("🎙️ โหมดแม่ค้าไลฟ์ขายเสื้อผ้า (รีวิวไม้แขวน/หุ่นโชว์)", value=False, disabled=product_only_mode)
                
                no_voiceover = st.checkbox("🚫 ไม่เอาบทพูด (เน้นดนตรีประกอบอย่างเดียว)", value=False)

                char_options = [
                    "สาวไทย (วัยรุ่น)", "หนุ่มไทย (วัยรุ่น)", "สาวไทย (วัยทำงาน)", "หนุ่มไทย (วัยทำงาน)",
                    "นางแบบอินเตอร์", "นายแบบอินเตอร์", "คุณแม่ (แม่และเด็ก)", "แม่บ้าน", "พ่อบ้าน", 
                    "แม่ค้า", "พ่อค้า", "ช่างซ่อม/ช่างเทคนิค", "พนักงานออฟฟิศ", "นักเรียน/นักศึกษา", 
                    "อินฟลูเอนเซอร์/ครีเอเตอร์", "ไรเดอร์/พนักงานส่งของ", "เชฟ/คนทำอาหาร", 
                    "ผู้หญิงทั่วไป", "ผู้ชายทั่วไป", "เด็กเล็ก", "คนแก่", "ครอบครัวพ่อแม่ลูก", 
                    "คู่รัก", "สุนัข", "แมว", "อื่นๆ"
                ]

                if fashion_mode or seller_mode:
                    fashion_item_type = st.selectbox("👗 2.1.2 ประเภทสินค้าแฟชั่น", ["เสื้อ (Tops)", "กางเกง/กระโปรง (Bottoms)", "ชุดเดรส/ชุดเซท (Dress/Sets)", "กระเป๋า (Bags)", "รองเท้า (Shoes)", "หมวก/เครื่องประดับ (Accessories)", "อื่นๆ"])
                    if fashion_item_type == "อื่นๆ":
                        fashion_item_type = st.text_input("ระบุประเภทสินค้าแฟชั่นอื่นๆ:")
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

                char_style = st.selectbox("🎨 2.2 สไตล์ภาพตัวละคร (Art Style)", ["คนจริงสวยงาม (Realistic)", "การ์ตูน 2D (Anime/Cartoon)", "อวตาร 3D (Pixar/3D Avatar)", "อื่นๆ"], disabled=no_char_mode)
                if char_style == "อื่นๆ":
                    char_style = st.text_input("ระบุสไตล์ภาพตัวละครอื่นๆ:", disabled=no_char_mode)
                
                char_skin = st.selectbox("🎨 2.3 สีผิวตัวละคร", ["ผิวขาว/สว่าง", "ผิวแทน/น้ำผึ้ง", "ผิวคล้ำเข้ม", "ไม่ระบุ (ให้ AI เลือกเอง)", "อื่นๆ"], disabled=no_char_mode)
                if char_skin == "อื่นๆ":
                    char_skin = st.text_input("ระบุสีผิวตัวละครอื่นๆ:", disabled=no_char_mode)
                
                char_traits_options = ["สวยน่ารัก", "เซ็กซี่เย้ายวน", "หน้าอกใหญ่", "หุ่นนายแบบ/นางแบบ", "หล่อเท่สมาร์ท", "แต่งตัวภูมิฐานดูแพง", "ตลกขบขัน", "ร่าเริงสดใส", "ลึกลับน่าค้นหา", "อื่นๆ"]
                char_traits = st.multiselect("✨ 2.4 บุคลิกภาพและรูปร่าง (เลือกได้หลายข้อ)", 
                    char_traits_options,
                    disabled=no_char_mode
                )
                if "อื่นๆ" in char_traits:
                    custom_trait = st.text_input("ระบุบุคลิกภาพอื่นๆ:", disabled=no_char_mode)
                    if custom_trait:
                        char_traits.remove("อื่นๆ")
                        char_traits.append(custom_trait)
                
            with st.expander("🖼️ 2.4 ฉากหลังและบรรยากาศ", expanded=True):
                bg_options = [
                    "ไม่ระบุ (อิสระตามเนื้อเรื่อง)", 
                    "ในเมือง/ถนนชิคๆ 🏙️", 
                    "คาเฟ่/ร้านมินิมอล ☕",
                    "ตลาด/สตรีทฟู้ด 🥢", 
                    "ห้างสรรพสินค้า 🛍️", 
                    "สวนสาธารณะ 🏞️", 
                    "ริมแม่น้ำ 🚤", 
                    "ทะเล/ชายหาด 🌊", 
                    "ภูเขา/ธรรมชาติป่าไม้ 🌳", 
                    "ในห้อง/มุมสบายนอกบ้าน 🛋️",
                    "อื่นๆ"
                ]
                char_bg = st.selectbox("🏞️ 2.4 ฉากหลัง (Background)", bg_options)
                
                if char_bg == "อื่นๆ":
                    char_bg = st.text_input("พิมพ์ระบุฉากหลังตามต้องการ:")
                
            with st.expander("🎙️ 2.5 - 2.7 เสียงและซาวด์เอฟเฟกต์", expanded=True):
                use_sfx = st.radio("🔊 2.5 ใส่ซาวด์เอฟเฟกต์ (Sound Effects) ในสคริปต์?", [
                    "ใส่ซาวด์ (เน้นลูกเล่นตื่นเต้น)", 
                    "ไม่ใส่ซาวด์ (เน้นพากย์เสียงอย่างเดียว)",
                    "ไม่ใส่ซาวด์ ไม่พากย์เสียง (เน้นดิบๆ เรียลๆ ภาพไม่กระตุกตามเสียง)"
                ])
                
                if "ไม่พากย์เสียง" in use_sfx:
                    no_voiceover = True
                    
                voice_type_options = [
                    "ไม่ระบุ (สุ่มให้เหมาะสม)", 
                    "👩 ผู้หญิงทั่วไป", 
                    "👨 ผู้ชายทั่วไป", 
                    "👱‍♀️ สาววัยรุ่น/วัยมหาลัย (สดใส ใช้คำวัยรุ่น/ตัวแม่)", 
                    "👦 หนุ่มวัยรุ่น (คุยเหมือนเพื่อน)",
                    "💃 แม่ค้าไลฟ์สด (พลังล้น ขายเก่ง เร้าใจ เสนอโปรโมชั่น)",
                    "💅 อินฟลูฯ สายคุณหนู/บิวตี้บล็อกเกอร์ (ติดหรู พูดจาอ้อนๆ)",
                    "🎙️ นักพากย์โฆษณา/MC (ดูโปร น่าเชื่อถือ)",
                    "👵 คนแก่/คุณยาย (ใจดี อบอุ่น)",
                    "👶 เด็กน้อย (เสียงเจื้อยแจ้ว น่าเอ็นดู)",
                    "🤖 หุ่นยนต์/AI", 
                    "🐶 สัตว์เลี้ยง (คนพากย์เป็นหมา/แมว)",
                    "🤪 สายฮา/เบียว (ติดตลก กวนๆ ตบมุก)",
                    "อื่นๆ"
                ]
                voice_type = st.selectbox("🎙️ 2.6 เสียง/สไตล์ผู้พากย์ (Voice Persona)", voice_type_options, disabled=no_voiceover)
                if voice_type == "อื่นๆ":
                    voice_type = st.text_input("ระบุเสียงผู้พากย์อื่นๆ:", disabled=no_voiceover)
                
                voice_emotion_options = [
                    "ไม่ระบุ (สุ่มให้เหมาะสม)", 
                    "🔥 ตื่นเต้นเร้าใจ ป้ายยา (Energetic/Hype)", 
                    "😂 ตลกขบขัน/กวนๆ (Funny)", 
                    "👔 จริงจัง/ให้ความรู้ (Professional/Educational)", 
                    "🤫 กระซิบ/น่าค้นหา (ASMR)", 
                    "🥺 สดใส/อ้อนๆ น่ารัก (Cute)", 
                    "😮 อึ้ง/ตกใจกับผลลัพธ์ (Shocked/Wow)",
                    "😢 ซึ้งกินใจ/ดราม่า (Emotional)",
                    "😎 ชิลๆ/มินิมอล/พูดเนือยๆ (Chill/Deadpan)",
                    "อื่นๆ"
                ]
                voice_emotion = st.selectbox("🎭 2.7 อารมณ์ในการพากย์ (Emotion)", voice_emotion_options, disabled=no_voiceover)
                if voice_emotion == "อื่นๆ":
                    voice_emotion = st.text_input("ระบุอารมณ์ในการพากย์อื่นๆ:", disabled=no_voiceover)
    
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
            st.subheader("🚀 4. วิเคราะห์และสร้าง Storyboard ด้วย AI (Gemini API)")
            if st.button("🚀 4.1 วิเคราะห์ด้วย AI ทันที", use_container_width=True):
                if not api_key:
                    st.error("⚠️ กรุณาใส่ Gemini API Key ในแผงตั้งค่าระบบด้านบนก่อนครับ!")
                else:
                    script_instruction = '3. คิดบทพากย์ (script) ที่ดึงดูด น่าสนใจ เป็นเรื่องราวเนื้อหาต่อเนื่องกันแบบเนียนๆ ตั้งแต่ซีนแรกจนถึงซีนสุดท้าย (ห้ามตัดจบดื้อๆ) และสอดคล้องกับ "เสียงผู้พากย์" และ "อารมณ์น้ำเสียง" อย่างเคร่งครัด'
                    video_voice_instruction = f'- **การรักษาความต่อเนื่อง:** บังคับให้ใส่ "Continuous motion from previous shot, exact same subject and natural environment." (Flow/Veo ไม่รองรับการสั่งให้มีเสียงคนพูด (Voiceover) ในพรอมต์ หากใส่ไป AI จะค้างที่ 99% ให้โฟกัสแค่ภาพและ Sound Effect หรือบรรยากาศ)'
                    
                    if no_char_mode:
                        char_rule = f"- เป็นวิดีโอโชว์สินค้าเพียวๆ ไม่มีคนหรือสัตว์ในภาพเลย (100% Product B-Roll)\\n- เน้นดนตรีประกอบน่าตื่นเต้น ตัดต่อเร้าใจ\\n"
                        scene_rule = f"2. ทุกซีนต้องเป็นภาพเจาะสินค้า (Product Shot) หรือภาพบรรยากาศสินค้า (Product in Environment) ห้ามวาดมนุษย์หรือตัวละครประหลาดลงในภาพเด็ดขาด\\n   - บังคับการเขียน Video Prompt ให้ใช้เทคนิคกล้องหวือหวา (เช่น Dynamic zoom in, Orbit around product, Dolly in, Cinematic pan) เหมือนถ่ายทำโฆษณาสินค้าไฮเอนด์"
                        if no_voiceover:
                            char_rule += "- **ย้ำ: ไม่ต้องคิดบทพูด (Voiceover) เด็ดขาด**\\n"
                            if no_bgm:
                                script_instruction = '3. **ห้ามแต่งบทพูดและซาวด์เด็ดขาด** ให้ปล่อยฟิลด์ script ว่างไว้'
                                video_voice_instruction = '- **Focus video prompt:** "Cinematic silent product b-roll, pure visual focus"'
                            else:
                                script_instruction = '3. **ห้ามแต่งบทพูดเด็ดขาด (No Voiceover)** ให้ปล่อยฟิลด์ script ว่างไว้ หรือเขียนเพียงแค่ "[ดนตรีบรรเลงเร้าใจ]"'
                                video_voice_instruction = '- **Focus video prompt:** "Cinematic product b-roll with energetic background feeling"'
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

                        char_rule = f"- โหมดแฟชั่น (ประเภทสินค้า: {fashion_item_type}): เน้นการถ่ายทอดรูปทรงและดีไซน์ของสินค้า ให้บรรยากาศดูเรียลๆ เหมือนใช้มือถือถ่ายเอง\\n- ตัวละครหลัก: {char_type}\\n- สีผิว: {char_skin}\\n- บุคลิกภาพ/รูปร่าง: {traits_str}\\n- **กฎตัวละครและสินค้า (CRITICAL CHARACTER & PRODUCT):** สำหรับ 'ตัวละคร/บุคคล' ในรูป ให้สร้างหน้าตาคนขึ้นมาใหม่ทั้งหมด ห้ามก๊อปปี้หน้าตาคนจากรูปอ้างอิงเด็ดขาด! แต่สำหรับ 'ตัวสินค้า' ต้องเหมือนรูปที่แนบมาเป๊ะๆ 100% (ให้เหมือนตัดแปะตัวสินค้าจากรูปจริง) โดยคุณต้องเขียน `image_prompt` กำชับ AI ให้ชัดเจนว่า 'A completely NEW character person, but the product is EXACTLY identical to the reference image, perfect match.' และต้องบรรยายรายละเอียดสินค้าอย่างถี่ยิบ\\n"
                        
                        scene_rule = f"""2. การจัดลำดับภาพแต่ละซีน (สำคัญมาก บังคับใช้ตามนี้):
   - ซีนช็อตที่ 1: เน้นภาพครึ่งตัว (Half-body) หรือเต็มตัว (Full-body shot) ตัวละครเดินอย่างเป็นธรรมชาติ (ไม่ต้องโฟกัสสินค้าใกล้เกินไป)
   - ซีนช็อตที่ 2: บังคับดีไซน์ภาพให้เจาะจงโฟกัสที่ **{focus_target}** แบบชัดๆ เลย์เอาต์สวยงาม
   - ซีนช็อตที่ 3: เน้นตัวละครโพสท่าชิคๆ อย่างเป็นธรรมชาติ (Natural posing)
   - ซีนช็อตที่ 4: **{pan_target}** อย่างชัดเจน
   (หากมีมากกว่า 4 ซีน ให้สลับหมุนเวียนให้เป็นธรรมชาติ)"""
                        
                        fashion_motion_instruction = f'\\n   - **ท่าทางการเคลื่อนไหวภาพ:** บังคับให้สร้างแอนิเมชันความเร็วปกติ ขยับแบบมนุษย์ทั่วไป "Natural everyday human movement, real-time speed, cinematic lighting, crisp focus"'
                        
                        if no_voiceover:
                            char_rule += "- **ย้ำ: ไม่ต้องคิดบทพูด (Voiceover) เด็ดขาด**\\n"
                            if no_bgm:
                                script_instruction = '3. **ห้ามแต่งบทพูดและซาวด์เด็ดขาด** ให้ปล่อยฟิลด์ script ว่างไว้'
                                video_voice_instruction = '- **Focus video prompt:** "Silent visual focus, natural feeling"' + fashion_motion_instruction
                            else:
                                script_instruction = '3. **ห้ามแต่งบทพูดเด็ดขาด (No Voiceover)** ให้ปล่อยฟิลด์ script ว่างไว้ หรือเขียนเพียงแค่ "[ดนตรีบรรเลงเร้าใจ]"'
                                video_voice_instruction = '- **Focus video prompt:** "Cinematic visual storytelling"' + fashion_motion_instruction
                        else:
                            video_voice_instruction += fashion_motion_instruction
                    elif seller_mode:
                        if "ชุดเซท" in fashion_item_type or "เซท" in fashion_item_type or "ชุด" in fashion_item_type:
                            presentation_detail = "ตัวละครนำเสนอสินค้าโดยแขวนแบบครบชุด (ทั้งเสื้อและกางเกง/กระโปรงเข้าชุดกัน) ไว้บนไม้แขวนเสื้ออย่างชัดเจน และโชว์สินค้าครบชุดสวมอยู่บนหุ่นโชว์เสื้อผ้า (Mannequin) ตั้งอยู่ 2 ตัว (ตัวหนึ่งสวมโชว์ด้านหน้า และอีกตัวสวมโชว์ด้านหลังเปรียบเทียบกัน)"
                            hanger_scene = "ถือไม้แขวนเสื้อที่มีสินค้าครบชุด (ทั้งเสื้อและกางเกง/กระโปรง) แขวนเตรียมไว้เพื่อนำเสนอด้วยความมั่นใจ"
                            mannequin_scene = "หุ่นโชว์เสื้อผ้า (Mannequin) 2 ตัว ที่สวมเสื้อผ้าครบชุด โชว์ด้านหน้าและด้านหลังของสินค้าชัดเจน"
                        else:
                            presentation_detail = "ตัวละครนำเสนอสินค้าแบบแม่ค้าออนไลน์ โดยถือสินค้าบนไม้แขวนเสื้อ และโชว์สินค้าบนหุ่นโชว์เสื้อผ้า (Mannequin) ตั้งอยู่ 2 ตัว (ตัวหนึ่งสวมโชว์ด้านหน้า และอีกตัวสวมโชว์ด้านหลัง)"
                            hanger_scene = "ถือไม้แขวนเสื้อที่มีสินค้านี้แขวนอยู่เพื่อนำเสนอด้วยความมั่นใจ"
                            mannequin_scene = "หุ่นโชว์เสื้อผ้า (Mannequin) 2 ตัว โชว์ด้านหน้าและด้านหลังของสินค้าชัดเจน"

                        char_rule = f"- โหมดบรรยากาศร้านขายเสื้อผ้า (สินค้า: {fashion_item_type}): เน้นฉากในร้านขายเสื้อผ้าที่ตกแต่งเข้ากับประเภทสินค้า ฉากหลังต้องชัดเจนกว้างขวางเห็นบรรยากาศร้าน (Absolutely NO background blur, deep depth of field)\\n- ตัวละครหลักพ่อค้า/แม่ค้า: {char_type} ซึ่งแต่งกายด้วยสไตล์ที่เข้ากับสินค้า\\n- สีผิว: {char_skin}\\n- บุคลิกภาพ: {traits_str}\\n- **กฎตัวละครและสินค้า (CRITICAL CHARACTER & PRODUCT):** สร้างหน้าตาคนใหม่หมด แต่ 'ตัวสินค้า' ต้องเหมือนรูปเป๊ะๆ 100% {presentation_detail}\\n"
                        scene_rule = f"2. การจัดลำดับภาพแต่ละซีน:\\n   - ซีนช็อตที่ 1: ตัวละครยืนอยู่ในร้านขายเสื้อผ้า {hanger_scene}\\n   - ซีนช็อตที่ 2: โฟกัสไปที่{mannequin_scene}\\n   - ซีนช็อตที่ 3: โฟกัสจับใกล้ดีเทลผืนผ้าขณะที่ตัวละครกำลังชี้หรือจับสินค้า\\n   - ซีนช็อตที่ 4: แพนกล้องให้เห็นตัวละครยืนคู่กับหุ่นโชว์เสื้อผ้า พร้อมยิ้มแย้มรีวิวเชียร์ขายสินค้า\\n"
                        
                        seller_motion_instruction = f'\\n   - **ท่าทางการเคลื่อนไหวภาพ:** ขยับแบบนักขายกำลังรีวิวสินค้า "Natural energetic seller movement, reviewing product details, real-time speed, crisp focus"'
                        
                        if no_voiceover:
                            char_rule += "- **ย้ำ: ไม่ต้องคิดบทพูด (Voiceover) เด็ดขาด**\\n"
                            if no_bgm:
                                script_instruction = '3. **ห้ามแต่งบทพูดและซาวด์เด็ดขาด** ให้ปล่อยฟิลด์ script ว่างไว้'
                                video_voice_instruction = '- **Focus video prompt:** "Silent seller visual focus, showing products on hangers and mannequins"' + seller_motion_instruction
                            else:
                                script_instruction = '3. **ห้ามแต่งบทพูดเด็ดขาด (No Voiceover)** ให้ปล่อยฟิลด์ script ว่างไว้ หรือเขียนเพียงแค่ "[ดนตรีประกอบสนุกสนาน]"'
                                video_voice_instruction = '- **Focus video prompt:** "Energetic seller presenting products visually"' + seller_motion_instruction
                        else:
                            script_instruction = '3. คิดบทพากย์ (script) โดยใช้ **"เสียงและอารมณ์แนวนักขาย (Hard Sell/Energetic Seller)"** แนะนำสินค้า เชียร์ขาย บอกโปรโมชั่น และกระตุ้นให้กดตะกร้าซื้ออย่างกระตือรือร้น'
                            video_voice_instruction = seller_motion_instruction
                    else:
                        char_rule = f"- ตัวละครหลัก: {char_type}\\n- สีผิว: {char_skin}\\n- บุคลิกภาพ/รูปร่าง: {traits_str}\\n- **กฎตัวละครและสินค้า (CRITICAL CHARACTER & PRODUCT):** สำหรับ 'ตัวละคร/บุคคล' ในรูป ให้สร้างหน้าตาคนขึ้นมาใหม่ทั้งหมด ห้ามก๊อปปี้หน้าตาคนจากรูปอ้างอิงเด็ดขาด! แต่สำหรับ 'ตัวสินค้า' ต้องเหมือนรูปที่แนบมาเป๊ะๆ 100% (ให้เหมือนตัดแปะตัวสินค้าจากรูปจริง) โดยคุณต้องเขียน `image_prompt` กำชับ AI ให้ชัดเจนว่า 'A completely NEW character person, but the product is EXACTLY identical to the reference image, perfect match.' และต้องบรรยายรายละเอียดสินค้าอย่างถี่ยิบ\\n"
                        scene_rule = f"2. ซีนที่ 1 บังคับให้เป็นภาพตัวละครครึ่งตัว (Half-body) หรือเต็มตัวเดิน (Full-body walking) ห้ามโฟกัสสินค้าใกล้เกินไป ส่วนซีนอื่นๆ ต้องมีฉากที่เจาะจงนำเสนอ 'ตัวสินค้าชัดๆ (Product Shot)' จำนวน {product_scene_count} ซีน และที่เหลือให้เป็น 'ฉากเล่าเรื่อง/ไลฟ์สไตล์ (Story/Lifestyle)' ที่มีตัวละครหลัก"
                        if no_voiceover:
                            if no_bgm:
                                script_instruction = '3. **ห้ามแต่งบทพูดและซาวด์เด็ดขาด** ให้ปล่อยฟิลด์ script ว่างไว้'
                                video_voice_instruction = '- **Focus video prompt:** "Silent visual focus, natural aesthetic"'
                            else:
                                script_instruction = '3. **ห้ามแต่งบทพูดเด็ดขาด (No Voiceover)** ให้ปล่อยฟิลด์ script ว่างไว้ หรือเขียนเพียงแค่ "[ดนตรีบรรเลงเร้าใจ]"'
                                video_voice_instruction = '- **Focus video prompt:** "Cinematic visual storytelling, natural aesthetic"'

                    consistent_char_phrase = "" if no_char_mode else "Consistent generic character model in every scene, consistent facial features, hair, and clothing, "

                    if no_char_mode or "คนจริง" in char_style:
                        image_style_instruction = '   - **สไตล์ภาพถ่ายสุดเรียล:** ให้ระบุใน prompt ว่า "Realistic smartphone lifestyle photo, clear background depth, sharp focus on subject." เพื่อให้ภาพดูสมจริง'
                        video_style_instruction = '   - **สไตล์เรียลๆ:** บังคับเพิ่ม "Realistic lifestyle footage, normal real-time speed, perfectly sharp background, cinematic composition, crisp focus" เสมอ'
                    elif "การ์ตูน 2D" in char_style:
                        image_style_instruction = '   - **สไตล์ภาพการ์ตูน 2D:** ให้กำหนดสไตล์ภาพเป็น "High quality 2D Anime style, vibrant colors, flat shading, Ghibli style background, sharp focus"'
                        video_style_instruction = '   - **สไตล์วิดีโอการ์ตูน 2D:** บังคับเพิ่ม "High quality 2D Anime animation, vibrant colors, flat shading, Ghibli style, normal real-time speed, sharp background" เสมอ'
                    else: # อวตาร 3D
                        image_style_instruction = '   - **สไตล์ภาพอวตาร 3D:** ให้กำหนดสไตล์ภาพเป็น "High quality 3D Pixar style, cute 3D character, vibrant lighting, highly detailed 3D render, sharp focus"'
                        video_style_instruction = '   - **สไตล์วิดีโออวตาร 3D:** บังคับเพิ่ม "High quality 3D Pixar style animation, highly detailed 3D render, normal real-time speed, sharp background" เสมอ'

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
   - **กฎการพากย์เสียง (CRITICAL SCRIPTING):** เขียนบทพากย์ให้สะท้อนเอกลักษณ์ของ 'Voice Persona ({voice_type})' และ 'อารมณ์น้ำเสียง ({voice_emotion})' แบบสุดโต่ง 100%! บังคับใช้คำแสลง, วิธีการพูด, และรูปประโยคที่แตกต่างกันไปตานคาแรคเตอร์ (ห้ามเขียนแพทเทิร์นพากย์ซ้ำเดิมจำเจเด็ดขาด ต้อง Unique ทุกครั้ง)
{f"4. **ไม่ต้องเขียนบทพากย์** แต่ละซีนมีความยาว {scene_duration} วินาที" if no_voiceover else f"4. เขียนบทพากย์ให้สามารถพูดจบได้ภายใน {scene_duration} วินาทีต่อซีน"}
5. เขียน image_prompt เป็นภาษาอังกฤษ เพื่อใช้ **เจนภาพนิ่งด้วย Gemini (Imagen 3)**
   - **สำคัญมาก (การติดป้ายชื่อซีน):** บังคับให้คุณขึ้นต้นประโยคแรกของ `image_prompt` ทุกซีนด้วยคำว่า "Scene 1: ", "Scene 2: " ... ตามลำดับซีนเสมอ (เช่น "Scene 1: Vertical 9:16 aspect ratio...")
   - บังคับให้ใส่: "Vertical 9:16 aspect ratio, {consistent_char_phrase}NO text overlays, NO typography, ONLY one single distinct scene, NO 4-panel grid, NO split screen"
   - **กฎการแยกภาพ (No Grid/Collage):** ห้ามให้ AI เจนภาพ 4 ซีนรวมอยู่ในรูปเดียว (กากบาท/ตาราง 4 ช่อง) อย่างเด็ดขาด! บังคับเขียนสั่งท้าย prompt ว่า "Single full frame, absolutely NO multi-panel collage"
   - **กฎการล็อกเป้า 100% (CRITICAL UNIFIED CORE_PROMPT):** คุณต้องรวบรวมรายละเอียดทั้งหมด ได้แก่ 1) การกำหนดสรีระรูปลักษณ์แบบเจาะจง (เช่น "A 25yo confident Asian female model with short black bob hair wearing a white t-shirt" **ห้ามตั้งชื่อบุคคลเฉพาะให้ตัวละครเด็ดขาดเพื่อป้องกัน AI บล็อกคำสั่ง**) เพื่อใช้เป็นกุญแจล็อคหน้าตาและชุดให้คล้ายเดิม 2) ลักษณะของรูปภาพสินค้า (อักษร ลายพิมพ์ สี) แบบละเอียดโคตรๆ และ 3) ฉากหลังที่เจาะจงมาก (เช่น A specific modern kitchen) 
   - นำข้อมูลทั้ง 3 ข้อด้านบนมาแต่งรวมกันเป็น 1 ย่อหน้า เรียกว่า `[CORE_PROMPT]` และ **คุณมีหน้าที่เรียงลำดับดังนี้: ขึั้นต้นด้วย "Scene X: " เป็นคำแรกสุด จากนั้นเว้นวรรคและตามด้วย `[CORE_PROMPT]` เป็นย่อหน้าแรกสุดใน `image_prompt` ของทุกๆ ซีนย่อย ห้ามตกหล่นแม้แต่ตัวอักษรเดียว! (ห้ามเอาอะไรมาบังหน้าคำว่า Scene X: เด็ดขาด)**
   - ส่วนที่เปลี่ยนได้ในแต่ละซีน คือแค่ "ท่าทางโพส (Pose)" และ "มุมกล้อง (Camera Angle)" ต่อท้าย `[CORE_PROMPT]` เท่านั้น! เพื่อบังคับให้ AI สร้างภาพ นางแบบเดิม ฉากเดิม สินค้าเดิม ตลอดทั้งคลิป!
   - **กฎเหล็กเพื่อความชัด (ห้ามเบลอฉากหลังเด็ดขาด):** บังคับให้ทุกประโยค `image_prompt` จบด้วยคำสั่งนี้เสมอ: "Taken with an ordinary smartphone camera, zero portrait mode. The background environment MUST BE 100% crystal clear and fully visible in sharp focus. Extreme deep depth of field, absolutely NO bokeh, NO background blur at all, perfectly sharp scenery background. Correct anatomical hands."
{image_style_instruction}
   - บรรยายแสงเงา บรรยากาศ มุมกล้อง ให้เป็นแบบ "แสงธรรมชาติทั่วไป (Natural daily lighting)" ห้ามจัดแสงสวยหรูแบบสตูดิโอเด็ดขาด และห้ามสั่งให้วาดป้ายราคาหรือข้อความทับลงไปในภาพเด็ดขาด
6. เขียน video_prompt เป็นภาษาอังกฤษ สำหรับ **เจนวนิเมชัน+เสียง บน Google Labs Flow**
{video_style_instruction}
   - ไม่ต้องขึ้นต้นด้วย "Scene X:" ใน `video_prompt` เพราะอาจทำให้ Flow ค้าง ให้เขียนคำสั่งภาพไปเลยตรงๆ
   - **ความเร็วและมุมกล้อง:** ให้ย้ำว่า "Normal speed cinematic camera motion." เน้นขยับกล้องเฉพาะด้านหน้า (Front view only) 
   - **หลีกเลี่ยงการใช้คำปฏิเสธเยอะๆ เช่น NO NO NO** เพราะจะทำให้ AI Model บล็อกคำสั่ง ให้เขียนบรรยายสิ่งที่ต้องการเห็นแทน เช่น "Clear footage, perfectly sharp" 
   - **ห้ามสั่ง AI ให้พากย์เสียงคนพูดเด็ดขาด (No voiceover requests in prompt)** เพราะเป็นข้อห้ามของระบบ Video AI และจะค้าง 99% ให้เขียนแค่ท่าทางและบรรยากาศ หรือเสียง Sound Effect ธรรมชาติ (เช่น Ambient sound)
   - การขยับ: เน้นสั่ง 'Camera motion' และ 'Subject motion' รวบกับ "Clean visual" อย่างกระชับ, ถ่ายแบบ UGC style 
   {video_voice_instruction}
7. **Task 1 (ข้อมูล JSON อย่างเดียว):** ส่งโครงสร้างบทวิเคราะห์ทั้งหมดมาเป็นดค้ด JSON อย่างเดียวโดยยึดตามโครงสร้างที่กำหนด (ไม่ต้องพยายามสร้างภาพกราฟิก)
8. **คำสั่งสำคัญเรื่องการตลาด:** หน้าที่ของคุณคือการเป็น Content Creator และนักการตลาดเชี่ยวชาญด้าน Affiliate Marketing บน TikTok โปรดดูภาพสินค้าที่ฉันแนบมานี้ และวิเคราะห์จุดขายเพื่อร่างข้อความโพสต์ใส่ลงใน `tiktok_post_data` ดังนี้
   - Product Details: เขียนสรรพคุณจุดเด่นชัดเจนของสินค้า (3-4 บรรทัด)
   - Overlay Text: ข้อความวางบนคลิปแบบแยกตามซีน (สั้นๆ กระชับ) **บังคับเขียนเรียงลำดับ เช่น "ซีน 1: [ข้อความ]\\nซีน 2: [ข้อความ]"**
   - Link Title: ชื่อปุ่มตะกร้าสีเหลืองที่ดึงดูดใจให้นิ้วลั่น (สั้นๆ เช่น ราคา "โปรไฟไหม้🔥 จิ้มเลย")
   - Post Caption: แคปชั่นใต้โพสต์สไตล์ TikTok เน้นภาษาเป็นกันเอง กระตุ้นให้อยากซื้อทันที
   - Hashtags: แฮชแท็กที่เกี่ยวข้องและเป็นกระแส (5-8 แท็ก)

ขอให้ตอบกลับด้วยรูปแบบ JSON ตามโครงสร้างด้านล่างนี้เพียงอย่างเดียว:
{VideoPlan.model_json_schema()}"""
                    
                    with st.spinner("⏳ AI กำลังวิเคราะห์รูปภาพและแต่งสคริปต์ (ใช้เวลาสักครู่)..."):
                        try:
                            # 1. อัปโหลดรูปทั้งหมดไปที่ Gemini
                            uploaded_gemini_files = []
                            for path in image_paths:
                                uploaded_file = genai.upload_file(path)
                                uploaded_gemini_files.append(uploaded_file)
                                
                            # 2. ค้นหารุ่นของโมเดลที่ดีที่สุดและรองรับจากบัญชี API ของคุณ
                            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                            
                            # ดึงโมเดล Flash ทั้งหมดที่มี (Flash เร็วและโควต้าฟรีเยอะสุด) และเรียงรุ่นใหม่ล่าสุดขึ้นก่อน
                            flash_models = sorted([m for m in available_models if 'flash' in m.lower()], reverse=True)
                            # ดึงโมเดล Pro ทั้งหมดที่มี
                            pro_models = sorted([m for m in available_models if 'pro' in m.lower() and 'flash' not in m.lower()], reverse=True)
                            
                            # จัดคิวลองใช้ Flash ก่อน ถ้าไม่ได้ค่อยลอง Pro
                            preferred_models = flash_models + pro_models
                            
                            response = None
                            last_error = None
                            
                            for pref in preferred_models:
                                if pref in available_models:
                                    try:
                                        model = genai.GenerativeModel(pref)
                                        prompt_parts = uploaded_gemini_files + [master_prompt]
                                        response = model.generate_content(
                                            prompt_parts,
                                            generation_config=genai.types.GenerationConfig(
                                                temperature=0.7,
                                                response_mime_type="application/json",
                                            ),
                                            safety_settings=[
                                                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                                                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                                                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                                                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                                            ]
                                        )
                                        break # ลูปนี้สำเร็จแล้วให้หลุดลูปออกมาเลย
                                    except Exception as e:
                                        last_error = e
                                        # ถ้าขัดข้อง (เช่นเกินโควต้า 429) ให้ลองรุ่นถัดไป
                                        continue
                            
                            if not response:
                                if last_error:
                                    raise last_error
                                else:
                                    raise Exception("บัญชี API นี้ไม่สามารถใช้งาน Model ที่รองรับได้ครบถ้วน")
                            
                            # ตรวจสอบการบล็อกจากระบบ Safety ของ Google
                            try:
                                result_json = response.text
                            except ValueError as e:
                                # ถ้า error เกี่ยวกับ finish_reason (เช่น โดนบล็อกเนื้อหา)
                                if response.candidates and response.candidates[0].finish_reason:
                                    fr = response.candidates[0].finish_reason
                                    raise Exception(f"Google AI บล็อกการสร้างข้อความเนื่องจากละเมิดนโยบายความปลอดภัย (Finish Reason: {fr}). รูปภาพหรือคำบรรยายที่คุณให้มาอาจมีเนื้อหาล่อแหลม รุนแรง หรือผิดกฎของ Google โปรดเปลี่ยนรูปภาพหรือลองใหม่อีกครั้ง")
                                else:
                                    raise e

                            # clean output just in case
                            cleaned_json = result_json.replace("```json", "").replace("```", "").strip()
                            video_plan = VideoPlan.model_validate_json(cleaned_json)
                            st.session_state.video_plan_json = cleaned_json
                            st.session_state.generated_images = {}
                            
                            # เพิ่มส่วนการเขียนไฟล์ให้ Bot ນําไปใช้
                            import json as final_json
                            with open("output/latest_plan.json", "w", encoding="utf-8") as f:
                                # จัดระเบียบ JSON ให้สวยงามและใช้งานง่ายสำหรับบอท
                                f.write(video_plan.model_dump_json(indent=4))
                                
                            st.success(f"✅ ประมวลผลเสร็จสิ้น! (สินค้า: {video_plan.product_name})")
                        except Exception as e:
                            st.error(f"❌ เกิดข้อผิดพลาดจาก API: {e}")
                


# ----------------------------------------------------------------------------------
# ส่วนแสดงผล Storyboard และข้อมูลโพสต์ (จะแสดงเสมอหากมี video_plan_json ใน session_state)
# ----------------------------------------------------------------------------------
if st.session_state.video_plan_json:
    try:
        video_plan = VideoPlan.model_validate_json(st.session_state.video_plan_json)
        

        st.markdown("---")
        st.subheader("📋 แผนการทำวิดีโอรายฉาก (Storyboard & Prompts)")
        st.info("แตะขวา/ซ้าย ที่แท็บเพื่อดูรายละเอียดและอัปโหลดวิดีโอทีละซีน👇")
        st.markdown("*(สำหรับกรณีที่คุณเจอมือเอง ไม่ใช้บอท ก๊อปปี้ไปเจนได้เลย)*")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.link_button("🖼️ สร้างรูปภาพด้วย Gemini", "https://gemini.google.com/app", use_container_width=True)
        with col_btn2:
            st.link_button("🎥 สร้างฟุตเทจด้วย Labs Flow", "https://labs.google/fx/tools/flow", use_container_width=True)

        os.makedirs("assets/video", exist_ok=True)
        os.makedirs("assets/audio", exist_ok=True)

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
        
if st.session_state.video_plan_json:
    st.markdown("---")
    st.subheader("📝 ข้อมูลสำหรับโพสต์ TikTok (Caption & Hashtags)")
    st.write("ข้อมูลแคปชั่นและโควตสำหรับวิดีโอถูกสร้างขึ้นเรียบร้อยแล้ว!")
    try:
        import json
        video_plan_data = json.loads(st.session_state.video_plan_json)
        post_data = video_plan_data.get('tiktok_post_data')
        
        if post_data:
            # แบ่งเป็นหมวดหมู่ให้ก๊อปปี้ง่ายๆ
            st.success("**📋 แบ่งหมวดหมู่ให้ก๊อปปี้ง่ายๆ กดที่ปุ่ม Copy มุมขวาของแต่ละกล่องได้เลย!**")
            
            st.markdown("### 📝 1. คำบรรยายโพสต์ (Caption & Hashtags)")
            st.info("💡 นำไปวางในช่อง 'คำอธิบายวิดีโอ' (Description) ก่อนกดโพสต์")
            st.code(f"{post_data.get('post_caption', '')}\n\n{post_data.get('hashtags', '')}", language="text")
            
            st.markdown("### 🛒 2. พิกัดสั่งซื้อ (Link Title)")
            st.info("💡 นำไปตั้งเป็นชื่อตอน 'เพิ่มลิงก์สินค้า' (Add Product Link)")
            st.code(post_data.get('link_title', ''), language="text")
            
            st.markdown("### 💡 3. ข้อความพาดหัวคลิป (Overlay Text)")
            st.info("💡 เอาไว้ใส่เป็นสติกเกอร์ข้อความ แปะไว้บนตัวคลิปวิดีโอเพื่อดึงดูดสายตาคนดู")
            st.code(post_data.get('overlay_text', ''), language="text")
            
            if post_data.get('product_details', ''):
                st.markdown("### 📌 4. สรุปจุดเด่นสินค้า (สำหรับใช้อ้างอิง)")
                st.code(post_data.get('product_details', ''), language="text")
        else:
            st.warning("⚠️ ไม่พบข้อมูลแคปชั่นและแฮชแท็กในประวัติ กรุณาลองสร้างใหม่อีกครั้งครับ")
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการวิเคราะห์ข้อมูลแคปชั่น: {e}")
