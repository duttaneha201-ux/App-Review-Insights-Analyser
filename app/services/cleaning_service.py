"""
Cleaning & PII Scrubber Service

Responsibilities:
- Text cleaning: HTML, emojis, URLs/links, whitespace, quotes
- PII detection: emails, phone numbers, URLs, usernames/IDs
- PII rewriting: redact PII while preserving meaning
- Duplicate detection: fuzzy matching on review text
"""

import logging
import html
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Iterable

import regex as re
from thefuzz import fuzz

from app.models.review import Review

logger = logging.getLogger(__name__)


@dataclass
class PiiMatch:
    """Represents a single PII match inside text."""

    type: str
    value: str


class CleaningService:
    """
    Provides text cleaning, PII scrubbing, and duplicate detection.

    Design goals:
    - Deterministic, simple, and fast
    - Conservative PII detection (avoid leaking obvious PII)
    - Preserve semantic meaning while redacting PII
    """

    # --- Regex patterns ---

    # Emails
    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        re.IGNORECASE,
    )

    # URLs (http/https, www, bare domains)
    URL_PATTERN = re.compile(
        r"(?i)\b("
        r"(?:https?://|www\.)\S+"
        r"|"
        r"[A-Za-z0-9.-]+\.(?:com|net|org|io|ai|co|in|uk|de|fr|it|es|ru|cn|br|jp|kr)"
        r"(?:/[^\s]*)?"
        r")"
    )

    # Phone numbers (international + local patterns, very approximate)
    PHONE_PATTERN = re.compile(
        r"""
        (?:
            (?:(?:\+|00)\d{1,3}[\s\-()]*)?        # country code
            (?:\d[\s\-()]*){7,12}                # digits with optional separators
        )
        """,
        re.VERBOSE,
    )

    # Usernames / IDs: @handle, or id: 123456, user123, etc.
    USERNAME_PATTERN = re.compile(
        r"(@[A-Za-z0-9_]+)|\b(id|user|uid|handle)[:\s]*[A-Za-z0-9_]{3,}\b",
        re.IGNORECASE,
    )

    # Simple name-like patterns following "Name:" or "By"
    NAME_CONTEXT_PATTERN = re.compile(
        r"\b(?:name|by)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        re.IGNORECASE,
    )

    # Emoji & symbol ranges (Unicode)
    EMOJI_PATTERN = re.compile(
        r"[\p{So}\p{Sk}\p{Cs}]",
        re.UNICODE,
    )

    # HTML tags
    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

    # Multiple whitespace
    MULTI_WHITESPACE_PATTERN = re.compile(r"\s+")

    # Curly quotes and similar punctuation to normalize
    QUOTE_MAP = {
        "“": '"',
        "”": '"',
        "„": '"',
        "‚": "'",
        "‘": "'",
        "’": "'",
        "«": '"',
        "»": '"',
    }

    # Fuzzy duplicate threshold (0–100)
    DEFAULT_DUPLICATE_THRESHOLD = 90

    def __init__(self, duplicate_threshold: int = None):
        self.duplicate_threshold = duplicate_threshold or self.DEFAULT_DUPLICATE_THRESHOLD

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clean_text(self, text: str) -> str:
        """
        Clean a piece of review text:
        - Decode HTML entities
        - Strip HTML tags
        - Remove emojis/symbols
        - Remove URLs
        - Normalize quotes
        - Normalize whitespace (single spaces, trimmed)
        """
        if not text:
            return ""

        original = text

        # Decode HTML entities
        text = html.unescape(text)

        # Remove HTML tags
        text = self.HTML_TAG_PATTERN.sub(" ", text)

        # Remove URLs/links early so we don't treat them as content
        text = self.URL_PATTERN.sub(" [link removed] ", text)

        # Remove emojis and other symbols
        text = self.EMOJI_PATTERN.sub("", text)

        # Normalize quotes
        for src, dst in self.QUOTE_MAP.items():
            text = text.replace(src, dst)

        # Normalize whitespace
        text = self.MULTI_WHITESPACE_PATTERN.sub(" ", text)
        text = text.strip()

        # Fix spacing before common punctuation (e.g., "world !" -> "world!")
        text = re.sub(r"\s+([!?.,;:])", r"\1", text)

        logger.debug("Cleaned text from %r to %r", original[:80], text[:80])
        return text

    def detect_pii(self, text: str) -> List[PiiMatch]:
        """
        Detect obvious PII in text (emails, phones, URLs, usernames/IDs, simple names).
        Returns a list of PiiMatch objects.
        """
        if not text:
            return []

        matches: List[PiiMatch] = []

        # Emails
        for m in self.EMAIL_PATTERN.finditer(text):
            matches.append(PiiMatch(type="email", value=m.group(0)))

        # URLs
        for m in self.URL_PATTERN.finditer(text):
            matches.append(PiiMatch(type="url", value=m.group(0)))

        # Phone numbers
        for m in self.PHONE_PATTERN.finditer(text):
            matches.append(PiiMatch(type="phone", value=m.group(0)))

        # Usernames / IDs
        for m in self.USERNAME_PATTERN.finditer(text):
            val = m.group(0)
            matches.append(PiiMatch(type="username_or_id", value=val))

        # Simple name patterns in explicit contexts
        for m in self.NAME_CONTEXT_PATTERN.finditer(text):
            val = m.group(1)
            matches.append(PiiMatch(type="name", value=val))

        return matches

    def rewrite_without_pii(self, text: str) -> str:
        """
        Rewrite text to remove obvious PII while preserving meaning.

        Strategy:
        - Replace emails with "[email removed]"
        - Replace phone numbers with "[phone removed]"
        - Replace URLs with "[link removed]"
        - Replace usernames/IDs with generic "the user" / "[id removed]"
        - Replace contextual names with "the user"
        """
        if not text:
            return ""

        rewritten = text

        # Emails
        rewritten = self.EMAIL_PATTERN.sub("[email removed]", rewritten)

        # URLs
        rewritten = self.URL_PATTERN.sub("[link removed]", rewritten)

        # Phones
        rewritten = self.PHONE_PATTERN.sub("[phone removed]", rewritten)

        # Usernames / IDs
        def _username_repl(match: re.Match) -> str:
            val = match.group(0)
            if val.startswith("@"):
                return "the user"
            return "[id removed]"

        rewritten = self.USERNAME_PATTERN.sub(_username_repl, rewritten)

        # Simple names in explicit context
        def _name_repl(match: re.Match) -> str:
            prefix = match.group(0)
            # Replace the captured name with "the user"
            return re.sub(match.group(1), "the user", prefix)

        rewritten = self.NAME_CONTEXT_PATTERN.sub(_name_repl, rewritten)

        # Normalize whitespace after replacements
        rewritten = self.MULTI_WHITESPACE_PATTERN.sub(" ", rewritten).strip()

        return rewritten

    def clean_and_scrub(self, text: str) -> Tuple[str, bool]:
        """
        High-level helper:
        - Detect & remove PII
        - Then clean text for downstream processing

        Returns:
            (cleaned_text, had_pii)
        """
        raw = text or ""

        # Detect PII on the raw text (before URL stripping)
        had_pii = bool(self.detect_pii(raw))

        # First scrub PII on raw text
        scrubbed_raw = self.rewrite_without_pii(raw)

        # Then run full cleaning pipeline on scrubbed text
        cleaned_scrubbed = self.clean_text(scrubbed_raw)

        return cleaned_scrubbed, had_pii

    # ------------------------------------------------------------------
    # Duplicate detection
    # ------------------------------------------------------------------

    def deduplicate_reviews(
        self,
        reviews: Iterable[Review],
        threshold: Optional[int] = None,
    ) -> List[Review]:
        """
        Remove duplicate reviews using fuzzy matching on text.

        Args:
            reviews: Iterable of Review objects
            threshold: Fuzzy similarity threshold (0-100). Reviews whose
                       text has similarity >= threshold are considered
                       duplicates (only first kept).

        Returns:
            List of unique Review objects.
        """
        threshold = threshold or self.duplicate_threshold
        unique: List[Review] = []
        seen_texts: List[str] = []

        for review in reviews:
            text = (review.text or "").strip()
            if not text:
                continue

            cleaned_text = self.clean_text(text).lower()
            if not cleaned_text:
                continue

            is_duplicate = False
            for existing in seen_texts:
                score = fuzz.ratio(cleaned_text, existing)
                if score >= threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(review)
                seen_texts.append(cleaned_text)

        logger.info("Deduplicated %d reviews to %d unique (threshold=%d)", len(list(reviews)), len(unique), threshold)
        return unique


def clean_text(text: str) -> str:
    """Convenience function for cleaning text."""
    return CleaningService().clean_text(text)


def detect_pii(text: str) -> List[PiiMatch]:
    """Convenience function for detecting PII."""
    return CleaningService().detect_pii(text)


def rewrite_without_pii(text: str) -> str:
    """Convenience function for rewriting text without PII."""
    return CleaningService().rewrite_without_pii(text)


def deduplicate_reviews(reviews: Iterable[Review], threshold: Optional[int] = None) -> List[Review]:
    """Convenience function for deduplicating reviews."""
    return CleaningService().deduplicate_reviews(reviews, threshold=threshold)


