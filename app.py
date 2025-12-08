import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime, timedelta
from fpdf import FPDF
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="centered", initial_sidebar_state="expanded")

# --- 2. GLOBAL SETTINGS ---
ADMIN_WHATSAPP = "919839940400"
ADMIN_EMAIL = "jeexaipro@gmail.com"
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome Champ! 🎓 Physics, Chemistry ya Maths—bas photo bhejo ya type karo. Let's crack it! 🚀"}]
if "processing" not in st.session_state: st.session_state.processing = False
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "audio_key" not in st.session_state: st.session_state.audio_key = 0
if "payment_step" not in st.session_state: st.session_state.payment_step = 1
if "user_details" not in st.session_state: st.session_state.user_details = {}

# --- 4. NUCLEAR DARK MODE CSS (No Config Needed) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* 1. FORCE ROOT VARIABLES */
    :root {
        --primary-color: #4A90E2;
        --background-color: #0E1117;
        --secondary-background-color: #161B26;
        --text-color: #E0E0E0;
        --font: 'Inter', sans-serif;
    }

    /* 2. FORCE BACKGROUNDS */
    html, body, .stApp {
        background-color: #0E1117 !important;
        color: #E0E0E0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* 3. SIDEBAR FORCE DARK */
    [data-testid="stSidebar"] {
        background-color: #161B26 !important;
        border-right: 1px solid #2B313E !important;
    }
    [data-testid="stSidebar"] * {
        color: #E0E0E0 !important;
    }

    /* 4. INPUT FIELDS (High Contrast Fix) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E2330 !important;
        color: #FFFFFF !important;
        border: 1px solid #4A90E2 !important;
        border-radius: 8px !important;
    }
    .stTextInput label {
        color: #E0E0E0 !important;
    }
    /* Placeholder Fix */
    ::placeholder {
        color: #888888 !important;
        opacity: 1;
    }

    /* 5. BUTTONS (Professional Blue) */
    div.stButton > button { 
        background-color: #4A90E2 !important; 
        color: white !important; 
        border: none !important; 
        border-radius: 8px; 
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
    }
    div.stButton > button:hover { 
        background-color: #357ABD !important; 
        box-shadow: 0px 4px 15px rgba(74, 144, 226, 0.4);
    }

    /* 6. CHAT BUBBLES */
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #1E2330 !important;
        border: 1px solid #2B313E !important;
        border-radius: 12px;
    }
    
    /* 7. LAYOUT ADJUSTMENTS */
    .block-container { padding-top: 1rem; padding-bottom: 140px; }
    [data-testid="stFileUploader"] { padding: 0px; }
    .stAudioInput { margin-top: 5px; }
    .stChatMessage .st-emotion-cache-1p1m4ay { width: 45px; height: 45px; }
    
    /* 8. HIDE HEADER */
    header[data-testid="stHeader"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 5. FUNCTIONS ---

def send_final_notification(name, email, phone, trans_id):
    try:
        url = f"https://formsubmit.co/{ADMIN_EMAIL}"
        # Browser Headers to bypass Spam Filters
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        payload = {
            "_subject": f"💰 PAID: {name}",
            "_captcha": "false",
            "_template": "table",
            "Name": name,
            "Email": email,
            "Phone": phone,
            "Trans ID": trans_id,
            "Time": str(datetime.now())
        }
        requests.post(url, data=payload, headers=headers)
        return True
    except:
        return False

def clean_latex(text):
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    return text.replace('$$$', '$')

def sanitize_text_for_pdf(text):
    text = text.replace('•', '-').replace('—', '-').replace('’', "'")
    return text.encode('latin-1', 'ignore').decode('latin-1')

def show_branding():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        try: st.image(LOGO_URL, width=280) 
        except: pass
    st.markdown("""
        <div style="text-align: center; margin-top: -15px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 42px; font-weight: 700; letter-spacing: 1px;">
                JEEx <span style="color:#4A90E2;">PRO</span>
            </h1>
            <p style="color: #AAAAAA; font-size: 15px; margin-top: 8px;">
                Your 24/7 AI Rank Booster | Master JEE Mains & Advanced 🚀
            </p>
        </div>
    """, unsafe_allow_html=True)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'JEEx Pro Notes', 0, 1, 'C')
        self.ln(5)
    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(74, 144, 226)
        self.cell(0, 10, sanitize_text_for_pdf(label), 0, 1, 'L')
        self.ln(2)
    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 7, sanitize_text_for_pdf(body))
        self.ln()

def generate_pdf(messages):
    pdf = PDF()
    pdf.add_page()
    for msg in messages:
        role = "JEEx" if msg["role"] == "assistant" else "Student"
        pdf.chapter_title(role)
        pdf.chapter_body(clean_latex(msg["content"]))
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 6. AUTHENTICATION ---
def check_key_status(user_key):
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"): return "ADMIN"
    expiry_db = st.secrets.get("KEY_EXPIRY", {})
    if user_key in expiry_db:
        try:
            exp = datetime.strptime(expiry_db[user_key], "%Y-%m-%d").date()
            if datetime.now().date() > exp: return "EXPIRED"
            else: return "VALID"
        except: return "INVALID"
    return "INVALID"

if st.session_state.get('logout', False):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    
    # Secure Password Input
    user_key = st.text_input("Enter Access Key:", type="password") 
    status = check_key_status(user_key)
    
    # --- UNLOCKED ---
    if status == "VALID" or status == "ADMIN":
        st.success(f"✅ Active")
        st.markdown("---")
        
        st.markdown("**📎 Attach Question**")
        uploaded_file = st.file_uploader("Upload", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
        
        st.markdown("**🎙️ Voice Chat**")
        audio_value = st.audio_input("Speak", key=f"audio_{st.session_state.audio_key}", label_visibility="collapsed")
        
        st.markdown("---")
        if len(st.session_state.messages) > 1:
            pdf_bytes = generate_pdf(st.session_state.messages)
            st.download_button("📥 Download Notes", data=pdf_bytes, file_name="JEEx_Notes.pdf", mime="application/pdf")
        
        if st.button("End Session"): st.session_state['logout'] = True; st.rerun()

    # --- LOCKED (PAYMENT FLOW) ---
    else:
        if user_key and status != "VALID": st.error("❌ Invalid Key")
        
        st.markdown("### ⚡ Subscribe Now")
        with st.expander("💎 Get Premium (₹99/mo)", expanded=True):
            
            # STEP 1
            if st.session_state.payment_step == 1:
                with st.form("reg"):
                    name = st.text_input("Name")
                    email = st.text_input("Email")
                    phone = st.text_input("WhatsApp")
                    sub = st.form_submit_button("🚀 Proceed")
                
                if sub:
                    if name and email and phone:
                        st.session_state.user_details = {"name": name, "email": email, "phone": phone}
                        st.session_state.payment_step = 2
                        st.rerun()
                    else: st.warning("Fill all fields.")

            # STEP 2
            elif st.session_state.payment_step == 2:
                st.info(f"Hi {st.session_state.user_details['name']}, scan to pay:")
                try: st.image("upi_qr.png", use_container_width=True)
                except: st.info(f"UPI: {ADMIN_WHATSAPP}@upi")
                
                st.markdown("---")
                trans_id = st.text_input("Enter UPI Trans ID:", placeholder="e.g. T230...")
                st.caption("ℹ️ Found in GPay/PhonePe History")
                
                if st.button("✅ Verify & Submit"):
                    if len(trans_id) > 6:
                        det = st.session_state.user_details
                        send_final_notification(det['name'], det['email'], det['phone'], trans_id)
                        st.session_state.user_details['trans_id'] = trans_id
                        st.session_state.payment_step = 3
                        st.rerun()
                    else: st.error("Invalid ID")
                
                if st.button("Back"):
                    st.session_state.payment_step = 1
                    st.rerun()

            # STEP 3
            elif st.session_state.payment_step == 3:
                st.success("🎉 Paid! Admin notified.")
                st.markdown("Please allow a few hours for verification. Your key will be sent to your WhatsApp/Email.")
                
                det = st.session_state.user_details
                msg = f"Hello JEEx!%0A*PAID*%0AName: {det['name']}%0AID: {det['trans_id']}"
                wa_link = f"https://wa.me/{ADMIN_WHATSAPP}?text={msg}"
                
                st.markdown(f'<a href="{wa_link}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:5px; font-weight:bold;">👉 Chat on WhatsApp</button></a>', unsafe_allow_html=True)
                
                if st.button("Start Over"):
                    st.session_state.payment_step = 1
                    st.rerun()

        with st.expander("📄 Terms"): st.markdown("1. Single User\n2. No Refunds\n3. AI Tool")

# --- 8. ADMIN ---
if status == "ADMIN":
    st.sidebar.success("🔑 Admin")
    new_id = st.text_input("New Key ID")
    days = st.number_input("Days", 30)
    if new_id:
        exp = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        st.code(f'"{new_id}" = "{exp}"', language="toml")
    st.stop()

# --- 9. LANDING PAGE ---
show_branding()

if status != "VALID":
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #1E2330; padding: 20px; border-radius: 12px; border-left: 5px solid #4A90E2; text-align: center; margin-bottom: 30px;">
        <p style="font-size: 18px; margin: 0; color: #E6E6E6;">👋 <strong>Welcome Student!</strong><br>Please enter your <strong>Access Key</strong> in the Sidebar to unlock.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🏆 Why Top Rankers Choose JEEx **PRO**")
    c1, c2 = st.columns(2)
    with c1:
        st.info("**🧠 Advanced Problem Solving**\n\nSolves Irodov, Cengage, and PYQ level problems.")
        st.info("**📄 Full Document Brain**\n\nUpload PDF assignments. Our Code Interpreter analyzes context.")
        st.info("**🎯 Concept-First Approach**\n\nWe explain the 'Why', not just the answer.")
    with c2:
        st.info("**👁️ Vision Intelligence (OCR)**\n\nReads handwritten questions from photos instantly.")
        st.info("**➗ Perfect Math Formatting**\n\nTextbook-quality LaTeX rendering.")
        st.info("**⚡ 24/7 Strategic Mentorship**\n\nYour personal AI coach for strategy.")
    st.stop()

# --- 10. CHAT ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    assistant_id = st.secrets["ASSISTANT_ID"]
except: st.error("🚨 Keys missing."); st.stop()

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# INPUT LOGIC
audio_prompt = None
if 'audio_value' in locals() and audio_value and not st.session_state.processing:
    with st.spinner("🎧 Listening..."):
        try:
            transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_value, language="en")
            audio_prompt = transcription.text
        except: pass

text_prompt = st.chat_input("Ask a doubt...", disabled=st.session_state.processing)
prompt = audio_prompt if audio_prompt else text_prompt

if prompt:
    st.session_state.processing = True
    
    # Store history
    msg_data = {"role": "user", "content": prompt}
    if uploaded_file:
        msg_data.update({"file_data": uploaded_file.getvalue(), "file_name": uploaded_file.name, "file_type": uploaded_file.type})
    st.session_state.messages.append(msg_data)
    st.rerun()

# DISPLAY
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=LOGO_URL if msg["role"]=="assistant" else "🧑‍🎓"):
        if "file_data" in msg:
            if msg["file_type"].startswith("image"): st.image(msg["file_data"], width=200)
            else: st.markdown(f"📄 *{msg['file_name']}*")
        st.markdown(clean_latex(msg["content"]))

# PROCESS RESPONSE
if st.session_state.processing and st.session_state.messages[-1]["role"] == "user":
    msg_text = st.session_state.messages[-1]["content"]
    api_content = [{"type": "text", "text": msg_text}]
    att = []
    
    if uploaded_file:
        try:
            tfile = f"temp_{uploaded_file.name}"
            with open(tfile, "wb") as f: f.write(uploaded_file.getbuffer())
            fres = client.files.create(file=open(tfile, "rb"), purpose="assistants")
            if uploaded_file.type == "application/pdf": att.append({"file_id": fres.id, "tools": [{"type": "code_interpreter"}]})
            else: api_content.append({"type": "image_file", "image_file": {"file_id": fres.id}})
            os.remove(tfile)
        except: pass

    client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=api_content, attachments=att if att else None)

    with st.chat_message("assistant", avatar=LOGO_URL):
        stream = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id, assistant_id=assistant_id, stream=True,
            additional_instructions="You are JEEx. Use LaTeX for math. Use code interpreter for PDFs."
        )
        resp_cont = st.empty()
        full_text = ""
        for event in stream:
            if event.event == "thread.message.delta":
                for c in event.data.delta.content:
                    if c.type == "text":
                        full_text += c.text.value
                        resp_cont.markdown(clean_latex(full_text) + "▌")
            elif event.event == "thread.run.completed": break
        
        resp_cont.markdown(clean_latex(full_text))
        st.session_state.messages.append({"role": "assistant", "content": full_text})

    st.session_state.uploader_key += 1
    if 'audio_value' in locals() and audio_value: st.session_state.audio_key += 1
    st.session_state.processing = False
    st.rerun()
