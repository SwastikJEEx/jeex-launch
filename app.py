import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime
import requests
import logging
import sqlite3
import json
import uuid

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="wide", initial_sidebar_state="expanded")

# *** EMAIL SETTINGS ***
ADMIN_EMAIL = "jeexaipro@gmail.com"  

# --- 2. GLOBAL CONSTANTS ---
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"
DB_FILE = "jeex_history.db"

# --- 3. DATABASE MANAGEMENT (SQLite for Persistence) ---
def init_db():
    """Initialize local SQLite database for chat history"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    # Users table (Simulating Google Account Link)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, name TEXT, picture TEXT)''')
    # Sessions table (Threads)
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (session_id TEXT PRIMARY KEY, user_email TEXT, title TEXT, created_at DATETIME)''')
    # Messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT, file_meta TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

def db_save_user(email, name, picture=""):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (email, name, picture) VALUES (?, ?, ?)", (email, name, picture))
    conn.commit()
    conn.close()

def db_create_session(user_email, title="New Chat"):
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (session_id, user_email, title, created_at) VALUES (?, ?, ?, ?)", 
              (session_id, user_email, title, datetime.now()))
    conn.commit()
    conn.close()
    return session_id

def db_get_user_sessions(user_email):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE user_email = ? ORDER BY created_at DESC", (user_email,))
    rows = c.fetchall()
    conn.close()
    return rows

def db_save_message(session_id, role, content, file_meta=None):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    file_json = json.dumps(file_meta) if file_meta else None
    c.execute("INSERT INTO messages (session_id, role, content, file_meta, timestamp) VALUES (?, ?, ?, ?, ?)", 
              (session_id, role, content, file_json, datetime.now()))
    conn.commit()
    conn.close()

def db_get_messages(session_id):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = c.fetchall()
    messages = []
    for row in rows:
        msg = {
            "role": row["role"],
            "content": row["content"],
            "file_meta": json.loads(row["file_meta"]) if row["file_meta"] else None
        }
        # Reconstruct file data for UI if needed (simplified for text history)
        if msg["file_meta"]:
            msg["file_name"] = msg["file_meta"].get("name")
            msg["file_type"] = msg["file_meta"].get("type")
        messages.append(msg)
    conn.close()
    return messages

def db_update_session_title(session_id, new_title):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("UPDATE sessions SET title = ? WHERE session_id = ?", (new_title, session_id))
    conn.commit()
    conn.close()

# Initialize DB on load
init_db()

# --- 4. SESSION STATE INITIALIZATION ---
if "user" not in st.session_state: st.session_state.user = None # Holds user dict {email, name, picture}
if "current_session_id" not in st.session_state: st.session_state.current_session_id = None
if "messages" not in st.session_state: st.session_state.messages = []
if "processing" not in st.session_state: st.session_state.processing = False
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "audio_key" not in st.session_state: st.session_state.audio_key = 0
if "current_uploaded_file" not in st.session_state: st.session_state.current_uploaded_file = None

# MODE STATES
if "ultimate_mode" not in st.session_state: st.session_state.ultimate_mode = False
if "deep_research_mode" not in st.session_state: st.session_state.deep_research_mode = False
if "mistake_analysis_mode" not in st.session_state: st.session_state.mistake_analysis_mode = False

# Simple logger
logger = logging.getLogger("jeex")
logger.setLevel(logging.INFO)

# --- 5. PROFESSIONAL CSS (NEON BLUE THEME) ---
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
    
    /* Inputs & selects - EXACT COPY OF NEETx LOGIC but Blue */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
        background-color: #050810 !important;
        border: 1px solid #00A6FF !important;
        border-radius: 8px !important;
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

    /* Dropdown & listbox */
    ul[data-baseweb="menu"], div[role="listbox"], .baseweb-popover, .baseweb-menu, .rc-virtual-list {
        background-color: #050810 !important;
        color: #E0E0E0 !important;
        border: 1px solid #0D1B2E !important;
    }
    li[data-baseweb="option"], ul[data-baseweb="menu"] li, .baseweb-menu li, .rc-virtual-list .list-item {
        color: #E0E0E0 !important;
        background-color: transparent !important;
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

    /* Chat input */
    .stChatInput, .stChatInput * {
        background-color: transparent !important;
        color: #E0E0E0 !important;
    }
    .stChatInput .css-1v3fvcr, .stChatInput .css-1y8i9bb { background: #000000 !important; color: #E0E0E0 !important; }
    .stChatInput { border-color: #00A6FF !important; }
    
    /* Spinner */
    .stSpinner > div > div { border-top-color: #00A6FF !important; }

    /* Misc */
    .css-1v3fvcr, .css-1y8i9bb { border: none !important; box-shadow: none !important; }
    .block-container { padding-top: 1rem; padding-bottom: 140px; max-width: 1200px; margin: 0 auto; }
    [data-testid="stFileUploader"] { padding: 8px !important; }
    .stAudioInput { margin-top: 5px; padding: 6px !important; }
    
    /* Google Button Style */
    .google-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #ffffff !important;
        color: #444444 !important;
        border: 1px solid #dddddd !important;
        border-radius: 8px;
        padding: 12px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        margin-top: 20px;
        text-decoration: none;
        transition: all 0.3s;
    }
    .google-btn:hover {
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- 6. HELPER FUNCTIONS ---

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

def login_ui():
    """Simulated Google Login UI"""
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div style="background-color: #050810; padding: 40px; border-radius: 12px; border: 1px solid #00A6FF; text-align: center;">
            <h2 style="color: #00A6FF;">Welcome Back, Champ! 🎓</h2>
            <p style="color: #AAAAAA;">Sign in to save your progress, track mistakes, and sync chats across devices.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # In a real production app, this would use OAuth2 redirect
        # For this demo/file, we simulate the authentication
        if st.button("🔵 Sign in with Google", use_container_width=True):
            with st.spinner("Connecting to Google Secure Server..."):
                time.sleep(1.5) # Simulate network delay
                # Mock User Data
                user_info = {
                    "email": "student@example.com",
                    "name": "JEEx Scholar",
                    "picture": ""
                }
                st.session_state.user = user_info
                db_save_user(user_info["email"], user_info["name"], user_info["picture"])
                st.toast("Login Successful!", icon="✅")
                st.rerun()
        
        st.markdown("<p style='text-align:center; font-size: 0.8em; color: #555;'>By continuing, you agree to JEEx Terms & Privacy Policy.</p>", unsafe_allow_html=True)

def create_new_chat():
    if st.session_state.user:
        sid = db_create_session(st.session_state.user["email"])
        st.session_state.current_session_id = sid
        st.session_state.messages = [{"role": "assistant", "content": "Hello Scholar! 🎓 I'm ready. What are we solving today?"}]
        # Save initial message
        db_save_message(sid, "assistant", st.session_state.messages[0]["content"])
        st.rerun()

def load_chat(session_id):
    st.session_state.current_session_id = session_id
    msgs = db_get_messages(session_id)
    if msgs:
        st.session_state.messages = msgs
    else:
        st.session_state.messages = [{"role": "assistant", "content": "Chat history loaded but empty."}]
    st.rerun()

# --- 7. MAIN APP LOGIC ---

# CHECK LOGIN STATUS
if not st.session_state.user:
    show_branding()
    login_ui()
    st.stop()

# --- SIDEBAR LOGIC (Tools & History) ---
with st.sidebar:
    # User Profile Header
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px; padding: 10px; background: #0D1B2E; border-radius: 8px;">
        <div style="font-size: 24px; margin-right: 10px;">👤</div>
        <div>
            <div style="color: #00A6FF; font-weight: bold;">{st.session_state.user['name']}</div>
            <div style="color: #AAAAAA; font-size: 12px;">{st.session_state.user['email']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("✨ New Chat", use_container_width=True):
        create_new_chat()
    
    st.markdown("---")
    
    # --- POWER TOOLS ---
    st.markdown("### ⚡ Power Tools")
    
    # 1. Ultimate Mode
    st.toggle("🔥 JEEx Ultimate", key="ultimate_mode", help="Unlock advanced problem solving and deep conceptual analysis.")
    
    # 2. Mistake Analysis (NEW)
    st.toggle("⚠️ Mistake Analyzer", key="mistake_analysis_mode", help="AI actively hunts for your logic errors and misconceptions.")
    if st.session_state.mistake_analysis_mode:
        st.caption("🔍 Analyzer: Active")

    # 3. Deep Research
    st.toggle("🔬 Deep Research", key="deep_research_mode", help="Enable deep theoretical explanations and first-principles derivations.")

    st.markdown("---")

    # --- HISTORY SECTION (Google Account Synced) ---
    st.markdown("### 🗂️ Previous Sessions")
    user_sessions = db_get_user_sessions(st.session_state.user["email"])
    
    if not user_sessions:
        st.caption("No history found.")
    else:
        for sess in user_sessions:
            # Use a unique key for each button
            btn_label = f"{sess['title'][:20]}... ({sess['created_at'][:10]})"
            if st.button(btn_label, key=f"hist_{sess['session_id']}", use_container_width=True):
                load_chat(sess['session_id'])

    st.markdown("---")
    if st.button("Logout", use_container_width=True): 
        st.session_state.user = None
        st.session_state.messages = []
        st.session_state.current_session_id = None
        st.rerun()

# --- MAIN INTERFACE ---
show_branding()

# Initialize session if needed
if not st.session_state.current_session_id:
    create_new_chat()

# --- CHAT LOGIC ---
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
    
    # Handle File Metadata
    file_meta = None
    if st.session_state.current_uploaded_file:
        uf = st.session_state.current_uploaded_file
        file_meta = {"name": getattr(uf, "name", "file"), "type": getattr(uf, "type", "")}
        msg_data.update({"file_data": uf.getvalue(), "file_name": file_meta["name"], "file_type": file_meta["type"]})
    
    # Update Session Title based on first prompt if it's "New Chat"
    if len(st.session_state.messages) <= 1:
        new_title = prompt[:30] if len(prompt) > 30 else prompt
        db_update_session_title(st.session_state.current_session_id, new_title)

    # 1. Update UI State
    st.session_state.messages.append(msg_data)
    
    # 2. Save to DB
    db_save_message(st.session_state.current_session_id, "user", prompt, file_meta)
    
    st.rerun()

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=LOGO_URL if msg["role"]=="assistant" else "🧑‍🎓"):
        if "file_data" in msg:
            if str(msg["file_type"]).startswith("image"): st.image(msg["file_data"], width=200)
            else: st.markdown(f"📄 *{msg.get('file_name')}*")
        # Check if file info is in DB format (reloaded from history)
        elif "file_meta" in msg and msg["file_meta"]:
             st.markdown(f"📄 *{msg['file_meta'].get('name')}* (Attachment)")
             
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
            pass # Continue without file if upload fails
    
    try:
        client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=api_content, attachments=att if att else None)
        
        # --- ENHANCED BOT INSTRUCTIONS ---
        base_instructions = """
        You are JEEx, an expert JEE (Joint Entrance Examination) tutor.
        
        CORE RULES:
        1. STRICT JEE DOMAIN: Only answer Physics, Chem, Math. For off-topic, politely redirect.
        2. FORMAT: Use LaTeX ($...$ and $$...$$) for all math.
        3. VERIFY: Use python code interpreter for complex calculations.
        """

        # JEEx ULTIMATE INJECTION
        if st.session_state.ultimate_mode:
            base_instructions += """
            \n\n*** ULTRA MODE ACTIVATED ***
            1. Assume Top 100 Rank goal.
            2. Derive formulas from Calculus.
            3. Combine concepts from different chapters.
            """

        # DEEP RESEARCH INJECTION
        if st.session_state.deep_research_mode:
            base_instructions += """
            \n\n*** DEEP RESEARCH MODE ACTIVATED ***
            1. Derive from First Principles (Newton/Maxwell/Schrodinger).
            2. Explain the physical significance of every term.
            """
            
        # --- MISTAKE ANALYSIS INJECTION (NEW FEATURE) ---
        if st.session_state.mistake_analysis_mode:
            base_instructions += """
            \n\n*** MISTAKE ANALYSIS MODE: CRITICAL ***
            The user wants to find errors in their logic.
            1. Analyze the user's question/solution for conceptual gaps, sign errors, or calculation mistakes.
            2. If the user presents a solution, DO NOT just give the right answer. First, explicitly state: "Here is where you went wrong: [Explain Error]".
            3. Then, provide the correct derivation.
            4. Be strict but constructive. Identify if the error is Conceptual (Logic) or Silly (Calculation).
            """

        with st.chat_message("assistant", avatar=LOGO_URL):
            stream = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id, assistant_id=assistant_id, stream=True,
                additional_instructions=base_instructions,
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
            
            # 1. Update UI State
            st.session_state.messages.append({"role": "assistant", "content": full_text})
            # 2. Save to DB
            db_save_message(st.session_state.current_session_id, "assistant", full_text)
            
    except Exception as e:
        st.session_state.messages.append({"role": "assistant", "content": "⚠️ Network issue. Please try again."})
        logger.error(f"Error: {e}")
    
    # --- AUTO-REMOVE ATTACHMENT ---
    st.session_state.current_uploaded_file = None
    st.session_state.uploader_key += 1
    if 'audio_value' in locals() and audio_value: st.session_state.audio_key += 1
    st.session_state.processing = False
    st.rerun()

# --- ATTACHMENT AREA (Always Visible) ---
st.markdown("---")
st.markdown("**📎 Attach Question / 🎙️ Voice Chat**")

col_input1, col_input2 = st.columns([1, 1])

with col_input1:
    # File Uploader Logic
    if st.session_state.processing:
        st.markdown("_Locked while answering._")
    else:
        uploaded_file = st.file_uploader("Upload", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
        if uploaded_file:
            st.session_state.current_uploaded_file = uploaded_file
            st.success(f"Attached: {uploaded_file.name}")

with col_input2:
     st.audio_input("Speak", key=f"audio_{st.session_state.audio_key}", label_visibility="collapsed")
