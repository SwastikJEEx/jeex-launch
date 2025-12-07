import streamlit as st
import time
from openai import OpenAI

# --- 1. CONFIG & SECURITY ---
st.set_page_config(page_title="JEEx", page_icon="⚛️", layout="centered")
# --- CUSTOM THEME (Dark & Professional) ---
st.markdown("""
<style>
    /* 1. Main Background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* 2. Chat Bubbles */
    /* User Message (Blue) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #1E2330;
        border: 1px solid #2B313E;
        border-radius: 12px;
    }
    /* Bot Message (Darker Grey) */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #131720;
        border: 1px solid #2B313E;
        border-radius: 12px;
    }
    
    /* 3. Sidebar Design */
    [data-testid="stSidebar"] {
        background-color: #161B26;
        border-right: 1px solid #2B313E;
    }
    
    /* 4. Input Box */
    .stChatInputContainer textarea {
        background-color: #1E2330;
        color: white;
        border: 1px solid #3E4654;
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
# --- 2. SIDEBAR (LOGIN) ---
with st.sidebar:
    # 1. LOGO & TITLE (Indented 4 spaces)
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.warning("Logo not found. Upload logo.png to GitHub.")
        
    st.markdown("<h2 style='text-align: center;'>Premium Access</h2>", unsafe_allow_html=True)
    
    # 2. INPUT BOX (Indented 4 spaces)
    user_key = st.text_input("Enter Access Key:", type="password")
    
    payment_link = "https://razorpay.me/YOUR_LINK" 
    
    # 3. CHECK KEYS (Indented 4 spaces)
    # Get the valid keys list (Default to empty if missing)
    valid_keys = st.secrets.get("VALID_KEYS", [])
    master_key = st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS")
    
    # Check if key is valid (Master Key OR Student Key)
    is_valid = (user_key == master_key) or (user_key in valid_keys)
    
    if not is_valid:
        if user_key: # Only show error if they typed something
            st.error("⛔ Invalid Key")
        
        st.warning("🔒 Chat Locked")
        st.markdown(f"**Need a key?** [**Subscribe Here**]({payment_link})")
        st.stop() # This STOPS the app here if key is wrong.

    # 4. SUCCESS MESSAGE (Indented 4 spaces)
    st.success(f"✅ Welcome, Student!")
    
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




