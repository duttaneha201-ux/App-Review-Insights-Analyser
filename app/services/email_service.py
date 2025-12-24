"""
Email Service Module

Module 7: Email composition and sending using SMTP.

Features:
- HTML email templates
- Audience-specific formatting
- Email validation
- SMTP integration (Gmail, Outlook, custom SMTP servers)
"""

import logging
import os
import re
import smtplib
from typing import List, Optional, Dict, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv

from app.services.weekly_synthesis import WeeklyPulse

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class EmailValidationError(Exception):
    """Raised when email validation fails"""
    pass


class EmailService:
    """
    Email service for sending Weekly Product Pulse emails via SMTP.
    
    Supports:
    - Gmail SMTP (smtp.gmail.com)
    - Outlook SMTP (smtp-mail.outlook.com)
    - Custom SMTP servers
    - HTML email templates
    - Audience-specific formatting
    - Email validation
    """
    
    # Audience types
    AUDIENCE_PRODUCT = "product"
    AUDIENCE_SUPPORT = "support"
    AUDIENCE_LEADERSHIP = "leadership"
    
    # Common SMTP servers
    SMTP_GMAIL = {
        'host': 'smtp.gmail.com',
        'port': 587,
        'use_tls': True
    }
    
    SMTP_OUTLOOK = {
        'host': 'smtp-mail.outlook.com',
        'port': 587,
        'use_tls': True
    }
    
    SMTP_YAHOO = {
        'host': 'smtp.mail.yahoo.com',
        'port': 587,
        'use_tls': True
    }
    
    # Default sender
    DEFAULT_FROM_EMAIL = "noreply@app-insights.com"
    DEFAULT_FROM_NAME = "App Review Insights"
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ):
        """
        Initialize email service with SMTP configuration.
        
        Args:
            smtp_host: SMTP server hostname (default: from SMTP_HOST env var or Gmail)
            smtp_port: SMTP server port (default: from SMTP_PORT env var or 587)
            smtp_username: SMTP username/email (default: from SMTP_USERNAME env var)
            smtp_password: SMTP password/app password (default: from SMTP_PASSWORD env var)
            use_tls: Use TLS encryption (default: True)
            from_email: Sender email address (default: from SMTP_FROM_EMAIL env var or smtp_username)
            from_name: Sender name (default: from SMTP_FROM_NAME env var or default)
        """
        # Get SMTP configuration from parameters or environment
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', self.SMTP_GMAIL['host'])
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', str(self.SMTP_GMAIL['port'])))
        self.smtp_username = smtp_username or os.getenv('SMTP_USERNAME')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
        self.use_tls = use_tls
        
        # Get sender information
        self.from_email = from_email or os.getenv('SMTP_FROM_EMAIL', self.smtp_username or self.DEFAULT_FROM_EMAIL)
        self.from_name = from_name or os.getenv('SMTP_FROM_NAME', self.DEFAULT_FROM_NAME)
        
        # Validate required fields
        if not self.smtp_username:
            raise ValueError(
                "SMTP username is required. Set SMTP_USERNAME environment variable "
                "or pass smtp_username parameter."
            )
        
        if not self.smtp_password:
            raise ValueError(
                "SMTP password is required. Set SMTP_PASSWORD environment variable "
                "or pass smtp_password parameter.\n"
                "For Gmail, use an App Password (not your regular password)."
            )
        
        logger.info(f"Initialized EmailService with SMTP: {self.smtp_host}:{self.smtp_port}")
        logger.info(f"From: {self.from_email} ({self.from_name})")
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
        
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    @staticmethod
    def validate_emails(emails: List[str]) -> tuple[List[str], List[str]]:
        """
        Validate a list of email addresses.
        
        Args:
            emails: List of email addresses
            
        Returns:
            Tuple of (valid_emails, invalid_emails)
        """
        valid = []
        invalid = []
        
        for email in emails:
            if EmailService.validate_email(email):
                valid.append(email.strip())
            else:
                invalid.append(email)
        
        return valid, invalid
    
    def _create_html_template(
        self,
        pulse: WeeklyPulse,
        app_name: Optional[str] = None,
        audience: str = AUDIENCE_PRODUCT
    ) -> str:
        """
        Create HTML email template from Weekly Pulse.
        
        Args:
            pulse: WeeklyPulse object
            app_name: Optional app name
            audience: Audience type (product, support, leadership)
            
        Returns:
            HTML email content
        """
        # Get audience-specific styling
        styles = self._get_audience_styles(audience)
        
        # Format date
        date_str = datetime.now().strftime("%B %d, %Y")
        
        # Build themes HTML
        themes_html = ""
        if pulse.themes:
            for i, theme in enumerate(pulse.themes, 1):
                theme_name = theme.get('name', 'Unknown Theme')
                theme_summary = theme.get('summary', '')
                themes_html += f"""
                <div style="margin-bottom: 20px;">
                    <h3 style="color: {styles['theme_color']}; margin-bottom: 8px; font-size: 18px;">
                        {i}. {self._escape_html(theme_name)}
                    </h3>
                    <p style="color: #666; line-height: 1.6; margin: 0;">
                        {self._escape_html(theme_summary)}
                    </p>
                </div>
                """
        else:
            themes_html = "<p style='color: #666;'>No themes identified this week.</p>"
        
        # Build quotes HTML
        quotes_html = ""
        if pulse.quotes:
            quotes_html = "<div style='background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;'>"
            for quote in pulse.quotes:
                quotes_html += f"""
                <p style="margin: 10px 0; font-style: italic; color: #555;">
                    "{self._escape_html(quote)}"
                </p>
                """
            quotes_html += "</div>"
        
        # Build actions HTML
        actions_html = ""
        if pulse.actions:
            actions_html = "<ul style='margin: 20px 0; padding-left: 20px;'>"
            for action in pulse.actions:
                actions_html += f"""
                <li style="margin: 8px 0; color: #333; line-height: 1.6;">
                    {self._escape_html(action)}
                </li>
                """
            actions_html += "</ul>"
        
        # Audience-specific header
        header_text = self._get_audience_header(audience, app_name)
        
        # Build complete HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Product Pulse</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px 0; text-align: center; background-color: {styles['header_bg']};">
                <h1 style="margin: 0; color: {styles['header_color']}; font-size: 24px;">
                    {header_text}
                </h1>
            </td>
        </tr>
        <tr>
            <td style="padding: 30px 20px; background-color: #ffffff;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <!-- Date -->
                    <p style="color: #999; font-size: 14px; margin: 0 0 20px 0;">
                        {date_str}
                    </p>
                    
                    <!-- Title -->
                    <h2 style="color: #333; font-size: 22px; margin: 0 0 15px 0; border-bottom: 2px solid {styles['accent_color']}; padding-bottom: 10px;">
                        {self._escape_html(pulse.title)}
                    </h2>
                    
                    <!-- Overview -->
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #333; line-height: 1.6; margin: 0; font-size: 16px;">
                            {self._escape_html(pulse.overview)}
                        </p>
                    </div>
                    
                    <!-- Themes -->
                    <div style="margin: 30px 0;">
                        <h3 style="color: #333; font-size: 20px; margin: 0 0 15px 0;">
                            Key Themes
                        </h3>
                        {themes_html}
                    </div>
                    
                    <!-- Quotes -->
                    {f'<div style="margin: 30px 0;"><h3 style="color: #333; font-size: 20px; margin: 0 0 15px 0;">User Quotes</h3>{quotes_html}</div>' if pulse.quotes else ''}
                    
                    <!-- Actions -->
                    {f'<div style="margin: 30px 0;"><h3 style="color: #333; font-size: 20px; margin: 0 0 15px 0;">Recommended Actions</h3>{actions_html}</div>' if pulse.actions else ''}
                    
                    <!-- Footer -->
                    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center;">
                        <p style="color: #999; font-size: 12px; margin: 5px 0;">
                            Generated by App Review Insights Analyzer
                        </p>
                        <p style="color: #999; font-size: 12px; margin: 5px 0;">
                            Word count: {pulse.word_count()} / 250
                        </p>
                    </div>
                </div>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return html.strip()
    
    def _get_audience_styles(self, audience: str) -> Dict[str, str]:
        """Get audience-specific styling"""
        styles = {
            self.AUDIENCE_PRODUCT: {
                'header_bg': '#007bff',
                'header_color': '#ffffff',
                'accent_color': '#007bff',
                'theme_color': '#007bff'
            },
            self.AUDIENCE_SUPPORT: {
                'header_bg': '#28a745',
                'header_color': '#ffffff',
                'accent_color': '#28a745',
                'theme_color': '#28a745'
            },
            self.AUDIENCE_LEADERSHIP: {
                'header_bg': '#6f42c1',
                'header_color': '#ffffff',
                'accent_color': '#6f42c1',
                'theme_color': '#6f42c1'
            }
        }
        return styles.get(audience, styles[self.AUDIENCE_PRODUCT])
    
    def _get_audience_header(self, audience: str, app_name: Optional[str] = None) -> str:
        """Get audience-specific header text"""
        app_text = f" - {app_name}" if app_name else ""
        
        headers = {
            self.AUDIENCE_PRODUCT: f"Weekly Product Pulse{app_text}",
            self.AUDIENCE_SUPPORT: f"Weekly Support Insights{app_text}",
            self.AUDIENCE_LEADERSHIP: f"Weekly Executive Summary{app_text}"
        }
        return headers.get(audience, headers[self.AUDIENCE_PRODUCT])
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return ""
        return (
            text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;')
        )
    
    def _create_text_template(
        self,
        pulse: WeeklyPulse,
        app_name: Optional[str] = None
    ) -> str:
        """Create plain text email template"""
        text = f"""
WEEKLY PRODUCT PULSE{' - ' + app_name if app_name else ''}
{datetime.now().strftime('%B %d, %Y')}

{pulse.title}

OVERVIEW:
{pulse.overview}

KEY THEMES:
"""
        for i, theme in enumerate(pulse.themes, 1):
            text += f"\n{i}. {theme.get('name', 'Unknown')}\n   {theme.get('summary', '')}\n"
        
        if pulse.quotes:
            text += "\nUSER QUOTES:\n"
            for quote in pulse.quotes:
                text += f'  "{quote}"\n'
        
        if pulse.actions:
            text += "\nRECOMMENDED ACTIONS:\n"
            for i, action in enumerate(pulse.actions, 1):
                text += f"  {i}. {action}\n"
        
        text += f"\n---\nGenerated by App Review Insights Analyzer\nWord count: {pulse.word_count()} / 250"
        
        return text.strip()
    
    def send_weekly_pulse(
        self,
        to_emails: List[str],
        pulse: WeeklyPulse,
        app_name: Optional[str] = None,
        audience: str = AUDIENCE_PRODUCT,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send Weekly Product Pulse email via SMTP.
        
        Args:
            to_emails: List of recipient email addresses
            pulse: WeeklyPulse object
            app_name: Optional app name
            audience: Audience type (product, support, leadership)
            subject: Optional custom subject line
            
        Returns:
            Dictionary with:
            - 'success': Boolean indicating success
            - 'sent_count': Number of emails sent
            - 'failed_count': Number of emails that failed
            - 'errors': List of error messages
        """
        # Validate emails
        valid_emails, invalid_emails = self.validate_emails(to_emails)
        
        if invalid_emails:
            logger.warning(f"Invalid email addresses: {invalid_emails}")
        
        if not valid_emails:
            raise EmailValidationError("No valid email addresses provided")
        
        # Generate subject if not provided
        if not subject:
            app_text = f" - {app_name}" if app_name else ""
            subject = f"Weekly Product Pulse{app_text} - {datetime.now().strftime('%B %d, %Y')}"
        
        # Create email content
        html_content = self._create_html_template(pulse, app_name, audience)
        text_content = self._create_text_template(pulse, app_name)
        
        results = {
            'success': False,
            'sent_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        # Send to each recipient
        for email in valid_emails:
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['From'] = formataddr((self.from_name, self.from_email))
                msg['To'] = email
                msg['Subject'] = subject
                
                # Add text and HTML parts
                part1 = MIMEText(text_content, 'plain')
                part2 = MIMEText(html_content, 'html')
                msg.attach(part1)
                msg.attach(part2)
                
                # Connect to SMTP server and send
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.use_tls:
                        server.starttls()
                    
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                
                results['sent_count'] += 1
                logger.info(f"Email sent successfully to {email}")
                
            except smtplib.SMTPAuthenticationError as e:
                results['failed_count'] += 1
                error_msg = f"SMTP authentication failed for {email}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
            except smtplib.SMTPException as e:
                results['failed_count'] += 1
                error_msg = f"SMTP error sending to {email}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
            except Exception as e:
                results['failed_count'] += 1
                error_msg = f"Error sending to {email}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        results['success'] = results['sent_count'] > 0
        
        return results


def send_weekly_pulse_email(
    to_emails: List[str],
    pulse: WeeklyPulse,
    app_name: Optional[str] = None,
    audience: str = EmailService.AUDIENCE_PRODUCT,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to send weekly pulse email.
    
    Args:
        to_emails: List of recipient email addresses
        pulse: WeeklyPulse object
        app_name: Optional app name
        audience: Audience type (product, support, leadership)
        smtp_host: Optional SMTP host (uses env var if not provided)
        smtp_port: Optional SMTP port (uses env var if not provided)
        smtp_username: Optional SMTP username (uses env var if not provided)
        smtp_password: Optional SMTP password (uses env var if not provided)
        
    Returns:
        Dictionary with send results
    """
    service = EmailService(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password
    )
    return service.send_weekly_pulse(to_emails, pulse, app_name, audience)
