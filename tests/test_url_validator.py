"""
Unit tests for URL Validation Service

Tests cover:
- URL format validation
- App ID extraction
- App existence verification
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.url_validator import (
    PlayStoreURLValidator,
    validate_play_store_url,
    extract_app_id,
    verify_app_exists
)


class TestURLFormatValidation:
    """Test URL format validation"""
    
    def test_valid_play_store_urls(self):
        """Test various valid Play Store URL formats"""
        validator = PlayStoreURLValidator()
        
        valid_urls = [
            "https://play.google.com/store/apps/details?id=com.example.app",
            "https://play.google.com/store/apps/details?id=com.whatsapp",
            "http://play.google.com/store/apps/details?id=com.spotify.music",
            "https://play.google.com/store/apps/details?id=com.google.android.gms&hl=en",
            "https://play.google.com/store/apps/details?id=com.example.app&hl=en_US&gl=US",
            "https://play.google.com.au/store/apps/details?id=com.example.app",
            "https://play.google.co.uk/store/apps/details?id=com.example.app",
            "https://play.google.co.in/store/apps/details?id=com.example.app",
        ]
        
        for url in valid_urls:
            assert validator.validate_play_store_url(url) is True, f"Should be valid: {url}"
    
    def test_invalid_play_store_urls(self):
        """Test various invalid URL formats"""
        validator = PlayStoreURLValidator()
        
        invalid_urls = [
            "https://example.com/app",
            "https://play.google.com/store/games/details?id=com.example.app",
            "https://apps.apple.com/app/id123456",
            "https://play.google.com/store/apps",
            "not-a-url",
            "",
            None,
            "ftp://play.google.com/store/apps/details?id=com.example.app",
        ]
        
        for url in invalid_urls:
            if url is None:
                assert validator.validate_play_store_url(url) is False
            else:
                assert validator.validate_play_store_url(url) is False, f"Should be invalid: {url}"
    
    def test_convenience_function(self):
        """Test the convenience function for URL validation"""
        assert validate_play_store_url("https://play.google.com/store/apps/details?id=com.example.app") is True
        assert validate_play_store_url("https://example.com") is False


class TestAppIDExtraction:
    """Test app ID extraction from URLs"""
    
    def test_extract_app_id_from_valid_urls(self):
        """Test extracting app IDs from various URL formats"""
        validator = PlayStoreURLValidator()
        
        test_cases = [
            ("https://play.google.com/store/apps/details?id=com.whatsapp", "com.whatsapp"),
            ("https://play.google.com/store/apps/details?id=com.spotify.music&hl=en", "com.spotify.music"),
            ("https://play.google.com/store/apps/details?id=com.google.android.gms", "com.google.android.gms"),
            ("https://play.google.com/store/apps/details?id=com.example.app&hl=en_US&gl=US", "com.example.app"),
        ]
        
        for url, expected_id in test_cases:
            app_id = validator.extract_app_id(url)
            assert app_id == expected_id, f"Expected {expected_id}, got {app_id} for URL: {url}"
    
    def test_extract_app_id_from_invalid_urls(self):
        """Test that invalid URLs return None"""
        validator = PlayStoreURLValidator()
        
        invalid_urls = [
            "https://example.com/app",
            "https://play.google.com/store/apps",
            "not-a-url",
            "",
            None,
        ]
        
        for url in invalid_urls:
            app_id = validator.extract_app_id(url)
            assert app_id is None, f"Should return None for invalid URL: {url}"
    
    def test_extract_app_id_without_id_parameter(self):
        """Test URLs without id parameter"""
        validator = PlayStoreURLValidator()
        
        # URL with valid format but no id parameter
        url = "https://play.google.com/store/apps/details"
        app_id = validator.extract_app_id(url)
        assert app_id is None
    
    def test_convenience_function(self):
        """Test the convenience function for app ID extraction"""
        url = "https://play.google.com/store/apps/details?id=com.example.app"
        app_id = extract_app_id(url)
        assert app_id == "com.example.app"


class TestAppIDValidation:
    """Test app ID format validation"""
    
    def test_valid_app_ids(self):
        """Test valid app ID formats"""
        validator = PlayStoreURLValidator()
        
        valid_ids = [
            "com.example.app",
            "com.whatsapp",
            "com.spotify.music",
            "com.google.android.gms",
            "com.example.subdomain.app",
            "com.example_app",
        ]
        
        for app_id in valid_ids:
            assert validator._is_valid_app_id(app_id) is True, f"Should be valid: {app_id}"
    
    def test_invalid_app_ids(self):
        """Test invalid app ID formats"""
        validator = PlayStoreURLValidator()
        
        invalid_ids = [
            "com.Example.app",  # Capital letters
            "com.example-app",  # Hyphens not allowed
            "123.com.example",  # Starts with number
            ".com.example",  # Starts with dot
            "com..example",  # Double dots
            "",
            None,
            "not an app id",
        ]
        
        for app_id in invalid_ids:
            assert validator._is_valid_app_id(app_id) is False, f"Should be invalid: {app_id}"


class TestAppExistenceVerification:
    """Test app existence verification"""
    
    def test_verify_existing_app(self):
        """Test verification of an existing app"""
        validator = PlayStoreURLValidator()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <html>
            <head><title>WhatsApp</title></head>
            <body>
                <h1 itemprop="name">WhatsApp</h1>
                <div class="rating">4.5</div>
                <button data-testid="install-button">Install</button>
            </body>
        </html>
        '''
        validator.session.get = Mock(return_value=mock_response)
        
        exists, error = validator.verify_app_exists("com.whatsapp")
        assert exists is True
        assert error is None
    
    def test_verify_nonexistent_app_404(self):
        """Test verification of non-existent app (404)"""
        validator = PlayStoreURLValidator()
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        validator.session.get = Mock(return_value=mock_response)
        
        exists, error = validator.verify_app_exists("com.nonexistent.app")
        assert exists is False
        assert "404" in error or "not found" in error.lower()
    
    def test_verify_nonexistent_app_error_page(self):
        """Test verification when Play Store returns error page"""
        validator = PlayStoreURLValidator()
        
        # Mock 200 response with error content
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <html>
            <body>
                <h1>We're sorry, the requested URL was not found</h1>
                <p>404 - App not found</p>
            </body>
        </html>
        '''
        validator.session.get = Mock(return_value=mock_response)
        
        exists, error = validator.verify_app_exists("com.nonexistent.app")
        assert exists is False
        assert "not found" in error.lower()
    
    def test_verify_app_rate_limit(self):
        """Test handling of rate limit (429)"""
        validator = PlayStoreURLValidator()
        
        # Mock 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        validator.session.get = Mock(return_value=mock_response)
        
        exists, error = validator.verify_app_exists("com.example.app")
        assert exists is False
        assert "rate limit" in error.lower()
    
    def test_verify_app_forbidden(self):
        """Test handling of forbidden access (403)"""
        validator = PlayStoreURLValidator()
        
        # Mock 403 response
        mock_response = Mock()
        mock_response.status_code = 403
        validator.session.get = Mock(return_value=mock_response)
        
        exists, error = validator.verify_app_exists("com.example.app")
        assert exists is False
        assert "forbidden" in error.lower() or "403" in error
    
    def test_verify_app_timeout(self):
        """Test handling of request timeout"""
        import requests.exceptions
        validator = PlayStoreURLValidator()
        
        # Mock timeout exception
        validator.session.get = Mock(side_effect=requests.exceptions.Timeout("Request timeout"))
        
        exists, error = validator.verify_app_exists("com.example.app")
        assert exists is False
        assert "timeout" in error.lower()
    
    def test_verify_app_connection_error(self):
        """Test handling of connection errors"""
        import requests.exceptions
        validator = PlayStoreURLValidator()
        
        # Mock connection error
        validator.session.get = Mock(side_effect=requests.exceptions.ConnectionError("Connection failed"))
        
        exists, error = validator.verify_app_exists("com.example.app")
        assert exists is False
        assert "connection" in error.lower() or "network" in error.lower()
    
    def test_verify_invalid_app_id(self):
        """Test verification with invalid app ID format"""
        validator = PlayStoreURLValidator()
        
        exists, error = validator.verify_app_exists("invalid-app-id")
        assert exists is False
        assert "Invalid app ID format" in error
    
    def test_verify_empty_app_id(self):
        """Test verification with empty app ID"""
        validator = PlayStoreURLValidator()
        
        exists, error = validator.verify_app_exists("")
        assert exists is False
        assert "Invalid app ID format" in error
    
    def test_verify_none_app_id(self):
        """Test verification with None app ID"""
        validator = PlayStoreURLValidator()
        
        exists, error = validator.verify_app_exists(None)
        assert exists is False
        assert "Invalid app ID format" in error
    
    def test_convenience_function(self):
        """Test the convenience function for app verification"""
        with patch('app.services.url_validator.PlayStoreURLValidator') as MockValidator:
            mock_instance = Mock()
            mock_instance.verify_app_exists.return_value = (True, None)
            MockValidator.return_value = mock_instance
            
            exists, error = verify_app_exists("com.example.app")
            assert exists is True
            assert error is None


class TestCompleteValidation:
    """Test complete validation workflow"""
    
    def test_validate_and_verify_success(self):
        """Test complete validation with successful result"""
        validator = PlayStoreURLValidator()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <html>
            <h1 itemprop="name">WhatsApp</h1>
            <div class="rating">4.5</div>
        </html>
        '''
        validator.session.get = Mock(return_value=mock_response)
        
        url = "https://play.google.com/store/apps/details?id=com.whatsapp"
        result = validator.validate_and_verify(url)
        
        assert result['valid'] is True
        assert result['app_id'] == "com.whatsapp"
        assert result['app_exists'] is True
        assert result['error'] is None
    
    def test_validate_and_verify_invalid_url(self):
        """Test complete validation with invalid URL"""
        validator = PlayStoreURLValidator()
        
        url = "https://example.com/app"
        result = validator.validate_and_verify(url)
        
        assert result['valid'] is False
        assert result['app_id'] is None
        assert result['app_exists'] is None
        assert result['error'] is not None
    
    def test_validate_and_verify_nonexistent_app(self):
        """Test complete validation with non-existent app"""
        validator = PlayStoreURLValidator()
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        validator.session.get = Mock(return_value=mock_response)
        
        url = "https://play.google.com/store/apps/details?id=com.nonexistent.app"
        result = validator.validate_and_verify(url)
        
        assert result['valid'] is True
        assert result['app_id'] == "com.nonexistent.app"
        assert result['app_exists'] is False
        assert result['error'] is not None


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_retry_strategy_configuration(self):
        """Test that retry strategy is properly configured"""
        validator = PlayStoreURLValidator(max_retries=5)
        assert validator.max_retries == 5
    
    def test_timeout_configuration(self):
        """Test that timeout is properly configured"""
        validator = PlayStoreURLValidator(timeout=20)
        assert validator.timeout == 20
    
    def test_unexpected_exception_handling(self):
        """Test handling of unexpected exceptions"""
        validator = PlayStoreURLValidator()
        
        # Mock unexpected exception
        validator.session.get = Mock(side_effect=ValueError("Unexpected error"))
        
        exists, error = validator.verify_app_exists("com.example.app")
        assert exists is False
        assert "error" in error.lower()
    
    def test_url_with_whitespace(self):
        """Test URL validation with whitespace"""
        validator = PlayStoreURLValidator()
        
        url = "  https://play.google.com/store/apps/details?id=com.example.app  "
        assert validator.validate_play_store_url(url) is True
        
        app_id = validator.extract_app_id(url)
        assert app_id == "com.example.app"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

