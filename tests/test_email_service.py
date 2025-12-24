"""
Unit tests for Email Service (SMTP)

Tests cover:
- Email validation
- HTML template generation
- Audience-specific formatting
- Email sending via SMTP (mocked)
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.email_service import (
    EmailService,
    EmailValidationError,
    send_weekly_pulse_email
)
from app.services.weekly_synthesis import WeeklyPulse


class TestEmailValidation:
    """Test email validation logic"""
    
    def test_validate_email_valid_addresses(self):
        """Test validation of valid email addresses"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.com",
            "user_123@test-domain.com"
        ]
        
        for email in valid_emails:
            assert EmailService.validate_email(email) is True
    
    def test_validate_email_invalid_addresses(self):
        """Test validation of invalid email addresses"""
        invalid_emails = [
            "",
            "not-an-email",
            "@example.com",
            "user@",
            "user@.com",
            "user @example.com",
            None,
            123
        ]
        
        for email in invalid_emails:
            assert EmailService.validate_email(email) is False
    
    def test_validate_emails_list(self):
        """Test validation of email list"""
        emails = [
            "valid1@example.com",
            "invalid-email",
            "valid2@example.com",
            "also-invalid",
            "valid3@test.com"
        ]
        
        valid, invalid = EmailService.validate_emails(emails)
        
        assert len(valid) == 3
        assert len(invalid) == 2
        assert "valid1@example.com" in valid
        assert "valid2@example.com" in valid
        assert "valid3@test.com" in valid
        assert "invalid-email" in invalid
        assert "also-invalid" in invalid


class TestEmailServiceInitialization:
    """Test EmailService initialization"""
    
    @patch.dict('os.environ', {'SMTP_USERNAME': 'test@example.com', 'SMTP_PASSWORD': 'password'})
    def test_initialization_with_env_vars(self):
        """Test initialization from environment variables"""
        service = EmailService()
        
        assert service.smtp_username == "test@example.com"
        assert service.smtp_password == "password"
        assert service.smtp_host == EmailService.SMTP_GMAIL['host']
        assert service.smtp_port == EmailService.SMTP_GMAIL['port']
    
    def test_initialization_with_parameters(self):
        """Test initialization with explicit parameters"""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=465,
            smtp_username="user@example.com",
            smtp_password="pass123"
        )
        
        assert service.smtp_host == "smtp.example.com"
        assert service.smtp_port == 465
        assert service.smtp_username == "user@example.com"
        assert service.smtp_password == "pass123"
    
    def test_initialization_missing_username(self):
        """Test initialization fails without username"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="SMTP username is required"):
                EmailService()
    
    def test_initialization_missing_password(self):
        """Test initialization fails without password"""
        with patch.dict('os.environ', {'SMTP_USERNAME': 'test@example.com'}, clear=True):
            with pytest.raises(ValueError, match="SMTP password is required"):
                EmailService()


class TestHTMLTemplateGeneration:
    """Test HTML email template generation"""
    
    def test_create_html_template_basic(self):
        """Test basic HTML template creation"""
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test Pulse",
            overview="This is a test overview",
            themes=[{"name": "Theme 1", "summary": "Summary 1"}],
            quotes=["Quote 1"],
            actions=["Action 1"]
        )
        
        html = service._create_html_template(pulse)
        
        assert "Test Pulse" in html
        assert "This is a test overview" in html
        assert "Theme 1" in html
        assert "Quote 1" in html
        assert "Action 1" in html
        assert "<html>" in html
        assert "</html>" in html
    
    def test_create_html_template_with_app_name(self):
        """Test HTML template with app name"""
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        
        html = service._create_html_template(pulse, app_name="WhatsApp")
        
        assert "WhatsApp" in html
    
    def test_create_html_template_audience_specific(self):
        """Test audience-specific styling"""
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        
        # Test product audience
        html_product = service._create_html_template(pulse, audience=EmailService.AUDIENCE_PRODUCT)
        assert "#007bff" in html_product  # Product blue
        
        # Test support audience
        html_support = service._create_html_template(pulse, audience=EmailService.AUDIENCE_SUPPORT)
        assert "#28a745" in html_support  # Support green
        
        # Test leadership audience
        html_leadership = service._create_html_template(pulse, audience=EmailService.AUDIENCE_LEADERSHIP)
        assert "#6f42c1" in html_leadership  # Leadership purple
    
    def test_create_html_template_escapes_html(self):
        """Test that HTML is properly escaped"""
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test <script>alert('xss')</script>",
            overview="Overview & more",
            themes=[{"name": "Theme <b>bold</b>", "summary": "Summary with 'quotes'"}],
            quotes=["Quote with \"quotes\""],
            actions=["Action & more"]
        )
        
        html = service._create_html_template(pulse)
        
        # Should escape HTML
        assert "&lt;script&gt;" in html
        assert "&amp;" in html
        assert "&quot;" in html
        assert "&#39;" in html
        # Should not contain raw HTML
        assert "<script>" not in html


class TestTextTemplateGeneration:
    """Test plain text email template generation"""
    
    def test_create_text_template(self):
        """Test plain text template creation"""
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test Pulse",
            overview="This is a test overview",
            themes=[{"name": "Theme 1", "summary": "Summary 1"}],
            quotes=["Quote 1"],
            actions=["Action 1"]
        )
        
        text = service._create_text_template(pulse)
        
        assert "Test Pulse" in text
        assert "This is a test overview" in text
        assert "Theme 1" in text
        assert "Quote 1" in text
        assert "Action 1" in text
        assert "WEEKLY PRODUCT PULSE" in text


class TestEmailSending:
    """Test email sending functionality via SMTP"""
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_weekly_pulse_success(self, mock_smtp_class):
        """Test successful email sending"""
        # Setup mock SMTP server
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test Pulse",
            overview="Overview",
            themes=[{"name": "Theme", "summary": "Summary"}],
            quotes=["Quote"],
            actions=["Action"]
        )
        
        result = service.send_weekly_pulse(
            to_emails=["recipient@example.com"],
            pulse=pulse
        )
        
        assert result['success'] is True
        assert result['sent_count'] == 1
        assert result['failed_count'] == 0
        assert len(result['errors']) == 0
        
        # Verify SMTP was called correctly
        mock_smtp_class.assert_called_once_with(service.smtp_host, service.smtp_port)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "password")
        mock_server.send_message.assert_called_once()
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_weekly_pulse_multiple_recipients(self, mock_smtp_class):
        """Test sending to multiple recipients"""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        
        result = service.send_weekly_pulse(
            to_emails=["user1@example.com", "user2@example.com"],
            pulse=pulse
        )
        
        assert result['sent_count'] == 2
        assert mock_server.send_message.call_count == 2
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_weekly_pulse_with_invalid_emails(self, mock_smtp_class):
        """Test sending with invalid email addresses"""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        
        result = service.send_weekly_pulse(
            to_emails=["valid@example.com", "invalid-email", "another@test.com"],
            pulse=pulse
        )
        
        # Should only send to valid emails
        assert result['sent_count'] == 2
        assert mock_server.send_message.call_count == 2
    
    def test_send_weekly_pulse_no_valid_emails(self):
        """Test sending with no valid emails raises error"""
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        
        with pytest.raises(EmailValidationError, match="No valid email addresses"):
            service.send_weekly_pulse(
                to_emails=["invalid-email", "also-invalid"],
                pulse=pulse
            )
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_weekly_pulse_auth_failure(self, mock_smtp_class):
        """Test handling of authentication failures"""
        import smtplib
        
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="wrong-password"
        )
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        
        result = service.send_weekly_pulse(
            to_emails=["test@example.com"],
            pulse=pulse
        )
        
        assert result['success'] is False
        assert result['sent_count'] == 0
        assert result['failed_count'] == 1
        assert len(result['errors']) == 1
        assert "authentication failed" in result['errors'][0].lower()
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_weekly_pulse_smtp_exception(self, mock_smtp_class):
        """Test handling of SMTP exceptions"""
        import smtplib
        
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPException("SMTP error")
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        
        result = service.send_weekly_pulse(
            to_emails=["test@example.com"],
            pulse=pulse
        )
        
        assert result['success'] is False
        assert result['failed_count'] == 1
        assert len(result['errors']) == 1
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_weekly_pulse_custom_subject(self, mock_smtp_class):
        """Test sending with custom subject"""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        
        result = service.send_weekly_pulse(
            to_emails=["test@example.com"],
            pulse=pulse,
            subject="Custom Subject Line"
        )
        
        assert result['success'] is True
        # Verify message was created with custom subject
        call_args = mock_server.send_message.call_args
        msg = call_args[0][0]
        assert msg['Subject'] == "Custom Subject Line"
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_weekly_pulse_no_tls(self, mock_smtp_class):
        """Test sending without TLS"""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password",
            use_tls=False
        )
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        
        result = service.send_weekly_pulse(
            to_emails=["test@example.com"],
            pulse=pulse
        )
        
        assert result['success'] is True
        # Should not call starttls when use_tls=False
        mock_server.starttls.assert_not_called()


class TestConvenienceFunction:
    """Test convenience function"""
    
    @patch('app.services.email_service.EmailService')
    def test_send_weekly_pulse_email_function(self, mock_service_class):
        """Test convenience function"""
        mock_service = MagicMock()
        mock_service.send_weekly_pulse.return_value = {
            'success': True,
            'sent_count': 1,
            'failed_count': 0,
            'errors': []
        }
        mock_service_class.return_value = mock_service
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        
        result = send_weekly_pulse_email(
            to_emails=["test@example.com"],
            pulse=pulse,
            smtp_username="user@example.com",
            smtp_password="pass"
        )
        
        assert result['success'] is True
        mock_service.send_weekly_pulse.assert_called_once()


class TestAudienceSpecificFormatting:
    """Test audience-specific formatting"""
    
    def test_get_audience_styles(self):
        """Test audience-specific styles"""
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        product_styles = service._get_audience_styles(EmailService.AUDIENCE_PRODUCT)
        assert product_styles['header_bg'] == '#007bff'
        
        support_styles = service._get_audience_styles(EmailService.AUDIENCE_SUPPORT)
        assert support_styles['header_bg'] == '#28a745'
        
        leadership_styles = service._get_audience_styles(EmailService.AUDIENCE_LEADERSHIP)
        assert leadership_styles['header_bg'] == '#6f42c1'
    
    def test_get_audience_header(self):
        """Test audience-specific headers"""
        service = EmailService(
            smtp_username="test@example.com",
            smtp_password="password"
        )
        
        product_header = service._get_audience_header(EmailService.AUDIENCE_PRODUCT, "WhatsApp")
        assert "Product Pulse" in product_header
        assert "WhatsApp" in product_header
        
        support_header = service._get_audience_header(EmailService.AUDIENCE_SUPPORT)
        assert "Support Insights" in support_header
        
        leadership_header = service._get_audience_header(EmailService.AUDIENCE_LEADERSHIP)
        assert "Executive Summary" in leadership_header


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
