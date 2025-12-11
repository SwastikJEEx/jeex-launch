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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="centered", initial_sidebar_state="expanded")

# *** EMAIL SETTINGS ***
SENDER_EMAIL = "jeexaipro@gmail.com"  
SENDER_PASSWORD = "JEExPROAI1109" # Updated Password
RECEIVER_EMAIL = "jeexaipro@gmail.com"

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

# Simple logger
logger = logging.getLogger("jeex")
logger.setLevel(logging.INFO)

# --- 4. PROFESSIONAL CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0E1117 !important; color: #E0E0E0 !important; }
    [data-testid="stSidebar"] { background-color: #161B26 !important; border-right: 1px solid #2B313E !important; }
    header, header * { background-color: #0E1117 !important; color: #E0E0E0 !important; }
    h1, h2, h3, h4, h5, h6, p, li, div, span, label, a, small, strong, code { color: #E0E0E0 !important; }
    strong { color: #FFD700 !important; font-weight: 600; }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
        background-color: #1E2330 !important; border: 1px solid #4A90E2 !important; border-radius: 8px !important;
    }
    input[type="text"], input[type="password"], textarea { color: #FFFFFF !important; }
    button, .stButton>button {
        background-color: #4A90E2 !important; color: #FFFFFF !important; border-radius: 8px !important; font-weight: 600 !important;
    }
    button:hover { background-color: #357ABD !important; }
    [data-testid="stFileUploader"] { background-color: #14181C !important; border: 1px solid #2B313E !important; border-radius: 8px !important; }
    .block-container { padding-top: 1rem; padding-bottom: 140px; }
</style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---

def send_smtp_email(name, email, phone):
    """Sends Lead Email using Robust SMTP"""
    try:
        # 1. SETUP HEADERS (Anti-Spam)
        msg = MIMEMultipart()
        msg['From'] = f"JEEx System <{SENDER_EMAIL}>"
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🚀 NEW USER: {name}"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        # 2. BODY
        body = f"""
        NEW USER REGISTRATION (FREE TRIAL)
        ==================================
        Name: {name}
        Email: {email}
        Phone: {phone}
        Timestamp: {datetime.now()}
        ==================================
        User has been granted access.
        """
        msg.attach(MIMEText(body, 'plain'))

        # 3. SEND
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        # PRINT ERROR TO UI SO USER CAN SEE WHY IT FAILED
        st.error(f"⚠️ Email Delivery Failed: {e}") 
        # We still return True to allow the user to enter the app
        return True 

def clean_latex_for_chat(text):
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    # Ensure standard dollar signs for math are preserved/fixed if needed
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    return text

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
        self.cell(0, 10, str(label), 0, 1, 'L')
        self.ln(2)
    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(50, 50, 50)
        # Basic cleanup for PDF
        clean = body.replace('$$', '').replace('$', '').encode('latin-1', 'replace').decode('latin-1')
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
                with st.spinner("Setting up your account..."):
                    # Send Email
                    sent = send_smtp_email(name, email, phone)
                    
                    # Grant Access
                    st.session_state.user_details = {"name": name, "email": email}
                    st.session_state.is_verified = True
                    st.success("✅ Success! Welcome aboard.")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("⚠️ Please fill in all details.")
    
    # B. IF VERIFIED -> SHOW TOOLS
    else:
        st.markdown(f"👤 **{st.session_state.user_details.get('name', 'Student')}**")
        st.success("✅ Pro Plan Active (Free)")
        st.markdown("---")
        
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
            st.download_button("📥 Download Notes", data=pdf_bytes, file_name="JEEx_Notes.pdf", mime="application/pdf")
        
        if st.button("Logout"): 
            st.session_state['logout'] = True
            st.rerun()

# --- 7. MAIN INTERFACE ---
show_branding()

# If not verified, show landing teaser and stop
if not st.session_state.is_verified:
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #1E2330; padding: 25px; border-radius: 12px; border-left: 5px solid #4A90E2; text-align: center; margin-bottom: 30px;">
        <h3 style="color: #FFFFFF; margin:0;">👋 Welcome to JEEx PRO</h3>
        <p style="color: #AAAAAA; margin-top: 10px;">
            The ultimate AI tool for JEE Mains & Advanced.<br>
            <strong>Use the Sidebar on the left to Register for FREE access!</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.info("**🧠 Advanced Problem Solving**\n\nSolves Irodov & Cengage level problems.")
    with c2:
        st.info("**👁️ Vision Intelligence**\n\nReads handwritten questions instantly.")
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
                # For PDFs, use code interpreter to read them
                att.append({"file_id": fres.id, "tools": [{"type": "code_interpreter"}]})
            else:
                # For images
                api_content.append({"type": "image_file", "image_file": {"file_id": fres.id}})
            
            try: os.remove(tfile)
            except: pass
        except:
            pass # Continue without file if upload fails
    
    try:
        client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=api_content, attachments=att if att else None)
        
        # --- ENHANCED BOT INSTRUCTIONS FOR ACCURACY & FORMATTING ---
        INSTRUCTIONS = """
        You are JEEx, an expert JEE tutor.
        MANDATORY RULES:
        1. FORMATTING: You MUST use LaTeX for ALL mathematical symbols, equations, and chemistry formulas.
           - Use $...$ for inline math (e.g. $x^2$).
           - Use $$...$$ for block math equations.
        2. ACCURACY & VERIFICATION:
           - Double-check every solution step.
           - Simulate a web search by using your internal knowledge base extensively to ensure up-to-date methods.
           - CRITICAL: For complex calculations or physics/math problems, use the Python Tool (Code Interpreter) to calculate and verify the answer before displaying it. Do not rely on mental math for complex integrals or arithmetic.
        3. Explain concepts deeply but efficiently.
        """
        
        with st.chat_message("assistant", avatar=LOGO_URL):
            stream = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id, assistant_id=assistant_id, stream=True,
                additional_instructions=INSTRUCTIONS,
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
        
    st.session_state.uploader_key += 1
    if 'audio_value' in locals() and audio_value: st.session_state.audio_key += 1
    st.session_state.processing = False
    st.rerun()
