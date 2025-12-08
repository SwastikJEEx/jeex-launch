import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="centered", initial_sidebar_state="expanded")

# --- 2. PROFESSIONAL UI CSS (ChatGPT/Gemini Style) ---
st.markdown("""
<style>
    /* Import Professional Font (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main Background */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #161B26; border-right: 1px solid #2B313E; }
    
    /* Layout Adjustments */
    .block-container { padding-top: 2rem; }
    
    /* --- CHAT BUBBLES --- */
    [data-testid="stChatMessage"] { 
        background-color: transparent; 
        border: none; 
        padding: 10px 0px; 
    }
    
    /* User Bubble */
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #1E2330;
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 10px;
        border: 1px solid #2B313E;
    }
    
    /* Assistant Bubble */
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: transparent;
        padding: 0px 20px;
        margin-bottom: 10px;
    }
    
    /* Chat Text Size & Color */
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] div {
        font-size: 16px !important;
        line-height: 1.6 !important;
        color: #E6E6E6 !important;
    }
    
    /* Highlights */
    strong { color: #FFD700 !important; } /* Gold for emphasis */
    code { color: #FF7043 !important; }   /* Orange for code/math */
    
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
        font-weight: 600;
    }
    div.stButton > button:hover { 
        border-color: #4A90E2 !important; 
        color: #4A90E2 !important;
    }
    
    /* Hide Defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Math Formatting */
    .katex { font-size: 1.2em; color: #FFD700 !important; } 
    
    /* Remove Padding from File Uploader */
    [data-testid="stFileUploader"] { padding: 0px; }
    
    /* Avatar Size Fix */
    .stChatMessage .st-emotion-cache-1p1m4ay { width: 42px; height: 42px; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def clean_latex(text):
    """Cleans OpenAI response: Removes source tags & fixes LaTeX"""
    if not text: return ""
    # 1. Remove Source Tags like 【4:4†source】
    text = re.sub(r'【.*?†source】', '', text)
    # 2. Fix LaTeX brackets
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    return text

# GLOBAL LOGO URL (Raw Link)
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

def show_branding():
    """Displays Centered Logo and Branding"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image(LOGO_URL, use_container_width=True)
        except:
            pass 
            
    st.markdown("""
        <div style="text-align: center; margin-top: -10px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 36px; font-weight: 700; letter-spacing: 1px;">
                JEEx <span style="color:#4A90E2;">PRO</span>
            </h1>
            <p style="color: #AAAAAA; font-size: 14px; margin-top: 8px;">
                Your 24/7 AI Rank Booster | Master JEE Mains & Advanced 🚀
            </p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. LOGOUT LOGIC ---
if st.session_state.get('logout', False):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 5. SMART KEY LOGIC ---
def check_key_status(user_key):
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"): return "VALID"

    expiry_db = st.secrets.get("KEY_EXPIRY", {})
    if user_key in expiry_db:
        try:
            expiry_date = datetime.strptime(expiry_db[user_key], "%Y-%m-%d").date()
            if datetime.now().date() > expiry_date: return "EXPIRED"
        except: pass 

    if user_key in st.secrets.get("VALID_KEYS", []): return "VALID"
    if len(user_key) != 9 or user_key[:5] != "JEExa" or not user_key[5:].isdigit(): return "INVALID"
    if 1 <= int(user_key[5:]) <= 1000: return "VALID"
    return "INVALID"

# --- 6. DETAILED TERMS & CONDITIONS ---
terms_text = """
**JEEx Terms of Service & Usage Policy**

**1. Service Description** JEEx Pro is an AI-powered educational assistant designed to aid students in JEE preparation. It uses advanced language models to solve problems and explain concepts.

**2. Accuracy Disclaimer** Artificial Intelligence can occasionally produce "hallucinations" or calculation errors. Users are strictly advised to verify critical data, formulas, and constants with standard resources (NCERT, HC Verma). JEEx is a study aid, not a replacement for official textbooks.

**3. Account Security** * **Single User License:** This Access Key is licensed to ONE individual only.
* **Zero Tolerance:** Our system monitors IP addresses. Sharing your key on Telegram, WhatsApp, or with friends will result in an **immediate, permanent ban** without refund.

**4. Payments & Refunds** * **No Refunds:** As this is a digital access service, all sales are final once the key is delivered.
* **Validity:** Monthly subscriptions are valid for exactly 30 days from activation.

**5. Privacy** Your chat data is processed securely via OpenAI APIs. We do not sell your personal data.
"""

# --- 7. SIDEBAR LOGIC ---
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
            st.warning("Your JEEx Pro monthly Plan has expired.")
            btn_text = "👉 Renew Now (₹99)"
        else:
            if user_key: st.warning("🔒 Chat Locked")
            btn_text = "👉 Subscribe for ₹99 / Month"
            
        payment_link = "https://pages.razorpay.com/pl_Hk7823hsk" 
        
        st.markdown(f"""
            <a href="{payment_link}" target="_blank">
                <button style="width:100%; background-color:#4A90E2; color:white; border:none; padding:12px; border-radius:8px; cursor:pointer; font-weight:bold; font-size:15px; margin-top:10px;">
                    {btn_text}
                </button>
            </a>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("📄 Terms & Conditions"):
             st.markdown(terms_text)

# --- 8. MAIN APP LOGIC ---

# SHOW BRANDING ON ALL PAGES
show_branding()

# SCENARIO A: LANDING PAGE (LOCKED)
if status != "VALID":
    st.markdown("---")
    
    # Instruction Box
    st.markdown("""
    <div style="background-color: #1E2330; padding: 25px; border-radius: 12px; border-left: 5px solid #4A90E2; margin-bottom: 30px; text-align: center;">
        <p style="font-size: 18px; margin: 0; color: #E6E6E6;">
            👋 <strong>Welcome Student!</strong><br>
            Please enter your <strong>Access Key</strong> in the Sidebar (↖️ Top Left) to unlock the AI.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Features List
    st.markdown("""
    <div style="background-color: #161B26; padding: 35px; border-radius: 15px; border: 1px solid #2B313E;">
        <h2 style="color: #4A90E2; margin-top: 0; font-size: 24px; border-bottom: 1px solid #3E4654; padding-bottom: 15px; margin-bottom: 20px; text-align: center;">
            🏆 Why Top Rankers Choose JEEx <span style="color:#4A90E2">PRO</span>
        </h2>
        <div style="display: flex; flex-direction: column; gap: 20px;">
            <div>
                <strong style="color: #FFD700; font-size: 19px;">🧠 Advanced Problem Solving</strong><br>
                <span style="color: #CCCCCC; font-size: 16px;">Instantly solves Irodov, Cengage, and PYQ level problems with step-by-step logic.</span>
            </div>
            <div>
                <strong style="color: #FFD700; font-size: 19px;">👁️ Vision Intelligence</strong><br>
                <span style="color: #CCCCCC; font-size: 16px;">Stuck on a handwritten question? Just upload a photo. JEEx solves it.</span>
            </div>
            <div>
                <strong style="color: #FFD700; font-size: 19px;">📄 Document Analysis</strong><br>
                <span style="color: #CCCCCC; font-size: 16px;">Upload entire PDF assignments. Our Code Interpreter analyzes the full context.</span>
            </div>
            <div>
                <strong style="color: #FFD700; font-size: 19px;">➗ Perfect Math Formatting</strong><br>
                <span style="color: #CCCCCC; font-size: 16px;">Renders complex integrals and matrices with textbook LaTeX precision.</span>
            </div>
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
    with st.expander("📄 Terms & Conditions"):
         st.markdown(terms_text)

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
    welcome_msg = "Welcome Champ! 🎓 Main hoon JEEx. \n\nPhysics ka numerical, Chemistry ka reaction, ya Maths ka integral—bas photo bhejo ya type karo. Let's crack it! 🚀"
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]

# Display Chat History with CUSTOM AVATARS
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        avatar_icon = LOGO_URL # Your Logo
    else:
        avatar_icon = "🧑‍🎓" # Student Icon
        
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(clean_latex(msg["content"]))

# Chat Input
if prompt := st.chat_input("Ask a doubt (e.g. Rotational Motion)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Show User Message
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
        if uploaded_file:
            if uploaded_file.type == "application/pdf": st.markdown(f"📄 *PDF Attached*")
            else: st.image(uploaded_file, width=200)

    # Prepare Message Content
    message_content = [{"type": "text", "text": prompt}]
    attachments = [] 
    if uploaded_file:
        with st.spinner("Analyzing file..."):
            try:
                temp_filename = f"temp_{uploaded_file.name}"
                with open(temp_filename, "wb") as f: f.write(uploaded_file.getbuffer())
                file_response = client.files.create(file=open(temp_filename, "rb"), purpose="assistants")
                
                if uploaded_file.type == "application/pdf":
                    attachments.append({"file_id": file_response.id, "tools": [{"type": "code_interpreter"}]})
                else:
                    message_content.append({"type": "image_file", "image_file": {"file_id": file_response.id}})
                os.remove(temp_filename)
            except: st.error("File upload failed.")

    # Send to Thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=message_content,
        attachments=attachments if attachments else None
    )

    # STREAMING RESPONSE
    with st.chat_message("assistant", avatar=LOGO_URL):
        stream = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            stream=True,
            additional_instructions="""
            You are JEEx, an elite JEE Advanced Tutor.
            1. LEVEL: Solve problems using Irodov/Cengage level rigor.
            2. FORMAT: STRICTLY use LaTeX for ALL math expressions ($$x^2$$ for block, $x$ for inline).
            3. TONE: Professional yet encouraging (Mentor vibe). Use Hinglish for motivation.
            4. PDFS: Use Code Interpreter to analyze uploaded PDFs.
            """
        )
        
        response_container = st.empty()
        collected_message = ""
        
        for event in stream:
            if event.event == "thread.message.delta":
                for content in event.data.delta.content:
                    if content.type == "text":
                        collected_message += content.text.value
                        # Clean on the fly
                        response_container.markdown(clean_latex(collected_message) + "▌")
            
            elif event.event == "thread.run.completed":
                break

        response_container.markdown(clean_latex(collected_message))
        
        st.session_state.messages.append({"role": "assistant", "content": collected_message})
        st.session_state.uploader_key += 1
