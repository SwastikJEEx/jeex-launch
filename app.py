import streamlit as st
import time
from openai import OpenAI

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx", page_icon="⚛️", layout="centered")

# --- 2. PROFESSIONAL LIGHT THEME CSS ---
st.markdown("""
<style>
    /* Force Light Theme Colors */
    .stApp {
        background-color: #FFFFFF;
        color: #000000 !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E0E0E0;
    }
    
    /* Text Visibility Fixes */
    h1, h2, h3, p, div, label, span {
        color: #0E1117 !important;
    }
    
    /* --- GREY INPUT BOX (Password) --- */
    [data-testid="stSidebar"] [data-testid="stTextInput"] input {
        background-color: #E9ECEF !important;
        color: #000000 !important;
        border: 1px solid #CED4DA !important;
    }
    
    /* --- GREY RESPONSIVE BUTTON (End Session) --- */
    div.stButton > button {
        background-color: #6C757D !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        background-color: #5A6268 !important;
        transform: scale(1.02);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Chat Message Bubbles */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #E8F0FE;
        border: 1px solid #D0E0FD;
        border-radius: 12px;
        padding: 15px;
    }
    
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #F8F9FA;
        border: 1px solid #E9ECEF;
        border-radius: 12px;
        padding: 15px;
    }
    
    /* Input Box Styling */
    .stChatInputContainer textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
    }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Success Message Style */
    .stSuccess {
        background-color: #D4EDDA !important;
        color: #155724 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SMART KEY LOGIC ---
def check_smart_key(user_key):
    # 1. Check Master Key (For you)
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"):
        return True
    
    # 2. Check "White List" from Secrets
    valid_list = st.secrets.get("VALID_KEYS", [])
    if user_key in valid_list:
        return True

    # 3. Check Pattern "JEExa0001" to "JEExa1000"
    if len(user_key) != 9:
        return False
    
    prefix = user_key[:5] # "JEExa"
    if prefix != "JEExa":
        return False
        
    number_part = user_key[5:] # "0001"
    if not number_part.isdigit():
        return False
        
    number = int(number_part)
    if 1 <= number <= 1000:
        return True
        
    return False

# --- 4. SIDEBAR (LOGIN SYSTEM) ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    st.markdown("---")
    
    # Input Box
    user_key = st.text_input("Enter Access Key:", type="password", help="Check your email for the key.")
    
    # Validation
    if not check_smart_key(user_key):
        st.warning("🔒 Chat Locked")
        st.info("Please enter a valid key to start.")
        
        # --- NEW PAYMENT LINK HERE ---
        payment_link = "https://rzp.io/rzp/wXI8i7t"
        
        st.markdown(f"""
            <a href="{payment_link}" target="_blank">
                <button style="
                    width:100%; 
                    background-color:#007BFF; 
                    color:white; 
                    border:none; 
                    padding:10px; 
                    border-radius:5px; 
                    cursor:pointer;
                    font-weight: bold;">
                    👉 Subscribe Now (₹99)
                </button>
            </a>
            """, unsafe_allow_html=True)
        
        # --- TERMS AND CONDITIONS (Visible for non-users too) ---
        st.markdown("---")
        with st.expander("📄 Terms & Conditions"):
            st.markdown("""
            **JEEx Usage Policy:**
            1. **Accuracy:** AI may occasionally make errors. Use as a study companion, not the sole source of truth.
            2. **Personal Use:** Keys are for single users only. Sharing keys will result in a permanent ban.
            3. **No Refunds:** As this is a digital product, all sales are final once the key is delivered.
            4. **Liability:** We are not responsible for exam results or service interruptions.
            """)
            
        st.stop() # STOP EVERYTHING HERE if key is invalid

    # If code reaches here, the Key is Valid
    st.success(f"✅ Active: {user_key}")
    
    # Reset Button
    if st.button("End Session"):
        st.rerun()
        
    # --- TERMS AND CONDITIONS (Visible for logged-in users) ---
    st.markdown("---")
    with st.expander("📄 Terms & Conditions"):
        st.markdown("""
        **JEEx Usage Policy:**
        1. **Accuracy:** AI may occasionally make errors. Use as a study companion.
        2. **Personal Use:** Keys are for single users only. Sharing keys leads to a ban.
        3. **No Refunds:** All sales are final.
        """)

# --- 5. MAIN CHAT APP ---
st.markdown("# ⚛️ **JEEx** <span style='color:#007BFF; font-size:0.6em'>PRO</span>", unsafe_allow_html=True)
st.caption("Your Personal AI Tutor for JEE Mains & Advanced | Powered by OpenAI")

# Load Secrets
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    assistant_id = st.secrets["ASSISTANT_ID"]
except:
    st.error("🚨 Configuration Error: API Keys are missing in Streamlit Secrets.")
    st.stop()

# Initialize Client
client = OpenAI(api_key=api_key)

# Initialize Session State
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []
    # Initial Greeting
    st.session_state.messages.append({"role": "assistant", "content": "Welcome back. I am ready to solve complex problems. What is your doubt today?"})

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input & Response Logic
if prompt := st.chat_input("Ask a doubt (e.g., Rotational Motion, Organic Chemistry)..."):
    
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Send to OpenAI
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id, role="user", content=prompt
    )

    # 3. Trigger Assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id, assistant_id=assistant_id
    )

    # 4. Wait for Answer
    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.markdown("**Thinking...** ⏳")
        
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id, run_id=run.id
            )
        
        if run.status == 'completed':
            status_box.empty()
            messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            # Get latest text
            full_response = messages.data[0].content[0].text.value
            st.markdown(full_response)
            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
