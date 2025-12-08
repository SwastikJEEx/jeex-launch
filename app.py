# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🔐 Premium Access")
    if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
    if "audio_key" not in st.session_state: st.session_state.audio_key = 0
    
    user_key = st.text_input("Enter Access Key:", type="password")
    status = check_key_status(user_key)
    
    # --- IF USER IS UNLOCKED (VALID) ---
    if status == "VALID" or status == "ADMIN":
        st.success(f"✅ Active")
        st.markdown("---")
        
        # 1. ATTACHMENT
        st.markdown("**📎 Attach Question**")
        uploaded_file = st.file_uploader("Upload Image/PDF", type=["jpg", "png", "pdf"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
        
        # 2. VOICE INPUT
        st.markdown("**🎙️ Voice Chat**")
        audio_value = st.audio_input("Speak", key=f"audio_{st.session_state.audio_key}", label_visibility="collapsed")
        
        st.markdown("---")
        if "messages" in st.session_state and len(st.session_state.messages) > 1:
            pdf_bytes = generate_pdf(st.session_state.messages)
            st.download_button("📥 Download Notes", data=pdf_bytes, file_name="JEEx_Notes.pdf", mime="application/pdf")
        
        if st.button("End Session"): st.session_state['logout'] = True; st.rerun()

    # --- IF USER IS LOCKED (SHOW PAYMENT QR) ---
    else:
        if status == "EXPIRED":
            st.error("⚠️ Plan Expired")
            st.warning("Renew to continue.")
        else:
            if user_key: st.warning("🔒 Invalid Key")
        
        # PAYMENT SECTION
        st.markdown("### ⚡ Get Premium Access")
        with st.expander("💎 Join JEEx Pro (₹99)", expanded=True):
            st.markdown("Scan to Pay ₹99 via UPI:")
            
            # SHOW QR CODE (Upload upi_qr.png to GitHub first!)
            # If file not found, shows text fallback
            try:
                st.image("upi_qr.png", use_container_width=True)
            except:
                st.info("UPI ID: **your-upi-id@okaxis**") # Change this to your actual ID if image fails
                
            st.markdown("---")
            st.markdown("**Step 2: Send Screenshot**")
            
            # WHATSAPP LINK GENERATOR
            # Replace '919876543210' with YOUR WhatsApp Number
            wa_link = "https://wa.me/919876543210?text=Hi%20JEEx,%20I%20have%20paid%20Rs.99.%20Here%20is%20my%20screenshot,%20please%20give%20me%20a%20Key."
            
            st.markdown(f"""
                <a href="{wa_link}" target="_blank">
                    <button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:8px; cursor:pointer; font-weight:bold; font-size:15px;">
                        👉 Claim Key on WhatsApp
                    </button>
                </a>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        with st.expander("📄 Terms & Conditions"): 
            st.markdown("**JEEx Policy:**\n1. Personal Use Only.\n2. No Refunds.\n3. AI may make errors.")
