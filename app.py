import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="centered", initial_sidebar_state="expanded")

# --- 2. PROFESSIONAL GEMINI-STYLE CSS ---
st.markdown("""
<style>
    /* Main Background & Text */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #161B26; border-right: 1px solid #2B313E; }
    
    /* Center Layout alignment */
    .block-container { padding-top: 2rem; }
    
    /* Chat Bubbles */
    [data-testid="stChatMessage"] { background-color: transparent; border: none; }
    
    /* USER BUBBLE (Blue/Grey Professional) */
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #1E2330;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #2B313E;
    }
    
    /* ASSISTANT BUBBLE (Transparent) */
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: transparent;
        padding: 15px;
        margin-bottom: 10px;
    }
    
    /* Text Colors & Highlights */
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
    
    /* Attachment Button Clean-up */
    [data-testid="stFileUploader"] { padding: 0px; }
    
    /* Avatar Styling Fixes */
    .stChatMessage .st-emotion-cache-1p1m4ay { width: 40px; height: 40px; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def clean_latex(text):
    if not text: return ""
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    return text

# GLOBAL LOGO URL (Used for Branding AND Chat Avatar)
# Corrected RAW link from your new permalink
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

def show_branding():
    """Displays Logo and Title Centered"""
    # Using columns to center the image perfectly
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image(LOGO_URL, width=220)
        except:
            pass # Fail silently if image breaks
            
    st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="margin: 0; font-size: 38px;">JEEx <span style="color:#4A90E2;">PRO</span></h1>
            <p style="color: #AAAAAA; font-size: 14px; margin-top: 5px;">
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

# --- 6. TERMS & CONDITIONS TEXT ---
terms_text = """
**JEEx Terms of Service & Usage Policy**

**1. Service Description:**
JEEx Pro is an AI-powered educational assistant designed to aid students in JEE preparation.

**2. Accuracy Disclaimer:**
Artificial Intelligence can occasionally produce "hallucinations". Users are strictly advised to verify critical data with standard resources (NCERT, HC Verma).

**3. Account Security:**
* **Single User License:** This Access Key is licensed to ONE individual.
* **Ban Policy:** Sharing your key will result in an immediate, permanent ban without refund.

**4. Payments & Refunds:**
* **No Refunds:** All sales are final once the key is delivered.
* **Validity:** Monthly subscriptions are valid for 30 days.

**5. Privacy:**
Your chat data is processed securely via OpenAI APIs.
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

# DISPLAY BRANDING ON EVERY PAGE
show_branding()

# SCENARIO A: LANDING PAGE (LOCKED)
if status != "VALID":
    st.markdown("---")
    
    st.markdown("""
    <div style="background-color: #1E2330; padding: 20px; border-radius: 12px; border-left: 5px solid #4A90E2; margin-bottom: 30px; text-align: center;">
        <p style="font-size: 18px; margin: 0; color: #E6E6E6;">
            👋 <strong>Welcome Student!</strong><br>
            Please enter your <strong>Access Key</strong> in the Sidebar (↖️ Top Left) to unlock.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #161B26; padding: 30px; border-radius: 15px; border: 1px solid #2B313E;">
        <h2 style="color: #4A90E2; margin-top: 0; font-size: 24px; border-bottom: 1px solid #3E4654; padding-bottom: 15px; margin-bottom: 20px; text-align: center;">
            🏆 Why Top Rankers Choose JEEx <span style="color:#4A90E2">PRO</span>
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
    # Logic to choose avatar
    if msg["role"] == "assistant":
        avatar_icon = LOGO_URL # Your Logo
    else:
        avatar_icon = "🧑‍🎓" # Professional Student Icon
        
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(clean_latex(msg["content"]))

# Chat Input
if prompt := st.chat_input("Ask a doubt (e.g. Rotational Motion)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Show User Message with Student Avatar
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

    # --- STREAMING RESPONSE LOGIC ---
    # Show Assistant Message with Your Logo Avatar
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
                        response_container.markdown(clean_latex(collected_message) + "▌")
            
            elif event.event == "thread.run.completed":
                break

        response_container.markdown(clean_latex(collected_message))
        
        st.session_state.messages.append({"role": "assistant", "content": collected_message})
        st.session_state.uploader_key += 1
