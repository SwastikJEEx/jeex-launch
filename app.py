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
# New Specifications States
if "target_exam" not in st.session_state: st.session_state.target_exam = "JEE Mains"
if "subject_focus" not in st.session_state: st.session_state.subject_focus = "All Subjects"

# Simple logger
logger = logging.getLogger("jeex")
logger.setLevel(logging.INFO)

# --- 4. PROFESSIONAL CSS (NEON BLUE THEME) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Main Background - Pure Black to merge with Logo */
    .stApp { background-color: #000000 !important; color: #E0E0E0 !important; }
    
    /* Sidebar - Very Dark Blue/Black */
    [data-testid="stSidebar"] { background-color: #050810 !important; border-right: 1px solid #0D1B2E !important; }
    
    /* Header / top bar */
    header, header * { background-color: #000000 !important; color: #E0E0E0 !important; border: none !important; box-shadow: none !important; }
    
    /* Global text */
    h1, h2, h3, h4, h5, h6, p, li, div, span, label, a, small, strong, code {
        color: #E0E0E0 !important;
    }

    /* BIGGER CHAT TEXT FOR READABILITY */
    .stChatMessage p, .stChatMessage li, .stChatMessage div {
        font-size: 1.15rem !important;
        line-height: 1.6 !important;
    }
    
    /* NEON BLUE ACCENTS */
    strong { color: #00A6FF !important; font-weight: 600; }
    code { color: #00A6FF !important; background-color: #0D1B2E !important; padding: 2px 4px; border-radius: 4px; }
    
    /* Inputs & selects - FIXED BOX STYLE */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
        background-color: #050810 !important;
        border: 1px solid #00A6FF !important;
        border-radius: 8px !important;
    }
    
    /* FIX: Force white text for SELECTED value in dropdowns so it is visible from outside */
    div[data-baseweb="select"] > div {
        color: #FFFFFF !important;
    }
    
    input[type="text"], input[type="password"], textarea, div[data-baseweb="select"] div {
        color: #FFFFFF !important;
        background-color: transparent !important;
        caret-color: #00A6FF !important;
    }
    ::placeholder { color: #AAAAAA !important; opacity: 1; }
    
    /* Buttons - Neon Blue Theme */
    button, input[type="submit"], input[type="button"], .stButton>button, .stDownloadButton, .st-bk {
        background-color: #00A6FF !important;
        color: #000000 !important; /* Black text for contrast */
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        transition: all 0.3s !important;
        box-shadow: none !important;
    }
    button:hover, input[type="submit"]:hover, input[type="button"]:hover, .stButton>button:hover, .stDownloadButton:hover {
        background-color: #008ECC !important;
        box-shadow: 0px 0px 10px rgba(0, 166, 255, 0.4) !important;
    }
    
    /* Download variants */
    button[title="Download"], button[aria-label="Download"], .stDownloadButton button, .st-download-button button {
        background-color: #00A6FF !important;
        color: #000000 !important;
    }

    /* Expanders */
    .streamlit-expanderHeader { background-color: #0D1B2E !important; color: #FFFFFF !important; border: 1px solid #00A6FF !important; border-radius: 8px; }
    .streamlit-expanderContent { background-color: #050810 !important; border: 1px solid #0D1B2E !important; color: #E0E0E0 !important; }

    /* katex - Neon Blue */
    .katex-display { overflow-x: auto; overflow-y: hidden; padding-bottom: 5px; color: #00A6FF !important; }

    /* File uploader */
    [data-testid="stFileUploader"], .stFileUploader, .stFileUploader * {
        background-color: #050810 !important;
        color: #E0E0E0 !important;
        border: 1px solid #0D1B2E !important;
        border-radius: 8px !important;
    }
    [data-testid="stFileUploader"] input::placeholder { color: #AAAAAA !important; opacity: 1 !important; }
    [data-testid="stFileUploader"] .css-1v0mbdj, [data-testid="stFileUploader"] .css-1f0tk5o { color: #E0E0E0 !important; }
    
    /* Voice / audio widget block */
    .stAudioInput, .stAudioInput *, .st-audio-player, audio {
        background-color: #050810 !important;
        color: #E0E0E0 !important;
        border: 1px solid #0D1B2E !important;
        border-radius: 8px !important;
    }
    .stAudioInput [role="status"], .stAudioInput .stText, .stAudioInput .stMarkdown {
        color: #E0E0E0 !important;
        background: transparent !important;
    }

    /* --- DROPDOWN & LISTBOX VISIBILITY FIX --- */
    div[data-baseweb="popover"], div[data-baseweb="menu"], div[role="listbox"] {
        background-color: #050810 !important;
        color: #E0E0E0 !important;
        border: 1px solid #00A6FF !important;
    }
    li[data-baseweb="option"] {
        color: #E0E0E0 !important;
    }
    div[data-baseweb="popover"] div {
        background-color: #050810 !important;
        color: #E0E0E0 !important;
    }
    li[data-baseweb="option"]:hover, li[data-baseweb="option"][aria-selected="true"] {
        background-color: #0D1B2E !important;
        color: #00A6FF !important;
        font-weight: bold !important;
    }
    .baseweb-popover * { color: #E0E0E0 !important; }
    
    /* Dropdown headings/labels */
    .css-1r6slb0, .css-1d391kg, .stSelectbox, div[role="option"], div[role="menuitem"] {
        color: #E0E0E0 !important;
    }
    
    /* Sidebar headings - Neon Blue */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: #00A6FF !important;
    }
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] p, [data-testid="stSidebar"] small {
        color: #E0E0E0 !important;
    }

    /* --- CHAT INPUT RESTORED TO ORIGINAL CLEAN STYLE --- */
    /* Only force background color to avoid white bars, but remove custom borders to restore default layout */
    .stChatInput, .stChatInputContainer, [data-testid="stChatInput"] {
        background-color: #000000 !important;
    }
    .stChatInput .css-1v3fvcr, .stChatInput .css-1y8i9bb { 
        background-color: #050810 !important; 
        color: #E0E0E0 !important;
        /* No border here for clean look, or subtle one */
        border: 1px solid #333 !important;
    }
    .stChatInput button {
        color: #00A6FF !important; /* Keep the send button blue */
        border: none !important;
        background: transparent !important;
    }
    
    /* Spinner */
    .stSpinner > div > div { border-top-color: #00A6FF !important; }

    /* Misc */
    .block-container { padding-top: 1rem; padding-bottom: 140px; max-width: 1200px; margin: 0 auto; }
    [data-testid="stFileUploader"] { padding: 8px !important; }
    .stAudioInput { margin-top: 5px; padding: 6px !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---

def send_lead_notification(name, email, phone):
    """Sends Lead Generation email via FormSubmit (Reliable, no SMTP errors)"""
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
    except Exception as e:
        logger.error(f"Lead send failed: {e}")
        return True

def cleanup_text_for_pdf(text):
    """Translates LaTeX and special chars to PDF-friendly text"""
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    
    replacements = {
        r'\alpha': 'alpha', r'\beta': 'beta', r'\gamma': 'gamma', r'\theta': 'theta',
        r'\pi': 'pi', r'\infty': 'infinity',
        r'\le': '<=', r'\ge': '>=', r'\neq': '!=', r'\approx': '~=',
        r'\rightarrow': '->', r'\leftarrow': '<-', r'\implies': '=>',
        r'\cdot': '*', r'\times': 'x',
        r'\frac': ' frac ', 
        r'\sqrt': 'sqrt',
        r'\int': 'Integral ', r'\sum': 'Sum ',
        '$$': '\n', '$': '' 
    }
    
    for latex, plain in replacements.items():
        text = text.replace(latex, plain)
        
    text = text.replace('{', '(').replace('}', ')')
    text = text.replace('\\', '')
    
    return text

def clean_latex_for_chat(text):
    """Refined LaTeX cleaning for better display"""
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    # Ensure standard dollar signs for math are preserved/fixed
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = text.replace('\\\\', '\\')
    return text

def show_branding():
    # Adjusted columns for wide layout to keep logo centered
    c1, c2, c3 = st.columns([2, 2, 2])
    with c2:
        try: st.image(LOGO_URL, use_container_width=True) 
        except: pass
    st.markdown("""
        <div style="text-align: center; margin-top: -15px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 52px; font-weight: 700; letter-spacing: 1px;">
                JEEx <span style="color:#00A6FF;">PRO</span>
            </h1>
            <p style="color: #AAAAAA; font-size: 18px; margin-top: 8px;">
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
        self.set_text_color(0, 166, 255) # Neon Blue for PDF
        self.cell(0, 10, str(label), 0, 1, 'L')
        self.ln(2)
    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(50, 50, 50)
        self.clean = cleanup_text_for_pdf(body)
        clean = self.clean.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 7, clean)
        self.ln()

def generate_pdf(messages):
    pdf = PDF()
    pdf.add_page()
    for msg in messages:
        role = "JEEx" if msg["role"] == "assistant" else "Student"
        pdf.chapter_title(role)
        pdf.chapter_body(msg["content"])
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# Handle logout properly
if st.session_state.get('logout', False):
    st.session_state.clear()
    st.rerun()

# --- 6. SIDEBAR LOGIC (FREE REGISTRATION & TOOLS) ---
with st.sidebar:
    # A. IF NOT VERIFIED -> SHOW REGISTRATION FORM
    if not st.session_state.is_verified:
        st.markdown("## 🔓 Get Free Access")
        st.info("Register now to unlock the AI Rank Booster instantly.")
        
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            phone = st.text_input("Phone Number")
            submit_reg = st.form_submit_button("🚀 Start Free Trial")
        
        if submit_reg:
            if name and email and phone:
                with st.spinner("Activating JEEx engine"):
                    send_lead_notification(name, email, phone)
                    st.session_state.user_details = {"name": name, "email": email}
                    st.session_state.is_verified = True
                    st.toast(f"Welcome, {name}! Let's study.", icon="🚀")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("⚠️ Please fill in all details.")
    
    # B. IF VERIFIED -> SHOW TOOLS
    else:
        st.markdown(f"👤 **{st.session_state.user_details.get('name', 'Student')}**")
        st.success("✅ JEEx Pro Active")
        st.markdown("---")
        
        # --- NEW FEATURES: JEEX ULTIMATE & TOOLS ---
        st.markdown("### ⚡ Power Tools")
        
        # 1. SPECIFICATIONS (Target & Subject)
        st.session_state.target_exam = st.selectbox("🎯 Target Exam", ["JEE Mains", "JEE Advanced"], index=0)
        st.session_state.subject_focus = st.selectbox("📚 Subject Focus", ["All Subjects", "Physics", "Chemistry", "Mathematics"], index=0)
        
        st.markdown("---")

        # 2. JEEx Ultimate Toggle
        st.toggle("🔥 JEEx Ultimate", key="ultimate_mode", help="Unlock advanced problem solving and deep conceptual analysis.")
        
        if st.session_state.ultimate_mode:
            st.caption("🚀 Advanced Mode: ON")
        
        # 3. Tools Buttons
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("📚 Formulas", use_container_width=True):
                 st.toast("Formula Sheet Mode: Ask for any chapter!", icon="📐")
                 st.session_state.messages.append({"role": "assistant", "content": "I'm ready! Which chapter's **Formula Sheet** do you need? (e.g., Electrostatics, Thermodynamics)"})
                 st.rerun()
            if st.button("🔍 PYQ Finder", use_container_width=True):
                 st.toast("PYQ Mode Active", icon="🔎")
                 st.session_state.messages.append({"role": "assistant", "content": "Tell me the Chapter or Topic, and I will generate the most important **Previous Year Questions (PYQs)** for you from my internal database. (e.g., 'Rotational Motion 2016')"})
                 st.rerun()

        with col_t2:
            if st.button("📝 Mock Test", use_container_width=True):
                st.toast("Mock Test Initialized...", icon="⏳")
                st.session_state.messages.append({"role": "assistant", "content": "Let's test your prep! 🎯 Topic batao, I'll generate a **Mini Mock Test** with 5 tough questions."})
                st.rerun()
            if st.button("🧠 Mistake Analysis", use_container_width=True):
                st.toast("Analysis Mode On", icon="🧠")
                st.session_state.messages.append({"role": "assistant", "content": "Upload your test paper or tell me your weak topic. I will analyze your mistakes and tell you **exactly where you are losing marks**."})
                st.rerun()
        
        # 4. Deep Research Toggle
        st.toggle("🔬 Deep Research", key="deep_research_mode", help="Enable deep theoretical explanations and first-principles derivations.")
        
        if st.session_state.deep_research_mode:
            st.caption("🧐 Research Mode: ON")

        st.markdown("---")

        # --- SESSION CONTROLS ---
        if st.button("✨ New Session", use_container_width=True):
            st.session_state.messages = [{"role": "assistant", "content": "Fresh start! 🌟 What topic shall we tackle now?"}]
            if "thread_id" in st.session_state:
                del st.session_state.thread_id
            st.toast("Chat history cleared!", icon="🧹")
            st.rerun()
        
        st.markdown("**📎 Attach Question**")
        
        # File Uploader Logic
        if st.session_state.processing:
            if st.session_state.current_uploaded_file:
                st.markdown("**Attachment (locked):**")
                st.markdown(f"📄 *{getattr(st.session_state.current_uploaded_file, 'name', 'file')}*")
            else:
                st.markdown("_Locked while answering._")
        else:
            uploaded_file = st.file_uploader("Upload", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
            if uploaded_file:
                st.session_state.current_uploaded_file = uploaded_file
            
            if st.session_state.current_uploaded_file:
                if st.button("Remove attachment"):
                    st.session_state.current_uploaded_file = None
                    st.session_state.uploader_key += 1
                    st.rerun()
        
        st.markdown("**🎙️ Voice Chat**")
        audio_value = st.audio_input("Speak", key=f"audio_{st.session_state.audio_key}", label_visibility="collapsed")
        st.markdown("---")
        
        if len(st.session_state.messages) > 1:
            pdf_bytes = generate_pdf(st.session_state.messages)
            st.download_button("📥 Download Notes", data=pdf_bytes, file_name="JEEx_Notes.pdf", mime="application/pdf", use_container_width=True)
        
        if st.button("Logout", use_container_width=True): 
            st.session_state['logout'] = True
            st.rerun()

    # --- CONTACT US DROPDOWN ---
    st.markdown("---")
    with st.expander("📞 Contact Us"):
        st.write("**Email:** jeexaipro@gmail.com")
        st.write("**WhatsApp:** +91 9839940400")
    
    # --- TERMS & CONDITIONS DROPDOWN (NEW) ---
    with st.expander("📄 Terms & Conditions"):
        st.markdown("""
        **1. Acceptance of Terms**
        By using JEEx Pro, you agree to these terms. This tool is an AI-powered educational aid designed to assist with JEE preparation.

        **2. AI Limitations**
        While we strive for high accuracy, JEEx is an AI system and may occasionally provide incorrect or incomplete information. Users should verify critical calculations and concepts with standard textbooks.

        **3. User Conduct**
        - You agree to use this service for personal educational purposes only.
        - Do not upload content that violates copyright or is illegal.
        - Do not share your account details with others.

        **4. Privacy & Data**
        - Questions and uploaded files are processed by third-party AI providers (OpenAI) to generate answers.
        - We do not sell your personal data.
        - We may contact you regarding product updates.

        **5. Limitation of Liability**
        JEEx Pro is not responsible for any exam results or academic outcomes. Success depends on your own study efforts and exam performance.

        **6. Updates**
        We reserve the right to modify these terms at any time. Continued use of the service constitutes acceptance of modified terms.
        """, unsafe_allow_html=True)

# --- 7. MAIN INTERFACE ---
show_branding()

# If not verified, show landing teaser and stop
if not st.session_state.is_verified:
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #050810; padding: 25px; border-radius: 12px; border-left: 5px solid #00A6FF; text-align: center; margin-bottom: 30px;">
        <h3 style="color: #FFFFFF; margin:0;">👋 Welcome to JEEx PRO</h3>
        <p style="color: #AAAAAA; margin-top: 10px;">
            The ultimate AI tool for JEE Mains & Advanced.<br>
            <strong>Use the Sidebar on the left to Register for FREE access!</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- UPDATED DESCRIPTION (6 POINTS) ---
    c1, c2 = st.columns(2)
    with c1:
        st.info("**🧠 Advanced Problem Solving**\n\nSolves Irodov & Cengage level problems with step-by-step logic.")
        st.info("**📄 Full Document Brain**\n\nUpload entire PDF assignments. Our Code Interpreter analyzes context.")
        st.info("**🎯 Concept-First Approach**\n\nWe don't just solve; we explain the 'Why'. Learn the derivation.")
    with c2:
        st.info("**👁️ Vision Intelligence**\n\nReads handwritten questions from photos instantly.")
        st.info("**➗ Perfect Math Formatting**\n\nTextbook-quality LaTeX rendering for Integrals and Organic Mechanisms.")
        st.info("**⚡ 24/7 Strategic Mentorship**\n\nYour personal AI coach for study planning and backlog management.")
    st.stop()

# --- 8. CHAT LOGIC ---
try:
    # Ensure you have .streamlit/secrets.toml set up!
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    assistant_id = st.secrets["ASSISTANT_ID"]
except Exception as e:
    st.error("🚨 System Error: OpenAI Keys missing in secrets.")
    st.stop()

if "thread_id" not in st.session_state:
    try:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    except:
        st.error("Connection error. Please refresh.")
        st.stop()

# Handle Audio Input
audio_prompt = None
if 'audio_value' in locals() and audio_value and not st.session_state.processing:
    with st.spinner("🎧 Listening..."):
        try:
            transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_value, language="en")
            audio_prompt = transcription.text
        except:
            pass

# Handle Text Input
text_prompt = st.chat_input("Ask a doubt...", disabled=st.session_state.processing)
prompt = audio_prompt if audio_prompt else text_prompt

if prompt:
    st.session_state.processing = True
    msg_data = {"role": "user", "content": prompt}
    
    if st.session_state.current_uploaded_file:
        uf = st.session_state.current_uploaded_file
        msg_data.update({"file_data": uf.getvalue(), "file_name": getattr(uf, "name", "file"), "file_type": getattr(uf, "type", "")})
            
    st.session_state.messages.append(msg_data)
    st.rerun()

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=LOGO_URL if msg["role"]=="assistant" else "🧑‍🎓"):
        if "file_data" in msg:
            if str(msg["file_type"]).startswith("image"): st.image(msg["file_data"], width=200)
            else: st.markdown(f"📄 *{msg.get('file_name')}*")
        st.markdown(clean_latex_for_chat(msg["content"]))

# Generate Response
if st.session_state.processing and st.session_state.messages[-1]["role"] == "user":
    msg_text = st.session_state.messages[-1]["content"]
    api_content = [{"type": "text", "text": msg_text}]
    att = []
    
    # Handle File Attachment for OpenAI
    uploaded_file_obj = st.session_state.current_uploaded_file
    if uploaded_file_obj:
        try:
            tfile = f"temp_{getattr(uploaded_file_obj, 'name', 'file')}"
            with open(tfile, "wb") as f: f.write(uploaded_file_obj.getbuffer())
            fres = client.files.create(file=open(tfile, "rb"), purpose="assistants")
            
            if uploaded_file_obj.type == "application/pdf":
                att.append({"file_id": fres.id, "tools": [{"type": "code_interpreter"}]})
            else:
                api_content.append({"type": "image_file", "image_file": {"file_id": fres.id}})
            
            try: os.remove(tfile)
            except: pass
        except:
            pass 
    
    try:
        client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=api_content, attachments=att if att else None)
        
        # --- ENHANCED BOT INSTRUCTIONS ---
        base_instructions = """
        You are JEEx, an expert JEE (Joint Entrance Examination) tutor and Rank Booster.
        
        ERROR_HANDLING_AND_SCOPE:
        1. **STRICT DOMAIN BOUNDARY**: Your knowledge is strictly limited to Physics, Chemistry, and Mathematics relevant to JEE Mains and Advanced.
        2. **IRRELEVANT TOPICS**: If the user asks about topics NOT related to JEE (e.g., general coding, politics, movies, cooking, dating, sports, general news):
            - **Action**: Provide a VERY BRIEF (maximum 1 sentence) factual definition of the topic to be polite.
            - **Pivot**: Immediately state that this is outside the scope of JEE preparation.
            - **Redirect**: Ask a relevant question to bring them back.
            - **Example**: User: "Who won the cricket match?" -> Bot: "India won the match. However, to win at JEE, we need to focus on your syllabus. Let's solve a Rotational Mechanics problem instead?"
        3. **MISSING FILES**: If the user asks you to "search the file", "read the document", or "analyze the image" BUT no file is attached to the current message:
           - **Action**: Do NOT try to use the code interpreter or retrieval tool to open a file.
           - **Response**: State clearly: "I don't see any file attached. Please upload it first so I can analyze it."
        
        CORE CAPABILITIES:
        1. **Deep JEE Knowledge Base**: Simulate an internet search by cross-referencing your internal database of JEE Advanced/Mains archives, NCERT nuances, and recent exam trends.
        2. **Search Engine Behavior**: When asked about specific data (e.g., "Cutoff for IIT Bombay"), use your internal knowledge to provide the most recent accurate estimates.
        
        MANDATORY RULES:
        1. **PYQ RETRIEVAL**: You possess extensive knowledge of past JEE exams (Mains & Advanced) up to 2023.
           - **CRITICAL:** If the user asks for "PYQs" or "Questions from [Year]", DO NOT refuse. You have this data in your training.
           - **Action:** Recall the specific question from your internal memory and display it. Even if you cannot "browse", you know the questions.
           - **Format:** "Here is a question from JEE Advanced [Year] on [Topic]: ... [Question] ..."
        2. **FORMATTING**: You MUST use LaTeX for ALL mathematical symbols, equations, and chemistry formulas.
            - Use $...$ for inline math (e.g. $x^2$).
            - Use $$...$$ for block math equations.
        3. **ACCURACY & VERIFICATION**:
            - **Think before you answer.**
            - For ANY complex calculation, organic reaction mechanism, or physics derivation, you MUST use the **Code Interpreter (Python Tool)** to verify your logic and numbers before presenting the final answer.
            - Never guess on numeric answers. Calculate them.
        4. **TEACHING STYLE**: Explain the 'Why', not just the 'How'.
        """

        # JEEx ULTIMATE INJECTION
        if st.session_state.ultimate_mode:
            base_instructions += """
            \n\n*** ULTRA MODE ACTIVATED ***
            The user has enabled 'JEEx Ultimate'. 
            1. INCREASE COMPLEXITY: Assume the user is aiming for Top 100 Rank in JEE Advanced.
            2. DERIVE EVERYTHING: Don't just give formulas. Derive them from first principles (Calculus).
            3. MULTI-CONCEPT: Actively look for ways to combine multiple chapters (e.g., Electrostatics + Rotation).
            4. TONE: Highly academic, rigorous, and demanding.
            """

        # DEEP RESEARCH INJECTION
        if st.session_state.deep_research_mode:
            base_instructions += """
            \n\n*** DEEP RESEARCH MODE ACTIVATED ***
            1. EXPLAIN LIKE A SCIENTIST: The user wants deep theoretical understanding.
            2. FIRST PRINCIPLES: Derive formulas rather than stating them. Start from fundamental laws (Newton's Laws, Maxwell's Equations).
            3. DEPTH OVER BREADTH: Go deep into the 'why' and 'how'.
            """
        
        # TARGET EXAM & SUBJECT INJECTION
        base_instructions += f"\n\nCONTEXT: The user is targeting **{st.session_state.target_exam}**. Focus specifically on **{st.session_state.subject_focus}** if applicable."

        with st.chat_message("assistant", avatar=LOGO_URL):
            stream = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id, assistant_id=assistant_id, stream=True,
                additional_instructions=base_instructions,
                # Force enabling code interpreter for double-checking if not already enabled on assistant
                tools=[{"type": "code_interpreter"}]
            )
            resp = st.empty()
            full_text = ""
            
            for event in stream:
                if event.event == "thread.message.delta":
                    for c in event.data.delta.content:
                        if c.type == "text":
                            full_text += c.text.value
                            resp.markdown(clean_latex_for_chat(full_text) + "▌")
            
            resp.markdown(clean_latex_for_chat(full_text))
            st.session_state.messages.append({"role": "assistant", "content": full_text})
            
    except Exception as e:
        st.session_state.messages.append({"role": "assistant", "content": "⚠️ Network issue. Please try again."})
    
    # --- AUTO-REMOVE ATTACHMENT AFTER ANSWERING ---
    st.session_state.current_uploaded_file = None
    
    st.session_state.uploader_key += 1
    if 'audio_value' in locals() and audio_value: st.session_state.audio_key += 1
    st.session_state.processing = False
    st.rerun()
