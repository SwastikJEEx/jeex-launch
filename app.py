# jeex_streamlit_app.py
import os
import re
import time
import requests
from datetime import datetime, timedelta

import streamlit as st
from fpdf import FPDF

try:
    # OpenAI client (the installed package & client surface might differ in your env)
    from openai import OpenAI
except Exception:
    OpenAI = None

# -----------------------------
# Configuration & Constants
# -----------------------------
st.set_page_config(
    page_title="JEEx PRO",
    page_icon="⚛️",
    layout="centered",
    initial_sidebar_state="expanded",
)

ADMIN_WHATSAPP = "919839940400"
ADMIN_EMAIL = "jeexaipro@gmail.com"
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png"

# -----------------------------
# Session state initialization
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Welcome Champ! Physics, Chemistry ya Maths — bas photo bhejo ya type karo. Let's crack it!"
        }
    ]
if "processing" not in st.session_state:
    st.session_state.processing = False
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0
if "payment_step" not in st.session_state:
    st.session_state.payment_step = 1
if "user_details" not in st.session_state:
    st.session_state.user_details = {}
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "audio_value" not in st.session_state:
    st.session_state.audio_value = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "key_input" not in st.session_state:
    st.session_state.key_input = ""
if "logout" not in st.session_state:
    st.session_state.logout = False

# -----------------------------
# CSS: theme aware (supports dark & light)
# -----------------------------
theme_css = """
<style>
:root {
  --bg: #0E1117;
  --panel: #111827;
  --muted: #A0AEC0;
  --accent: #4A90E2;
  --text: #E6E6E6;
  --card-bg: #0b1220;
}
html[data-theme="light"] :root {
  --bg: #f6f8fa;
  --panel: #ffffff;
  --muted: #4a5568;
  --accent: #2563eb;
  --text: #0f172a;
  --card-bg: #ffffff;
}
body, .stApp {
  background: linear-gradient(180deg, var(--bg), #0b1220);
  color: var(--text);
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial;
}
.block-container {
  padding-top: 1rem;
  padding-bottom: 4rem;
}
.stSidebar {
  background: linear-gradient(180deg, var(--panel), #0b1220);
  border-right: 1px solid rgba(255,255,255,0.04);
}
.stButton>button {
  background-color: var(--accent) !important;
  color: white !important;
  border-radius: 8px !important;
  padding: 10px 18px !important;
  font-weight: 600;
}
input, textarea, .stTextInput, .stTextArea {
  color: var(--text) !important;
  background: transparent !important;
}
.streamlit-expanderHeader {
  background-color: rgba(255,255,255,0.03) !important;
  border-radius: 8px;
}
.chat-box {
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.02));
  padding: 12px;
}
.small-muted {
  color: var(--muted);
  font-size: 13px;
}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

# -----------------------------
# Helpers
# -----------------------------
def send_final_notification(name: str, email: str, phone: str, trans_id: str) -> bool:
    try:
        url = f"https://formsubmit.co/{ADMIN_EMAIL}"
        headers = {
            "User-Agent": "JEEx/1.0",
        }
        payload = {
            "_subject": f"💰 NEW PAYMENT: {name}",
            "_captcha": "false",
            "_template": "table",
            "Name": name,
            "Email": email,
            "Phone": phone,
            "Transaction ID": trans_id,
            "Status": "Paid - Waiting for Key",
            "Timestamp": str(datetime.utcnow())
        }
        requests.post(url, data=payload, headers=headers, timeout=10)
        return True
    except Exception:
        return False

def clean_latex(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'【.*?†source】', '', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    return text.replace('$$$', '$')

def sanitize_text_for_pdf(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    text = text.replace('•', '-').replace('—', '-').replace('’', "'")
    return text.encode('latin-1', 'ignore').decode('latin-1')

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
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    for msg in messages:
        role = "JEEx" if msg.get("role", "") == "assistant" else "Student"
        content = clean_latex(msg.get("content", "")).replace('*', '')
        pdf.chapter_title(role)
        pdf.chapter_body(content)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

def check_key_status(user_key: str) -> str:
    master = st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS")
    if user_key and user_key == master:
        return "ADMIN"
    expiry_db = st.secrets.get("KEY_EXPIRY", {}) or {}
    if user_key in expiry_db:
        try:
            exp = datetime.strptime(expiry_db[user_key], "%Y-%m-%d").date()
            if datetime.utcnow().date() > exp:
                return "EXPIRED"
            else:
                return "VALID"
        except Exception:
            return "INVALID"
    return "INVALID"

# -----------------------------
# Prepare sidebar & capture input key early (so `status` is available globally)
# -----------------------------
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    key_input = st.text_input("Enter Access Key:", type="password", value=st.session_state.key_input)
    st.session_state.key_input = key_input
    status = check_key_status(key_input)

    if status == "VALID" or status == "ADMIN":
        st.success("✅ Active")
        st.markdown("---")
        st.markdown("**📎 Attach Question**")
        uploaded_file = st.file_uploader("Upload (jpg/png/pdf)", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
        # persist uploader across session_state
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file

        st.markdown("**🎙️ Voice Chat**")
        try:
            audio_value = st.audio_input("Speak", key=f"audio_{st.session_state.audio_key}", label_visibility="collapsed")
            if audio_value is not None:
                st.session_state.audio_value = audio_value
        except Exception:
            # audio_input might not be available in some Streamlit versions
            st.info("Voice input not supported in your environment.")

        st.markdown("---")
        if len(st.session_state.messages) > 1:
            pdf_bytes = generate_pdf(st.session_state.messages)
            st.download_button("📥 Download Notes", data=pdf_bytes, file_name="JEEx_Notes.pdf", mime="application/pdf")
        if st.button("End Session"):
            st.session_state.logout = True
            st.experimental_rerun()
    else:
        if key_input and status != "VALID":
            st.error("❌ Invalid Key")

        st.markdown("### ⚡ Subscribe Now")
        with st.expander("💎 Get Premium (₹99/mo)", expanded=True):
            if st.session_state.payment_step == 1:
                st.markdown("Fill details to get your key:")
                with st.form("reg_form"):
                    name = st.text_input("Name")
                    email = st.text_input("Email")
                    phone = st.text_input("WhatsApp No.")
                    sub = st.form_submit_button("🚀 Proceed to Pay")
                if sub:
                    if name and email and phone:
                        st.session_state.user_details = {"name": name, "email": email, "phone": phone}
                        st.session_state.payment_step = 2
                        st.experimental_rerun()
                    else:
                        st.warning("⚠️ Fill all details.")
            elif st.session_state.payment_step == 2:
                det = st.session_state.user_details or {}
                st.info(f"Hi {det.get('name', '')}, scan to pay:")
                qr_path = "upi_qr.png"
                if os.path.exists(qr_path):
                    st.image(qr_path, caption="UPI QR", use_container_width=True)
                else:
                    st.info(f"Pay to: **{ADMIN_WHATSAPP}@upi**")

                st.markdown("---")
                trans_id = st.text_input("UPI Transaction ID:", placeholder="e.g. T230...")
                st.caption("ℹ️ *Found in Payment History (GPay/PhonePe/Paytm).*")
                if st.button("✅ Verify & Submit"):
                    if trans_id and len(trans_id) > 6:
                        det = st.session_state.user_details
                        send_final_notification(det.get('name', ''), det.get('email', ''), det.get('phone', ''), trans_id)
                        st.session_state.user_details['trans_id'] = trans_id
                        st.session_state.payment_step = 3
                        st.experimental_rerun()
                    else:
                        st.error("Invalid ID")
                if st.button("Back"):
                    st.session_state.payment_step = 1
                    st.experimental_rerun()
            elif st.session_state.payment_step == 3:
                st.success("🎉 Payment Submitted!")
                st.markdown("Please allow a few hours for verification. Once verified you will receive your access key on the provided email and WhatsApp number.")
                det = st.session_state.user_details or {}
                msg = f"Hello JEEx!%0A*PAID*%0AName: {det.get('name','')}%0AID: {det.get('trans_id','')}"
                wa_link = f"https://wa.me/{ADMIN_WHATSAPP}?text={msg}"
                st.markdown(
                    f'<a href="{wa_link}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:5px; font-weight:bold;">👉 Chat on WhatsApp</button></a>',
                    unsafe_allow_html=True
                )
                if st.button("Start Over"):
                    st.session_state.payment_step = 1
                    st.experimental_rerun()

        st.markdown("---")
        with st.expander("📄 Detailed Terms & Conditions"):
            st.markdown("""
            **1. Service Scope:** JEEx Pro is an AI-powered educational aid for JEE preparation. It provides explanations, solves numericals, and offers strategies.
            **2. Account Usage:** Keys are strictly personal. Sharing keys results in ban.
            **3. Payment Policy:** Keys are digital; refunds not provided after key issuance.
            **4. AI Limitations:** AI can make errors. Cross-check important steps with NCERT.
            """)

# -----------------------------
# Admin quick panel (outside the main sidebar block so `status` always exists)
# -----------------------------
if status == "ADMIN":
    st.sidebar.success("🔑 Admin Mode")
    c1, c2 = st.columns(2)
    with c1:
        new_id = st.text_input("Key ID")
    with c2:
        days = st.number_input("Days", value=30, min_value=1, max_value=3650)
    if new_id:
        exp = (datetime.utcnow() + timedelta(days=int(days))).strftime("%Y-%m-%d")
        st.code(f'"{new_id}" = "{exp}"', language="toml")
    st.stop()

# -----------------------------
# Landing / Branding
# -----------------------------
def show_branding():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        try:
            st.image(LOGO_URL, width=220)
        except Exception:
            pass
    st.markdown(
        """
        <div style="text-align: center; margin-top: -10px; margin-bottom: 18px;">
            <h1 style="margin: 0; font-size: 36px; font-weight: 700;">
                JEEx <span style="color:#4A90E2;">PRO</span>
            </h1>
            <p class="small-muted" style="margin-top: 6px;">
                Your 24/7 AI Rank Booster | Master JEE Mains & Advanced
            </p>
        </div>
        """, unsafe_allow_html=True
    )

show_branding()

if status != "VALID":
    st.markdown("---")
    st.markdown("""
    <div style="background-color: rgba(74,144,226,0.06); padding: 18px; border-radius: 10px; border-left: 5px solid #4A90E2; text-align: center;">
        <p style="font-size: 16px; margin: 0; color: inherit;">👋 <strong>Welcome Student!</strong><br>Please enter your <strong>Access Key</strong> in the Sidebar to unlock.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🏆 Why Top Rankers Choose JEEx **PRO**")
    c1, c2 = st.columns(2)
    with c1:
        st.info("**🧠 Advanced Problem Solving**\n\nSolves Irodov, Cengage, and PYQ level problems with step-by-step logic.")
        st.info("**📄 Full Document Brain**\n\nUpload entire PDF assignments. Our Code Interpreter analyzes context.")
        st.info("**🎯 Concept-First Approach**\n\nWe don't just solve; we explain the 'Why'.")
    with c2:
        st.info("**👁️ Vision Intelligence (OCR)**\n\nReads handwritten questions from photos instantly.")
        st.info("**➗ Perfect Math Formatting**\n\nTextbook-quality rendering for Integrals and Organic Mechanisms.")
        st.info("**⚡ 24/7 Strategic Mentorship**\n\nYour personal AI coach for study planning and backlog management.")
    st.stop()

# -----------------------------
# Chat Interface / LLM Setup
# -----------------------------
if OpenAI is None:
    st.error("OpenAI python client not available. Please install the required package.")
    st.stop()

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    assistant_id = st.secrets["ASSISTANT_ID"]
except Exception:
    st.error("🚨 Keys missing. Set OPENAI_API_KEY and ASSISTANT_ID in Streamlit secrets.")
    st.stop()

if st.session_state.thread_id is None:
    try:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    except Exception:
        st.error("Failed to create assistant thread. Check API keys & network.")
        st.stop()

# Input capture
audio_prompt = None
if st.session_state.audio_value:
    if not st.session_state.processing:
        with st.spinner("🎧 Listening..."):
            try:
                transcription = client.audio.transcriptions.create(model="whisper-1", file=st.session_state.audio_value, language="en")
                audio_prompt = getattr(transcription, "text", None) or transcription.get("text", None)
            except Exception:
                audio_prompt = None

text_prompt = st.chat_input("Ask a doubt...", disabled=st.session_state.processing)
prompt = audio_prompt if audio_prompt else text_prompt

if prompt:
    st.session_state.processing = True
    msg_data = {"role": "user", "content": prompt}
    if st.session_state.uploaded_file:
        uploaded_file = st.session_state.uploaded_file
        try:
            file_bytes = uploaded_file.getvalue()
            msg_data.update({
                "file_data": file_bytes,
                "file_name": uploaded_file.name,
                "file_type": uploaded_file.type
            })
        except Exception:
            # fallback if getvalue not supported
            pass
    st.session_state.messages.append(msg_data)
    st.experimental_rerun()

# Display messages
for msg in st.session_state.messages:
    avatar = LOGO_URL if msg.get("role") == "assistant" else "🧑‍🎓"
    with st.chat_message(msg.get("role", "user"), avatar=avatar):
        if "file_data" in msg:
            ftype = msg.get("file_type", "")
            if ftype.startswith("image"):
                st.image(msg["file_data"], width=250)
            else:
                st.markdown(f"📄 *{msg.get('file_name','attachment')}*")
        st.markdown(clean_latex(msg.get("content", "")))

# Process latest user message
if st.session_state.processing and st.session_state.messages and st.session_state.messages[-1].get("role") == "user":
    user_msg = st.session_state.messages[-1]
    msg_text = user_msg.get("content", "")
    api_content = [{"type": "text", "text": msg_text}]
    attachments = []

    if st.session_state.uploaded_file:
        try:
            tname = f"temp_{int(time.time())}_{st.session_state.uploaded_file.name}"
            with open(tname, "wb") as f:
                f.write(st.session_state.uploaded_file.getbuffer())
            fres = client.files.create(file=open(tname, "rb"), purpose="assistants")
            if st.session_state.uploaded_file.type == "application/pdf":
                attachments.append({"file_id": fres.id, "tools": [{"type": "code_interpreter"}]})
            else:
                api_content.append({"type": "image_file", "image_file": {"file_id": fres.id}})
            try:
                os.remove(tname)
            except Exception:
                pass
        except Exception:
            st.error("Upload failed. Please try again without attachment.")

    try:
        client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=api_content, attachments=attachments or None)
    except Exception:
        st.error("Failed to send message to assistant. Check API & network.")
        st.session_state.processing = False
        st.experimental_rerun()

    with st.chat_message("assistant", avatar=LOGO_URL):
        try:
            stream = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=assistant_id,
                stream=True,
                additional_instructions="You are JEEx. Use LaTeX for math and provide step-by-step explanations. Keep tone encouraging."
            )
        except Exception:
            st.error("Assistant run failed to start.")
            st.session_state.processing = False
            st.experimental_rerun()

        resp = st.empty()
        full_text = ""
        try:
            for event in stream:
                if getattr(event, "event", None) == "thread.message.delta":
                    # event.data.delta.content could be list-like
                    for c in getattr(event.data.delta, "content", []) or []:
                        if getattr(c, "type", None) == "text":
                            # c.text may have provider-specific structure
                            part = getattr(c.text, "value", None) or getattr(c.text, "text", None) or ""
                            full_text += part
                            resp.markdown(clean_latex(full_text) + "▌")
                elif getattr(event, "event", None) == "thread.run.completed":
                    break
        except Exception:
            # if streaming fails, try to request final message
            pass

        # finalize display & store to history
        resp.markdown(clean_latex(full_text))
        st.session_state.messages.append({"role": "assistant", "content": full_text})

    # increment keys to refresh uploader/audio input components
    st.session_state.uploader_key += 1
    if st.session_state.audio_value:
        st.session_state.audio_key += 1
    st.session_state.processing = False
    st.experimental_rerun()
