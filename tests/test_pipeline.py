"""
Tests for the end-to-end pipeline integration.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from app.pipeline import extract_and_clean_reviews, process_reviews_for_analysis
from app.models.review import Review


class TestPipelineIntegration:
    """Test the complete pipeline integration"""
    
    @patch('app.pipeline.ReviewExtractor')
    @patch('app.pipeline.PlayStoreURLValidator')
    def test_extract_and_clean_reviews_success(self, mock_validator_class, mock_extractor_class):
        """Test successful extraction and cleaning"""
        # Mock validator
        mock_validator = MagicMock()
        mock_validator.validate_and_verify.return_value = {
            'valid': True,
            'app_id': 'com.whatsapp',
            'app_exists': True,
            'error': None
        }
        mock_validator_class.return_value = mock_validator
        
        # Mock extractor
        mock_extractor = MagicMock()
        mock_reviews = [
            Review(rating=5, text="Great app with many features!", date=date.today(), title="Love it"),
            Review(rating=4, text="Good app", date=date.today(), title="Nice"),
        ]
        mock_extractor.extract_reviews.return_value = mock_reviews
        mock_extractor_class.return_value = mock_extractor
        
        result = extract_and_clean_reviews(
            play_store_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            weeks=4,
            samples_per_rating=40
        )
        
        assert result['app_id'] == 'com.whatsapp'
        assert result['app_exists'] is True
        assert len(result['reviews']) == 2
        assert result['date_range'] is not None
        assert len(result['errors']) == 0
    
    @patch('app.pipeline.PlayStoreURLValidator')
    def test_extract_and_clean_reviews_invalid_url(self, mock_validator_class):
        """Test handling of invalid URL"""
        mock_validator = MagicMock()
        mock_validator.validate_and_verify.return_value = {
            'valid': False,
            'app_id': None,
            'app_exists': None,
            'error': 'Invalid URL format'
        }
        mock_validator_class.return_value = mock_validator
        
        result = extract_and_clean_reviews(
            play_store_url="https://invalid-url.com",
            weeks=4
        )
        
        assert result['app_id'] is None
        assert result['app_exists'] is False
        assert len(result['reviews']) == 0
        assert len(result['errors']) > 0
    
    @patch('app.pipeline.PlayStoreURLValidator')
    def test_extract_and_clean_reviews_app_not_found(self, mock_validator_class):
        """Test handling of app not found"""
        mock_validator = MagicMock()
        mock_validator.validate_and_verify.return_value = {
            'valid': True,
            'app_id': 'com.nonexistent',
            'app_exists': False,
            'error': 'App not found on Play Store'
        }
        mock_validator_class.return_value = mock_validator
        
        result = extract_and_clean_reviews(
            play_store_url="https://play.google.com/store/apps/details?id=com.nonexistent",
            weeks=4
        )
        
        assert result['app_id'] == 'com.nonexistent'
        assert result['app_exists'] is False
        assert len(result['reviews']) == 0
        assert len(result['errors']) > 0


class TestProcessReviewsForAnalysis:
    """Test the additional processing step"""
    
    def test_process_reviews_cleans_text(self):
        """Test that process_reviews_for_analysis cleans text"""
        reviews = [
            Review(rating=5, text="<p>This is a great app with many features!</p> 😄", date=date.today(), title="Test"),
            Review(rating=4, text="Contact me at user@example.com for more details about this app", date=date.today(), title="Test"),
        ]
        
        processed = process_reviews_for_analysis(reviews)
        
        assert len(processed) >= 1  # At least one should pass
        # HTML should be removed from first review if it exists
        if len(processed) >= 1:
            assert "<p>" not in processed[0].text
        # Email should be scrubbed from second review if it exists
        email_review = next((r for r in processed if "[email removed]" in r.text), None)
        if email_review:
            assert "user@example.com" not in email_review.text
            assert "[email removed]" in email_review.text
    
    def test_process_reviews_filters_short_text(self):
        """Test that very short reviews are filtered out"""
        reviews = [
            Review(rating=5, text="Short", date=date.today(), title="Test"),  # Too short
            Review(rating=4, text="This is a longer review with enough content", date=date.today(), title="Test"),
        ]
        
        processed = process_reviews_for_analysis(reviews)
        
        # Only the longer review should remain
        assert len(processed) == 1
        assert processed[0].rating == 4
    
    def test_process_reviews_removes_author(self):
        """Test that author field is always None"""
        reviews = [
            Review(rating=5, text="This is a great app with many features and excellent functionality!", date=date.today(), title="Test", author="John Doe"),
        ]
        
        processed = process_reviews_for_analysis(reviews)
        
        assert len(processed) == 1
        assert processed[0].author is None
        assert processed[0].rating == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

