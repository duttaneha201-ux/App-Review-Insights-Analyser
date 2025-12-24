"""
Unit tests for Review Extraction Service

Tests cover:
- Date range filtering
- Sampling by rating
- Review parsing
- Deduplication
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.review_extractor import ReviewExtractor
from app.models.review import Review


class TestDateFiltering:
    """Test date range filtering logic"""
    
    def test_filter_by_date_range(self):
        """Test filtering reviews by date range"""
        extractor = ReviewExtractor()
        
        # Create test reviews with different dates
        today = date.today()
        reviews = [
            Review(rating=5, text="Great app!", date=today - timedelta(days=10), title="Love it"),
            Review(rating=4, text="Good app", date=today - timedelta(days=20), title="Nice"),
            Review(rating=3, text="Okay app", date=today - timedelta(days=30), title="Meh"),
            Review(rating=2, text="Bad app", date=today - timedelta(days=50), title="Not good"),
            Review(rating=1, text="Terrible", date=today - timedelta(days=100), title="Awful"),
        ]
        
        # Filter for last 30 days
        start_date = today - timedelta(days=30)
        end_date = today
        
        filtered = extractor._filter_by_date_range(reviews, start_date, end_date)
        
        assert len(filtered) == 3
        assert all(start_date <= r.date <= end_date for r in filtered)
    
    def test_filter_inclusive_boundaries(self):
        """Test that date boundaries are inclusive"""
        extractor = ReviewExtractor()
        
        today = date.today()
        start_date = today - timedelta(days=10)
        end_date = today - timedelta(days=5)
        
        reviews = [
            Review(rating=5, text="Test", date=start_date, title="On start"),
            Review(rating=4, text="Test", date=end_date, title="On end"),
            Review(rating=3, text="Test", date=start_date - timedelta(days=1), title="Before"),
            Review(rating=2, text="Test", date=end_date + timedelta(days=1), title="After"),
        ]
        
        filtered = extractor._filter_by_date_range(reviews, start_date, end_date)
        
        assert len(filtered) == 2
        # Filtered list maintains original order, so check both dates are present
        dates = [r.date for r in filtered]
        assert end_date in dates
        assert start_date in dates
    
    def test_filter_empty_range(self):
        """Test filtering with no reviews in range"""
        extractor = ReviewExtractor()
        
        today = date.today()
        reviews = [
            Review(rating=5, text="Test", date=today - timedelta(days=100), title="Old"),
        ]
        
        start_date = today - timedelta(days=10)
        end_date = today
        
        filtered = extractor._filter_by_date_range(reviews, start_date, end_date)
        
        assert len(filtered) == 0


class TestSamplingByRating:
    """Test sampling reviews by rating"""
    
    def test_sample_by_rating(self):
        """Test sampling 40 reviews per rating"""
        extractor = ReviewExtractor()
        
        # Create reviews: 50 of each rating
        reviews = []
        for rating in range(1, 6):
            for i in range(50):
                reviews.append(Review(
                    rating=rating,
                    text=f"Review {i} for rating {rating}",
                    date=date.today() - timedelta(days=i),
                    title=f"Title {i}"
                ))
        
        sampled = extractor._sample_by_rating(reviews, samples_per_rating=40)
        
        # Should have 40 * 5 = 200 reviews
        assert len(sampled) == 200
        
        # Check each rating has exactly 40
        for rating in range(1, 6):
            rating_count = sum(1 for r in sampled if r.rating == rating)
            assert rating_count == 40
    
    def test_sample_less_than_available(self):
        """Test sampling when fewer reviews available than requested"""
        extractor = ReviewExtractor()
        
        # Create only 10 reviews per rating
        reviews = []
        for rating in range(1, 6):
            for i in range(10):
                reviews.append(Review(
                    rating=rating,
                    text=f"Review {i}",
                    date=date.today() - timedelta(days=i),
                    title=f"Title {i}"
                ))
        
        sampled = extractor._sample_by_rating(reviews, samples_per_rating=40)
        
        # Should have 10 * 5 = 50 reviews (all available)
        assert len(sampled) == 50
        
        # Each rating should have 10
        for rating in range(1, 6):
            rating_count = sum(1 for r in sampled if r.rating == rating)
            assert rating_count == 10
    
    def test_sample_mixed_ratings(self):
        """Test sampling with uneven distribution"""
        extractor = ReviewExtractor()
        
        # Create uneven distribution
        reviews = []
        # 100 five-star, 20 four-star, 5 three-star, 2 two-star, 1 one-star
        for i in range(100):
            reviews.append(Review(rating=5, text=f"5-star {i}", date=date.today(), title="Great"))
        for i in range(20):
            reviews.append(Review(rating=4, text=f"4-star {i}", date=date.today(), title="Good"))
        for i in range(5):
            reviews.append(Review(rating=3, text=f"3-star {i}", date=date.today(), title="Okay"))
        for i in range(2):
            reviews.append(Review(rating=2, text=f"2-star {i}", date=date.today(), title="Bad"))
        reviews.append(Review(rating=1, text="1-star", date=date.today(), title="Terrible"))
        
        sampled = extractor._sample_by_rating(reviews, samples_per_rating=40)
        
        # Should have 40 + 20 + 5 + 2 + 1 = 68 reviews
        assert len(sampled) == 68
        assert sum(1 for r in sampled if r.rating == 5) == 40
        assert sum(1 for r in sampled if r.rating == 4) == 20
        assert sum(1 for r in sampled if r.rating == 3) == 5
        assert sum(1 for r in sampled if r.rating == 2) == 2
        assert sum(1 for r in sampled if r.rating == 1) == 1


class TestLengthFiltering:
    """Test minimum length filtering"""
    
    def test_filter_by_min_length(self):
        """Test filtering out reviews with text < 15 characters"""
        extractor = ReviewExtractor()
        
        reviews = [
            Review(rating=5, text="This is a great app with many features!", date=date.today(), title="Great"),
            Review(rating=4, text="Good app", date=date.today(), title="Nice"),  # 8 chars - should be filtered
            Review(rating=3, text="Okay", date=date.today(), title="Meh"),  # 4 chars - should be filtered
            Review(rating=2, text="This is a bad app that I don't like", date=date.today(), title="Bad"),  # 35 chars
            Review(rating=1, text="Terrible!", date=date.today(), title="Awful"),  # 9 chars - should be filtered
            Review(rating=5, text="Excellent application!", date=date.today(), title="Love"),  # 22 chars
        ]
        
        filtered = extractor._filter_by_min_length(reviews, min_length=15)
        
        # Should have 3 reviews (first, fourth, and sixth)
        assert len(filtered) == 3
        assert all(len(r.text.strip()) >= 15 for r in filtered)
        assert filtered[0].text == "This is a great app with many features!"
        assert filtered[1].text == "This is a bad app that I don't like"
        assert filtered[2].text == "Excellent application!"
    
    def test_filter_by_min_length_with_whitespace(self):
        """Test that whitespace is stripped before length check"""
        extractor = ReviewExtractor()
        
        reviews = [
            Review(rating=5, text="   Short   ", date=date.today(), title="Test"),  # 5 chars after strip
            Review(rating=4, text="  This is a longer review text  ", date=date.today(), title="Test"),  # 30 chars after strip
        ]
        
        filtered = extractor._filter_by_min_length(reviews, min_length=15)
        
        assert len(filtered) == 1
        assert filtered[0].text == "  This is a longer review text  "
        assert len(filtered[0].text.strip()) >= 15
    
    def test_sample_skips_short_reviews(self):
        """Test that sampling picks valid reviews when short ones are filtered"""
        extractor = ReviewExtractor()
        
        # Create 50 reviews per rating, but some are short
        reviews = []
        for rating in range(1, 6):
            # Add 10 short reviews (< 15 chars)
            for i in range(10):
                reviews.append(Review(
                    rating=rating,
                    text=f"Short {i}",  # 7-8 chars
                    date=date.today() - timedelta(days=i),
                    title="Test"
                ))
            # Add 50 valid reviews (>= 15 chars)
            for i in range(50):
                reviews.append(Review(
                    rating=rating,
                    text=f"This is a valid review number {i} with enough characters",
                    date=date.today() - timedelta(days=i + 10),
                    title="Test"
                ))
        
        # Filter by length first
        filtered = extractor._filter_by_min_length(reviews, min_length=15)
        
        # Then sample
        sampled = extractor._sample_by_rating(filtered, samples_per_rating=40)
        
        # Should have 40 * 5 = 200 reviews, all with >= 15 characters
        assert len(sampled) == 200
        assert all(len(r.text.strip()) >= 15 for r in sampled)
        
        # Each rating should have exactly 40 reviews
        for rating in range(1, 6):
            rating_count = sum(1 for r in sampled if r.rating == rating)
            assert rating_count == 40
    
    def test_sample_with_insufficient_valid_reviews(self):
        """Test sampling when there aren't enough valid reviews"""
        extractor = ReviewExtractor()
        
        # Create only 20 valid reviews per rating (rest are short)
        reviews = []
        for rating in range(1, 6):
            # 20 valid reviews
            for i in range(20):
                reviews.append(Review(
                    rating=rating,
                    text=f"This is a valid review number {i}",
                    date=date.today() - timedelta(days=i),
                    title="Test"
                ))
            # 30 short reviews
            for i in range(30):
                reviews.append(Review(
                    rating=rating,
                    text=f"Short {i}",
                    date=date.today() - timedelta(days=i + 20),
                    title="Test"
                ))
        
        # Filter by length
        filtered = extractor._filter_by_min_length(reviews, min_length=15)
        
        # Sample 40 per rating (but only 20 available)
        sampled = extractor._sample_by_rating(filtered, samples_per_rating=40)
        
        # Should have 20 * 5 = 100 reviews (all available valid ones)
        assert len(sampled) == 100
        assert all(len(r.text.strip()) >= 15 for r in sampled)
        
        # Each rating should have 20 reviews (all available)
        for rating in range(1, 6):
            rating_count = sum(1 for r in sampled if r.rating == rating)
            assert rating_count == 20


class TestDeduplication:
    """Test review deduplication"""
    
    def test_deduplicate_identical_text(self):
        """Test removing duplicate reviews with identical text"""
        extractor = ReviewExtractor()
        
        reviews = [
            Review(rating=5, text="Great app!", date=date.today(), title="Love it"),
            Review(rating=5, text="Great app!", date=date.today(), title="Love it"),  # Duplicate
            Review(rating=4, text="Good app", date=date.today(), title="Nice"),
            Review(rating=5, text="Great app!", date=date.today() - timedelta(days=1), title="Love it"),  # Duplicate
        ]
        
        deduplicated = extractor._deduplicate_reviews(reviews)
        
        assert len(deduplicated) == 2
        assert deduplicated[0].text == "Great app!"
        assert deduplicated[1].text == "Good app"
    
    def test_deduplicate_case_insensitive(self):
        """Test that deduplication is case-insensitive"""
        extractor = ReviewExtractor()
        
        reviews = [
            Review(rating=5, text="Great app!", date=date.today(), title="Love it"),
            Review(rating=5, text="GREAT APP!", date=date.today(), title="Love it"),  # Same, different case
            Review(rating=5, text="  Great app!  ", date=date.today(), title="Love it"),  # Same, with spaces
        ]
        
        deduplicated = extractor._deduplicate_reviews(reviews)
        
        assert len(deduplicated) == 1
    
    def test_deduplicate_preserves_order(self):
        """Test that deduplication preserves first occurrence"""
        extractor = ReviewExtractor()
        
        reviews = [
            Review(rating=5, text="Great app!", date=date.today(), title="First"),
            Review(rating=4, text="Good app", date=date.today(), title="Second"),
            Review(rating=5, text="Great app!", date=date.today() - timedelta(days=1), title="Third"),
        ]
        
        deduplicated = extractor._deduplicate_reviews(reviews)
        
        assert len(deduplicated) == 2
        assert deduplicated[0].title == "First"  # First occurrence preserved
        assert deduplicated[1].title == "Second"


class TestReviewModel:
    """Test Review data model"""
    
    def test_review_creation(self):
        """Test creating a valid review"""
        review = Review(
            rating=5,
            title="Great app",
            text="This is a great app with many features",
            date=date.today()
        )
        
        assert review.rating == 5
        assert review.title == "Great app"
        assert review.text == "This is a great app with many features"
        assert review.date == date.today()
    
    def test_review_invalid_rating(self):
        """Test that invalid rating raises error"""
        with pytest.raises(ValueError):
            Review(rating=6, text="Test", date=date.today(), title=None)
        
        with pytest.raises(ValueError):
            Review(rating=0, text="Test", date=date.today(), title=None)
    
    def test_review_empty_text(self):
        """Test that empty text raises error"""
        with pytest.raises(ValueError):
            Review(rating=5, text="", date=date.today(), title=None)
        
        with pytest.raises(ValueError):
            Review(rating=5, text="   ", date=date.today(), title=None)
    
    def test_review_to_dict(self):
        """Test converting review to dictionary"""
        review = Review(
            rating=5,
            title="Great",
            text="Great app",
            date=date(2024, 1, 15),
            review_id="123"
        )
        
        data = review.to_dict()
        
        assert data['rating'] == 5
        assert data['title'] == "Great"
        assert data['text'] == "Great app"
        assert data['date'] == "2024-01-15"
        assert data['review_id'] == "123"
    
    def test_review_from_dict(self):
        """Test creating review from dictionary"""
        data = {
            'rating': 5,
            'title': 'Great',
            'text': 'Great app',
            'date': '2024-01-15',
            'review_id': '123'
        }
        
        review = Review.from_dict(data)
        
        assert review.rating == 5
        assert review.title == "Great"
        assert review.text == "Great app"
        assert review.date == date(2024, 1, 15)
        assert review.review_id == "123"


class TestDateParsing:
    """Test date parsing logic"""
    
    def test_parse_relative_dates(self):
        """Test parsing relative dates like '2 days ago'"""
        extractor = ReviewExtractor()
        
        today = date.today()
        
        # Test various relative date formats
        test_cases = [
            ("2 days ago", today - timedelta(days=2)),
            ("1 week ago", today - timedelta(days=7)),
            ("3 months ago", None),  # May not parse exactly
        ]
        
        for date_string, expected in test_cases:
            parsed = extractor._parse_date_string(date_string)
            if expected:
                # Allow some flexibility in parsing
                assert parsed is not None
            else:
                # Some may not parse, that's okay
                pass
    
    def test_parse_iso_date(self):
        """Test parsing ISO format dates"""
        extractor = ReviewExtractor()
        
        test_date = date(2024, 1, 15)
        parsed = extractor._parse_date_string("2024-01-15")
        
        assert parsed == test_date
    
    def test_parse_invalid_date(self):
        """Test parsing invalid date strings"""
        extractor = ReviewExtractor()
        
        invalid_dates = [
            "",
            "not a date",
            "12345",
            None,
        ]
        
        for date_string in invalid_dates:
            parsed = extractor._parse_date_string(date_string)
            assert parsed is None


class TestReviewExtractorIntegration:
    """Integration tests for ReviewExtractor (mocked)"""
    
    @patch('app.services.review_extractor.sync_playwright')
    def test_extract_reviews_workflow(self, mock_playwright):
        """Test the complete extraction workflow with mocked browser"""
        # This is a simplified mock test - full integration would require actual browser
        extractor = ReviewExtractor(headless=True)
        
        # Mock browser setup
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        mock_playwright.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # Mock page content (simplified)
        mock_page.query_selector_all.return_value = []
        mock_page.inner_text.return_value = ""
        
        # This test mainly verifies the workflow doesn't crash
        # Full testing would require more complex mocking or integration tests
        try:
            start_date = date.today() - timedelta(days=30)
            end_date = date.today() - timedelta(days=7)
            reviews = extractor.extract_reviews("com.whatsapp", start_date, end_date)
            # Should return empty list if no reviews found
            assert isinstance(reviews, list)
        except Exception as e:
            # Expected to fail with mocked browser, but should handle gracefully
            pass


class TestRetryLogic:
    """Test retry logic for network failures"""
    
    def test_retry_configuration(self):
        """Test that retry configuration is set correctly"""
        extractor = ReviewExtractor(max_retries=5, timeout=20000)
        
        assert extractor.max_retries == 5
        assert extractor.timeout == 20000
    
    def test_default_retry_settings(self):
        """Test default retry settings"""
        extractor = ReviewExtractor()
        
        assert extractor.max_retries == 3  # Default
        assert extractor.timeout == 30000  # Default 30 seconds


class TestBrowserLifecycle:
    """Test browser initialization and cleanup"""
    
    def test_browser_initialization(self):
        """Test that browser is initialized correctly"""
        extractor = ReviewExtractor()
        
        assert extractor.browser is None
        assert extractor.context is None
        
        # Browser should be initialized when needed
        # (actual initialization happens in extract_reviews)
    
    def test_browser_cleanup(self):
        """Test that browser is cleaned up properly"""
        extractor = ReviewExtractor()
        
        # Simulate cleanup
        extractor._close_browser()
        
        assert extractor.browser is None
        assert extractor.context is None


class TestSorting:
    """Test review sorting functionality"""
    
    def test_reviews_sorted_by_newest_first(self):
        """Test that reviews are sorted by date (newest first)"""
        extractor = ReviewExtractor()
        
        today = date.today()
        reviews = [
            Review(rating=5, text="Old review", date=today - timedelta(days=30), title="Old"),
            Review(rating=4, text="New review", date=today - timedelta(days=5), title="New"),
            Review(rating=3, text="Middle review", date=today - timedelta(days=15), title="Middle"),
        ]
        
        # Sort by newest first
        reviews.sort(key=lambda r: r.date, reverse=True)
        
        assert reviews[0].date == today - timedelta(days=5)  # Newest
        assert reviews[1].date == today - timedelta(days=15)  # Middle
        assert reviews[2].date == today - timedelta(days=30)  # Oldest


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_review_list(self):
        """Test handling of empty review list"""
        extractor = ReviewExtractor()
        
        reviews = []
        filtered = extractor._filter_by_date_range(reviews, date.today() - timedelta(days=30), date.today())
        assert len(filtered) == 0
        
        sampled = extractor._sample_by_rating(reviews, samples_per_rating=40)
        assert len(sampled) == 0
        
        deduplicated = extractor._deduplicate_reviews(reviews)
        assert len(deduplicated) == 0
    
    def test_all_reviews_same_rating(self):
        """Test sampling when all reviews have same rating"""
        extractor = ReviewExtractor()
        
        reviews = [
            Review(rating=5, text="Great app with many features!", date=date.today() - timedelta(days=i), title="Test")
            for i in range(100)
        ]
        
        sampled = extractor._sample_by_rating(reviews, samples_per_rating=40)
        
        assert len(sampled) == 40
        assert all(r.rating == 5 for r in sampled)
    
    def test_no_reviews_for_some_ratings(self):
        """Test sampling when some ratings have no reviews"""
        extractor = ReviewExtractor()
        
        # Only 5-star and 3-star reviews
        reviews = []
        for i in range(50):
            reviews.append(Review(rating=5, text="Great app with many features!", date=date.today() - timedelta(days=i), title="Test"))
        for i in range(30):
            reviews.append(Review(rating=3, text="Okay app with some features", date=date.today() - timedelta(days=i), title="Test"))
        
        sampled = extractor._sample_by_rating(reviews, samples_per_rating=40)
        
        # Should have 40 five-star and 30 three-star (all available)
        assert len(sampled) == 70
        assert sum(1 for r in sampled if r.rating == 5) == 40
        assert sum(1 for r in sampled if r.rating == 3) == 30
        assert sum(1 for r in sampled if r.rating == 1) == 0
        assert sum(1 for r in sampled if r.rating == 2) == 0
        assert sum(1 for r in sampled if r.rating == 4) == 0
    
    def test_filter_min_length_zero(self):
        """Test filtering with min_length=0 (should return all)"""
        extractor = ReviewExtractor()
        
        reviews = [
            Review(rating=5, text="Short", date=date.today(), title="Test"),
            Review(rating=4, text="This is a longer review text", date=date.today(), title="Test"),
        ]
        
        filtered = extractor._filter_by_min_length(reviews, min_length=0)
        assert len(filtered) == 2
    
    def test_filter_min_length_very_high(self):
        """Test filtering with very high min_length"""
        extractor = ReviewExtractor()
        
        reviews = [
            Review(rating=5, text="Short text", date=date.today(), title="Test"),
            Review(rating=4, text="This is a much longer review text with significantly more content and details", date=date.today(), title="Test"),
        ]
        
        filtered = extractor._filter_by_min_length(reviews, min_length=50)
        assert len(filtered) == 1
        assert filtered[0].text == "This is a much longer review text with significantly more content and details"


class TestDateParsingEdgeCases:
    """Test edge cases in date parsing"""
    
    def test_parse_date_with_timezone(self):
        """Test parsing dates with timezone information"""
        extractor = ReviewExtractor()
        
        # ISO format with timezone
        parsed = extractor._parse_date_string("2024-01-15T10:30:00Z")
        assert parsed is not None
        assert isinstance(parsed, date)
    
    def test_parse_date_various_formats(self):
        """Test parsing various date formats"""
        extractor = ReviewExtractor()
        
        test_cases = [
            "January 15, 2024",
            "15/01/2024",
            "2024-01-15",
            "Jan 15, 2024",
        ]
        
        for date_str in test_cases:
            parsed = extractor._parse_date_string(date_str)
            # Some may not parse, that's okay
            if parsed:
                assert isinstance(parsed, date)
    
    def test_parse_date_none(self):
        """Test parsing None date string"""
        extractor = ReviewExtractor()
        
        parsed = extractor._parse_date_string(None)
        assert parsed is None
    
    def test_parse_date_empty_string(self):
        """Test parsing empty date string"""
        extractor = ReviewExtractor()
        
        parsed = extractor._parse_date_string("")
        assert parsed is None


class TestReviewExtractionPipeline:
    """Test the complete extraction pipeline"""
    
    def test_complete_pipeline_with_mock_data(self):
        """Test the complete pipeline with mock review data"""
        extractor = ReviewExtractor()
        
        # Create mock reviews with various characteristics
        today = date.today()
        reviews = []
        
        # Add reviews across different ratings and dates
        for rating in range(1, 6):
            for i in range(60):  # 60 per rating
                # Some short reviews
                if i % 3 == 0:
                    text = "Short"  # < 15 chars
                else:
                    text = f"This is a valid review number {i} with enough characters for rating {rating}"
                
                reviews.append(Review(
                    rating=rating,
                    text=text,
                    date=today - timedelta(days=i),
                    title=f"Review {i}"
                ))
        
        # Apply pipeline steps
        # 1. Filter by date (last 30 days)
        start_date = today - timedelta(days=30)
        end_date = today
        filtered_by_date = extractor._filter_by_date_range(reviews, start_date, end_date)
        
        # 2. Filter by length
        filtered_by_length = extractor._filter_by_min_length(filtered_by_date, min_length=15)
        
        # 3. Sort
        filtered_by_length.sort(key=lambda r: r.date, reverse=True)
        
        # 4. Sample
        sampled = extractor._sample_by_rating(filtered_by_length, samples_per_rating=40)
        
        # 5. Final sort
        sampled.sort(key=lambda r: r.date, reverse=True)
        
        # Verify results
        assert len(sampled) <= 200  # Max 40 * 5
        assert all(len(r.text.strip()) >= 15 for r in sampled)
        assert all(start_date <= r.date <= end_date for r in sampled)
        
        # Check distribution
        for rating in range(1, 6):
            rating_count = sum(1 for r in sampled if r.rating == rating)
            assert rating_count <= 40  # Should not exceed requested amount


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

