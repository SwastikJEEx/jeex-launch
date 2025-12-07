import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx", page_icon="⚛️", layout="centered", initial_sidebar_state="expanded")

# --- 2. PROFESSIONAL DARK THEME CSS ---
st.markdown("""
<style>
    /* Base Theme */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #161B26; border-right: 1px solid #2B313E; }
    
    /* Text & Math Visibility */
    h1, h2, h3, p, div, label, span, li { color: #E6E6E6 !important; }
    .katex { font-size: 1.1em; color: #FFD700 !important; } 
    
    /* Inputs */
    .stTextInput input, .stTextArea textarea { 
        background-color: #1E2330 !important; 
        color: white !important; 
        border: 1px solid #3E4654 !important; 
    }
    
    /* Buttons */
    div.stButton > button { 
        background-color: #2B313E !important; 
        color: white !important; 
        border: 1px solid #3E4654 !important; 
        width: 100%; 
    }
    div.stButton > button:hover { border-color: #4A90E2 !important; }
    
    /* Chat Bubbles */
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1E2330; border: 1px solid #2B313E; border-radius: 12px; }
    [data-testid="stChatMessage"]:nth-child(even) { background-color: #131720; border: 1px solid #2B313E; border-radius: 12px; }
    
    /* Hide Menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Sidebar Attachment Style */
    [data-testid="stFileUploader"] {
        padding: 0px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. MATH CLEANING FUNCTION ---
def clean_latex(text):
    if not text: return ""
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\\)\[\s*(.*?=.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    return text

# --- 4. SHOW TITLE & EPIC TAGLINE ---
st.markdown("# ⚛️ **JEEx** <span style='color:#4A90E2; font-size:0.6em'>PRO</span>", unsafe_allow_html=True)
st.caption("Your 24/7 AI Rank Booster | Master JEE Mains & Advanced with Precision 🚀")

# --- 5. LOGOUT LOGIC ---
if st.session_state.get('logout', False):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 6. SMART KEY LOGIC (WITH EXPIRY) ---
def check_key_status(user_key):
    # 1. Check Master Key
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"): 
        return "VALID"

    # 2. Check Expiry Date
    expiry_db = st.secrets.get("KEY_EXPIRY", {})
    if user_key in expiry_db:
        try:
            expiry_date = datetime.strptime(expiry_db[user_key], "%Y-%m-%d").date()
            if datetime.now().date() > expiry_date:
                return "EXPIRED"
        except:
            pass 

    # 3. Check Whitelist
    if user_key in st.secrets.get("VALID_KEYS", []): 
        return "VALID"

    # 4. Check Pattern "JEExa0001"
    if len(user_key) != 9 or user_key[:5] != "JEExa" or not user_key[5:].isdigit(): 
        return "INVALID"
    if 1 <= int(user_key[5:]) <= 1000: 
        return "VALID"
        
    return "INVALID"

# --- 7. SIDEBAR (LOGIN & PAYMENT) ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
        
    user_key = st.text_input("Enter Access Key:", type="password")
    
    # Check Status
    status = check_key_status(user_key)
    
    # IF KEY IS INVALID/EXPIRED, SHOW PAYMENT OPTIONS IN SIDEBAR
    if status != "VALID":
        if status == "EXPIRED":
            st.error("⚠️ Plan Expired")
            btn_text = "👉 Renew Now (₹99)"
        else:
            if user_key: st.warning("🔒 Chat Locked")
            btn_text = "👉 Subscribe for ₹99 / Month"
            
        payment_link = "https://pages.razorpay.com/pl_Hk7823hsk" # Your Page Link
        
        st.markdown(f"""
            <a href="{payment_link}" target="_blank">
                <button style="
                    width:100%; 
                    background-color:#4A90E2; 
                    color:white; 
                    border:none; 
                    padding:10px; 
                    border-radius:5px; 
                    cursor:pointer;
                    font-weight: bold;
                    font-size: 15px;">
                    {btn_text}
                </button>
            </a>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("📄 Terms & Conditions"):
             st.markdown("""
            **JEEx Usage Policy:**
            1. **Accuracy:** AI may make errors. Verify data.
            2. **Personal Use:** Keys are for single users only.
            3. **No Refunds:** All sales are final.
            """)

# --- 8. MAIN AREA LOGIC ---

# SCENARIO A: USER IS LOCKED (Show Landing Page in Center)
if status != "VALID":
    st.markdown("---")
    
    # 1. INSTRUCTION BOX (Cleaned Up)
    st.markdown("""
    <div style="background-color: #1E2330; padding: 20px; border-radius: 10px; border-left: 5px solid #4A90E2; margin-bottom: 30px;">
        <p style="font-size: 18px; margin: 0; color: #E6E6E6;">
            👋 <strong>Welcome Student!</strong><br>
            Please enter your <strong>Access Key</strong> in the Sidebar (↖️ Top Left) to unlock the AI.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 2. PROFESSIONAL FEATURE LIST (Fixed Formatting)
    st.markdown("""
    <div style="background-color: #161B26; padding: 30px; border-radius: 15px; border: 1px solid #2B313E; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <h2 style="color: #4A90E2; margin-top: 0; font-size: 26px; border-bottom: 1px solid #3E4654; padding-bottom: 15px; margin-bottom: 20px;">
            🏆 Why Top Rankers Choose JEEx Pro
        </h2>
        
        <ul style="list-style-type: none; padding-left: 0; margin: 0;">
            
            <li style="margin-bottom: 20px;">
                <strong style="color: #FFD700; font-size: 20px;">🧠 Advanced Problem Solving</strong><br>
                <span style="font-size: 17px; color: #CCCCCC; line-height: 1.6;">
                    Instantly solves Irodov, Cengage, and PYQ level problems with step-by-step logic.
                </span>
            </li>
            
            <li style="margin-bottom: 20px;">
                <strong style="color: #FFD700; font-size: 20px;">👁️ Vision Intelligence (OCR)</strong><br>
                <span style="font-size: 17px; color: #CCCCCC; line-height: 1.6;">
                    Stuck on a handwritten question? Just upload a photo. JEEx reads and solves it.
                </span>
            </li>
            
            <li style="margin-bottom: 20px;">
                <strong style="color: #FFD700; font-size: 20px;">📄 Full Document Analysis</strong><br>
                <span style="font-size: 17px; color: #CCCCCC; line-height: 1.6;">
                    Upload entire PDF assignments or test papers. Analyzes full document context.
                </span>
            </li>
            
            <li style="margin-bottom: 20px;">
                <strong style="color: #FFD700; font-size: 20px;">➗ Perfect Math Formatting</strong><br>
                <span style="font-size: 17px; color: #CCCCCC; line-height: 1.6;">
                    Powered by LaTeX to render complex integrals, matrices, and equations with precision.
                </span>
            </li>
            
            <li style="margin-bottom: 10px;">
                <strong style="color: #FFD700; font-size: 20px;">⚡ 24/7 Personal Mentorship</strong><br>
                <span style="font-size: 17px; color: #CCCCCC; line-height: 1.6;">
                    Your AI Tutor never sleeps. Clear backlogs and doubts at 3 AM.
                </span>
            </li>
            
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.stop() # ⛔ THIS STOPS THE APP HERE SO THEY CAN'T SEE CHAT

# SCENARIO B: USER IS UNLOCKED (Show Chat Interface)

# Sidebar Tools (Only visible when unlocked)
with st.sidebar:
    st.success(f"✅ Active: {user_key}")
    st.markdown("---")
    st.markdown("### 📎 Attach Question")
    uploaded_file = st.file_uploader(
        "Upload Image or PDF", 
        type=["jpg", "png", "jpeg", "pdf"], 
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed"
    )
    if uploaded_file:
        st.info(f"Attached: {uploaded_file.name}")
    
    st.markdown("---")
    if st.button("End Session"):
        st.session_state['logout'] = True
        st.rerun()

# Main Chat Logic
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    assistant_id = st.secrets["ASSISTANT_ID"]
except:
    st.error("🚨 Keys missing in Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    welcome_msg = "Welcome Champ! 🎓 Main hoon JEEx. JEE ki journey mushkil hai par main tumhare saath hoon. \n\nKoi bhi doubt ho—Physics ka numerical, Chemistry ka reaction, ya Maths ka integral—bas photo bhejo ya type karo. Chalo phodte hain! 🚀"
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(clean_latex(msg["content"]))

# Input Area
prompt = st.chat_input("Ask a doubt...")

# Handling Send
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                st.markdown(f"📄 *Attached PDF: {uploaded_file.name}*")
            else:
                st.image(uploaded_file, caption="Attached Image", width=200)

    message_content = [{"type": "text", "text": prompt}]
    attachments = [] 

    if uploaded_file:
        with st.spinner("Processing file..."):
            try:
                temp_filename = f"temp_{uploaded_file.name}"
                with open(temp_filename, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                file_response = client.files.create(
                    file=open(temp_filename, "rb"),
                    purpose="assistants"
                )
                
                if uploaded_file.type == "application/pdf":
                    attachments.append({
                        "file_id": file_response.id,
                        "tools": [{"type": "code_interpreter"}]
                    })
                else:
                    message_content.append({
                        "type": "image_file",
                        "image_file": {"file_id": file_response.id}
                    })
                os.remove(temp_filename)
            except Exception as e:
                st.error(f"Upload failed: {e}")

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=message_content,
        attachments=attachments if attachments else None
    )

    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id,
        additional_instructions="""
        IMPORTANT:
        1. MATH: Use LaTeX ($x^2$ or $$x^2$$). DO NOT use \[ or \(.
        2. PDF: Use 'code_interpreter' to read PDFs immediately.
        """
    )

    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.markdown("**Solving...** ⏳")
        
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id, run_id=run.id
            )
        
        if run.status == 'completed':
            status_box.empty()
            messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            final_response = clean_latex(messages.data[0].content[0].text.value)
            
            st.markdown(final_response)
            st.session_state.messages.append({"role": "assistant", "content": final_response})
            st.session_state.uploader_key += 1
            st.rerun()
