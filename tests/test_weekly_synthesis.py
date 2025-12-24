"""
Unit tests for Weekly Synthesis Engine

Tests cover:
- Theme selection (top 3)
- Word count validation
- Compression logic
- JSON parsing
- Output structure validation
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.services.weekly_synthesis import (
    WeeklySynthesisEngine,
    WeeklyPulse,
    synthesize_weekly_pulse
)
from app.services.theme_chunker import AggregatedTheme
from app.services.llm_orchestrator import LLMOrchestrator


class TestWeeklyPulseModel:
    """Test WeeklyPulse data model"""
    
    def test_weekly_pulse_creation(self):
        """Test creating a WeeklyPulse"""
        pulse = WeeklyPulse(
            title="Test Pulse",
            overview="This is a test overview",
            themes=[{"name": "Theme 1", "summary": "Summary 1"}],
            quotes=["Quote 1", "Quote 2"],
            actions=["Action 1"]
        )
        
        assert pulse.title == "Test Pulse"
        assert len(pulse.themes) == 1
        assert len(pulse.quotes) == 2
        assert len(pulse.actions) == 1
    
    def test_weekly_pulse_word_count(self):
        """Test word count calculation"""
        pulse = WeeklyPulse(
            title="Test Title",
            overview="This is a test overview with multiple words",
            themes=[{"name": "Theme", "summary": "Summary text"}],
            quotes=["First quote", "Second quote"],
            actions=["First action"]
        )
        
        count = pulse.word_count()
        assert count > 0
        assert isinstance(count, int)
    
    def test_weekly_pulse_to_dict(self):
        """Test serialization to dictionary"""
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[{"name": "T", "summary": "S"}],
            quotes=["Q"],
            actions=["A"]
        )
        
        data = pulse.to_dict()
        assert data['title'] == "Test"
        assert isinstance(data['themes'], list)
        assert isinstance(data['quotes'], list)
        assert isinstance(data['actions'], list)
    
    def test_weekly_pulse_from_dict(self):
        """Test deserialization from dictionary"""
        data = {
            "title": "Test",
            "overview": "Overview",
            "themes": [{"name": "T", "summary": "S"}],
            "quotes": ["Q"],
            "actions": ["A"]
        }
        
        pulse = WeeklyPulse.from_dict(data)
        assert pulse.title == "Test"
        assert len(pulse.themes) == 1


class TestThemeSelection:
    """Test top theme selection logic"""
    
    def test_select_top_themes_by_frequency(self):
        """Test that themes are selected by frequency"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        themes = [
            AggregatedTheme(theme="Low Frequency", key_points=["P1"], candidate_quotes=["Q1"], frequency=1),
            AggregatedTheme(theme="High Frequency", key_points=["P1", "P2"], candidate_quotes=["Q1", "Q2"], frequency=5),
            AggregatedTheme(theme="Medium Frequency", key_points=["P1"], candidate_quotes=["Q1"], frequency=3),
        ]
        
        top = engine._select_top_themes(themes, max_themes=2)
        
        assert len(top) == 2
        assert top[0].theme == "High Frequency"  # Highest frequency
        assert top[1].theme == "Medium Frequency"  # Second highest
    
    def test_select_top_themes_limits_count(self):
        """Test that selection limits to max themes"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        themes = [
            AggregatedTheme(theme=f"Theme {i}", key_points=["P"], candidate_quotes=["Q"], frequency=i)
            for i in range(10)
        ]
        
        top = engine._select_top_themes(themes, max_themes=3)
        
        assert len(top) == 3
        # Should be sorted by frequency (descending)
        assert top[0].frequency >= top[1].frequency
        assert top[1].frequency >= top[2].frequency


class TestWordCountValidation:
    """Test word count validation and compression"""
    
    def test_validate_within_limit(self):
        """Test that pulse within limit is not compressed"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        pulse = WeeklyPulse(
            title="Short Title",
            overview="Short overview",
            themes=[{"name": "T", "summary": "S"}],
            quotes=["Q"],
            actions=["A"]
        )
        
        validated = engine._validate_and_compress(pulse)
        
        # Should return same pulse if within limit
        assert validated.title == pulse.title
    
    def test_compress_when_exceeds_limit(self):
        """Test that pulse exceeding limit is compressed"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        # Create a pulse that will exceed word limit
        long_text = "word " * 100  # 100 words
        pulse = WeeklyPulse(
            title="Very Long Title " * 10,
            overview=long_text,
            themes=[
                {"name": "Theme", "summary": long_text}
                for _ in range(3)
            ],
            quotes=[long_text] * 3,
            actions=[long_text] * 3
        )
        
        validated = engine._validate_and_compress(pulse)
        
        # Should be compressed
        assert validated.word_count() <= engine.MAX_WORDS + 10  # Allow small margin
    
    def test_compress_text(self):
        """Test text compression function"""
        engine = WeeklySynthesisEngine.__new__(WeeklySynthesisEngine)
        engine._compress_text = WeeklySynthesisEngine._compress_text.__get__(engine, WeeklySynthesisEngine)
        
        long_text = "word " * 50  # 50 words
        compressed = engine._compress_text(long_text, target_words=20)
        
        compressed_words = len(compressed.split())
        assert compressed_words <= 25  # Allow some margin
        assert compressed_words >= 15  # Should have substantial content


class TestCompression:
    """Test compression logic"""
    
    def test_compress_pulse_preserves_structure(self):
        """Test that compression preserves required structure"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        pulse = WeeklyPulse(
            title="Title",
            overview="Overview " * 20,
            themes=[
                {"name": "Theme 1", "summary": "Summary " * 20},
                {"name": "Theme 2", "summary": "Summary " * 20},
                {"name": "Theme 3", "summary": "Summary " * 20},
            ],
            quotes=["Quote " * 20] * 3,
            actions=["Action " * 20] * 3
        )
        
        compressed = engine._compress_pulse(pulse)
        
        # Should preserve structure
        assert compressed.title
        assert compressed.overview
        assert len(compressed.themes) <= engine.MAX_THEMES
        assert len(compressed.quotes) <= engine.MAX_QUOTES
        assert len(compressed.actions) <= engine.MAX_ACTIONS
    
    def test_aggressive_compress(self):
        """Test aggressive compression"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        pulse = WeeklyPulse(
            title="Title " * 20,
            overview="Overview " * 50,
            themes=[
                {"name": "Theme " * 10, "summary": "Summary " * 30}
                for _ in range(3)
            ],
            quotes=["Quote " * 30] * 3,
            actions=["Action " * 30] * 3
        )
        
        aggressive = engine._aggressive_compress(pulse)
        
        # Should be much shorter
        assert aggressive.word_count() < pulse.word_count()
        assert aggressive.word_count() <= engine.MAX_WORDS + 20  # Allow margin


class TestJSONParsing:
    """Test JSON parsing from LLM responses"""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON response"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        # Mock parse_json_response to return the expected data
        mock_orchestrator.parse_json_response.return_value = {
            "title": "Weekly Pulse",
            "overview": "This is an overview",
            "themes": [{"name": "Theme 1", "summary": "Summary 1"}],
            "quotes": ["Quote 1"],
            "actions": ["Action 1"]
        }
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        json_response = json.dumps({
            "title": "Weekly Pulse",
            "overview": "This is an overview",
            "themes": [{"name": "Theme 1", "summary": "Summary 1"}],
            "quotes": ["Quote 1"],
            "actions": ["Action 1"]
        })
        
        pulse = engine._parse_pulse_response(json_response)
        
        assert pulse.title == "Weekly Pulse"
        assert len(pulse.themes) == 1
        assert len(pulse.quotes) == 1
        assert len(pulse.actions) == 1
    
    def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        # Mock parse_json_response to return the expected data (orchestrator handles markdown extraction)
        mock_orchestrator.parse_json_response.return_value = {
            "title": "Weekly Pulse",
            "overview": "Overview",
            "themes": [{"name": "Theme", "summary": "Summary"}],
            "quotes": ["Quote"],
            "actions": ["Action"]
        }
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        markdown_response = """Here's the pulse:

```json
{
  "title": "Test",
  "overview": "Overview",
  "themes": [],
  "quotes": [],
  "actions": []
}
```"""
        
        pulse = engine._parse_pulse_response(markdown_response)
        
        assert pulse.title == "Test"
    
    def test_parse_invalid_json_handles_gracefully(self):
        """Test that invalid JSON is handled gracefully"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        # Make parse_json_response raise ValueError for invalid JSON
        mock_orchestrator.parse_json_response.side_effect = ValueError("Invalid JSON")
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        invalid_response = "This is not JSON"
        
        with pytest.raises(ValueError):
            engine._parse_pulse_response(invalid_response)


class TestSynthesisIntegration:
    """Integration tests for synthesis"""
    
    def test_synthesize_with_empty_themes(self):
        """Test synthesis with no themes"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        pulse = engine.synthesize_weekly_pulse([])
        
        assert pulse.title == "No Themes Identified"
        assert len(pulse.themes) == 0
    
    def test_synthesize_creates_fallback_on_error(self):
        """Test that fallback pulse is created on LLM error"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        themes = [
            AggregatedTheme(theme="Test Theme", key_points=["P1"], candidate_quotes=["Q1"], frequency=1)
        ]
        
        # Mock LLM to raise error
        engine._call_llm = Mock(side_effect=Exception("API Error"))
        
        pulse = engine.synthesize_weekly_pulse(themes)
        
        # Should return fallback pulse
        assert pulse.title == "Weekly Product Pulse"
        assert len(pulse.themes) > 0


class TestOutputStructure:
    """Test output structure validation"""
    
    def test_output_has_required_fields(self):
        """Test that output has all required fields"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[{"name": "T", "summary": "S"}],
            quotes=["Q"],
            actions=["A"]
        )
        
        data = pulse.to_dict()
        
        assert "title" in data
        assert "overview" in data
        assert "themes" in data
        assert "quotes" in data
        assert "actions" in data
    
    def test_output_respects_max_limits(self):
        """Test that output respects maximum limits"""
        mock_orchestrator = MagicMock(spec=LLMOrchestrator)
        # Mock parse_json_response to return data with too many items
        pulse_data = {
            "title": "Test",
            "overview": "Overview",
            "themes": [{"name": f"T{i}", "summary": "S"} for i in range(10)],
            "quotes": [f"Q{i}" for i in range(10)],
            "actions": [f"A{i}" for i in range(10)]
        }
        mock_orchestrator.parse_json_response.return_value = pulse_data
        engine = WeeklySynthesisEngine(orchestrator=mock_orchestrator)
        
        # Parse should limit
        pulse = engine._parse_pulse_response(json.dumps(pulse_data))
        
        assert len(pulse.themes) <= engine.MAX_THEMES
        assert len(pulse.quotes) <= engine.MAX_QUOTES
        assert len(pulse.actions) <= engine.MAX_ACTIONS


class TestConvenienceFunction:
    """Test convenience function"""
    
    @patch('app.services.weekly_synthesis.WeeklySynthesisEngine')
    def test_synthesize_weekly_pulse_function(self, mock_engine_class):
        """Test convenience function"""
        mock_engine = MagicMock()
        mock_pulse = WeeklyPulse(
            title="Test",
            overview="Overview",
            themes=[],
            quotes=[],
            actions=[]
        )
        mock_engine.synthesize_weekly_pulse.return_value = mock_pulse
        mock_engine_class.return_value = mock_engine
        
        themes = [
            AggregatedTheme(theme="T", key_points=["P"], candidate_quotes=["Q"], frequency=1)
        ]
        
        pulse = synthesize_weekly_pulse(themes)
        
        assert pulse.title == "Test"
        mock_engine.synthesize_weekly_pulse.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

