import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="centered", initial_sidebar_state="expanded")

# --- 2. PROFESSIONAL & MODERN CSS (Gemini Style) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #161B26; border-right: 1px solid #2B313E; }
    
    /* Center Layout alignment */
    .block-container { padding-top: 3rem; }
    
    /* Chat Bubbles - Gemini Style */
    [data-testid="stChatMessage"] {
        background-color: transparent;
        border: none;
    }
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #1E2330;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }
    [data-testid="stChatMessage"][data-testid="assistant"] {
        padding: 15px;
        margin-bottom: 10px;
    }
    
    /* Text Colors */
    h1, h2, h3, p, li, span { color: #E6E6E6 !important; }
    strong { color: #FFD700 !important; } /* Gold highlights */
    
    /* Inputs */
    .stTextInput input, .stTextArea textarea { 
        background-color: #1E2330 !important; 
        color: white !important; 
        border: 1px solid #3E4654 !important; 
        border-radius: 10px;
    }
    
    /* Buttons */
    div.stButton > button { 
        background-color: #2B313E !important; 
        color: white !important; 
        border: 1px solid #3E4654 !important; 
        border-radius: 8px;
        width: 100%; 
        transition: all 0.3s;
    }
    div.stButton > button:hover { 
        border-color: #4A90E2 !important; 
        color: #4A90E2 !important;
    }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Math Formatting */
    .katex { font-size: 1.15em; color: #FFD700 !important; } 
    
    /* Attachment Button (Clean) */
    [data-testid="stFileUploader"] { padding: 0px; }
</style>
""", unsafe_allow_html=True)

# --- 3. MATH CLEANING FUNCTION ---
def clean_latex(text):
    if not text: return ""
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    return text

# --- 4. SHOW LOGO & BRANDING (Fixed) ---
# We use columns to center the logo and text professionally
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # 1. THE LOGO (Using Raw GitHub Link)
    logo_url = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/main/logo.png"
    try:
        st.image(logo_url, use_column_width=True)
    except:
        st.markdown("## ⚛️ JEEx Pro") # Fallback if image fails

# 2. THE BRANDING TEXT (Centered)
st.markdown("""
    <div style="text-align: center; margin-top: -10px; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 40px;">JEEx <span style="color:#4A90E2;">PRO</span></h1>
        <p style="color: #AAAAAA; font-size: 14px; margin-top: 5px;">
            Your 24/7 AI Rank Booster | Master JEE Mains & Advanced 🚀
        </p>
    </div>
""", unsafe_allow_html=True)

# --- 5. LOGOUT LOGIC ---
if st.session_state.get('logout', False):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 6. SMART KEY LOGIC ---
def check_key_status(user_key):
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"): return "VALID"

    # Check Expiry
    expiry_db = st.secrets.get("KEY_EXPIRY", {})
    if user_key in expiry_db:
        try:
            expiry_date = datetime.strptime(expiry_db[user_key], "%Y-%m-%d").date()
            if datetime.now().date() > expiry_date: return "EXPIRED"
        except: pass 

    # Check Whitelist & Pattern
    if user_key in st.secrets.get("VALID_KEYS", []): return "VALID"
    if len(user_key) != 9 or user_key[:5] != "JEExa" or not user_key[5:].isdigit(): return "INVALID"
    if 1 <= int(user_key[5:]) <= 1000: return "VALID"
    return "INVALID"

# --- 7. SIDEBAR (LOGIN & TOOLS) ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
        
    user_key = st.text_input("Enter Access Key:", type="password")
    status = check_key_status(user_key)
    
    # --- IF LOCKED ---
    if status != "VALID":
        if status == "EXPIRED":
            st.error("⚠️ Plan Expired")
            btn_text = "👉 Renew Now (₹99)"
        else:
            if user_key: st.warning("🔒 Chat Locked")
            btn_text = "👉 Subscribe for ₹99 / Month"
            
        payment_link = "https://rzp.io/rzp/wXI8i7t" 
        
        st.markdown(f"""
            <a href="{payment_link}" target="_blank">
                <button style="width:100%; background-color:#4A90E2; color:white; border:none; padding:12px; border-radius:8px; cursor:pointer; font-weight:bold; font-size:15px; margin-top:10px;">
                    {btn_text}
                </button>
            </a>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("📄 Terms & Conditions"):
             st.markdown("**JEEx Policy:** AI is a study aid. No refunds. Personal use only.")

# --- 8. MAIN AREA LOGIC ---

# SCENARIO A: LANDING PAGE (When Locked)
if status != "VALID":
    st.markdown("---")
    
    # Instruction Box
    st.markdown("""
    <div style="background-color: #1E2330; padding: 20px; border-radius: 12px; border-left: 5px solid #4A90E2; margin-bottom: 30px; text-align: center;">
        <p style="font-size: 18px; margin: 0; color: #E6E6E6;">
            👋 <strong>Welcome Student!</strong><br>
            Please enter your <strong>Access Key</strong> in the Sidebar (↖️ Top Left) to unlock.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature List
    st.markdown("""
    <div style="background-color: #161B26; padding: 30px; border-radius: 15px; border: 1px solid #2B313E;">
        <h2 style="color: #4A90E2; margin-top: 0; font-size: 24px; border-bottom: 1px solid #3E4654; padding-bottom: 15px; margin-bottom: 20px; text-align: center;">
            🏆 Why Top Rankers Choose JEEx Pro
        </h2>
        <div style="display: flex; flex-direction: column; gap: 20px;">
            <div><strong style="color: #FFD700; font-size: 18px;">🧠 Advanced Problem Solving</strong><br><span style="color: #CCCCCC;">Solves Irodov, Cengage, and PYQ level problems with step-by-step logic.</span></div>
            <div><strong style="color: #FFD700; font-size: 18px;">👁️ Vision Intelligence</strong><br><span style="color: #CCCCCC;">Stuck on a handwritten question? Just upload a photo. JEEx solves it.</span></div>
            <div><strong style="color: #FFD700; font-size: 18px;">📄 Document Analysis</strong><br><span style="color: #CCCCCC;">Upload PDF assignments. Our Code Interpreter analyzes the full context.</span></div>
            <div><strong style="color: #FFD700; font-size: 18px;">➗ Perfect Math Formatting</strong><br><span style="color: #CCCCCC;">Renders complex integrals and matrices with LaTeX precision.</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop() 

# SCENARIO B: UNLOCKED CHAT INTERFACE

# Sidebar Tools
with st.sidebar:
    st.success(f"✅ Active")
    st.markdown("---")
    st.markdown("### 📎 Attach Question")
    uploaded_file = st.file_uploader("Upload Image/PDF", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
    if uploaded_file: st.info(f"Attached: {uploaded_file.name}")
    st.markdown("---")
    if st.button("End Session"): st.session_state['logout'] = True; st.rerun()

# Setup OpenAI
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    assistant_id = st.secrets["ASSISTANT_ID"]
    client = OpenAI(api_key=api_key)
except:
    st.error("🚨 Configuration Error: Keys missing.")
    st.stop()

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    # Greeting
    welcome_msg = "Welcome Champ! 🎓 Main hoon JEEx. \n\nPhysics ka numerical, Chemistry ka reaction, ya Maths ka integral—bas photo bhejo ya type karo. Let's crack it! 🚀"
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(clean_latex(msg["content"]))

# Chat Input
if prompt := st.chat_input("Ask a doubt (e.g. Rotational Motion)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file:
            if uploaded_file.type == "application/pdf": st.markdown(f"📄 *PDF Attached*")
            else: st.image(uploaded_file, width=200)

    # Prepare Message
    message_content = [{"type": "text", "text": prompt}]
    attachments = [] 
    if uploaded_file:
        with st.spinner("Analyzing file..."):
            try:
                # Save & Upload
                temp_filename = f"temp_{uploaded_file.name}"
                with open(temp_filename, "wb") as f: f.write(uploaded_file.getbuffer())
                file_response = client.files.create(file=open(temp_filename, "rb"), purpose="assistants")
                
                if uploaded_file.type == "application/pdf":
                    attachments.append({"file_id": file_response.id, "tools": [{"type": "code_interpreter"}]})
                else:
                    message_content.append({"type": "image_file", "image_file": {"file_id": file_response.id}})
                os.remove(temp_filename)
            except: st.error("File upload failed.")

    # Send & Run with SMART INSTRUCTIONS
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=message_content,
        attachments=attachments if attachments else None
    )

    # --- THE BRAIN: JEE KNOWLEDGE INJECTION ---
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id,
        additional_instructions="""
        You are JEEx, an expert JEE Advanced Tutor.
        1. LEVEL: Solve problems using Irodov/Cengage level rigor. Never simplify unnecessarily.
        2. FORMAT: STRICTLY use LaTeX for math ($$x^2$$). Do not use [ ] or ( ).
        3. TONE: Professional, encouraging, and precise. Use "Hinglish" for motivation.
        4. PDFS: Always use Code Interpreter to analyze uploaded PDFs deeper.
        """
    )

    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.markdown("**Thinking...** ⏳")
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
        
        if run.status == 'completed':
            status_box.empty()
            messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            final_response = clean_latex(messages.data[0].content[0].text.value)
            st.markdown(final_response)
            st.session_state.messages.append({"role": "assistant", "content": final_response})
            st.session_state.uploader_key += 1
            st.rerun()
