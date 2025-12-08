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

# --- 4. PROFESSIONAL CSS (UNIVERSAL THEME FORCE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* --- 1. FORCE DARK BACKGROUNDS --- */
    .stApp { background-color: #0E1117 !important; color: #E0E0E0 !important; }
    [data-testid="stSidebar"] { background-color: #161B26 !important; border-right: 1px solid #2B313E !important; }
    
    /* --- 2. UNIVERSAL TEXT VISIBILITY --- */
    h1, h2, h3, h4, h5, h6, p, li, div, span, label {
        color: #E0E0E0 !important;
    }
    strong { color: #FFD700 !important; font-weight: 600; }
    code { color: #FF7043 !important; }

    /* --- 3. INPUT FIELDS (High Contrast) --- */
    div[data-baseweb="input"], .stTextInput input {
        background-color: #1E2330 !important;
        border: 1px solid #4A90E2 !important; /* Blue Border */
        border-radius: 8px !important;
        color: #FFFFFF !important; /* Force White Text */
        -webkit-text-fill-color: #FFFFFF !important;
    }
    ::placeholder { color: #AAAAAA !important; opacity: 1; }

    /* --- 4. BUTTONS (Professional Blue) --- */
    div.stButton > button { 
        background-color: #4A90E2 !important; /* JEEx Blue */
        color: white !important; 
        border: none !important; 
        border-radius: 8px; 
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
    }
    div.stButton > button:hover { 
        background-color: #357ABD !important; /* Darker Blue Hover */
        box-shadow: 0px 4px 15px rgba(74, 144, 226, 0.4);
    }

    /* --- 5. EXPANDER & CONTAINERS --- */
    .streamlit-expanderHeader {
        background-color: #1E2330 !important;
        color: #E0E0E0 !important;
        border-radius: 8px;
    }
    
    /* --- 6. LAYOUT FIXES --- */
    .block-container { padding-top: 1rem; padding-bottom: 140px; }
    [data-testid="stFileUploader"] { padding: 0px; }
    .stAudioInput { margin-top: 5px; }
    .stChatMessage .st-emotion-cache-1p1m4ay { width: 45px; height: 45px; }
    
    /* Lock Input when Processing */
    .stApp[data-test-state="running"] .stChatInput { opacity: 0.5; pointer-events: none; }
</style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---

def send_final_notification(name, email, phone, trans_id):
    """Sends FINAL email with Transaction ID to Admin"""
    try:
        url = f"https://formsubmit.co/{ADMIN_EMAIL}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://jeex-pro.streamlit.app/"
        }
        payload = {
            "_subject": f"💰 PAYMENT VERIFICATION: {name}",
            "_captcha": "false",
            "_template": "table",
            "Name": name,
            "Email": email,
            "Phone": phone,
            "Transaction ID": trans_id,
            "Status": "Paid - Waiting for Key",
            "Timestamp": str(datetime.now())
        }
        resp = requests.post(url, data=payload, headers=headers)
        return resp.status_code == 200
    except:
        return False

def clean_latex(text):
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    text = text.replace('$$$', '$')
    return text

def sanitize_text_for_pdf(text):
    text = text.replace('•', '-').replace('—', '-').replace('’', "'")
    return text.encode('latin-1', 'ignore').decode('latin-1')

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

# --- 6. AUTH & LOGIC ---
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

# --- 7. SIDEBAR (SMART PAYMENT FLOW) ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    
    user_key = st.text_input("Enter Access Key:", type="password") 
    status = check_key_status(user_key)
    
    # --- UNLOCKED TOOLS ---
    if status == "VALID" or status == "ADMIN":
        st.success(f"✅ Active")
        st.markdown("---")
        
        st.markdown("**📎 Attach Question**")
        uploaded_file = st.file_uploader("Upload", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
        
        st.markdown("**🎙️ Voice Chat**")
        # NOTE: Key is kept dynamic to allow reset, but layout is cleaner now
        audio_value = st.audio_input("Speak", key=f"audio_{st.session_state.audio_key}", label_visibility="collapsed")
        
        st.markdown("---")
        if len(st.session_state.messages) > 1:
            pdf_bytes = generate_pdf(st.session_state.messages)
            st.download_button("📥 Download Notes", data=pdf_bytes, file_name="JEEx_Notes.pdf", mime="application/pdf")
        
        if st.button("End Session"): st.session_state['logout'] = True; st.rerun()

    # --- LOCKED (NEW PAYMENT WORKFLOW) ---
    else:
        if user_key and status != "VALID": st.error("❌ Invalid or Expired Key")
        
        st.markdown("### ⚡ Subscribe Now")
        with st.expander("💎 Get Premium (₹99/mo)", expanded=True):
            
            # STEP 1: COLLECT USER DETAILS
            if st.session_state.payment_step == 1:
                st.markdown("Fill details to get your key:")
                with st.form("reg_form"):
                    name = st.text_input("Name")
                    email = st.text_input("Email")
                    phone = st.text_input("WhatsApp No.")
                    submitted = st.form_submit_button("🚀 Proceed to Pay")
                
                if submitted:
                    if name and email and phone:
                        # Save details locally (No Email Yet)
                        st.session_state.user_details = {"name": name, "email": email, "phone": phone}
                        st.session_state.payment_step = 2 # Move to Payment
                        st.rerun()
                    else:
                        st.warning("⚠️ Please fill all details.")

            # STEP 2: QR + TRANSACTION ID INPUT
            elif st.session_state.payment_step == 2:
                st.info(f"Hi {st.session_state.user_details['name']}, scan to pay:")
                
                # Show QR
                try: st.image("upi_qr.png", caption="Scan UPI QR", use_container_width=True)
                except: st.info(f"Pay to: **{ADMIN_WHATSAPP}@upi**")
                
                st.markdown("---")
                
                # Transaction ID Form
                st.markdown("**Step 2: Enter Transaction ID**")
                trans_id = st.text_input("UPI Transaction ID (or Ref No.):", placeholder="e.g. T2308191234")
                st.caption("ℹ️ *Open GPay/PhonePe > History > Tap Transaction > Copy 'Txn ID' or 'UPI Ref No'*")
                
                # VERIFY BUTTON (Triggers Email)
                if st.button("✅ Verify & Submit"):
                    if len(trans_id) > 8: # Basic validation
                        details = st.session_state.user_details
                        # NOW SEND EMAIL
                        is_sent = send_final_notification(details['name'], details['email'], details['phone'], trans_id)
                        
                        st.session_state.user_details['trans_id'] = trans_id
                        st.session_state.payment_step = 3
                        st.rerun()
                    else:
                        st.error("⚠️ Please enter a valid Transaction ID.")
                
                if st.button("🔙 Go Back"):
                    st.session_state.payment_step = 1
                    st.rerun()

            # STEP 3: SUCCESS & WHATSAPP
            elif st.session_state.payment_step == 3:
                st.success("🎉 Payment Submitted! Admin notified.")
                st.markdown("Please allow few hours for verification. Once verified you will receive your access key on the provided email and Whatsapp number.")
                
                details = st.session_state.user_details
                msg = f"Hello JEEx Team!%0A%0A*PAYMENT VERIFICATION REQUEST*%0A👤 Name: {details['name']}%0A📧 Email: {details['email']}%0A📱 Phone: {details['phone']}%0A🆔 Trans ID: {details['trans_id']}%0A%0AI have paid ₹99. Please send my key."
                wa_link = f"https://wa.me/{ADMIN_WHATSAPP}?text={msg}"
                
                st.markdown(f'<a href="{wa_link}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:5px; cursor:pointer; font-weight:bold;">👉 Chat on WhatsApp (Faster)</button></a>', unsafe_allow_html=True)
                
                if st.button("Start Over"):
                    st.session_state.payment_step = 1
                    st.rerun()

        st.markdown("---")
        with st.expander("📄 Terms & Conditions"): 
            st.markdown("Detailed terms available on main page.")

# --- 8. ADMIN PANEL ---
if status == "ADMIN":
    st.sidebar.success("🔑 Admin Mode")
    c1, c2 = st.columns(2)
    with c1: new_id = st.text_input("Key ID")
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
    
    # FIXED: Replaced HTML with Native Streamlit Columns for clean layout
    st.markdown("### 🏆 Why Top Rankers Choose JEEx **PRO**")
    
    c1, c2 = st.columns(2)
    with c1:
        st.info("**🧠 Advanced Problem Solving**\n\nSolves Irodov, Cengage, and PYQ level problems with step-by-step logic, not just answers.")
        st.info("**📄 Full Document Brain**\n\nUpload entire PDF assignments. Our Code Interpreter analyzes the full document context to solve multiple questions.")
        st.info("**🎯 Concept-First Approach**\n\nWe don't just solve; we explain the 'Why'. Learn the derivation and underlying concept behind every solution.")
    
    with c2:
        st.info("**👁️ Vision Intelligence (OCR)**\n\nStuck on a handwritten question? Just upload a photo. JEEx reads handwriting and graphs instantly.")
        st.info("**➗ Perfect Math Formatting**\n\nExperience textbook-quality rendering for Integrals, Matrices, and Organic Mechanisms with LaTeX precision.")
        st.info("**⚡ 24/7 Strategic Mentorship**\n\nYour personal AI coach for study planning, backlog management, and exam strategy at 3 AM.")
    
    st.markdown("---")
    with st.expander("📄 Detailed Terms of Service & Privacy"):
        st.markdown("""
        ### JEEx Pro Terms of Service
        **1. Acceptance of Terms:** By accessing JEEx Pro, you confirm that you are a student preparing for competitive exams and agree to use this tool solely for educational purposes.
        **2. License Grant:** JEEx grants you a limited, non-exclusive, non-transferable license. Your Access Key is strictly personal. Sharing it will result in an immediate ban.
        **3. AI Accuracy:** JEEx utilizes GPT-4o. While highly accurate, hallucinations can occur. You agree to verify all formulas with standard textbooks (NCERT).
        **4. Refund Policy:** Access Keys are digital goods. **No Refunds** will be provided once a key is issued.
        **5. Privacy:** We respect your privacy. Chat logs are processed securely via OpenAI APIs and are not sold to third parties.
        """)
    st.stop()

# --- 10. CHAT INTERFACE & LOGIC ---

# Setup OpenAI
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    assistant_id = st.secrets["ASSISTANT_ID"]
    client = OpenAI(api_key=api_key)
except:
    st.error("🚨 Keys missing in Secrets."); st.stop()

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# --- INPUT HANDLING (FIXED VOICE & LOCKING) ---

# 1. Processing Logic (Voice First)
user_input_content = None

if 'audio_value' in locals() and audio_value:
    if not st.session_state.processing:
        with st.spinner("🎧 Listening..."):
            try:
                # Force English to fix hallucinations
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_value, 
                    language="en",
                    prompt="Physics, Chemistry, Maths, JEE, Integration"
                )
                user_input_content = transcription.text
            except Exception as e:
                st.error(f"Voice Error: {e}")

# 2. Text Input (Disabled if processing)
if st.session_state.processing:
    chat_val = st.chat_input("Thinking...", disabled=True)
else:
    chat_val = st.chat_input("Ask a doubt...")

# 3. Determine Final Prompt
if user_input_content:
    prompt = user_input_content
elif chat_val:
    prompt = chat_val
else:
    prompt = None

# --- MAIN EXECUTION LOOP ---
if prompt and not st.session_state.processing:
    st.session_state.processing = True # LOCK INTERFACE
    
    # 1. Store File Data for History
    file_data_entry = {}
    if uploaded_file:
        file_data_entry = {
            "file_data": uploaded_file.getvalue(),
            "file_name": uploaded_file.name,
            "file_type": uploaded_file.type
        }

    # 2. Append User Message
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt,
        **file_data_entry
    })
    
    # 3. Force UI Update
    st.rerun()

# --- DISPLAY HISTORY ---
for msg in st.session_state.messages:
    avatar_icon = LOGO_URL if msg["role"] == "assistant" else "🧑‍🎓"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        if "file_data" in msg:
            if msg["file_type"].startswith("image"):
                st.image(msg["file_data"], width=200)
            else:
                st.markdown(f"📄 *{msg['file_name']}*")
        st.markdown(clean_latex(msg["content"]))

# --- GENERATE RESPONSE ---
if st.session_state.processing and st.session_state.messages[-1]["role"] == "user":
    
    last_msg = st.session_state.messages[-1]
    msg_text = last_msg["content"]
    
    # 4. API Request
    message_content = [{"type": "text", "text": msg_text}]
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
            4. PDFS: Always use Code Interpreter to analyze uploaded PDFs.
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
        
    # 6. UNLOCK AND RESET
    st.session_state.uploader_key += 1
    if 'audio_value' in locals() and audio_value:
        st.session_state.audio_key += 1
        
    st.session_state.processing = False
    st.rerun()
