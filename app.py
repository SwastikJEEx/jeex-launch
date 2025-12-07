import streamlit as st
import time
from openai import OpenAI

# --- 1. CONFIG & SECURITY ---
st.set_page_config(page_title="JEEx", page_icon="⚛️", layout="centered")
# --- CUSTOM LIGHT THEME & LOGO ---
st.markdown("""
<style>
    /* 1. Main Background (White) */
    .stApp {
        background-color: #FFFFFF;
        color: #0E1117; /* Dark text for contrast */
    }
    
    /* 2. Chat Bubbles */
    /* User Message (Light Blue) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #E8F0FE;
        border: 1px solid #D0E0FD;
        color: #0E1117;
        border-radius: 12px;
    }
    /* Bot Message (Off-White/Gray) */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #F8F9FA;
        border: 1px solid #E9ECEF;
        color: #0E1117;
        border-radius: 12px;
    }
    
    /* 3. Sidebar Design (Light Gray) */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E9ECEF;
    }
    
    /* 4. Input Box */
    .stChatInputContainer textarea {
        background-color: #FFFFFF;
        color: #0E1117;
        border: 1px solid #CED4DA;
    }
    
    /* 5. Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)
# Hide source code menu
st.markdown("""
<style>
    .stDeployButton {display:none;}
    #MainMenu {display: none;}
</style>
""", unsafe_allow_html=True)

# --- FUNCTION TO CHECK KEYS ---
def is_valid_key(user_key):
    # 1. Check Master Key (For you)
    if user_key == st.secrets.get("MASTER_KEY"):
        return True
    
    # 2. Check the pattern "JEExa0001" to "JEExa1000"
    # Format must be exactly 9 characters long
    if len(user_key) != 9:
        return False
    
    # Must start with "JEExa"
    prefix = user_key[:5] # First 5 letters
    if prefix != "JEExa":
        return False
        
    # Last 4 characters must be numbers
    number_part = user_key[5:] # The "0001" part
    if not number_part.isdigit():
        return False
        
    # Check if number is between 1 and 1000
    number = int(number_part)
    if 1 <= number <= 1000:
        return True
        
    return False

# --- 2. SIDEBAR (LOGIN) ---
with st.sidebar:
    # --- 2. SIDEBAR (LOGIN) ---
with st.sidebar:
    # Add the logo at the top of the sidebar
    st.image("logo.png", use_column_width=True)
    
    # The title goes below the logo now
    st.markdown("<h2 style='text-align: center;'>Premium Access</h2>", unsafe_allow_html=True)
    
    # ... rest of your sidebar code (user_key, etc.) follows here ...
    
    user_key = st.text_input("Enter Access Key:", type="password")
    
    # YOUR PAYMENT LINK
    payment_link = "https://razorpay.me/YOUR_LINK" 
    
    # Validate the key using our smart function
    if not is_valid_key(user_key):
        if user_key: # Only show warning if they actually typed something
            st.error("⛔ Invalid Key")
        st.warning("🔒 Chat Locked")
        st.markdown(f"**Get a Key:** [**Subscribe (₹99)**]({payment_link})")
        st.stop() # Stops app here

    st.success(f"✅ Access Granted")
    if st.button("Logout"):
        st.rerun()

# --- 3. MAIN APP ---
st.title("JEEx ⚛️")

# Load Credentials
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    assistant_id = st.secrets["ASSISTANT_ID"]
except:
    st.error("🚨 Keys missing in secrets.toml")
    st.stop()

client = OpenAI(api_key=api_key)

# Initialize Chat
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "I am JEEx. Ready to solve."})

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Ask a doubt..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id, role="user", content=prompt
    )

    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id, assistant_id=assistant_id
    )

    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.markdown("Thinking... ⏳")
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id, run_id=run.id
            )
        
        if run.status == 'completed':
            status_box.empty()
            messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            full_response = messages.data[0].content[0].text.value
            st.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})


