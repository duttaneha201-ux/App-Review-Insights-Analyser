"""
Unsubscribe Page for App Review Insights Analyzer

Allows users to unsubscribe from email notifications by providing
their email address and the Play Store app URL.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from app.db.database import get_db_session
from app.db.repository import AppRepository, SubscriptionRepository
from app.services.url_validator import PlayStoreURLValidator

# Set page config
st.set_page_config(
    page_title="Unsubscribe - App Review Insights",
    page_icon="📧",
    layout="centered"
)

def main():
    st.title("📧 Unsubscribe from Email Notifications")
    st.markdown("""
    Enter your email address and the Play Store app URL to unsubscribe from 
    weekly product insights emails.
    """)
    
    st.divider()
    
    with st.form("unsubscribe_form", clear_on_submit=False):
        email = st.text_input(
            "Email Address *",
            placeholder="your-email@example.com",
            help="The email address you used to subscribe"
        )
        
        app_url = st.text_input(
            "Play Store App URL *",
            placeholder="https://play.google.com/store/apps/details?id=com.example.app",
            help="The Play Store URL of the app you subscribed to"
        )
        
        submitted = st.form_submit_button("Unsubscribe", type="primary")
        
        if submitted:
            # Validate inputs
            if not email or not email.strip():
                st.error("❌ Please enter your email address")
                return
            
            if not app_url or not app_url.strip():
                st.error("❌ Please enter the Play Store app URL")
                return
            
            # Validate email format (basic)
            if "@" not in email or "." not in email.split("@")[1]:
                st.error("❌ Please enter a valid email address")
                return
            
            # Validate and extract app ID from URL
            try:
                validator = PlayStoreURLValidator()
                validation_result = validator.validate_and_verify(app_url.strip())
                
                if not validation_result['valid']:
                    st.error("❌ Invalid Play Store URL format")
                    st.info("Please enter a URL like: https://play.google.com/store/apps/details?id=com.example.app")
                    return
                
                if not validation_result['app_exists']:
                    st.error("❌ This app does not exist on Play Store")
                    return
                
                app_id_str = validation_result['app_id']
                
            except Exception as e:
                st.error(f"❌ Error validating URL: {str(e)}")
                return
            
            # Find and deactivate subscription
            try:
                with get_db_session() as session:
                    # Find app by Play Store ID
                    app = AppRepository.get_by_playstore_id(session, app_id_str)
                    
                    if not app:
                        st.warning("⚠️ No subscription found for this app and email combination")
                        st.info("You may not be subscribed, or the app URL is incorrect.")
                        return
                    
                    # Find and deactivate subscription
                    success, message = SubscriptionRepository.deactivate_by_email_and_app(
                        session,
                        email.strip().lower(),
                        app.id
                    )
                    
                    if success:
                        session.commit()
                        st.success("✅ " + message)
                        st.balloons()
                        st.info("""
                        **You have been unsubscribed successfully.**
                        
                        You will no longer receive weekly product insights emails for this app.
                        """)
                    else:
                        st.warning("⚠️ " + message)
                        if "already inactive" in message.lower():
                            st.info("This subscription was already inactive.")
                        
            except Exception as e:
                st.error(f"❌ Error processing unsubscribe request: {str(e)}")
                st.exception(e)
    
    st.divider()
    st.markdown("""
    **Need help?**
    - Make sure you're using the exact email address you subscribed with
    - Use the full Play Store URL (e.g., https://play.google.com/store/apps/details?id=com.example.app)
    - Contact support if you continue to receive emails after unsubscribing
    """)

if __name__ == "__main__":
    main()

