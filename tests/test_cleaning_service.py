"""
Unit tests for Cleaning & PII Scrubber (Module 3)

Covers:
- Text cleaning (HTML, emojis, links, whitespace, quotes)
- PII detection (emails, phones, URLs, usernames/IDs, simple names)
- PII rewriting (redaction while preserving meaning)
- Duplicate detection (fuzzy matching)
"""

import pytest
from datetime import date

from app.services.cleaning_service import (
    CleaningService,
    clean_text,
    detect_pii,
    rewrite_without_pii,
    deduplicate_reviews,
    PiiMatch,
)
from app.models.review import Review


class TestTextCleaning:
    """Test text cleaning pipeline."""

    def test_strip_html_and_entities(self):
        service = CleaningService()
        raw = "<p>Hello&nbsp;<strong>world</strong>!</p>"
        cleaned = service.clean_text(raw)
        assert cleaned == "Hello world!"

    def test_remove_emojis_and_links(self):
        service = CleaningService()
        raw = "Great app 😄! Check this out: https://example.com/page 👍"
        cleaned = service.clean_text(raw)
        assert "😄" not in cleaned
        assert "👍" not in cleaned
        assert "[link removed]" in cleaned
        assert "https://example.com" not in cleaned

    def test_normalize_whitespace_and_quotes(self):
        service = CleaningService()
        raw = "  This   is  “quoted”   text\nwith  multiple   spaces.  "
        cleaned = service.clean_text(raw)
        assert cleaned == 'This is "quoted" text with multiple spaces.'

    def test_clean_text_convenience_function(self):
        raw = "<b>Hello</b> world"
        cleaned = clean_text(raw)
        assert cleaned == "Hello world"


class TestPiiDetection:
    """Test PII detection patterns."""

    def test_detect_email(self):
        text = "Contact me at user@example.com for details."
        matches = detect_pii(text)
        types = {m.type for m in matches}
        values = {m.value for m in matches}
        assert "email" in types
        assert "user@example.com" in values

    def test_detect_phone_number(self):
        text = "My phone number is +1 (555) 123-4567."
        matches = detect_pii(text)
        assert any(m.type == "phone" for m in matches)

    def test_detect_url(self):
        text = "Visit http://example.org or www.example.com today."
        matches = detect_pii(text)
        url_matches = [m for m in matches if m.type == "url"]
        assert len(url_matches) >= 1

    def test_detect_username_and_id(self):
        text = "My handle is @cool_user and user id: user1234"
        matches = detect_pii(text)
        types = {m.type for m in matches}
        assert "username_or_id" in types

    def test_detect_name_in_context(self):
        text = "Name: John Doe left this review."
        matches = detect_pii(text)
        assert any(m.type == "name" for m in matches)


class TestPiiRewriting:
    """Test PII rewriting logic."""

    def test_rewrite_email_and_url_and_phone(self):
        service = CleaningService()
        text = (
            "Email me at user@example.com or visit https://example.com. "
            "Call me at +44 20 7946 0958."
        )
        rewritten = service.rewrite_without_pii(text)
        assert "user@example.com" not in rewritten
        assert "https://example.com" not in rewritten
        assert "+44 20 7946 0958" not in rewritten
        assert "[email removed]" in rewritten
        assert "[link removed]" in rewritten
        assert "[phone removed]" in rewritten

    def test_rewrite_username_and_name(self):
        service = CleaningService()
        text = "By @cool_user. Name: Jane Smith wrote this."
        rewritten = service.rewrite_without_pii(text)
        assert "@cool_user" not in rewritten
        assert "Jane Smith" not in rewritten
        assert "the user" in rewritten or "[id removed]" in rewritten

    def test_clean_and_scrub_combined(self):
        service = CleaningService()
        raw = "<p>Contact @user via john@example.com 🙃</p>"
        scrubbed, had_pii = service.clean_and_scrub(raw)
        assert had_pii is True
        assert "@user" not in scrubbed
        assert "john@example.com" not in scrubbed
        assert "[email removed]" in scrubbed

    def test_rewrite_without_pii_convenience(self):
        text = "Email: user@example.com"
        rewritten = rewrite_without_pii(text)
        assert "user@example.com" not in rewritten
        assert "[email removed]" in rewritten


class TestDuplicateDetection:
    """Test fuzzy duplicate detection."""

    def test_deduplicate_exact_duplicates(self):
        service = CleaningService(duplicate_threshold=95)
        today = date.today()
        reviews = [
            Review(rating=5, title="A", text="Great app with many features!", date=today),
            Review(rating=4, title="B", text="Great app with many features!", date=today),
            Review(rating=3, title="C", text="Different content here.", date=today),
        ]
        unique = service.deduplicate_reviews(reviews)
        # One of the exact duplicates should be removed
        assert len(unique) == 2
        texts = [r.text for r in unique]
        assert "Different content here." in texts

    def test_deduplicate_fuzzy_similar(self):
        service = CleaningService(duplicate_threshold=90)
        today = date.today()
        reviews = [
            Review(rating=5, title="A", text="Great app with many features!", date=today),
            Review(rating=4, title="B", text="Great app with many awesome features.", date=today),
            Review(rating=3, title="C", text="This app is terrible.", date=today),
        ]
        unique = service.deduplicate_reviews(reviews)
        # First two are very similar, so only one kept
        assert len(unique) == 2
        texts = {r.text for r in unique}
        assert "This app is terrible." in texts

    def test_deduplicate_reviews_convenience(self):
        today = date.today()
        reviews = [
            Review(rating=5, title="A", text="Nice app", date=today),
            Review(rating=5, title="B", text="Nice app", date=today),
        ]
        unique = deduplicate_reviews(reviews, threshold=95)
        assert len(unique) == 1


class TestNoStorageOfPII:
    """Policy checks: we don't surface obvious PII in cleaned outputs."""

    def test_clean_and_scrub_removes_emails_and_usernames(self):
        service = CleaningService()
        raw = "User @john_doe with email john.doe+test@example.co.uk said this."
        scrubbed, had_pii = service.clean_and_scrub(raw)

        assert had_pii is True
        assert "@john_doe" not in scrubbed
        assert "john.doe+test@example.co.uk" not in scrubbed
        assert "[email removed]" in scrubbed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


