"""
LLM Orchestration Utilities

Module 6: Shared LLM orchestration layer for Groq.

Responsibilities:
- Central Groq client and configuration
- Prompt construction helpers
- Robust JSON parsing with markdown/fallback handling
- Retry logic for API failures
- Simple token estimation and chunking utilities

This module is designed to be reused by theme chunking, weekly synthesis,
email composition, and any future LLM-powered features.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

try:  # Optional import; tests patch this.
    from groq import Groq
except ImportError:  # pragma: no cover - handled in initializer
    Groq = None  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for Groq LLM calls."""

    model: str = "llama-3.1-8b-instant"
    temperature: float = 0.3
    max_tokens: int = 1_000
    max_retries: int = 3
    backoff_seconds: float = 1.0


class LLMOrchestrator:
    """Shared orchestration layer for Groq LLM calls.

    This class centralizes:
    - Client initialization
    - Prompt construction
    - JSON parsing with fallbacks
    - Retry logic
    - Token estimation and chunking helpers
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[LLMConfig] = None,
        client: Optional["Groq"] = None,
    ) -> None:
        if Groq is None and client is None:
            raise ImportError(
                "groq package is required. Install with: pip install groq\n"
                "Get your free API key from: https://console.groq.com/"
            )

        self.config = config or LLMConfig()

        # Resolve API key
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key and client is None:
            raise ValueError(
                "Groq API key is required. Set GROQ_API_KEY environment variable "
                "or pass api_key/client explicitly."
            )

        # Allow injecting a preconfigured client (useful for tests)
        self.client: "Groq" = client or Groq(api_key=self.api_key)  # type: ignore[call-arg]

        logger.info(
            "Initialized LLMOrchestrator with model=%s, temperature=%.2f",
            self.config.model,
            self.config.temperature,
        )

    # ------------------------------------------------------------------
    # Prompt helpers
    # ------------------------------------------------------------------

    @staticmethod
    def build_prompt(template: str, **kwargs: Any) -> str:
        """Fill a prompt template using Python's format syntax.

        Example::

            template = "Hello {name}, you have {count} messages."
            prompt = LLMOrchestrator.build_prompt(template, name="Alice", count=3)
        """

        try:
            return template.format(**kwargs)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error formatting prompt: %s", exc, exc_info=True)
            raise

    # ------------------------------------------------------------------
    # Core call method with retry logic
    # ------------------------------------------------------------------

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Call Groq chat completion API expecting a JSON object response.

        This method applies retry logic with exponential backoff.

        Returns the *raw* model response text (which should be JSON).
        """

        cfg = self.config
        max_tokens = max_tokens or cfg.max_tokens

        last_error: Optional[Exception] = None

        for attempt in range(1, cfg.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=cfg.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=cfg.temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                    if "llama" in cfg.model.lower()
                    else None,
                )

                content = response.choices[0].message.content or ""
                content = content.strip()
                logger.debug("LLM response (truncated): %s", content[:200])
                return content

            except Exception as exc:  # pragma: no cover - network dependent
                last_error = exc
                logger.warning(
                    "Groq API call failed on attempt %d/%d: %s",
                    attempt,
                    cfg.max_retries,
                    exc,
                )
                if attempt >= cfg.max_retries:
                    break
                # Exponential backoff
                sleep_for = cfg.backoff_seconds * (2 ** (attempt - 1))
                time.sleep(sleep_for)

        # If we reach here, all retries failed
        assert last_error is not None
        logger.error("All Groq API attempts failed: %s", last_error, exc_info=True)
        raise last_error

    # ------------------------------------------------------------------
    # JSON parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def extract_json_snippet(response: str) -> str:
        """Extract a JSON object/array from an LLM response.

        Handles:
        - Raw JSON
        - Markdown code blocks (```json ... ```)
        - Extra text before/after JSON
        """

        text = response.strip()
        if not text:
            raise ValueError("Empty LLM response")

        # Markdown fenced code block with language
        if "```json" in text:
            start = text.find("```json") + len("```json")
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Any fenced code block
        if "```" in text:
            start = text.find("```") + len("```")
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Scan for a JSON object or array
        start_idx: Optional[int] = None
        end_idx: Optional[int] = None
        stack: List[str] = []

        for i, ch in enumerate(text):
            if ch in "[{" and start_idx is None:
                start_idx = i
                stack.append(ch)
            elif ch in "[{" and start_idx is not None:
                stack.append(ch)
            elif ch in "]}" and stack:
                stack.pop()
                if not stack:
                    end_idx = i + 1
                    break

        if start_idx is not None and end_idx is not None:
            return text[start_idx:end_idx]

        # Fallback: assume whole text is JSON (may still fail json.loads)
        return text

    @classmethod
    def parse_json_response(cls, response: str) -> Any:
        """Parse JSON from a model response with robust extraction.

        Raises ValueError if JSON cannot be parsed.
        """

        snippet = cls.extract_json_snippet(response)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode JSON from response: %s", exc)
            logger.debug("Response snippet was: %s", snippet[:500])
            raise ValueError(f"Invalid JSON from LLM: {exc}") from exc

    # ------------------------------------------------------------------
    # Token estimation & chunking
    # ------------------------------------------------------------------

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Roughly estimate token count for text.

        Groq uses Llama-style tokenization. As an approximation, we treat
        1 token ≈ 0.75 words.
        """

        if not text:
            return 0
        words = text.split()
        # 1 token ≈ 0.75 words → tokens ≈ words / 0.75
        return max(1, int(len(words) / 0.75))

    @classmethod
    def chunk_texts_by_tokens(
        cls,
        texts: Sequence[str],
        *,
        max_tokens: int,
        buffer_tokens: int = 100,
    ) -> List[List[str]]:
        """Group texts into batches under a token budget.

        Args:
            texts: Sequence of text segments
            max_tokens: Hard token budget per batch
            buffer_tokens: Reserved tokens for prompt/response
        """

        if max_tokens <= buffer_tokens:
            raise ValueError("max_tokens must be greater than buffer_tokens")

        batches: List[List[str]] = []
        current_batch: List[str] = []
        current_tokens = 0
        limit = max_tokens - buffer_tokens

        for text in texts:
            t_tokens = cls.estimate_tokens(text)
            # If a single text exceeds limit, put it in its own batch
            if t_tokens > limit:
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_tokens = 0
                batches.append([text])
                continue

            if current_tokens + t_tokens > limit and current_batch:
                batches.append(current_batch)
                current_batch = [text]
                current_tokens = t_tokens
            else:
                current_batch.append(text)
                current_tokens += t_tokens

        if current_batch:
            batches.append(current_batch)

        return batches


__all__ = ["LLMConfig", "LLMOrchestrator"]

{
  "cells": [],
  "metadata": {
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}