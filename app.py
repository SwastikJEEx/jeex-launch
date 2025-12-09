import streamlit as st
import datetime
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="JEEx - Advanced JEE Bot",
    page_icon="⚛️",
    layout="centered"
)

# --- Custom CSS (Professional Blue & Dark Theme) ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
        color: #C9D1D9;
    }
    
    /* Login Screen Styling */
    .login-container {
        text-align: center;
        margin-top: 50px;
        padding: 40px;
        background-color: #161B22;
        border-radius: 10px;
        border: 1px solid #30363D;
    }

    /* JEEx Title Styling */
    .jeex-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
    }
    
    /* Subtitle Styling */
    .jeex-subtitle {
        font-size: 1.2rem;
        color: #8B949E;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    
    /* 'PRO' Badge - Professional Blue */
    .pro-badge {
        background-color: #4A90E2; 
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        vertical-align: super;
    }

    /* Chat Message Styling */
    .chat-message {
        padding: 1.5rem; 
        border-radius: 0.5rem; 
        margin-bottom: 1rem; 
        display: flex;
        flex-direction: row;
        align-items: flex-start;
    }
    .chat-message.user {
        background-color: #161B22;
        border: 1px solid #30363D;
    }
    .chat-message.bot {
        background-color: #1F242C;
        border: 1px solid #30363D;
    }
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        font-weight: bold;
    }
    .chat-message.user .avatar {
        background-color: #238636;
        color: white;
    }
    .chat-message.bot .avatar {
        background-color: #1F6FEB;
        color: white;
    }
    .chat-message .content {
        flex-grow: 1;
        color: #E6EDF3;
    }

    /* Form Inputs */
    input[type=text], input[type=email], textarea, input[type=password] {
        width: 100%;
        padding: 12px;
        border: 1px solid #30363D;
        border-radius: 6px;
        background-color: #0D1117;
        color: white;
        margin-top: 6px;
        margin-bottom: 16px;
    }
    
    /* Buttons */
    button[type=submit], .stButton>button {
        background-color: #238636;
        color: white;
        padding: 12px 20px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: bold;
        width: 100%;
        transition: background-color 0.3s;
    }
    button[type=submit]:hover, .stButton>button:hover {
        background-color: #2EA043;
    }
    
    /* Pricing Tags */
    .price-tag {
        font-size: 1.1rem;
        font-weight: bold;
        color: #E6EDF3;
    }
    .slashed-price {
        text-decoration: line-through;
        color: #8B949E;
        font-size: 0.9rem;
        margin-right: 8px;
    }
    .actual-price {
        color: #4A90E2; 
        font-size: 1.2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Authentication Logic ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        entered_key = st.session_state["password"]
        
        # 1. Check if key is in the valid range format (JEExa0001 - JEExa9999)
        # Length must be 9 (JEExa + 4 digits)
        if entered_key.startswith("JEExa") and len(entered_key) == 9:
            
            # 2. Check if the key exists in secrets.toml (Activation Check)
            if entered_key in st.secrets["passwords"]:
                expiry_str = st.secrets["passwords"][entered_key]
                expiry_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d").date()
                
                # 3. Check Date Validity
                if datetime.date.today() <= expiry_date:
                    st.session_state["password_correct"] = True
                    # Remove password from session state for security
                    del st.session_state["password"]
                else:
                    st.session_state["password_correct"] = False
                    st.error(f"❌ Key Expired. This plan ended on {expiry_str}.")
            else:
                st.session_state["password_correct"] = False
                st.error("❌ Key Not Activated. Please purchase a plan to activate this key.")
        else:
            st.session_state["password_correct"] = False
            st.error("❌ Invalid Key Format. (Example: JEExa0001)")

    # Initialize Session State
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # Show Login Input if not logged in
    if not st.session_state["password_correct"]:
        st.markdown('<h1 class="jeex-title">JEEx <span class="pro-badge">LOGIN</span></h1>', unsafe_allow_html=True)
        st.write("")
        st.text_input(
            "Enter your JEEx Access Key", 
            type="password", 
            on_change=password_entered, 
            key="password",
            placeholder="Ex: JEExa0001"
        )
        st.caption("Keys are disabled by default until a plan is purchased.")
        return False
    
    return True

# --- MAIN APP EXECUTION ---
if check_password():
    
    # --- Header ---
    st.markdown('<h1 class="jeex-title">JEEx <span class="pro-badge">PRO</span></h1>', unsafe_allow_html=True)
    st.markdown('<p class="jeex-subtitle">Your Advanced AI Companion for JEE Prep</p>', unsafe_allow_html=True)

    # --- Sidebar / Premium Section ---
    with st.sidebar:
        st.header("💎 Upgrade Plan")
        st.write("Need to extend your validity or unlock new features?")
        
        with st.expander("Get Premium (Select Plan)", expanded=True):
            st.write("### Choose your Plan")
            
            # Plan Data Dictionary
            plans = {
                "Weekly": {
                    "name": "JEEx PRO Weekly",
                    "slashed": "₹49",
                    "price": "₹29",
                    "link": "https://topmate.io/jeexpro/1840366"
                },
                "Monthly": {
                    "name": "JEEx PRO Monthly",
                    "slashed": "₹99",
                    "price": "₹59",
                    "link": "https://topmate.io/jeexpro/1840721"
                },
                "3 Months": {
                    "name": "JEEx PRO 3 Month",
                    "slashed": "₹199",
                    "price": "₹159",
                    "link": "https://topmate.io/jeexpro/1840723"
                },
                "6 Months": {
                    "name": "JEEx PRO 6 Month",
                    "slashed": "₹349",
                    "price": "₹279",
                    "link": "https://topmate.io/jeexpro/1840732"
                }
            }
            
            # Formatting options for radio button
            plan_options = list(plans.keys())
            def format_plan_label(option):
                p = plans[option]
                return f"{option}: {p['price']} (was {p['slashed']})"

            selected_option = st.radio(
                "Select Validity:",
                plan_options,
                format_func=format_plan_label
            )
            
            selected_plan = plans[selected_option]
            
            # Display Plan Details
            st.markdown("---")
            st.markdown(f"**Plan:** {selected_plan['name']}")
            st.markdown(
                f'<span class="price-tag"><span class="slashed-price">{selected_plan["slashed"]}</span> <span class="actual-price">{selected_plan["price"]}</span></span>', 
                unsafe_allow_html=True
            )
            st.caption("Fill the form to proceed.")

            # --- HTML FORM (Fixed Email) ---
            contact_form = f"""
            <form action="https://formsubmit.co/jeexaipro@gmail.com" method="POST">
                <input type="hidden" name="_captcha" value="false">
                <input type="hidden" name="_template" value="table">
                <input type="hidden" name="_subject" value="New JEEx PRO Subscription Request">
                <input type="hidden" name="_next" value="{selected_plan['link']}">
                
                <input type="hidden" name="Selected_Plan" value="{selected_plan['name']} - {selected_plan['price']}">

                <label for="name">Full Name</label>
                <input type="text" name="name" placeholder="Swastik" required>
                
                <label for="email">Email Address</label>
                <input type="email" name="email" placeholder="swastik@example.com" required>
                
                <label for="message">Specific Requirements?</label>
                <textarea name="message" placeholder="I need help with Physics..." rows="2"></textarea>
                
                <button type="submit">Proceed to Pay {selected_plan['price']}</button>
            </form>
            """
            st.markdown(contact_form, unsafe_allow_html=True)
            # --- HTML FORM END ---

    # --- Chat Interface ---
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am JEEx PRO. Access granted. How can I help you crack JEE Advanced today?"}
        ]

    for message in st.session_state.messages:
        role_class = "user" if message["role"] == "user" else "bot"
        avatar_text = "S" if message["role"] == "user" else "J"
        
        st.markdown(f"""
            <div class="chat-message {role_class}">
                <div class="avatar">{avatar_text}</div>
                <div class="content">{message["content"]}</div>
            </div>
        """, unsafe_allow_html=True)

    if prompt := st.chat_input("Ask a doubt or request a schedule..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        st.markdown(f"""
            <div class="chat-message user">
                <div class="avatar">S</div>
                <div class="content">{prompt}</div>
            </div>
        """, unsafe_allow_html=True)

        # Placeholder Response Logic
        response_text = "Analyzing..."
        time.sleep(1)
        if "schedule" in prompt.lower():
            response_text = "Let's update your schedule. Since you have the PRO plan, I can create a custom 15-day revision block for you."
        else:
            response_text = f"I've received your query: '{prompt}'. Let's solve this."

        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()
