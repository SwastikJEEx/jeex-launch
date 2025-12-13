import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime
from fpdf import FPDF
import requests
import logging

# ======================================================
# 1. CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="JEEx Pro",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

ADMIN_EMAIL = "jeexaipro@gmail.com"
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

# ======================================================
# 2. SESSION STATE
# ======================================================
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Welcome Champ! 🎓 Physics, Chemistry ya Maths—bas photo bhejo ya type karo. Let's crack it! 🚀"
    }]

if "processing" not in st.session_state: st.session_state.processing = False
if "target_exam" not in st.session_state: st.session_state.target_exam = "JEE Mains"
if "subject_focus" not in st.session_state: st.session_state.subject_focus = "All Subjects"
if "force_send" not in st.session_state: st.session_state.force_send = False
if "is_verified" not in st.session_state: st.session_state.is_verified = True

# ======================================================
# 3. CSS — ONLY VISIBILITY & UX FIXES
# ======================================================
st.markdown("""
<style>

/* --------------------------------------------------
   FIX 1: Target Exam & Subject text visibility
-------------------------------------------------- */
div[data-baseweb="select"] > div {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    background-color: #050810 !important;
}

div[data-baseweb="select"] span {
    color: #FFFFFF !important;
}

/* Dropdown menu */
li[data-baseweb="option"] {
    background-color: #000000 !important;
    color: #FFFFFF !important;
}
li[data-baseweb="option"]:hover,
li[data-baseweb="option"][aria-selected="true"] {
    background-color: #0D1B2E !important;
    color: #00A6FF !important;
    font-weight: 600;
}

/* --------------------------------------------------
   FIX 2: Remove neon blue outline from typing bar
-------------------------------------------------- */
.stChatInput textarea {
    background-color: #050810 !important;
    color: #FFFFFF !important;
    border: 1px solid #333333 !important;
    box-shadow: none !important;
    outline: none !important;
}
.stChatInput textarea:focus {
    border: 1px solid #444444 !important;
    box-shadow: none !important;
}

/* --------------------------------------------------
   FIX 3: Sidebar Send Button (theme-matched)
-------------------------------------------------- */
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

# ======================================================
# 4. SIDEBAR (NO STRUCTURE CHANGED)
# ======================================================
with st.sidebar:
    st.markdown("### ⚡ Power Tools")

    st.selectbox(
        "🎯 Target Exam",
        ["JEE Mains", "JEE Advanced"],
        key="target_exam"
    )

    st.selectbox(
        "📚 Subject Focus",
        ["All Subjects", "Physics", "Chemistry", "Mathematics"],
        key="subject_focus"
    )

    st.markdown("---")

    # ✅ Sidebar Send Button
    if st.button("📨 Send Message", use_container_width=True):
        st.session_state.force_send = True

# ======================================================
# 5. BRANDING
# ======================================================
c1, c2, c3 = st.columns([2, 2, 2])
with c2:
    st.image(LOGO_URL, use_container_width=True)

st.markdown("""
<div style="text-align:center; margin-top:-15px; margin-bottom:30px;">
    <h1 style="font-size:52px; font-weight:700;">
        JEEx <span style="color:#00A6FF;">PRO</span>
    </h1>
    <p style="color:#AAAAAA; font-size:18px;">
        Your 24/7 AI Rank Booster | JEE Mains & Advanced
    </p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# 6. CHAT INPUT
# ======================================================
text_prompt = st.chat_input("Ask a doubt...", disabled=st.session_state.processing)

# ✅ Unified send trigger (chat OR sidebar)
if text_prompt or st.session_state.force_send:
    prompt = text_prompt
    st.session_state.force_send = False

    if prompt:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        st.rerun()

# ======================================================
# 7. DISPLAY CHAT
# ======================================================
for msg in st.session_state.messages:
    with st.chat_message(
        msg["role"],
        avatar=LOGO_URL if msg["role"] == "assistant" else "🧑‍🎓"
    ):
        st.markdown(msg["content"])
