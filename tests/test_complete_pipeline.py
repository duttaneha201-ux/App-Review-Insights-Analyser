"""
Test Complete Pipeline Flow

This script tests the complete end-to-end flow:
1. Extract reviews from Play Store
2. Clean and scrub PII
3. Identify themes
4. Generate weekly pulse
5. Send email

It explicitly loads the GROQ_API_KEY from the .env file and passes it
into the pipeline so that theme identification and weekly synthesis
always have access to the correct key.
"""

import os
import sys

from dotenv import load_dotenv

from app.pipeline import extract_clean_and_synthesize
from app.services.email_service import EmailService


def test_complete_pipeline(recipient_email=None):
    """Test the complete pipeline flow"""
    
    print("=" * 70)
    print("COMPLETE PIPELINE TEST")
    print("=" * 70)
    
    # Get recipient email from command line or prompt
    if not recipient_email:
        if len(sys.argv) > 1:
            recipient_email = sys.argv[1]
        else:
            try:
                recipient_email = input("\nEnter your email address to receive test email: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[ERROR] No email provided. Usage: python test_complete_pipeline.py your-email@example.com")
                return
    
    if not recipient_email:
        print("[ERROR] No email provided. Usage: python test_complete_pipeline.py your-email@example.com")
        return
    
    print(f"\n[OK] Will send test email to: {recipient_email}")
    
    # Ensure environment variables from .env are loaded (including GROQ_API_KEY)
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print(
            "\n[ERROR] GROQ_API_KEY not found in environment.\n"
            "Make sure your .env file contains a line like:\n"
            "GROQ_API_KEY=your-real-api-key-here\n"
        )
        return
    print("\n" + "=" * 70)
    print("STEP 1: Running Complete Analysis Pipeline...")
    print("=" * 70)
    print("(This may take a few minutes - extracting reviews, identifying themes, generating pulse)\n")
    
    try:
        # Run analysis
        result = extract_clean_and_synthesize(
            play_store_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            weeks=4,  # Start with 4 weeks for faster testing
            groq_api_key=groq_api_key,
        )
        
        # Check for errors
        if result.get('errors'):
            print("\n[ERROR] Errors during analysis:")
            for error in result['errors']:
                print(f"  - {error}")
            return
        
        # Display results
        print("\n" + "=" * 70)
        print("ANALYSIS RESULTS")
        print("=" * 70)
        print(f"\nApp ID: {result.get('app_id', 'N/A')}")
        print(f"Reviews extracted: {result['stats'].get('total_reviews', 0)}")
        print(f"Themes identified: {result['stats'].get('themes_identified', 0)}")
        print(f"Pulse generated: {result['stats'].get('pulse_generated', False)}")
        
        if result.get('weekly_pulse'):
            pulse = result['weekly_pulse']
            print(f"\nWeekly Pulse:")
            print(f"  Title: {pulse.title}")
            print(f"  Word Count: {pulse.word_count()} / 250")
            print(f"  Themes: {len(pulse.themes)}")
            print(f"  Quotes: {len(pulse.quotes)}")
            print(f"  Actions: {len(pulse.actions)}")
        else:
            print("\n[WARNING] No weekly pulse generated")
            return
        
        # Send email
        print("\n" + "=" * 70)
        print("STEP 2: Sending Email...")
        print("=" * 70)
        print("(Using SMTP credentials from .env file)\n")
        
        try:
            service = EmailService()
            
            email_result = service.send_weekly_pulse(
                to_emails=[recipient_email],
                pulse=result['weekly_pulse'],
                app_name=result.get('app_id', 'WhatsApp')
            )
            
            print("\n" + "=" * 70)
            print("EMAIL SEND RESULTS")
            print("=" * 70)
            print(f"\nSuccess: {email_result['success']}")
            print(f"Sent: {email_result['sent_count']}")
            print(f"Failed: {email_result['failed_count']}")
            
            if email_result.get('errors'):
                print(f"\nErrors:")
                for error in email_result['errors']:
                    print(f"  - {error}")
            
            if email_result['success']:
                print("\n" + "=" * 70)
                print("[SUCCESS] COMPLETE PIPELINE TEST SUCCESSFUL!")
                print("=" * 70)
                print(f"\nCheck {recipient_email} inbox (and spam folder) for the email.")
                print("Email should arrive within a few minutes.")
            else:
                print("\n" + "=" * 70)
                print("[ERROR] EMAIL SENDING FAILED")
                print("=" * 70)
                print("\nTroubleshooting:")
                print("  1. Check SMTP credentials in .env file")
                print("  2. For Gmail, use App Password (not regular password)")
                print("  3. Verify SMTP settings are correct")
                print("  4. Check firewall isn't blocking SMTP port")
                
        except Exception as e:
            print(f"\n[ERROR] Error sending email: {e}")
            print("\nTroubleshooting:")
            print("  1. Check SMTP credentials in .env file")
            print("  2. Verify .env file is in project root")
            print("  3. Restart terminal/IDE to reload .env")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"\n[ERROR] Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_complete_pipeline()

