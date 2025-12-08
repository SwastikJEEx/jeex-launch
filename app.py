import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime, timedelta
from fpdf import FPDF
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="centered", initial_sidebar_state="expanded")

# --- 2. PROFESSIONAL INTERFACE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161B26; border-right: 1px solid #2B313E; }
    .block-container { padding-top: 2rem; }
    
    /* Chat Bubbles */
    [data-testid="stChatMessage"] { background-color: transparent; border: none; padding: 10px 0px; }
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #1E2330; border-radius: 12px; padding: 15px 20px; margin-bottom: 10px; border: 1px solid #2B313E;
    }
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: transparent; padding: 0px 20px; margin-bottom: 10px;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] div {
        font-size: 16px !important; line-height: 1.6 !important; color: #E6E6E6 !important;
    }
    
    /* Highlights & Inputs */
    strong { color: #FFD700 !important; } 
    code { color: #FF7043 !important; }
    .stTextInput input, .stTextArea textarea { background-color: #1E2330 !important; color: white !important; border: 1px solid #3E4654 !important; border-radius: 10px; }
    
    /* Buttons */
    div.stButton > button { 
        background-color: #2B313E !important; color: white !important; border: 1px solid #3E4654 !important; border-radius: 8px; width: 100%; transition: all 0.3s; font-weight: 600;
    }
    div.stButton > button:hover { border-color: #4A90E2 !important; color: #4A90E2 !important; }
    
    /* Branding */
    .branding-text { text-align: center; margin-top: -10px; margin-bottom: 30px; }
    .branding-header { margin: 0; font-size: 36px; font-weight: 700; letter-spacing: 1px; color: #E6E6E6; }
    .branding-sub { color: #AAAAAA; font-size: 14px; margin-top: 8px; }
    
    /* Hide Defaults */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
    .katex { font-size: 1.2em; color: #FFD700 !important; } 
    [data-testid="stFileUploader"] { padding: 0px; }
    .stChatMessage .st-emotion-cache-1p1m4ay { width: 42px; height: 42px; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def clean_latex(text):
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    return text

LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

def show_branding():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try: st.image(LOGO_URL, use_container_width=True)
        except: pass
    st.markdown(f"""
        <div class="branding-text">
            <h1 class="branding-header">JEEx <span style="color:#4A90E2;">PRO</span></h1>
            <p class="branding-sub">Your 24/7 AI Rank Booster | Master JEE Mains & Advanced 🚀</p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. PDF GENERATOR (PROFESSIONAL NOTES) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'JEEx Pro - Study Session Notes', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(74, 144, 226) # JEEx Blue
        self.cell(0, 10, label, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 7, body)
        self.ln()

def generate_pdf(messages):
    pdf = PDF()
    pdf.add_page()
    for msg in messages:
        role = "JEEx AI Tutor" if msg["role"] == "assistant" else "Student"
        content = clean_latex(msg["content"]).replace('*', '').replace('#', '') # Basic markdown cleanup
        pdf.chapter_title(role)
        pdf.chapter_body(content)
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 5. SMART KEY LOGIC (STRICT MODE) ---
def check_key_status(user_key):
    # ADMIN
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"): return "ADMIN"

    # STRICT EXPIRY CHECK
    # Logic: Only keys present in [KEY_EXPIRY] are valid. Everything else is invalid.
    expiry_db = st.secrets.get("KEY_EXPIRY", {})
    
    if user_key in expiry_db:
        try:
            expiry_date = datetime.strptime(expiry_db[user_key], "%Y-%m-%d").date()
            if datetime.now().date() > expiry_date:
                return "EXPIRED"
            else:
                return "VALID"
        except:
            return "INVALID" # Date format error = Invalid
    
    # If key is NOT in secrets, it's strictly INVALID (Locked by default)
    return "INVALID"

# --- 6. LOGOUT ---
if st.session_state.get('logout', False):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- 7. TERMS TEXT ---
terms_text = """
**JEEx Terms of Service**
**1. Service:** AI educational assistant for JEE.
**2. Accuracy:** Verify critical data with NCERT.
**3. Security:** Single User License. Sharing = Ban.
**4. Refunds:** No Refunds. Sales are final.
"""

# --- 8. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
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
        with st.expander("📄 Terms & Conditions"): st.markdown(terms_text)

# --- 9. ADMIN PANEL ---
if status == "ADMIN":
    st.sidebar.success("🔑 Admin Mode")
    st.markdown("## 🛠️ Admin Dashboard")
    st.info("Generate code to PASTE into `secrets.toml` to activate a student.")
    c1, c2 = st.columns(2)
    with c1: new_id = st.text_input("Student Key (e.g. JEExa005)")
    with c2: days = st.number_input("Days", 30)
    if new_id:
        exp = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        st.code(f'"{new_id}" = "{exp}"', language="toml")
    if st.button("Logout"): st.session_state['logout'] = True; st.rerun()
    st.stop()

# --- 10. MAIN APP ---
show_branding()

# LANDING PAGE
if status != "VALID":
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #1E2330; padding: 25px; border-radius: 12px; border-left: 5px solid #4A90E2; margin-bottom: 30px; text-align: center;">
        <p style="font-size: 18px; margin: 0; color: #E6E6E6;">👋 <strong>Welcome Student!</strong><br>Please enter your <strong>Access Key</strong> in the Sidebar to unlock.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #161B26; padding: 35px; border-radius: 15px; border: 1px solid #2B313E;">
        <h2 style="color: #4A90E2; margin-top: 0; text-align: center;">🏆 Why Top Rankers Choose JEEx <span style="color:#4A90E2">PRO</span></h2>
        <div style="display: flex; flex-direction: column; gap: 20px;">
            <div><strong style="color: #FFD700; font-size: 19px;">🧠 Advanced Solving</strong><br><span style="color: #CCCCCC;">Solves Irodov & Cengage level problems.</span></div>
            <div><strong style="color: #FFD700; font-size: 19px;">👁️ Vision Intelligence</strong><br><span style="color: #CCCCCC;">Upload handwritten questions instantly.</span></div>
            <div><strong style="color: #FFD700; font-size: 19px;">➗ Perfect Math</strong><br><span style="color: #CCCCCC;">LaTeX precision for Integrals & Matrices.</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# UNLOCKED INTERFACE
with st.sidebar:
    st.success(f"✅ Active")
    st.markdown("---")
    st.markdown("### 📎 Attach Question")
    uploaded_file = st.file_uploader("Upload Image/PDF", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
    if uploaded_file: st.info(f"Attached: {uploaded_file.name}")
    
    # PDF DOWNLOAD BUTTON
    if "messages" in st.session_state and len(st.session_state.messages) > 1:
        st.markdown("---")
        pdf_bytes = generate_pdf(st.session_state.messages)
        st.download_button(label="📥 Download Notes (PDF)", data=pdf_bytes, file_name="JEEx_Notes.pdf", mime="application/pdf")

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
    welcome_msg = "Welcome Champ! 🎓 Main hoon JEEx. \n\nPhysics, Chemistry ya Maths—bas photo bhejo ya type karo. Let's crack it! 🚀"
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]

# DISPLAY HISTORY
for msg in st.session_state.messages:
    avatar_icon = LOGO_URL if msg["role"] == "assistant" else "🧑‍🎓"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(clean_latex(msg["content"]))

# --- VOICE & TEXT INPUT AREA ---
col_mic, col_input = st.columns([1, 8])

audio_prompt = None
with col_mic:
    # VOICE INPUT (Using Native Streamlit Audio Input)
    audio_value = st.audio_input("🎙️", label_visibility="collapsed")

# Handle Audio Transcription
if audio_value:
    with st.spinner("Listening..."):
        try:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_value
            )
            audio_prompt = transcription.text
        except Exception as e:
            st.error(f"Voice Error: {e}")

# Text Input
text_prompt = st.chat_input("Ask a doubt...")

# Determine Final Prompt (Voice takes priority if present)
prompt = audio_prompt if audio_value else text_prompt

# HANDLE MESSAGE
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
        if uploaded_file:
            if uploaded_file.type == "application/pdf": st.markdown(f"📄 *PDF Attached*")
            else: st.image(uploaded_file, width=200)

    # Process Message
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
        st.session_state.uploader_key += 1
        # If using voice, rerun to clear the audio input widget for next turn
        if audio_value: time.sleep(1); st.rerun()
