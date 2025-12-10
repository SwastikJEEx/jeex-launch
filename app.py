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

# --- 4. PROFESSIONAL CSS (VISIBILITY FIXED / DROPDOWNS & SIDEBAR BLOCKS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* 1. FORCE DARK BACKGROUNDS (app + sidebar) */
    .stApp { background-color: #0E1117 !important; color: #E0E0E0 !important; }
    [data-testid="stSidebar"] { background-color: #161B26 !important; border-right: 1px solid #2B313E !important; }

    /* 2. GLOBAL TEXT COLOR FORCE */
    h1, h2, h3, h4, h5, h6, p, li, div, span, label, a, small, strong, code {
        color: #E0E0E0 !important;
    }
    strong { color: #FFD700 !important; font-weight: 600; }
    code { color: #FF7043 !important; background-color: #1E2330 !important; padding: 2px 4px; border-radius: 4px; }

    /* 3. INPUT FIELDS & DROPDOWNS */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
        background-color: #1E2330 !important;
        border: 1px solid #4A90E2 !important;
        border-radius: 8px !important;
    }
    input[type="text"], input[type="password"], textarea, div[data-baseweb="select"] div {
        color: #FFFFFF !important;
        background-color: transparent !important;
        caret-color: #4A90E2 !important;
    }
    ::placeholder { color: #AAAAAA !important; opacity: 1; }

    /* 4. BUTTONS (force consistent appearance across dark & light) */
    button, input[type="submit"], input[type="button"], .stButton>button, .stDownloadButton, .st-bk {
        background-color: #4A90E2 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s !important;
        box-shadow: none !important;
    }
    button:hover, input[type="submit"]:hover, input[type="button"]:hover, .stButton>button:hover, .stDownloadButton:hover {
        background-color: #357ABD !important;
        box-shadow: 0px 4px 15px rgba(74, 144, 226, 0.4) !important;
        color: #FFFFFF !important;
    }

    /* 5. SPECIFIC DOWNLOAD / STREAMLIT VARIANTS */
    button[title="Download"], button[aria-label="Download"], .stDownloadButton button, .st-download-button button {
        background-color: #4A90E2 !important;
        color: #FFFFFF !important;
    }

    /* 6. CUSTOM PAY BUTTONS (HTML anchors) */
    .pay-btn-link {
        display: block;
        width: 100%;
        background-color: #4A90E2;
        color: white !important;
        text-align: center;
        padding: 12px;
        margin-bottom: 12px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        border: 1px solid #4A90E2;
        transition: all 0.3s ease;
    }
    .pay-btn-link:hover {
        background-color: #357ABD;
        box-shadow: 0px 4px 15px rgba(74, 144, 226, 0.4);
        border-color: #357ABD;
    }
    .slashed { text-decoration: line-through; opacity: 0.7; margin-right: 5px; font-size: 0.9em; }

    /* 7. EXPANDERS & CONTENT AREAS */
    .streamlit-expanderHeader { background-color: #2B313E !important; color: #FFFFFF !important; border: 1px solid #4A90E2 !important; border-radius: 8px; }
    .streamlit-expanderContent { background-color: #161B26 !important; border: 1px solid #2B313E !important; color: #E0E0E0 !important; }

    /* 8. KAteX / math block styling */
    .katex-display { overflow-x: auto; overflow-y: hidden; padding-bottom: 5px; color: #FFD700 !important; }

    /* 9. FILE UPLOADER + ATTACHMENT BLOCK (force readable background & controls) */
    [data-testid="stFileUploader"], .stFileUploader, .stFileUploader * {
        background-color: #14181C !important;
        color: #E0E0E0 !important;
        border: 1px solid #2B313E !important;
        border-radius: 8px !important;
    }
    [data-testid="stFileUploader"] .css-1f0tk5o, [data-testid="stFileUploader"] .css-1v0mbdj {
        color: #E0E0E0 !important;
    }
    /* placeholder text inside uploader */
    [data-testid="stFileUploader"] input::placeholder { color: #AAAAAA !important; opacity: 1 !important; }

    /* 10. VOICE / AUDIO INPUT BLOCK (fix error message readability + background) */
    .stAudioInput, .stAudioInput *, .st-audio-player, audio, .stAudioInput .css-1offfwp {
        background-color: #14181C !important;
        color: #E0E0E0 !important;
        border: 1px solid #2B313E !important;
        border-radius: 8px !important;
    }
    /* messages / status text that appear inside audio widget (errors, transcribe status) */
    .stAudioInput [role="status"], .stAudioInput .stText, .stAudioInput .stMarkdown, .stAudioInput .css-1bga2a5 {
        color: #E0E0E0 !important;
        background: transparent !important;
    }

    /* 11. FORCE DROPDOWN / SELECT MENU VISIBILITY (covers baseweb popovers & listboxes) */
    ul[data-baseweb="menu"], div[role="listbox"], .baseweb-popover, .baseweb-menu, .rc-virtual-list {
        background-color: #161B26 !important;
        color: #E0E0E0 !important;
        border: 1px solid #2B313E !important;
    }
    li[data-baseweb="option"], ul[data-baseweb="menu"] li, .baseweb-menu li, .rc-virtual-list .list-item {
        color: #E0E0E0 !important;
        background-color: transparent !important;
    }
    .baseweb-popover * { color: #E0E0E0 !important; }

    /* 12. SELECT / DROPDOWN LABELS & HEADINGS inside open menu */
    .css-1r6slb0, .css-1d391kg, .stSelectbox, div[role="option"], div[role="menuitem"] {
        color: #E0E0E0 !important;
    }

    /* 13. SIDEBAR LABELS (Attach Question / Voice Chat headings) */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: #FFD700 !important;
    }
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] p, [data-testid="stSidebar"] small {
        color: #E0E0E0 !important;
    }

    /* 14. CHAT INPUT bar (keep visible on white theme) */
    .stChatInput, .stChatInput * {
        background-color: transparent !important;
        color: #E0E0E0 !important;
    }

    /* 15. make sure icons/buttons inside sidebar remain visible */
    [data-testid="stSidebar"] button, [data-testid="stSidebar"] a, [data-testid="stSidebar"] .stButton>button {
        background-color: #4A90E2 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }

    /* 16. reduce unnatural white borders added by some host themes */
    .css-1v3fvcr, .css-1y8i9bb {
        border: none !important;
        box-shadow: none !important;
    }

    /* 17. small spacing tweaks */
    .block-container { padding-top: 1rem; padding-bottom: 140px; }
    [data-testid="stFileUploader"] { padding: 8px !important; }
    .stAudioInput { margin-top: 5px; padding: 6px !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---

def send_lead_notification(name, email, phone):
    """Sends Lead Generation email to Admin immediately using Requests"""
    # URL for FormSubmit
    url = f"https://formsubmit.co/{ADMIN_EMAIL}"
    
    # Data Payload
    payload = {
        "_subject": f"🔥 NEW JEEx LEAD: {name}",
        "_captcha": "false",  # Disable captcha
        "_template": "table", # Clean table format
        "Name": name,
        "Email": email,
        "Phone": phone,
        "Status": "Details Submitted - Viewing Payment Plans",
        "Timestamp": str(datetime.now())
    }
    
    try:
        # We use a standard POST request
        response = requests.post(url, data=payload)
        # Check if the request was successful (Status Code 200)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        return False

def clean_latex_for_chat(text):
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    return text

def translate_latex_for_pdf(text):
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    text = re.sub(r'\\frac{(.*?)}{(.*?)}', r'(\1 / \2)', text)
    text = re.sub(r'\\int_\{(.*?)\}\^\{(.*?)\}', r'int_\1^\2', text)
    text = text.replace(r'\int', 'int')
    text = text.replace(r'\left[', '[').replace(r'\right]', ']')
    text = text.replace(r'\left(', '(').replace(r'\right)', ')')
    text = text.replace(r'\{', '{').replace(r'\}', '}')
    commands = [r'\cdot', r'\times', r'\sqrt', r'\approx', r'\le', r'\ge', r'\infty', r'\pi', r'\theta', r'\sin', r'\cos', r'\tan']
    for cmd in commands:
        text = text.replace(cmd, cmd.replace('\\', ''))
    text = text.replace('$$', '').replace('$', '').replace('\\', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text.encode('latin-1', 'replace').decode('latin-1')

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
        self.cell(0, 10, translate_latex_for_pdf(label), 0, 1, 'L')
        self.ln(2)
    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 7, translate_latex_for_pdf(body))
        self.ln()

def generate_pdf(messages):
    pdf = PDF()
    pdf.add_page()
    for msg in messages:
        role = "JEEx" if msg["role"] == "assistant" else "Student"
        pdf.chapter_title(role)
        pdf.chapter_body(msg["content"])
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 6. AUTH & LOGIC (UPDATED FOR JEExa0001-9999) ---
def check_key_status(user_key):
    # 1. Admin Master Key
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"): 
        return "ADMIN"
    
    # 2. Check Key Format (JEExa0001 to JEExa9999)
    if not re.match(r"^JEExa\d{4}$", user_key):
        return "INVALID"

    # 3. Check Secrets.toml for Activation & Expiry
    expiry_db = st.secrets.get("KEY_EXPIRY", {})
    
    if user_key in expiry_db:
        try:
            exp_str = expiry_db[user_key]
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            if datetime.now().date() <= exp_date:
                return "VALID"
            else:
                return "EXPIRED"
        except:
            return "INVALID"
    
    return "INVALID"

if st.session_state.get('logout', False):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- 7. SIDEBAR (NEW PAYMENT FLOW) ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    
    # Password Input (FIXED: REMOVED EXAMPLE TEXT)
    user_key = st.text_input("Enter Access Key:", type="password", placeholder="Enter key here...") 
    status = check_key_status(user_key)
    
    # --- UNLOCKED TOOLS ---
    if status == "VALID" or status == "ADMIN":
        st.success(f"✅ Active")
        st.markdown("---")
        
        st.markdown("**📎 Attach Question**")
        uploaded_file = st.file_uploader("Upload", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
        
        st.markdown("**🎙️ Voice Chat**")
        audio_value = st.audio_input("Speak", key=f"audio_{st.session_state.audio_key}", label_visibility="collapsed")
        
        st.markdown("---")
        if len(st.session_state.messages) > 1:
            pdf_bytes = generate_pdf(st.session_state.messages)
            st.download_button("📥 Download Notes", data=pdf_bytes, file_name="JEEx_Notes.pdf", mime="application/pdf")
        
        if st.button("End Session"): st.session_state['logout'] = True; st.rerun()

    # --- LOCKED (NEW PAYMENT WORKFLOW) ---
    else:
        if user_key and status == "EXPIRED": st.error("❌ Key Expired")
        elif user_key and status == "INVALID": st.error("❌ Invalid or Inactive Key")
        
        st.markdown("### ⚡ Subscribe Now")
        with st.expander("💎 Get Premium Plans", expanded=True):
            
            # STEP 1: CAPTURE DETAILS
            if st.session_state.payment_step == 1:
                st.markdown("Fill details to unlock plan options:")
                with st.form("reg_form"):
                    name = st.text_input("Name")
                    email = st.text_input("Email")
                    phone = st.text_input("WhatsApp No.")
                    sub = st.form_submit_button("🚀 Submit Details")
                
                if sub:
                    if name and email and phone:
                        st.session_state.user_details = {"name": name, "email": email, "phone": phone}
                        
                        # --- EMAIL SENDING ---
                        with st.spinner("Submitting details..."):
                            success = send_lead_notification(name, email, phone)
                        
                        if success:
                            st.toast("✅ Details Sent! Choose a plan below.")
                        else:
                            st.toast("⚠️ Connection issue, but you can still proceed.")
                        
                        st.session_state.payment_step = 2
                        st.rerun()
                    else: st.warning("⚠️ Fill all details.")

            # STEP 2: SHOW PLAN BUTTONS
            elif st.session_state.payment_step == 2:
                st.info(f"Hi {st.session_state.user_details['name']}, choose your rank booster:")
                
                # PLAN 1: Weekly
                st.markdown("""
                <a href="https://superprofile.bio/vp/BfdrAn72" target="_blank" class="pay-btn-link">
                    Buy Weekly Plan &nbsp; <span class="slashed">₹49</span> ₹29
                </a>
                """, unsafe_allow_html=True)

                # PLAN 2: Monthly
                st.markdown("""
                <a href="https://superprofile.bio/vp/JEExPRO" target="_blank" class="pay-btn-link">
                    Buy Monthly Plan &nbsp; <span class="slashed">₹99</span> ₹59
                </a>
                """, unsafe_allow_html=True)

                # PLAN 3: 3 Months
                st.markdown("""
                <a href="https://superprofile.bio/vp/1sXJLqv3" target="_blank" class="pay-btn-link">
                    Buy 3 Month Plan &nbsp; <span class="slashed">₹199</span> ₹159
                </a>
                """, unsafe_allow_html=True)

                # PLAN 4: 6 Months
                st.markdown("""
                <a href="https://superprofile.bio/vp/EbjbO_0N" target="_blank" class="pay-btn-link">
                    Buy 6 Month Plan &nbsp; <span class="slashed">₹349</span> ₹279
                </a>
                """, unsafe_allow_html=True)
                
                st.caption("ℹ️ *After payment, you will receive your valid JEExa Key via Email/WhatsApp.*")

                if st.button("Back"):
                    st.session_state.payment_step = 1
                    st.rerun()

        st.markdown("---")
        with st.expander("📄 Detailed Terms & Conditions"): 
            st.markdown("""
            **1. Service Scope:** JEEx Pro is an AI-powered educational aid for JEE preparation.
            **2. Account Usage:** Single User. Keys are strictly personal.
            **3. Payment Policy:** No Refunds once the key is issued.
            **4. Key Activation:** Keys are activated manually after payment verification.
            """)

# --- 8. ADMIN PANEL ---
if status == "ADMIN":
    st.sidebar.success("🔑 Admin Mode")
    c1, c2 = st.columns(2)
    with c1: new_id = st.text_input("Key ID (e.g. JEExa0001)")
    with c2: days = st.number_input("Days", 30)
    if new_id:
        exp = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        st.code(f'"{new_id}" = "{exp}"', language="toml")
    st.stop()

# --- 9. LANDING PAGE ---
show_branding()

if status != "VALID":
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #1E2330; padding: 20px; border-radius: 12px; border-left: 5px solid #4A90E2; text-align: center; margin-bottom: 30px;">
        <p style="font-size: 18px; margin: 0; color: #E6E6E6;">👋 <strong>Welcome Student!</strong><br>Please enter your <strong>Access Key</strong> in the Sidebar to unlock.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🏆 Why Top Rankers Choose JEEx **PRO**")
    c1, c2 = st.columns(2)
    with c1:
        st.info("**🧠 Advanced Problem Solving**\n\nSolves Irodov, Cengage, and PYQ level problems with step-by-step logic.")
        st.info("**📄 Full Document Brain**\n\nUpload entire PDF assignments. Our Code Interpreter analyzes context.")
        st.info("**🎯 Concept-First Approach**\n\nWe don't just solve; we explain the 'Why'. Learn the derivation.")
    with c2:
        st.info("**👁️ Vision Intelligence (OCR)**\n\nReads handwritten questions from photos instantly.")
        st.info("**➗ Perfect Math Formatting**\n\nTextbook-quality rendering for Integrals and Organic Mechanisms.")
        st.info("**⚡ 24/7 Strategic Mentorship**\n\nYour personal AI coach for study planning and backlog management.")
    
    st.stop()

# --- 10. CHAT INTERFACE ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    assistant_id = st.secrets["ASSISTANT_ID"]
except: st.error("🚨 Keys missing."); st.stop()

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# INPUT LOGIC
audio_prompt = None
if 'audio_value' in locals() and audio_value:
    if not st.session_state.processing:
        with st.spinner("🎧 Listening..."):
            try:
                transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_value, language="en")
                audio_prompt = transcription.text
            except: pass

text_prompt = st.chat_input("Ask a doubt...", disabled=st.session_state.processing)
prompt = audio_prompt if audio_prompt else text_prompt

if prompt:
    st.session_state.processing = True
    msg_data = {"role": "user", "content": prompt}
    if uploaded_file:
        msg_data.update({"file_data": uploaded_file.getvalue(), "file_name": uploaded_file.name, "file_type": uploaded_file.type})
    st.session_state.messages.append(msg_data)
    st.rerun()

# DISPLAY
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=LOGO_URL if msg["role"]=="assistant" else "🧑‍🎓"):
        if "file_data" in msg:
            if msg["file_type"].startswith("image"): st.image(msg["file_data"], width=200)
            else: st.markdown(f"📄 *{msg['file_name']}*")
        st.markdown(clean_latex_for_chat(msg["content"]))

# PROCESS RESPONSE
if st.session_state.processing and st.session_state.messages[-1]["role"] == "user":
    msg_text = st.session_state.messages[-1]["content"]
    api_content = [{"type": "text", "text": msg_text}]
    att = []
    
    if uploaded_file:
        try:
            tfile = f"temp_{uploaded_file.name}"
            with open(tfile, "wb") as f: f.write(uploaded_file.getbuffer())
            fres = client.files.create(file=open(tfile, "rb"), purpose="assistants")
            
            if uploaded_file.type == "application/pdf":
                att.append({"file_id": fres.id, "tools": [{"type": "code_interpreter"}]})
            else:
                api_content.append({"type": "image_file", "image_file": {"file_id": fres.id}})
            
            os.remove(tfile)
        except: st.error("Upload failed.")

    client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=api_content, attachments=att if att else None)

    with st.chat_message("assistant", avatar=LOGO_URL):
        stream = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id, assistant_id=assistant_id, stream=True,
            additional_instructions="You are JEEx. Use $$...$$ for block math and $...$ for inline. Strictly LaTeX."
        )
        resp = st.empty()
        full_text = ""
        for event in stream:
            if event.event == "thread.message.delta":
                for c in event.data.delta.content:
                    if c.type == "text":
                        full_text += c.text.value
                        resp.markdown(clean_latex_for_chat(full_text) + "▌")
            elif event.event == "thread.run.completed": break
        
        resp.markdown(clean_latex_for_chat(full_text))
        st.session_state.messages.append({"role": "assistant", "content": full_text})

    st.session_state.uploader_key += 1
    if 'audio_value' in locals() and audio_value: st.session_state.audio_key += 1
    st.session_state.processing = False
    st.rerun()
