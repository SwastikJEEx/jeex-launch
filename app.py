import streamlit as st
import time
from openai import OpenAI

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx", page_icon="⚛️", layout="centered")

# --- 2. PROFESSIONAL LIGHT THEME CSS ---


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
    
    # Input Box (Now Grey due to CSS above)
    user_key = st.text_input("Enter Access Key:", type="password", help="Check your email for the key.")
    
    # Validation
    if not check_smart_key(user_key):
        st.warning("🔒 Chat Locked")
        st.info("Please enter a valid key to start.")
        
        # Payment Link Button
        payment_link = "https://razorpay.me/YOUR_LINK"
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
        st.stop() # STOP EVERYTHING HERE if key is invalid

    # If code reaches here, the Key is Valid
    st.success(f"✅ Active: {user_key}")
    
    # Reset Button (Now Grey & Responsive)
    if st.button("End Session"):
        st.rerun()

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

