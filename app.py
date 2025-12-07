import streamlit as st
import time
from openai import OpenAI
import os
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx", page_icon="⚛️", layout="centered", initial_sidebar_state="expanded")

# --- 2. PROFESSIONAL DARK THEME CSS ---
st.markdown("""
<style>
    /* Base Theme */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #161B26; border-right: 1px solid #2B313E; }
    
    /* Text & Math Visibility */
    h1, h2, h3, p, div, label, span, li { color: #E6E6E6 !important; }
    .katex { font-size: 1.1em; color: #FFD700 !important; } 
    
    /* Inputs */
    .stTextInput input, .stTextArea textarea { 
        background-color: #1E2330 !important; 
        color: white !important; 
        border: 1px solid #3E4654 !important; 
    }
    
    /* Buttons */
    div.stButton > button { 
        background-color: #2B313E !important; 
        color: white !important; 
        border: 1px solid #3E4654 !important; 
        width: 100%; 
    }
    div.stButton > button:hover { border-color: #4A90E2 !important; }
    
    /* Chat Bubbles */
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1E2330; border: 1px solid #2B313E; border-radius: 12px; }
    [data-testid="stChatMessage"]:nth-child(even) { background-color: #131720; border: 1px solid #2B313E; border-radius: 12px; }
    
    /* Hide Menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Attachment Button Style */
    [data-testid="stPopover"] > div > button {
        border: none !important;
        background: transparent !important;
        font-size: 1.5rem !important;
        padding: 0px !important;
        margin-top: 5px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. MATH CLEANING FUNCTION ---
def clean_latex(text):
    if not text: return ""
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    return text

# --- 4. SHOW TITLE & EPIC TAGLINE ---
st.markdown("# ⚛️ **JEEx** <span style='color:#4A90E2; font-size:0.6em'>PRO</span>", unsafe_allow_html=True)
st.caption("Your 24/7 AI Rank Booster | Master JEE Mains & Advanced with Precision 🚀")

# --- 5. LOGOUT LOGIC ---
if st.session_state.get('logout', False):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 6. SMART KEY LOGIC ---
def check_smart_key(user_key):
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"): return True
    if user_key in st.secrets.get("VALID_KEYS", []): return True
    if len(user_key) != 9 or user_key[:5] != "JEExa" or not user_key
