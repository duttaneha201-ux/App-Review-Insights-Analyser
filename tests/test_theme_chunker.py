"""
Unit tests for Theme Chunking Engine

Tests cover:
- Week-based chunking
- JSON parsing
- Theme aggregation
- Edge cases
"""

import pytest
import json
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.theme_chunker import (
    ThemeChunker,
    ThemeChunk,
    AggregatedTheme,
    chunk_reviews_by_week
)
from app.models.review import Review
from app.services.llm_orchestrator import LLMOrchestrator


class TestWeekChunking:
    """Test week-based chunking logic"""
    
    def test_chunk_reviews_by_week(self):
        """Test chunking reviews into weeks"""
        today = date.today()
        reviews = [
            Review(rating=5, text="Great app!", date=today - timedelta(days=5), title="Test"),
            Review(rating=4, text="Good app", date=today - timedelta(days=6), title="Test"),
            Review(rating=3, text="Okay app", date=today - timedelta(days=12), title="Test"),
            Review(rating=2, text="Bad app", date=today - timedelta(days=13), title="Test"),
        ]
        
        start_date = today - timedelta(days=20)
        end_date = today
        
        week_chunks = chunk_reviews_by_week(reviews, start_date, end_date)
        
        # Should have at least one week
        assert len(week_chunks) >= 1
        
        # All reviews should be in chunks
        total_in_chunks = sum(len(reviews) for reviews in week_chunks.values())
        assert total_in_chunks == len(reviews)
    
    def test_chunk_reviews_filters_by_date_range(self):
        """Test that chunking respects date range"""
        today = date.today()
        reviews = [
            Review(rating=5, text="Recent", date=today - timedelta(days=5), title="Test"),
            Review(rating=4, text="Old", date=today - timedelta(days=100), title="Test"),
        ]
        
        start_date = today - timedelta(days=10)
        end_date = today
        
        week_chunks = chunk_reviews_by_week(reviews, start_date, end_date)
        
        # Only recent review should be included
        total_in_chunks = sum(len(reviews) for reviews in week_chunks.values())
        assert total_in_chunks == 1
    
    def test_chunk_reviews_sorts_by_date(self):
        """Test that reviews within a week are sorted by date"""
        today = date.today()
        reviews = [
            Review(rating=5, text="Newer", date=today - timedelta(days=1), title="Test"),
            Review(rating=4, text="Older", date=today - timedelta(days=3), title="Test"),
        ]
        
        start_date = today - timedelta(days=10)
        end_date = today
        
        week_chunks = chunk_reviews_by_week(reviews, start_date, end_date)
        
        # Reviews should be sorted newest first
        for week_reviews in week_chunks.values():
            dates = [r.date for r in week_reviews]
            assert dates == sorted(dates, reverse=True)


class TestJSONParsing:
    """Test JSON parsing from LLM responses"""
    
    def test_parse_valid_json_response(self):
        """Test parsing valid JSON response"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        # Mock parse_json_response to return the expected data
        mock_orchestrator.parse_json_response.return_value = [
            {
                "theme": "Performance Issues",
                "key_points": ["App is slow", "Crashes frequently"],
                "candidate_quotes": ["The app crashes all the time", "Very slow"]
            }
        ]
        chunker = ThemeChunker(orchestrator=mock_orchestrator)
        
        # Valid JSON response
        json_response = json.dumps([
            {
                "theme": "Performance Issues",
                "key_points": ["App is slow", "Crashes frequently"],
                "candidate_quotes": ["The app crashes all the time", "Very slow"]
            }
        ])
        
        week_start = date.today()
        week_end = date.today() + timedelta(days=6)
        
        themes = chunker._parse_theme_response(json_response, week_start, week_end)
        
        assert len(themes) == 1
        assert themes[0].theme == "Performance Issues"
        assert len(themes[0].key_points) == 2
        assert len(themes[0].candidate_quotes) == 2
    
    def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        # Mock parse_json_response to return the expected data (orchestrator handles markdown extraction)
        mock_orchestrator.parse_json_response.return_value = [
            {
                "theme": "User Interface",
                "key_points": ["Hard to navigate"],
                "candidate_quotes": ["UI is confusing"]
            }
        ]
        chunker = ThemeChunker(orchestrator=mock_orchestrator)
        
        # JSON wrapped in markdown
        markdown_response = """Here's the analysis:

```json
[
  {
    "theme": "User Interface",
    "key_points": ["Hard to navigate"],
    "candidate_quotes": ["UI is confusing"]
  }
]
```"""
        
        week_start = date.today()
        week_end = date.today() + timedelta(days=6)
        
        themes = chunker._parse_theme_response(markdown_response, week_start, week_end)
        
        assert len(themes) == 1
        assert themes[0].theme == "User Interface"
    
    def test_parse_invalid_json_handles_gracefully(self):
        """Test that invalid JSON is handled gracefully"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        # Make parse_json_response raise ValueError for invalid JSON
        mock_orchestrator.parse_json_response.side_effect = ValueError("Invalid JSON")
        
        chunker = ThemeChunker(orchestrator=mock_orchestrator)
        
        # Invalid JSON
        invalid_response = "This is not JSON at all"
        
        week_start = date.today()
        week_end = date.today() + timedelta(days=6)
        
        themes = chunker._parse_theme_response(invalid_response, week_start, week_end)
        
        # Should return empty list, not crash
        assert isinstance(themes, list)
        assert len(themes) == 0


class TestThemeAggregation:
    """Test theme aggregation across weeks"""
    
    def test_aggregate_themes_combines_similar(self):
        """Test that similar themes are aggregated"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        chunker = ThemeChunker(orchestrator=mock_orchestrator)
        
        today = date.today()
        week1_start = today - timedelta(days=7)
        week1_end = today - timedelta(days=1)
        week2_start = today - timedelta(days=14)
        week2_end = today - timedelta(days=8)
        
        theme_chunks = [
            ThemeChunk(
                theme="Performance Issues",
                key_points=["Slow", "Crashes"],
                candidate_quotes=["Very slow"],
                week_start=week1_start,
                week_end=week1_end
            ),
            ThemeChunk(
                theme="Performance Issues",
                key_points=["Freezes", "Laggy"],
                candidate_quotes=["App freezes"],
                week_start=week2_start,
                week_end=week2_end
            ),
            ThemeChunk(
                theme="User Interface",
                key_points=["Confusing"],
                candidate_quotes=["Hard to use"],
                week_start=week1_start,
                week_end=week1_end
            ),
        ]
        
        aggregated = chunker.aggregate_themes(theme_chunks)
        
        # Should have 2 aggregated themes
        assert len(aggregated) == 2
        
        # Performance Issues should have combined key points
        perf_theme = next(t for t in aggregated if t.theme == "Performance Issues")
        assert len(perf_theme.key_points) >= 2
        assert perf_theme.frequency == 2
    
    def test_aggregate_themes_limits_to_max(self):
        """Test that aggregation limits to max themes"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        chunker = ThemeChunker(orchestrator=mock_orchestrator)
        
        today = date.today()
        week_start = today - timedelta(days=7)
        week_end = today - timedelta(days=1)
        
        # Create more than MAX_THEMES_TOTAL themes
        theme_chunks = [
            ThemeChunk(
                theme=f"Theme {i}",
                key_points=["Point"],
                candidate_quotes=["Quote"],
                week_start=week_start,
                week_end=week_end
            )
            for i in range(10)
        ]
        
        aggregated = chunker.aggregate_themes(theme_chunks)
        
        # Should be limited to MAX_THEMES_TOTAL (5)
        assert len(aggregated) <= chunker.MAX_THEMES_TOTAL
    
    def test_aggregate_themes_deduplicates_points_and_quotes(self):
        """Test that aggregation removes duplicate points and quotes"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        chunker = ThemeChunker(orchestrator=mock_orchestrator)
        
        today = date.today()
        week_start = today - timedelta(days=7)
        week_end = today - timedelta(days=1)
        
        theme_chunks = [
            ThemeChunk(
                theme="Same Theme",
                key_points=["Duplicate point", "Unique point"],
                candidate_quotes=["Duplicate quote", "Unique quote"],
                week_start=week_start,
                week_end=week_end
            ),
            ThemeChunk(
                theme="Same Theme",
                key_points=["Duplicate point", "Another point"],
                candidate_quotes=["Duplicate quote", "Another quote"],
                week_start=week_start,
                week_end=week_end
            ),
        ]
        
        aggregated = chunker.aggregate_themes(theme_chunks)
        
        assert len(aggregated) == 1
        theme = aggregated[0]
        
        # Should have deduplicated points
        assert len(theme.key_points) == 3  # 3 unique points
        assert "Duplicate point" in theme.key_points
        assert "Unique point" in theme.key_points
        assert "Another point" in theme.key_points


class TestThemeChunkerIntegration:
    """Integration tests for ThemeChunker"""
    
    def test_theme_chunker_initialization(self):
        """Test ThemeChunker initialization"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        mock_orchestrator.api_key = "test-key"
        mock_orchestrator.config.model = ThemeChunker.DEFAULT_MODEL
        
        chunker = ThemeChunker(orchestrator=mock_orchestrator)
        
        assert chunker.model == ThemeChunker.DEFAULT_MODEL
        assert chunker.orchestrator is not None
    
    def test_theme_chunker_uses_env_var(self):
        """Test that ThemeChunker uses environment variable"""
        import os
        os.environ['GROQ_API_KEY'] = 'env-key'
        
        try:
            chunker = ThemeChunker()
            assert chunker.orchestrator.api_key == 'env-key'
        finally:
            # Cleanup
            if 'GROQ_API_KEY' in os.environ:
                del os.environ['GROQ_API_KEY']
    
    def test_get_week_key(self):
        """Test week key generation"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        chunker = ThemeChunker(orchestrator=mock_orchestrator)
        
        test_date = date(2024, 3, 15)  # A known date
        week_key = chunker._get_week_key(test_date)
        
        # Should be in format YYYY-WW
        assert '-' in week_key
        assert week_key.startswith('2024')
        assert 'W' in week_key


class TestThemeChunkModel:
    """Test ThemeChunk and AggregatedTheme models"""
    
    def test_theme_chunk_to_dict(self):
        """Test ThemeChunk serialization"""
        today = date.today()
        chunk = ThemeChunk(
            theme="Test Theme",
            key_points=["Point 1", "Point 2"],
            candidate_quotes=["Quote 1"],
            week_start=today,
            week_end=today + timedelta(days=6)
        )
        
        data = chunk.to_dict()
        
        assert data['theme'] == "Test Theme"
        assert data['key_points'] == ["Point 1", "Point 2"]
        assert data['candidate_quotes'] == ["Quote 1"]
        assert 'week_start' in data
        assert 'week_end' in data
    
    def test_theme_chunk_from_dict(self):
        """Test ThemeChunk deserialization"""
        today = date.today()
        data = {
            'theme': 'Test Theme',
            'key_points': ['Point 1'],
            'candidate_quotes': ['Quote 1'],
            'week_start': today.isoformat(),
            'week_end': (today + timedelta(days=6)).isoformat()
        }
        
        chunk = ThemeChunk.from_dict(data)
        
        assert chunk.theme == "Test Theme"
        assert chunk.key_points == ["Point 1"]
        assert chunk.week_start == today
    
    def test_aggregated_theme_to_dict(self):
        """Test AggregatedTheme serialization"""
        theme = AggregatedTheme(
            theme="Test Theme",
            key_points=["Point 1"],
            candidate_quotes=["Quote 1"],
            frequency=3
        )
        
        data = theme.to_dict()
        
        assert data['theme'] == "Test Theme"
        assert data['frequency'] == 3
        assert 'key_points' in data
        assert 'candidate_quotes' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

