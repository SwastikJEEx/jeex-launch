import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="centered", initial_sidebar_state="collapsed")

# --- 2. PROFESSIONAL CSS (Gemini/ChatGPT Style) ---
st.markdown("""
<style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Theme Colors */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161B26; border-right: 1px solid #2B313E; }
    
    /* Center Layout */
    .block-container { padding-top: 1rem; padding-bottom: 150px; } /* Padding for bottom toolbar */
    
    /* Chat Bubbles */
    [data-testid="stChatMessage"] { background-color: transparent; border: none; padding: 10px 0px; }
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #1E2330; border-radius: 12px; padding: 15px 20px; 
        margin-bottom: 10px; border: 1px solid #2B313E;
    }
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: transparent; padding: 0px 20px; margin-bottom: 10px;
    }
    
    /* Text Styling */
    p, li, div { font-size: 16px !important; line-height: 1.6 !important; color: #E6E6E6 !important; }
    strong { color: #FFD700 !important; } 
    code { color: #FF7043 !important; }
    
    /* Buttons & Inputs */
    .stTextInput input { background-color: #1E2330 !important; color: white !important; border-radius: 10px; }
    div.stButton > button { 
        background-color: #2B313E !important; color: white !important; border: 1px solid #3E4654 !important; 
        border-radius: 8px; width: 100%; transition: all 0.3s; font-weight: 600;
    }
    div.stButton > button:hover { border-color: #4A90E2 !important; color: #4A90E2 !important; }
    
    /* Hide Defaults */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
    
    /* Math & Formatting */
    .katex { font-size: 1.2em; color: #FFD700 !important; } 
    [data-testid="stFileUploader"] { padding: 0px; }
    .stChatMessage .st-emotion-cache-1p1m4ay { width: 42px; height: 42px; }
    
    /* Toolbar Alignment */
    div[data-testid="column"] { display: flex; align-items: flex-end; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def clean_latex(text):
    """Cleans OpenAI response: Removes source tags & fixes LaTeX"""
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    text = text.replace('$$$', '$')
    return text

def sanitize_text_for_pdf(text):
    """Aggressively cleans text to prevent PDF crashes"""
    # Replace common special chars
    text = text.replace('•', '-').replace('—', '-')
    # Encode to ASCII, ignoring errors (removes emojis/korean/etc), then decode
    return text.encode('ascii', 'ignore').decode('ascii')

LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

def show_branding():
    """Displays Logo and Title PERFECTLY CENTERED"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try: st.image(LOGO_URL, use_container_width=True)
        except: pass
            
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

# --- 4. PDF GENERATOR (FIXED) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'JEEx Pro - Study Session', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(74, 144, 226) # Blue
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

# --- 5. LOGIC & AUTH ---
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

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
    if "audio_key" not in st.session_state: st.session_state.audio_key = 0 # NEW: For resetting audio
    
    user_key = st.text_input("Enter Access Key:", type="password")
    status = check_key_status(user_key)
    
    if status != "VALID" and status != "ADMIN":
        if status == "EXPIRED":
            st.error("⚠️ Plan Expired")
            st.warning("Your JEEx Pro monthly Plan has expired.")
            btn_text = "👉 Renew Now (₹99)"
        else:
            if user_key: st.warning("🔒 Chat Locked")
            btn_text = "👉 Subscribe for ₹99 / Month"
        
        payment_link = "https://pages.razorpay.com/pl_Hk7823hsk" 
        st.markdown(f'<a href="{payment_link}" target="_blank"><button style="width:100%; background-color:#4A90E2; color:white; border:none; padding:12px; border-radius:8px; cursor:pointer; font-weight:bold; font-size:15px; margin-top:10px;">{btn_text}</button></a>', unsafe_allow_html=True)
        st.markdown("---")
        with st.expander("📄 Terms & Conditions"): 
            st.markdown("**JEEx Policy:**\n1. Personal Use Only.\n2. No Refunds.\n3. AI may make errors; verify with NCERT.")

# --- 7. ADMIN PANEL ---
if status == "ADMIN":
    st.sidebar.success("🔑 Admin Mode")
    st.info("Generate Student Keys:")
    c1, c2 = st.columns(2)
    with c1: new_id = st.text_input("Key ID")
    with c2: days = st.number_input("Days", 30)
    if new_id:
        exp = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        st.code(f'"{new_id}" = "{exp}"', language="toml")
    if st.button("Logout"): st.session_state['logout'] = True; st.rerun()
    st.stop()

# --- 8. LANDING PAGE (LOCKED) ---
show_branding()

if status != "VALID":
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #1E2330; padding: 20px; border-radius: 12px; border-left: 5px solid #4A90E2; text-align: center; margin-bottom: 30px;">
        <p style="font-size: 18px; margin: 0; color: #E6E6E6;">👋 <strong>Welcome Student!</strong><br>Please enter your <strong>Access Key</strong> in the Sidebar to unlock.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # FIXED: Clean Markdown Structure for description to prevent HTML errors
    st.markdown("### 🏆 Why Top Rankers Choose JEEx **PRO**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🧠 Advanced Problem Solving Engine**")
        st.caption("Tuned for Irodov, Cengage, and PathFinder level rigor. It breaks down complex mechanics and calculus problems.")
        st.markdown("**👁️ Vision Intelligence (OCR)**")
        st.caption("Stuck on a handwritten question? Just upload a photo. JEEx reads and solves it instantly.")
    with col2:
        st.markdown("**📄 Full PDF Document Analysis**")
        st.caption("Upload the PDF assignment. JEEx uses its Code Interpreter brain to analyze the entire document and solve multiple questions.")
        st.markdown("**➗ Perfect Math & Chemical Formatting**")
        st.caption("Renders complex integrals and Organic Mechanisms with textbook-quality LaTeX precision.")
    
    st.stop()

# UNLOCKED INTERFACE (CHAT)
with st.sidebar:
    st.success(f"✅ Active")
    if "messages" in st.session_state and len(st.session_state.messages) > 1:
        pdf_bytes = generate_pdf(st.session_state.messages)
        st.download_button(label="📥 Download Session PDF", data=pdf_bytes, file_name="JEEx_Notes.pdf", mime="application/pdf")
    if st.button("End Session"): st.session_state['logout'] = True; st.rerun()

# SETUP OPENAI
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    assistant_id = st.secrets["ASSISTANT_ID"]
    client = OpenAI(api_key=api_key)
except:
    st.error("🚨 Keys missing in Secrets."); st.stop()

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = [{"role": "assistant", "content": "Welcome Champ! 🎓 Physics, Chemistry ya Maths—bas photo bhejo ya type karo. Let's crack it! 🚀"}]

# DISPLAY HISTORY
for msg in st.session_state.messages:
    avatar_icon = LOGO_URL if msg["role"] == "assistant" else "🧑‍🎓"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(clean_latex(msg["content"]))

# --- 9. INPUT TOOLBAR & PROCESSING ---

# 1. TOOLBAR: Placed above chat_input
col_tools_1, col_tools_2, col_tools_gap = st.columns([1, 1, 6])

with col_tools_1:
    # VOICE INPUT (Microphone)
    audio_value = st.audio_input("🎙️", key=f"audio_{st.session_state.audio_key}", label_visibility="collapsed")
    
with col_tools_2:
    # ATTACHMENT INPUT
    uploaded_file = st.file_uploader("📎", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")

# 2. CHAT INPUT
text_prompt = st.chat_input("Ask a doubt...")

# 3. LOGIC
audio_prompt = None
if audio_value:
    with st.spinner("Processing Voice..."):
        try:
            # FIXED: Force English to stop foreign language hallucinations
            transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_value, language="en")
            audio_prompt = transcription.text
        except Exception as e: st.error(f"Voice Error: {e}")

prompt = audio_prompt if audio_value else text_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🎓"):
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
                temp_filename = f"temp_{uploaded_file.name}"
                with open(temp_filename, "wb") as f: f.write(uploaded_file.getbuffer())
                file_response = client.files.create(file=open(temp_filename, "rb"), purpose="assistants")
                if uploaded_file.type == "application/pdf":
                    attachments.append({"file_id": file_response.id, "tools": [{"type": "code_interpreter"}]})
                else:
                    message_content.append({"type": "image_file", "image_file": {"file_id": file_response.id}})
                os.remove(temp_filename)
            except: st.error("File upload failed.")

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
                        response_container.markdown(clean_latex(collected_message) + "▌")
            elif event.event == "thread.run.completed": break

        response_container.markdown(clean_latex(collected_message))
        st.session_state.messages.append({"role": "assistant", "content": collected_message})
        
        # FIXED: Reset inputs properly to prevent loops
        st.session_state.uploader_key += 1
        if audio_value: 
            st.session_state.audio_key += 1 
            time.sleep(0.5) 
            st.rerun()
            
