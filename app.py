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

# --- 2. GLOBAL CONSTANTS ---
ADMIN_WHATSAPP = "919839940400"
ADMIN_EMAIL = "jeexaipro@gmail.com"
TOPMATE_LINK = "https://topmate.io/jeexpro/1840366"
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

# --- 3. SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome Champ! 🎓 Physics, Chemistry ya Maths—bas photo bhejo ya type karo. Let's crack it! 🚀"}]
if "processing" not in st.session_state: st.session_state.processing = False
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "audio_key" not in st.session_state: st.session_state.audio_key = 0

# --- 4. PROFESSIONAL CSS (BLUE THEME & VISIBILITY FIXED) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* 1. FORCE DARK BACKGROUNDS */
    .stApp { background-color: #0E1117 !important; color: #E0E0E0 !important; }
    [data-testid="stSidebar"] { background-color: #161B26 !important; border-right: 1px solid #2B313E !important; }
    
    /* 2. TEXT COLOR FORCE */
    h1, h2, h3, h4, h5, h6, p, li, div, span, label { color: #E0E0E0 !important; }
    strong { color: #FFD700 !important; font-weight: 600; }
    code { color: #FF7043 !important; background-color: #1E2330; }

    /* 3. INPUT FIELDS (High Contrast) */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
        background-color: #1E2330 !important;
        border: 1px solid #4A90E2 !important;
        border-radius: 8px !important;
    }
    input[type="text"], input[type="password"], textarea, div[data-baseweb="select"] div {
        color: #FFFFFF !important;
        background-color: transparent !important;
        caret-color: #4A90E2 !important;
    }
    ::placeholder { color: #AAAAAA !important; opacity: 1; }

    /* 4. BUTTONS (Professional Blue) */
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
        color: white !important;
    }

    /* 5. EXPANDERS & DROPDOWNS (Professional Blue Heading) */
    .streamlit-expanderHeader {
        background-color: #4A90E2 !important; /* Professional Blue Background */
        color: #FFFFFF !important; /* White Text */
        border-radius: 8px;
        border: 1px solid #357ABD !important;
    }
    .streamlit-expanderHeader:hover {
        background-color: #357ABD !important;
        color: #FFFFFF !important;
    }
    /* The content inside the dropdown */
    .streamlit-expanderContent {
        background-color: #161B26 !important;
        border: 1px solid #4A90E2;
        border-top: none;
        color: #E0E0E0 !important;
    }
    
    /* 6. PASSWORD EYE ICON */
    button[aria-label="Show password"] { color: #E0E0E0 !important; }

    /* 7. LAYOUT */
    .block-container { padding-top: 1rem; padding-bottom: 140px; }
    [data-testid="stFileUploader"] { padding: 0px; }
    .stAudioInput { margin-top: 5px; }
    .stChatMessage .st-emotion-cache-1p1m4ay { width: 45px; height: 45px; }
    .stApp[data-test-state="running"] .stChatInput { opacity: 0.5; pointer-events: none; }
    .katex-display { overflow-x: auto; overflow-y: hidden; padding-bottom: 5px; color: #FFD700 !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---

def send_lead_notification(name, email, phone):
    """Sends Lead Details to Admin Email"""
    try:
        url = f"https://formsubmit.co/{ADMIN_EMAIL}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        }
        payload = {
            "_subject": f"🚀 NEW LEAD: {name}",
            "_captcha": "false",
            "_template": "table",
            "Name": name,
            "Email": email,
            "Phone": phone,
            "Action": "Clicked Proceed to Pay",
            "Timestamp": str(datetime.now())
        }
        requests.post(url, data=payload, headers=headers)
        return True
    except:
        return False

def clean_latex_for_chat(text):
    """Formats LaTeX for Chat Display"""
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    return text

def translate_latex_for_pdf(text):
    """Translates LaTeX to Clean Mathematical Notation for PDF"""
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    
    # 1. Fractions: \frac{a}{b} -> (a/b)
    text = re.sub(r'\\frac{(.*?)}{(.*?)}', r'(\1 / \2)', text)
    
    # 2. Integrals: \int_{a}^{b} -> int_a^b
    text = re.sub(r'\\int_\{(.*?)\}\^\{(.*?)\}', r'int_\1^\2', text)
    text = text.replace(r'\int', 'int')
    
    # 3. Limits / Brackets
    text = text.replace(r'\left[', '[').replace(r'\right]', ']')
    text = text.replace(r'\left(', '(').replace(r'\right)', ')')
    text = text.replace(r'\{', '{').replace(r'\}', '}')
    
    # 4. Clean up LaTeX syntax
    commands = [r'\cdot', r'\times', r'\sqrt', r'\approx', r'\le', r'\ge', r'\infty', r'\pi', r'\theta', r'\sin', r'\cos', r'\tan']
    for cmd in commands:
        text = text.replace(cmd, cmd.replace('\\', ''))
        
    # 5. Remove delimiters
    text = text.replace('$$', '').replace('$', '').replace('\\', '')
    
    # 6. Compress spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text.encode('latin-1', 'replace').decode('latin-1')

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
        self.cell(0, 10, 'JEEx Pro - Study Session', 0, 1, 'C')
        self.ln(5)
    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(74, 144, 226)
        self.cell(0, 10, translate_latex_for_pdf(label), 0, 1, 'L')
        self.ln(2)
    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 7, translate_latex_for_pdf(body))
        self.ln()

def generate_pdf(messages):
    pdf = PDF()
    pdf.add_page()
    for msg in messages:
        role = "JEEx" if msg["role"] == "assistant" else "Student"
        pdf.chapter_title(role)
        pdf.chapter_body(msg["content"])
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 6. AUTH & LOGIC ---
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

# --- 7. SIDEBAR (TOPMATE FLOW) ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    
    user_key = st.text_input("Enter Access Key:", type="password") 
    status = check_key_status(user_key)
    
    # --- UNLOCKED TOOLS ---
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

    # --- LOCKED (TOPMATE INTEGRATION) ---
    else:
        if user_key and status != "VALID": st.error("❌ Invalid Key")
        
        st.markdown("### ⚡ Subscribe Now")
        with st.expander("💎 Get Premium (₹99/mo)", expanded=True):
            st.markdown("Fill details to proceed:")
            
            with st.form("reg_form"):
                name = st.text_input("Name")
                email = st.text_input("Email")
                phone = st.text_input("WhatsApp No.")
                # This button triggers the email
                submitted = st.form_submit_button("🚀 Proceed to Pay")
            
            if submitted:
                if name and email and phone:
                    # 1. Send Data to You
                    send_lead_notification(name, email, phone)
                    
                    st.success("Details Recorded! Click below to pay:")
                    
                    # 2. Show Link to Topmate
                    st.markdown(f'''
                        <a href="{TOPMATE_LINK}" target="_blank">
                            <button style="width:100%; background-color:#4A90E2; color:white; border:none; padding:12px; border-radius:8px; font-weight:bold; font-size:16px; cursor:pointer;">
                                💳 Pay Now on Topmate
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
                    st.caption("Secure payment via UPI/Cards on Topmate.")
                else:
                    st.warning("⚠️ Please fill all details.")

        st.markdown("---")
        with st.expander("📄 Detailed Terms & Conditions"): 
            st.markdown("""
            **1. Service Scope:** JEEx Pro is an AI-powered educational aid for JEE preparation. It provides explanations, solves numericals, and offers strategies.
            
            **2. Account Usage:** - **Single User:** Keys are strictly personal.
            - **Prohibited:** Sharing keys on public groups results in an immediate ban.
            
            **3. Payment Policy:** - Access Keys are digital goods. 
            - **No Refunds** are provided once the key is issued.
            
            **4. AI Limitations:** - While accurate, AI can make errors. Verify critical data with NCERT.
            """)

# --- 8. ADMIN PANEL ---
if status == "ADMIN":
    st.sidebar.success("🔑 Admin Mode")
    c1, c2 = st.columns(2)
    with c1: new_id = st.text_input("Key ID")
    with c2: days = st.number_input("Days", 30)
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
        st.info("**🧠 Advanced Problem Solving**\n\nSolves Irodov, Cengage, and PYQ level problems with step-by-step logic.")
        st.info("**📄 Full Document Brain**\n\nUpload entire PDF assignments. Our Code Interpreter analyzes context.")
        st.info("**🎯 Concept-First Approach**\n\nWe don't just solve; we explain the 'Why'. Learn the derivation.")
    with c2:
        st.info("**👁️ Vision Intelligence (OCR)**\n\nReads handwritten questions from photos instantly.")
        st.info("**➗ Perfect Math Formatting**\n\nTextbook-quality rendering for Integrals and Organic Mechanisms.")
        st.info("**⚡ 24/7 Strategic Mentorship**\n\nYour personal AI coach for study planning and backlog management.")
    
    st.stop()

# --- 10. CHAT INTERFACE ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    assistant_id = st.secrets["ASSISTANT_ID"]
except: st.error("🚨 Keys missing."); st.stop()

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# INPUT LOGIC
audio_prompt = None
if 'audio_value' in locals() and audio_value:
    if not st.session_state.processing:
        with st.spinner("🎧 Listening..."):
            try:
                transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_value, language="en")
                audio_prompt = transcription.text
            except: pass

text_prompt = st.chat_input("Ask a doubt...", disabled=st.session_state.processing)
prompt = audio_prompt if audio_prompt else text_prompt

if prompt:
    st.session_state.processing = True
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
        st.markdown(clean_latex_for_chat(msg["content"]))

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
            
            if uploaded_file.type == "application/pdf":
                att.append({"file_id": fres.id, "tools": [{"type": "code_interpreter"}]})
            else:
                api_content.append({"type": "image_file", "image_file": {"file_id": fres.id}})
            
            os.remove(tfile)
        except: st.error("Upload failed.")

    client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=api_content, attachments=att if att else None)

    with st.chat_message("assistant", avatar=LOGO_URL):
        stream = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id, assistant_id=assistant_id, stream=True,
            additional_instructions="You are JEEx. Use $$...$$ for block math and $...$ for inline. Strictly LaTeX."
        )
        resp = st.empty()
        full_text = ""
        for event in stream:
            if event.event == "thread.message.delta":
                for c in event.data.delta.content:
                    if c.type == "text":
                        full_text += c.text.value
                        resp.markdown(clean_latex_for_chat(full_text) + "▌")
            elif event.event == "thread.run.completed": break
        
        resp.markdown(clean_latex_for_chat(full_text))
        st.session_state.messages.append({"role": "assistant", "content": full_text})

    st.session_state.uploader_key += 1
    if 'audio_value' in locals() and audio_value: st.session_state.audio_key += 1
    st.session_state.processing = False
    st.rerun()
