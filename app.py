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

# --- 2. GLOBAL CONSTANTS & TEXT ---
ADMIN_WHATSAPP = "919839940400"
ADMIN_EMAIL = "jeexaipro@gmail.com"
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

# Defined GLOBALLY to prevent NameError
TERMS_TEXT = """
### JEEx Pro Terms of Service & End User License Agreement

**1. Acceptance of Terms**
By accessing JEEx Pro, you confirm that you are a student preparing for competitive exams and agree to use this tool solely for educational purposes.

**2. License Grant & Restrictions**
* **License:** JEEx grants you a limited, non-exclusive, non-transferable license to use the AI tutor.
* **Single User Only:** Your Access Key is strictly personal. Sharing it on public forums (Telegram, WhatsApp, Reddit) or with friends is a violation of this agreement.
* **Security Monitoring:** Our system actively logs IP addresses and device fingerprints. Simultaneous logins from multiple locations will trigger an automatic, irreversible ban.

**3. AI Accuracy & Educational Disclaimer**
* **Nature of AI:** JEEx Pro utilizes advanced LLMs (GPT-4o) to generate responses. While highly accurate, "hallucinations" (incorrect data) can occur.
* **User Responsibility:** You agree to verify all formulas, constants, and solutions with standard textbooks (NCERT, H.C. Verma). JEEx is a study companion, not a replacement for official academic instruction.
* **Liability:** JEEx is not liable for any loss of marks, exam results, or academic consequences resulting from reliance on the tool.

**4. Payments & Refund Policy**
* **Digital Goods:** Access Keys are classified as intangible digital goods. Once a key is generated and delivered to you, the service is considered "consumed."
* **No Refunds:** We enforce a strict **No Refund Policy**. All sales are final.
* **Validity:** Subscriptions are valid for exactly 30 days from the date of activation in our system.

**5. Privacy Policy**
We respect your privacy. Chat logs are processed securely via OpenAI APIs for generating responses. User data (Name, Phone, Email) collected during registration is used solely for account management and is not sold to third-party advertisers.
"""

# --- 3. SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome Champ! 🎓 Physics, Chemistry ya Maths—bas photo bhejo ya type karo. Let's crack it! 🚀"}]
if "processing" not in st.session_state: st.session_state.processing = False
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "audio_key" not in st.session_state: st.session_state.audio_key = 0

# PAYMENT STATE
if "payment_step" not in st.session_state: st.session_state.payment_step = 1
if "user_details" not in st.session_state: st.session_state.user_details = {}

# --- 4. PROFESSIONAL CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161B26; border-right: 1px solid #2B313E; }
    
    /* Layout */
    .block-container { padding-top: 1rem; padding-bottom: 140px; }
    
    /* Chat Bubbles */
    [data-testid="stChatMessage"] { background-color: transparent; border: none; padding: 10px 0px; }
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #1E2330; border-radius: 12px; padding: 15px 25px; 
        margin-bottom: 10px; border: 1px solid #2B313E;
    }
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: transparent; padding: 0px 25px; margin-bottom: 10px;
    }
    
    /* Typography */
    p, li, div { font-size: 17px !important; line-height: 1.6 !important; color: #E6E6E6 !important; }
    strong { color: #FFD700 !important; font-weight: 600; } 
    code { color: #FF7043 !important; }
    
    /* Buttons */
    div.stButton > button { 
        background-color: #2B313E !important; color: white !important; border: 1px solid #3E4654 !important; 
        border-radius: 8px; width: 100%; transition: all 0.3s; font-weight: 600;
    }
    div.stButton > button:hover { border-color: #4A90E2 !important; color: #4A90E2 !important; }
    
    /* Sidebar Input Styling (Universal Theme Fix) */
    [data-testid="stSidebar"] input {
        background-color: #1E2330 !important;
        color: white !important;
        border: 1px solid #3E4654 !important;
    }
    [data-testid="stFileUploader"] { padding: 0px; }
    .stAudioInput { margin-top: 5px; }
    .stChatMessage .st-emotion-cache-1p1m4ay { width: 45px; height: 45px; }
    
    /* Locking UI */
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
    text = re
