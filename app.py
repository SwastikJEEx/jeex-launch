import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid

# --- 1. SETUP PAGE & INPUTS (Must be at the top) ---
st.set_page_config(page_title="JEExPro Registration", page_icon="🚀")

st.title("JEExPro Access")
st.subheader("Complete your registration")

# These variables MUST be defined before the button
name = st.text_input("Full Name")
phone = st.text_input("Phone Number")
email = st.text_input("Email Address")
plan = st.selectbox("Select Plan", ["Basic - ₹59", "Pro - ₹99"])
transaction_id = st.text_input("Transaction ID (from UPI payment)")

st.write("---")

# --- 2. SUBMIT BUTTON & EMAIL LOGIC ---
if st.button("Submit Details", type="primary"):
    # Check if inputs are empty
    if not name or not email or not phone or not transaction_id:
        st.error("⚠️ Please fill in all details.")
    else:
        # --- EMAIL SENDING LOGIC ---
        try:
            # A. CREDENTIALS (REPLACE WITH YOURS)
            sender_email = "YOUR_EMAIL@gmail.com"  
            sender_password = "YOUR_APP_PASSWORD" # 16-digit Google App Password
            receiver_email = "swastik1@fam" # Your receiving email
            
            # B. CONSTRUCT EMAIL (Anti-Spam Headers)
            msg = MIMEMultipart()
            msg['From'] = f"JEExPro System <{sender_email}>"
            msg['To'] = receiver_email
            msg['Subject'] = f"New JEExPro User: {name}"
            msg['Date'] = formatdate(localtime=True) 
            msg['Message-ID'] = make_msgid() 
            
            body_text = f"""
            NEW REGISTRATION DETAILS
            ========================
            Name: {name}
            Phone: {phone}
            Email: {email}
            Plan: {plan}
            Transaction ID: {transaction_id}
            ========================
            """
            msg.attach(MIMEText(body_text, 'plain'))

            # C. SEND
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()

            # D. SUCCESS
            st.success(f"✅ Request Submitted! We will verify and email you shortly.")
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ System Error: {e}")
