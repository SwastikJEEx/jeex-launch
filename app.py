import streamlit as st
import time
from openai import OpenAI
import os

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
    .katex { font-size: 1.1em; color: #FFD700 !important; } /* Gold color for Math formulas */
    
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

# --- 3. SMART KEY LOGIC ---
def check_smart_key(user_key):
    if user_key == st.secrets.get("MASTER_KEY", "JEEx-ADMIN-ACCESS"): return True
    if user_key in st.secrets.get("VALID_KEYS", []): return True
    if len(user_key) != 9 or user_key[:5] != "JEExa" or not user_key[5:].isdigit(): return False
    return 1 <= int(user_key[5:]) <= 1000

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    user_key = st.text_input("Enter Access Key:", type="password")
    
    if not check_smart_key(user_key):
        st.warning("🔒 Chat Locked")
        payment_link = "https://rzp.io/rzp/wXI8i7t" 
        st.markdown(f'<a href="{payment_link}" target="_blank"><button style="background-color:#4A90E2; color:white; border:none; padding:10px; border-radius:5px; width:100%; font-weight:bold;">👉 Subscribe (₹99)</button></a>', unsafe_allow_html=True)
        st.stop()

    st.success(f"✅ Active: {user_key}")
    if st.button("End Session"): st.rerun()

# --- 5. MAIN APP ---
st.markdown("# ⚛️ **JEEx** <span style='color:#4A90E2; font-size:0.6em'>PRO</span>", unsafe_allow_html=True)
st.caption("Upload Questions (Image/PDF) | Powered by OpenAI Vision")

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
    st.session_state.messages = [{"role": "assistant", "content": "I am ready. Upload a PDF or Image, or just ask a doubt."}]
    st.session_state.uploader_key = 0

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. INPUT AREA ---
col1, col2 = st.columns([0.1, 0.9])

with col1:
    with st.popover("📎", help="Attach File"):
        # UPDATED: Allows PDF now
        uploaded_file = st.file_uploader(
            "Upload File", 
            type=["jpg", "png", "jpeg", "pdf"], 
            key=f"uploader_{st.session_state.uploader_key}"
        )

with col2:
    prompt = st.chat_input("Ask a doubt...")

# --- 7. HANDLING SEND ---
if prompt:
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file:
            # Show small preview if it's an image, or just filename if PDF
            if uploaded_file.type == "application/pdf":
                st.markdown(f"📄 *Attached PDF: {uploaded_file.name}*")
            else:
                st.image(uploaded_file, caption="Attached Image", width=200)

    # 2. Prepare Message Content
    message_content = [{"type": "text", "text": prompt}]
    attachments = [] # List to hold file IDs for tools

    # 3. Handle File Upload
    if uploaded_file:
        with st.spinner("Processing file..."):
            try:
                # Save temp file
                temp_filename = f"temp_{uploaded_file.name}"
                with open(temp_filename, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Upload to OpenAI
                file_response = client.files.create(
                    file=open(temp_filename, "rb"),
                    purpose="assistants" # Important for PDFs
                )
                
                # LOGIC: Check if PDF or Image
                if uploaded_file.type == "application/pdf":
                    # For PDF -> Attach for Code Interpreter to read
                    attachments.append({
                        "file_id": file_response.id,
                        "tools": [{"type": "code_interpreter"}]
                    })
                else:
                    # For Image -> Use Vision
                    message_content.append({
                        "type": "image_file",
                        "image_file": {"file_id": file_response.id}
                    })
                
                # Cleanup
                os.remove(temp_filename)
                
            except Exception as e:
                st.error(f"Upload failed: {e}")

    # 4. Send to Thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=message_content,
        attachments=attachments if attachments else None
    )

    # 5. Run Assistant (WITH MATH FIX INSTRUCTIONS)
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id,
        # THIS LINE FIXES THE MATH FORMATTING AND DOTS ISSUE
        additional_instructions="""
        IMPORTANT: You are a JEE Tutor. 
        1. Format ALL mathematical equations using LaTeX. 
        2. Use SINGLE dollar signs for inline math: $x^2$. 
        3. Use DOUBLE dollar signs for block math: $$x^2$$. 
        4. Do NOT use brackets \( \) or \[ \] for math. 
        5. Do not use bold/italics for variables, strictly use LaTeX.
        """
    )

    # 6. Wait for Answer
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
            full_response = messages.data[0].content[0].text.value
            
            # Show cleaned response
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Reset Uploader
            st.session_state.uploader_key += 1
            st.rerun()
