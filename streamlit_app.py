"""
Streamlit App for App Review Insights Analyzer
Deploy to Streamlit Cloud: https://streamlit.io/cloud
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import date, timedelta
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set page config
st.set_page_config(
    page_title="App Review Insights Analyzer",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import app modules
from app.services.url_validator import PlayStoreURLValidator
from app.pipeline import extract_clean_and_synthesize
from app.db.database import get_db_session, init_db
from app.db.repository import (
    AppRepository,
    SubscriptionRepository,
)

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'result' not in st.session_state:
    st.session_state.result = None
if 'error' not in st.session_state:
    st.session_state.error = None


def validate_inputs(playstore_url: str, weeks: int, email: str) -> tuple[bool, str]:
    """Validate user inputs"""
    if not playstore_url or not playstore_url.strip():
        return False, "Please enter a Play Store URL"
    
    if not playstore_url.startswith(('http://', 'https://')):
        return False, "URL must start with http:// or https://"
    
    if 'play.google.com' not in playstore_url:
        return False, "Please enter a valid Google Play Store URL"
    
    if not (1 <= weeks <= 12):
        return False, "Weeks must be between 1 and 12"
    
    if not email or '@' not in email or '.' not in email.split('@')[1]:
        return False, "Please enter a valid email address"
    
    return True, ""


def check_database_initialized():
    """Check if database tables exist, create if not"""
    try:
        with get_db_session() as session:
            from sqlalchemy import inspect
            inspector = inspect(session.bind)
            tables = inspector.get_table_names()
            if not tables:
                st.info("Initializing database...")
                init_db()
                st.success("Database initialized!")
                st.rerun()
    except Exception as e:
        st.warning(f"Database check: {e}")


def main():
    """Main Streamlit app"""
    
    # Header
    st.title("📱 App Review Insights Analyzer")
    st.markdown("""
    Analyze Google Play Store reviews and get weekly product insights delivered to your email.
    
    **How it works:**
    1. Enter a Play Store app URL
    2. Select the number of weeks to analyze (1-12)
    3. Enter your email address
    4. Click "Start Analysis" to begin processing
    
    The analysis will extract reviews, identify themes, generate insights, and send you a detailed report via email.
    """)
    
    st.divider()
    
    # Check database
    check_database_initialized()
    
    # Main form
    with st.form("subscription_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            playstore_url = st.text_input(
                "Play Store URL *",
                placeholder="https://play.google.com/store/apps/details?id=com.whatsapp",
                help="Enter the full URL of the app from Google Play Store"
            )
            
            weeks = st.slider(
                "Number of Weeks *",
                min_value=1,
                max_value=12,
                value=8,
                help="Select how many weeks of reviews to analyze (1-12)"
            )
        
        with col2:
            email = st.text_input(
                "Email Address *",
                placeholder="your-email@example.com",
                help="Enter your email to receive insights"
            )
            
            st.markdown("### ")
            submit_button = st.form_submit_button(
                "🚀 Start Analysis",
                use_container_width=True,
                type="primary"
            )
        
        # Validation
        if submit_button:
            is_valid, error_msg = validate_inputs(playstore_url, weeks, email)
            
            if not is_valid:
                st.error(f"❌ {error_msg}")
                st.session_state.processing = False
            else:
                st.session_state.processing = True
                st.session_state.result = None
                st.session_state.error = None
    
    # Processing section
    if st.session_state.processing:
        st.divider()
        st.info("🔄 Processing your request... This may take a few minutes.")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        error_container = st.empty()
        
        try:
            # Step 1: Validate URL
            status_text.text("Step 1/5: Validating Play Store URL...")
            progress_bar.progress(20)
            
            validator = PlayStoreURLValidator()
            validation_result = validator.validate_and_verify(playstore_url)
            
            if not validation_result['valid']:
                st.error("❌ Invalid Play Store URL format")
                st.session_state.processing = False
                return
            
            if not validation_result['app_exists']:
                st.error("❌ This app does not exist on Play Store.")
                st.session_state.processing = False
                return
            
            app_id = validation_result['app_id']
            st.success(f"✅ Validated: {app_id}")
            
            # Step 2: Create subscription
            status_text.text("Step 2/5: Creating subscription...")
            progress_bar.progress(40)
            
            with get_db_session() as session:
                # Get or create app
                app = AppRepository.get_or_create_by_playstore_id(
                    session,
                    playstore_app_id=app_id,
                    app_name=app_id.split('.')[-1].title(),
                    app_url=playstore_url,
                )
                session.commit()
                
                # Create subscription
                start_date = date.today()
                subscription = SubscriptionRepository.create(
                    session,
                    app_id=app.id,
                    email=email,
                    start_date=start_date,
                    is_active=True,
                )
                session.commit()
                
                st.success(f"✅ Subscription created (ID: {subscription.id})")
            
            # Step 3: Extract and analyze
            status_text.text("Step 3/5: Extracting reviews from Play Store...")
            progress_bar.progress(50)
            
            status_text.text("Step 4/5: Analyzing reviews and identifying themes...")
            progress_bar.progress(70)
            
            result = extract_clean_and_synthesize(
                play_store_url=playstore_url,
                weeks=weeks,
                samples_per_rating=15,
                exclude_last_days=7,
            )
            
            # Step 5: Check results
            status_text.text("Step 5/5: Finalizing...")
            progress_bar.progress(100)
            
            if result.get('errors'):
                error_msg = '; '.join(result['errors'])
                st.error(f"❌ Analysis errors: {error_msg}")
                st.session_state.processing = False
                st.session_state.error = error_msg
                return
            
            if result.get('stats', {}).get('total_reviews', 0) == 0:
                st.warning("⚠️ No reviews found for the selected time range.")
                st.session_state.processing = False
                return
            
            # Success
            st.session_state.result = result
            st.session_state.processing = False
            
            st.success("✅ Analysis completed successfully!")
            progress_bar.empty()
            status_text.empty()
            
            # Display results
            st.divider()
            st.subheader("📊 Analysis Results")
            
            stats = result.get('stats', {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Reviews", stats.get('total_reviews', 0))
            with col2:
                themes_count = stats.get('themes_identified', 0)
                key_themes_count = len(weekly_pulse.themes) if weekly_pulse and weekly_pulse.themes else 0
                if themes_count > 0 and key_themes_count > 0:
                    st.metric("Key Themes", f"{key_themes_count} of {themes_count}")
                else:
                    st.metric("Themes Identified", themes_count)
            with col3:
                pulse_status = "✅ Yes" if stats.get('pulse_generated') else "❌ No"
                st.metric("Pulse Generated", pulse_status)
            
            # Show weekly pulse if available
            weekly_pulse = result.get('weekly_pulse')
            if weekly_pulse:
                st.divider()
                st.subheader("📝 Weekly Product Pulse")
                
                st.markdown(f"### {weekly_pulse.title}")
                st.markdown(f"**Overview:** {weekly_pulse.overview}")
                
                if weekly_pulse.themes:
                    st.markdown("#### Key Themes")
                    for i, theme in enumerate(weekly_pulse.themes, 1):
                        theme_name = theme.get('name', theme.get('theme', 'Unknown Theme'))
                        theme_summary = theme.get('summary', '')
                        st.markdown(f"{i}. **{theme_name}**: {theme_summary}")
                
                if weekly_pulse.quotes:
                    st.markdown("#### User Quotes")
                    for quote in weekly_pulse.quotes:
                        st.markdown(f"> *\"{quote}\"*")
                
                if weekly_pulse.actions:
                    st.markdown("#### Recommended Actions")
                    for action in weekly_pulse.actions:
                        st.markdown(f"- {action}")
            
            # Send email
            if weekly_pulse:
                try:
                    from app.services.email_service import EmailService
                    
                    status_text.text("Sending email...")
                    email_service = EmailService()
                    
                    # Get app name from result
                    app_name = result.get('app_id', 'App')
                    if app_name:
                        app_name = app_name.split('.')[-1].title()
                    
                    email_result = email_service.send_weekly_pulse(
                        to_emails=[email],
                        pulse=weekly_pulse,
                        app_name=app_name,
                        audience='product_manager'
                    )
                    
                    if email_result.get('success'):
                        st.success(f"📧 Email sent successfully to {email}! Check your inbox (and spam folder).")
                    else:
                        st.warning(f"⚠️ Email sending failed: {email_result.get('errors', ['Unknown error'])[0]}")
                        st.info("📧 You can view the analysis results above. Email will be retried automatically.")
                except Exception as e:
                    st.warning(f"⚠️ Could not send email: {str(e)}")
                    st.info("📧 You can view the analysis results above. Email will be retried automatically.")
            else:
                st.info("📧 No weekly pulse generated, so no email will be sent.")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)
            st.session_state.processing = False
            st.session_state.error = str(e)
            progress_bar.empty()
            status_text.empty()
    
    # Display previous result if available
    if st.session_state.result and not st.session_state.processing:
        st.divider()
        if st.button("🔄 Analyze Another App"):
            st.session_state.result = None
            st.session_state.error = None
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This tool analyzes Google Play Store reviews and generates actionable insights.
        
        **Features:**
        - Automated review extraction
        - PII scrubbing
        - Theme identification
        - Weekly synthesis
        - Email delivery
        """)
        
        st.divider()
        
        st.header("⚙️ Configuration Status")
        
        # Check environment variables
        env_status = {
            'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
            'SMTP_HOST': os.getenv('SMTP_HOST'),
            'SMTP_USERNAME': os.getenv('SMTP_USERNAME'),
            'DATABASE_URL': os.getenv('DATABASE_URL'),
        }
        
        for key, value in env_status.items():
            if value:
                st.success(f"✅ {key}")
            else:
                st.error(f"❌ {key} not set")
        
        if st.checkbox("Show database info"):
            db_url = os.getenv("DATABASE_URL", "Not set")
            if db_url.startswith("postgresql://"):
                st.success("✅ PostgreSQL configured")
                # Mask password
                if "@" in db_url:
                    parts = db_url.split("@")
                    st.code(f"postgresql://***@{parts[1] if len(parts) > 1 else 'unknown'}")
            elif db_url.startswith("sqlite://"):
                st.warning("⚠️ Using SQLite (not recommended for production)")
            else:
                st.info("Using default SQLite")
        
        st.divider()
        
        st.header("📚 Documentation")
        st.markdown("""
        - [Neon Database Setup](./NEON_DATABASE_SETUP.md)
        - [Credentials Guide](./CREDENTIALS_LOCATIONS.md)
        - [GitHub Actions](./GITHUB_ACTIONS_SETUP.md)
        """)


if __name__ == "__main__":
    main()

