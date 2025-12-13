import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime, timedelta
from fpdf import FPDF
import requests
import traceback
import logging

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="wide", initial_sidebar_state="expanded")

# *** EMAIL SETTINGS ***
ADMIN_EMAIL = "jeexaipro@gmail.com"  

# --- 2. GLOBAL CONSTANTS ---
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

# --- 3. SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome Champ! 🎓 Physics, Chemistry ya Maths—bas photo bhejo ya type karo. Let's crack it! 🚀"}]
if "processing" not in st.session_state: st.session_state.processing = False
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "audio_key" not in st.session_state: st.session_state.audio_key = 0
if "current_uploaded_file" not in st.session_state: st.session_state.current_uploaded_file = None

# AUTH & REGISTRATION STATE
if "is_verified" not in st.session_state: st.session_state.is_verified = False
if "user_details" not in st.session_state: st.session_state.user_details = {}

# MODE STATES
if "ultimate_mode" not in st.session_state: st.session_state.ultimate_mode = False
if "deep_research_mode" not in st.session_state: st.session_state.deep_research_mode = False

# NEW SPECIFICATION STATES
if "target_exam" not in st.session_state: st.session_state.target_exam = "JEE Mains"
if "subject_focus" not in st.session_state: st.session_state.subject_focus = "All Subjects"

# SEND TRIGGER (ADDITIVE)
if "force_send" not in st.session_state: st.session_state.force_send = False

# Logger
logger = logging.getLogger("jeex")
logger.setLevel(logging.INFO)

# --- 4. PROFESSIONAL CSS (ORIGINAL + ADDITIVE FIXES ONLY) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stApp { background-color: #000000 !important; color: #E0E0E0 !important; }
    [data-testid="stSidebar"] { background-color: #050810 !important; border-right: 1px solid #0D1B2E !important; }
    header, header * { background-color: #000000 !important; color: #E0E0E0 !important; }

    h1, h2, h3, h4, h5, h6, p, li, div, span, label {
        color: #E0E0E0 !important;
    }

    strong { color: #00A6FF !important; }
    code { color: #00A6FF !important; background-color: #0D1B2E !important; }

    /* INPUTS */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #050810 !important;
        border: 1px solid #00A6FF !important;
        border-radius: 8px !important;
    }

    /* ============================
       FIX 1: DROPDOWN VISIBILITY
       ============================ */
    div[data-baseweb="select"] > div {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    div[data-baseweb="select"] span {
        color: #FFFFFF !important;
    }
    li[data-baseweb="option"] {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    li[data-baseweb="option"]:hover,
    li[data-baseweb="option"][aria-selected="true"] {
        background-color: #0D1B2E !important;
        color: #00A6FF !important;
        font-weight: 600 !important;
    }

    /* ============================
       FIX 2: REMOVE NEON CHAT GLOW
       ============================ */
    .stChatInput textarea {
        background-color: #050810 !important;
        border: 1px solid #333333 !important;
        box-shadow: none !important;
        outline: none !important;
        color: #FFFFFF !important;
    }
    .stChatInput textarea:focus {
        border: 1px solid #444444 !important;
        box-shadow: none !important;
    }

    /* ============================
       FIX 3: SIDEBAR SEND BUTTON
       ============================ */
    .sidebar-send-btn > button {
        width: 100% !important;
        background-color: #00A6FF !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---
# (UNCHANGED — EXACTLY AS YOUR ORIGINAL)

def send_lead_notification(name, email, phone):
    url = f"https://formsubmit.co/{ADMIN_EMAIL}"
    payload = {
        "_subject": f"🚀 NEW JEEx USER: {name}",
        "_captcha": "false",
        "_template": "table",
        "Name": name,
        "Email": email,
        "Phone": phone,
        "Status": "Free Trial Activated",
        "Timestamp": str(datetime.now())
    }
    try:
        requests.post(url, data=payload)
        return True
    except:
        return True

# --- 6. SIDEBAR LOGIC (ORIGINAL + ADDITIVE SEND BUTTON) ---
with st.sidebar:
    if not st.session_state.is_verified:
        st.markdown("## 🔓 Get Free Access")
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            phone = st.text_input("Phone Number")
            submit_reg = st.form_submit_button("🚀 Start Free Trial")

        if submit_reg and name and email and phone:
            send_lead_notification(name, email, phone)
            st.session_state.user_details = {"name": name, "email": email}
            st.session_state.is_verified = True
            st.rerun()

    else:
        st.markdown("### ⚡ Power Tools")

        st.selectbox("🎯 Target Exam", ["JEE Mains", "JEE Advanced"], key="target_exam")
        st.selectbox("📚 Subject Focus", ["All Subjects", "Physics", "Chemistry", "Mathematics"], key="subject_focus")

        st.markdown("---")

        # ✅ ADDITIVE SEND BUTTON
        if st.button("📨 Send Message", use_container_width=True):
            st.session_state.force_send = True

# --- 7. BRANDING ---
c1, c2, c3 = st.columns([2, 2, 2])
with c2:
    st.image(LOGO_URL, use_container_width=True)

st.markdown("""
<div style="text-align:center; margin-top:-15px; margin-bottom:30px;">
    <h1 style="font-size:52px; font-weight:700;">
        JEEx <span style="color:#00A6FF;">PRO</span>
    </h1>
    <p style="color:#AAAAAA; font-size:18px;">
        Your 24/7 AI Rank Booster | Master JEE Mains & Advanced 🚀
    </p>
</div>
""", unsafe_allow_html=True)

# --- 8. CHAT INPUT ---
text_prompt = st.chat_input("Ask a doubt...", disabled=st.session_state.processing)

# ✅ MODIFIED CONDITION (ADDITIVE ONLY)
if text_prompt or st.session_state.force_send:
    prompt = text_prompt
    st.session_state.force_send = False

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# --- 9. DISPLAY CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=LOGO_URL if msg["role"]=="assistant" else "🧑‍🎓"):
        st.markdown(msg["content"])
