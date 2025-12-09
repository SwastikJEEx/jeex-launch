import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid # These prevent Spam

# ... (Your inputs remain here) ...

if st.button("Submit Details", type="primary"):
    if not name or not email or not phone or not transaction_id:
        st.error("⚠️ Please fill in all details.")
    else:
        # --- ROBUST EMAIL SYSTEM START ---
        try:
            # 1. CREDENTIALS
            sender_email = "YOUR_EMAIL@gmail.com"  
            sender_password = "YOUR_APP_PASSWORD" # 16-digit App Password
            receiver_email = "swastik1@fam" # Where you want to receive it
            
            # 2. CONSTRUCT THE "REAL" EMAIL HEADERS
            # These headers are what stop it from going to Spam
            msg = MIMEMultipart()
            msg['From'] = f"JEExPro Admin <{sender_email}>" # Shows a professional name
            msg['To'] = receiver_email
            msg['Subject'] = f"Action Required: New User ({name})"
            msg['Date'] = formatdate(localtime=True) # Essential for spam filters
            msg['Message-ID'] = make_msgid() # Unique ID for every email
            
            # 3. THE EMAIL BODY
            body_text = f"""
            NEW USER REGISTRATION
            =====================
            
            User Details:
            - Name: {name}
            - Phone: {phone}
            - User Email: {email}
            
            Payment Info:
            - Plan: {plan}
            - Transaction ID: {transaction_id}
            
            ---------------------------------------
            Sent via JEExPro Internal System
            """
            msg.attach(MIMEText(body_text, 'plain'))

            # 4. SENDING (Standard Secure SMTP)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg) # prefer send_message over sendmail for better headers
            server.quit()

            # 5. SUCCESS UI
            st.success(f"✅ Request Submitted! Welcome to JEExPro, {name}.")
            st.caption("We have received your details and will verify shortly.")
            
        except Exception as e:
            st.error(f"System Error: {e}")
        # --- EMAIL SYSTEM END ---
