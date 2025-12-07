import streamlit as st
import time
from openai import OpenAI
import os
import re

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
    
    /* Attachment Button Style */
    [data-testid="stPopover"] > div > button {
        border: none !important;
        background: transparent !important;
        font-size: 1.5rem !important;
        padding: 0px !important;
        margin-top: 5px !important;
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
# NEW: Professional & Epic Tagline
st.caption("Your 24/7 AI Rank Booster | Master JEE Mains & Advanced with Precision 🚀")

# --- 5. LOGOUT LOGIC ---
if st.session_state.get('logout', False):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 6. SMART KEY LOGIC ---
def check_smart_key(user_key):
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"): return True
    if user_key in st.secrets.get("VALID_KEYS", []): return True
    if len(user_key) != 9 or user_key[:5] != "JEExa" or not user_key[5:].isdigit(): return False
    return 1 <= int(user_key[5:]) <= 1000

# --- 7. SIDEBAR (LOGIN) ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    user_key = st.text_input("Enter Access Key:", type="password")
    
    # DETAILED TERMS & CONDITIONS TEXT
    terms_text = """
    **JEEx Terms of Service**
    
    **1. Usage Policy**
    * **AI Limitations:** JEEx is an AI-powered tool. While highly accurate, it can occasionally make errors ("hallucinations"). Always verify critical data with NCERT/Standard Textbooks.
    * **Fair Use:** This key is for **Personal Use Only**.
    
    **2. Security & Bans**
    * **Zero Sharing Policy:** Sharing your Access Key with friends, Telegram groups, or public forums is strictly prohibited.
    * **Automatic Ban:** Our system detects simultaneous logins. If multiple IPs use the same key, it will be **permanently banned** without warning.
    
    **3. Payments & Refunds**
    * **Final Sale:** As this is a digital access product, all sales are final. **No refunds** will be issued once the key is delivered.
    * **Validity:** Subscription is valid for 30 days from the date of purchase.
    
    **4. Liability**
    * JEEx is not responsible for exam results, rank outcomes, or service interruptions caused by third-party API outages.
    """

    if not check_smart_key(user_key):
        st.warning("🔒 Chat Locked")
        payment_link = "https://rzp.io/rzp/wXI8i7t" 
        st.markdown(f'<a href="{payment_link}" target="_blank"><button style="background-color:#4A90E2; color:white; border:none; padding:10px; border-radius:5px; width:100%; font-weight:bold;">👉 Subscribe (₹99)</button></a>', unsafe_allow_html=True)
        
        # T&C for non-logged in users
        st.markdown("---")
        with st.expander("📄 Terms & Conditions (Read Carefully)"):
            st.markdown(terms_text)
        st.stop()

    st.success(f"✅ Active: {user_key}")
    
    if st.button("End Session"):
        st.session_state['logout'] = True
        st.rerun()
        
    # T&C for logged in users
    st.markdown("---")
    with st.expander("📄 Terms & Conditions"):
        st.markdown(terms_text)

# --- 8. MAIN APP LOGIC ---
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
    # NEW: Friendly Hinglish Starting Message
    welcome_msg = "Welcome Champ! 🎓 Main hoon JEEx. JEE ki journey mushkil hai par main tumhare saath hoon. \n\nKoi bhi doubt ho—Physics ka numerical, Chemistry ka reaction, ya Maths ka integral—bas photo bhejo ya type karo. Chalo phodte hain! 🚀"
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
    st.session_state.uploader_key = 0

# Display History (Cleaned)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(clean_latex(msg["content"]))

# --- 9. INPUT AREA ---
col1, col2 = st.columns([0.1, 0.9])

with col1:
    with st.popover("📎", help="Attach File"):
        uploaded_file = st.file_uploader(
            "Upload File", 
            type=["jpg", "png", "jpeg", "pdf"], 
            key=f"uploader_{st.session_state.uploader_key}"
        )

with col2:
    prompt = st.chat_input("Ask a doubt...")

# --- 10. HANDLING SEND ---
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
