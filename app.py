import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="centered", initial_sidebar_state="expanded")

# --- 2. PROFESSIONAL CSS ---
st.markdown("""
<style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Theme Colors */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161B26; border-right: 1px solid #2B313E; }
    
    /* Layout */
    .block-container { padding-top: 2rem; padding-bottom: 100px; }
    
    /* Chat Bubbles */
    [data-testid="stChatMessage"] { background-color: transparent; border: none; padding: 10px 0px; }
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #1E2330; border-radius: 12px; padding: 15px 20px; 
        margin-bottom: 10px; border: 1px solid #2B313E;
    }
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: transparent; padding: 0px 20px; margin-bottom: 10px;
    }
    
    /* Typography */
    p, li, div { font-size: 17px !important; line-height: 1.6 !important; color: #E6E6E6 !important; }
    strong { color: #FFD700 !important; } 
    code { color: #FF7043 !important; }
    
    /* Buttons */
    div.stButton > button { 
        background-color: #2B313E !important; color: white !important; border: 1px solid #3E4654 !important; 
        border-radius: 8px; width: 100%; transition: all 0.3s; font-weight: 600;
    }
    div.stButton > button:hover { border-color: #4A90E2 !important; color: #4A90E2 !important; }
    
    /* Sidebar Elements */
    [data-testid="stFileUploader"] { padding: 0px; }
    .stAudioInput { margin-top: 10px; }
    
    /* Avatar */
    .stChatMessage .st-emotion-cache-1p1m4ay { width: 45px; height: 45px; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def clean_latex(text):
    if not text: return ""
    text = re.sub(r'【.*?†source】', '', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    text = text.replace('$$$', '$')
    return text

def sanitize_text_for_pdf(text):
    text = text.replace('•', '-').replace('—', '-')
    return text.encode('latin-1', 'ignore').decode('latin-1')

LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"

def show_branding():
    """Displays Logo and Title PERFECTLY CENTERED"""
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

# --- 4. PDF GENERATOR ---
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

# --- 6. DETAILED TERMS & CONDITIONS ---
terms_text = """
### JEEx Pro Terms of Service & End User License Agreement

**1. Acceptance of Terms**
By accessing JEEx Pro, you confirm that you are a student preparing for competitive exams and agree to use this tool solely for educational purposes.

**2. License Grant & Restrictions**
* **License:** JEEx grants you a limited, non-exclusive, non-transferable license to use the AI tutor.
* **Single User Only:** Your Access Key is strictly personal. Sharing it on public forums (Telegram, WhatsApp, Reddit) or with friends is a violation of this agreement.
* **Security Monitoring:** Our system actively logs IP addresses and device fingerprints. Simultaneous logins from multiple locations will trigger an automatic, irreversible ban.

**3. AI Accuracy & Educational Disclaimer**
* **Nature of AI:** JEEx Pro utilizes advanced LLMs (GPT-4o) to generate responses. While highly accurate, "hallucinations" (incorrect data) can occur.
* **User Verification:** You agree to verify all formulas, constants, and solutions with standard textbooks (NCERT, H.C. Verma). JEEx is a study companion, not a replacement for official academic instruction.
* **Liability:** JEEx is not liable for any loss of marks, exam results, or academic consequences resulting from reliance on the tool.

**4. Payments & Refund Policy**
* **Digital Goods:** Access Keys are classified as intangible digital goods. Once a key is generated and delivered to you, the service is considered "consumed."
* **No Refunds:** We enforce a strict **No Refund Policy**. All sales are final.
* **Validity:** Subscriptions are valid for exactly 30 days from the date of activation in our system.

**5. Intellectual Property**
The branding, code, logos, and interface of JEEx Pro are the intellectual property of the developers. Unauthorized reproduction or reverse engineering is prohibited.

**6. Termination**
We reserve the right to terminate your access immediately, without notice or refund, if you violate these terms (e.g., key sharing, abusive language, scraping data).
"""

# --- 7. SIDEBAR (Tools Moved Here) ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
    if "audio_key" not in st.session_state: st.session_state.audio_key = 0
    
    user_key = st.text_input("Enter Access Key:", type="password")
    status = check_key_status(user_key)
    
    # UNLOCKED TOOLS
    if status == "VALID" or status == "ADMIN":
        st.success(f"✅ Active")
        st.markdown("---")
        
        # 1. ATTACHMENT
        st.markdown("**📎 Attach Question**")
        uploaded_file = st.file_uploader("Upload Image/PDF", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
        
        # 2. VOICE INPUT
        st.markdown("**🎙️ Voice Chat**")
        audio_value = st.audio_input("Speak", key=f"audio_{st.session_state.audio_key}", label_visibility="collapsed")
        
        st.markdown("---")
        if "messages" in st.session_state and len(st.session_state.messages) > 1:
            pdf_bytes = generate_pdf(st.session_state.messages)
            st.download_button("📥 Download Notes", data=pdf_bytes, file_name="JEEx_Notes.pdf", mime="application/pdf")
        
        if st.button("End Session"): st.session_state['logout'] = True; st.rerun()

    # LOCKED STATE
    else:
        if status == "EXPIRED":
            st.error("⚠️ Plan Expired")
            st.warning("Your JEEx Pro monthly Plan has expired.")
            btn_text = "👉 Renew Now (₹99)"
        else:
            if user_key: st.warning("🔒 Chat Locked")
            btn_text = "👉 Subscribe for ₹99 / Month"
        
        payment_link = "https://rzp.io/rzp/wXI8i7t" 
        st.markdown(f'<a href="{payment_link}" target="_blank"><button style="width:100%; background-color:#4A90E2; color:white; border:none; padding:12px; border-radius:8px; cursor:pointer; font-weight:bold; font-size:15px; margin-top:10px;">{btn_text}</button></a>', unsafe_allow_html=True)
        st.markdown("---")
        with st.expander("📄 Terms & Conditions"): 
            st.markdown("Please read the detailed terms on the main page.")

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

# --- 9. LANDING PAGE (LOCKED) ---
show_branding()

if status != "VALID":
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #1E2330; padding: 20px; border-radius: 12px; border-left: 5px solid #4A90E2; text-align: center; margin-bottom: 30px;">
        <p style="font-size: 18px; margin: 0; color: #E6E6E6;">👋 <strong>Welcome Student!</strong><br>Please enter your <strong>Access Key</strong> in the Sidebar to unlock.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 6 STRONG POINTS DESCRIPTION
    st.markdown("### 🏆 Why Top Rankers Choose JEEx **PRO**")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🧠 Advanced Problem Solving**")
        st.caption("Solves Irodov, Cengage, and PYQ level problems with step-by-step logic, not just answers.")
        
        st.markdown("**📄 Full Document Brain**")
        st.caption("Upload entire PDF assignments. Our Code Interpreter analyzes the full document context to solve multiple questions.")
        
        st.markdown("**🎯 Concept-First Approach**")
        st.caption("We don't just solve; we explain the 'Why'. Learn the derivation and underlying concept behind every solution.")

    with c2:
        st.markdown("**👁️ Vision Intelligence (OCR)**")
        st.caption("Stuck on a handwritten question? Just upload a photo. JEEx reads handwriting and graphs instantly.")
        
        st.markdown("**➗ Perfect Math Formatting**")
        st.caption("Experience textbook-quality rendering for Integrals, Matrices, and Organic Mechanisms with LaTeX precision.")
        
        st.markdown("**⚡ 24/7 Strategic Mentorship**")
        st.caption("Your personal AI coach for study planning, backlog management, and exam strategy at 3 AM.")
    
    st.markdown("---")
    with st.expander("📄 Read Detailed Terms & Conditions"):
        st.markdown(terms_text)
    st.stop()

# --- 10. UNLOCKED CHAT ---

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
    st.session_state.messages = [{"role": "assistant", "content": "Welcome Champ! 🎓 Physics, Chemistry ya Maths—bas photo bhejo ya type karo. Let's crack it! 🚀"}]

# DISPLAY HISTORY (NOW INCLUDES ATTACHMENTS PERMANENTLY)
for msg in st.session_state.messages:
    avatar_icon = LOGO_URL if msg["role"] == "assistant" else "🧑‍🎓"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        # Render File if exists in history
        if "file_data" in msg:
            if msg["file_type"].startswith("image"):
                st.image(msg["file_data"], width=200)
            else:
                st.markdown(f"📄 *{msg['file_name']}*")
        # Render Text
        st.markdown(clean_latex(msg["content"]))

# --- CHAT INPUT & LOGIC ---

# 1. Processing Logic (Voice First)
audio_prompt = None
if 'audio_value' in locals() and audio_value:
    with st.spinner("Processing Voice..."):
        try:
            transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_value, language="en")
            audio_prompt = transcription.text
        except Exception as e: pass # Silent fail for smoother UX

# 2. Input Box (Fixed at Bottom)
text_prompt = st.chat_input("Ask a doubt...")

# 3. Determine Prompt
prompt = audio_prompt if (locals().get('audio_value')) else text_prompt

if prompt:
    # PREPARE ATTACHMENT DATA FOR HISTORY (Crucial Step)
    file_data_entry = {}
    if uploaded_file:
        file_data_entry = {
            "file_data": uploaded_file.getvalue(), # Store bytes so it persists
            "file_name": uploaded_file.name,
            "file_type": uploaded_file.type
        }

    # ADD USER MESSAGE TO HISTORY (With File)
    user_msg_dict = {"role": "user", "content": prompt}
    user_msg_dict.update(file_data_entry) # Merge file data
    st.session_state.messages.append(user_msg_dict)
    
    # RENDER USER MESSAGE IMMEDIATELY
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
        if uploaded_file:
            if uploaded_file.type == "application/pdf": st.markdown(f"📄 *{uploaded_file.name}*")
            else: st.image(uploaded_file, width=200)

    # 4. API Request
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
        thread_id=st.session_state.thread_id, role="user", content=message_content, attachments=attachments if attachments else None
    )

    # 5. Streaming Response
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
        
        # 6. Reset Inputs (Wait longer to avoid voice widget crash)
        st.session_state.uploader_key += 1
        if locals().get('audio_value'): 
            st.session_state.audio_key += 1 
            time.sleep(0.5) # Increased buffer for stability
            st.rerun()

