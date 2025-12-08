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
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

# --- 3. SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome Champ! 🎓 Physics, Chemistry ya Maths—bas photo bhejo ya type karo. Let's crack it! 🚀"}]
if "processing" not in st.session_state: st.session_state.processing = False
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "audio_key" not in st.session_state: st.session_state.audio_key = 0

# PAYMENT STATE
if "payment_step" not in st.session_state: st.session_state.payment_step = 1
if "user_details" not in st.session_state: st.session_state.user_details = {}

# --- 4. PROFESSIONAL CSS (UNIVERSAL THEME FORCE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* --- 1. FORCE DARK BACKGROUNDS --- */
    .stApp { background-color: #0E1117 !important; color: #E0E0E0 !important; }
    [data-testid="stSidebar"] { background-color: #161B26 !important; border-right: 1px solid #2B313E !important; }
    
    /* --- 2. UNIVERSAL TEXT VISIBILITY --- */
    h1, h2, h3, h4, h5, h6, p, li, div, span, label {
        color: #E0E0E0 !important;
    }
    strong { color: #FFD700 !important; font-weight: 600; }
    code { color: #FF7043 !important; }

    /* --- 3. INPUT FIELDS (High Contrast) --- */
    div[data-baseweb="input"], .stTextInput input {
        background-color: #1E2330 !important;
        border: 1px solid #4A90E2 !important; /* Blue Border */
        border-radius: 8px !important;
        color: #FFFFFF !important; /* Force White Text */
        -webkit-text-fill-color: #FFFFFF !important;
    }
    ::placeholder { color: #AAAAAA !important; opacity: 1; }

    /* --- 4. BUTTONS (Professional Blue) --- */
    div.stButton > button { 
        background-color: #4A90E2 !important; /* JEEx Blue */
        color: white !important; 
        border: none !important; 
        border-radius: 8px; 
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
    }
    div.stButton > button:hover { 
        background-color: #357ABD !important; /* Darker Blue Hover */
        box-shadow: 0px 4px 15px rgba(74, 144, 226, 0.4);
    }

    /* --- 5. EXPANDER & CONTAINERS --- */
    .streamlit-expanderHeader {
        background-color: #1E2330 !important;
        color: #E0E0E0 !important;
        border-radius: 8px;
    }
    
    /* --- 6. LAYOUT FIXES --- */
    .block-container { padding-top: 1rem; padding-bottom: 140px; }
    [data-testid="stFileUploader"] { padding: 0px; }
    .stAudioInput { margin-top: 5px; }
    .stChatMessage .st-emotion-cache-1p1m4ay { width: 45px; height: 45px; }
    
    /* Lock Input when Processing */
    .stApp[data-test-state="running"] .stChatInput { opacity: 0.5; pointer-events: none; }
</style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---

def send_final_notification(name, email, phone, trans_id):
    """Sends FINAL email with Transaction ID to Admin"""
    try:
        url = f"https://formsubmit.co/{ADMIN_EMAIL}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://jeex-pro.streamlit.app/"
        }
        payload = {
            "_subject": f"💰 PAYMENT VERIFICATION: {name}",
            "_captcha": "false",
            "_template": "table",
            "Name": name,
            "Email": email,
            "Phone": phone,
            "Transaction ID": trans_id,
            "Status": "Paid - Waiting for Key",
            "Timestamp": str(datetime.now())
        }
        resp = requests.post(url, data=payload, headers=headers)
        return resp.status_code == 200
    except:
        return False

def clean_latex(text):
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    text = text.replace('$$$', '$')
    return text

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
        self.cell(0, 10, 'JEEx Pro - Study Session', 0, 1, 'C')
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
        content = clean_latex(msg["content"]).replace('*', '')
        pdf.chapter_title(role)
        pdf.chapter_body(content)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 6. AUTH & LOGIC ---
def check_key_status(user_key):
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"): return "ADMIN"
    expiry_db = st.secrets.get("KEY_EXPIRY", {})
    if user_key in expiry_db:
        try:
            expiry_date = datetime.strptime(expiry_db[user_key], "%Y-%m-%d").date()
            if datetime.now().date() > expiry_date: return "EXPIRED"
            else: return "VALID"
        except: return "INVALID"
    return "INVALID"

if st.session_state.get('logout', False):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- 7. SIDEBAR (SMART PAYMENT FLOW) ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    
    user_key = st.text_input("Enter Access Key:", type="
