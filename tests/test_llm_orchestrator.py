"""
Unit tests for LLM Orchestrator (Module 6)

Tests cover:
- Prompt generation
- JSON extraction & parsing (with markdown)
- Retry logic for API failures
- Token estimation and chunking
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.llm_orchestrator import (
    LLMConfig,
    LLMOrchestrator,
)


class TestPromptGeneration:
    """Test prompt template handling"""

    def test_build_prompt_substitutes_variables(self):
        template = "Hello {name}, you have {count} messages."
        prompt = LLMOrchestrator.build_prompt(template, name="Alice", count=3)

        assert "Alice" in prompt
        assert "3" in prompt


class TestJsonParsing:
    """Test JSON extraction and parsing"""

    def test_parse_plain_json(self):
        data = {"foo": "bar", "n": 1}
        response = json.dumps(data)

        parsed = LLMOrchestrator.parse_json_response(response)
        assert parsed == data

    def test_parse_markdown_json_block(self):
        response = """Here is your data:

```json
{
  "title": "Test",
  "value": 42
}
```"""
        parsed = LLMOrchestrator.parse_json_response(response)

        assert parsed["title"] == "Test"
        assert parsed["value"] == 42

    def test_parse_json_with_extra_text(self):
        response = 'Some intro {"a": 1, "b": 2} some outro'

        parsed = LLMOrchestrator.parse_json_response(response)
        assert parsed == {"a": 1, "b": 2}

    def test_parse_invalid_json_raises_value_error(self):
        response = "this is not json"

        with pytest.raises(ValueError):
            LLMOrchestrator.parse_json_response(response)


class TestRetryLogic:
    """Test retry behaviour for chat_json"""

    @patch("app.services.llm_orchestrator.Groq")
    def test_chat_json_retries_on_failure(self, mock_groq_cls):
        # Configure mock client to fail twice then succeed
        mock_client = MagicMock()

        class DummyChoices:
            def __init__(self, content: str):
                self.message = type("M", (), {"content": content})

        def side_effect(*args, **kwargs):
            side_effect.counter += 1
            if side_effect.counter < 3:
                raise RuntimeError("Temporary error")
            return type("Resp", (), {"choices": [DummyChoices('{"ok": true}')]})

        side_effect.counter = 0
        mock_client.chat.completions.create.side_effect = side_effect
        mock_groq_cls.return_value = mock_client

        config = LLMConfig(max_retries=3, backoff_seconds=0)  # no sleep in tests
        orchestrator = LLMOrchestrator(api_key="test-key", config=config)

        response = orchestrator.chat_json("sys", "user")
        assert response == '{"ok": true}'
        assert side_effect.counter == 3

    @patch("app.services.llm_orchestrator.Groq")
    def test_chat_json_raises_after_max_retries(self, mock_groq_cls):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("Always fails")
        mock_groq_cls.return_value = mock_client

        config = LLMConfig(max_retries=2, backoff_seconds=0)
        orchestrator = LLMOrchestrator(api_key="test-key", config=config)

        with pytest.raises(RuntimeError):
            orchestrator.chat_json("sys", "user")


class TestTokenEstimationAndChunking:
    """Test token estimation and chunking helpers"""

    def test_estimate_tokens_increases_with_length(self):
        short = "short text"
        long = " ".join(["word"] * 100)

        short_tokens = LLMOrchestrator.estimate_tokens(short)
        long_tokens = LLMOrchestrator.estimate_tokens(long)

        assert long_tokens > short_tokens

    def test_chunk_texts_by_tokens_respects_limit(self):
        texts = [" ".join(["word"] * 50) for _ in range(10)]  # each ≈ 67 tokens

        batches = LLMOrchestrator.chunk_texts_by_tokens(
            texts,
            max_tokens=200,
            buffer_tokens=50,
        )

        # All texts should be present
        flattened = [t for batch in batches for t in batch]
        assert flattened == texts

        # No batch should exceed limit - buffer in effect
        for batch in batches:
            tokens = sum(LLMOrchestrator.estimate_tokens(t) for t in batch)
            assert tokens <= 200 - 50

    def test_chunk_texts_by_tokens_handles_large_single_text(self):
        # Single very long text should be in its own batch
        long_text = " ".join(["word"] * 500)  # very long
        texts = ["short text", long_text, "another short text"]

        batches = LLMOrchestrator.chunk_texts_by_tokens(
            texts,
            max_tokens=300,
            buffer_tokens=50,
        )

        # Ensure long text is present and isolated in some batch
        assert any(len(batch) == 1 and batch[0] == long_text for batch in batches)

    def test_chunk_texts_by_tokens_invalid_params(self):
        with pytest.raises(ValueError):
            LLMOrchestrator.chunk_texts_by_tokens(["x"], max_tokens=50, buffer_tokens=60)


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])


