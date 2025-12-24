"""
Review Extraction Service for Google Play Store

This module provides functionality to:
- Scrape reviews from Play Store using Playwright
- Filter reviews by date range
- Sample reviews by rating (40 per rating)
- Handle pagination and lazy loading
- Extract reviews from modal components
"""

import logging
import time
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Tuple
from dataclasses import asdict

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import dateparser
from google_play_scraper import reviews as gp_reviews, Sort

from app.models.review import Review
from app.services.cleaning_service import CleaningService

logger = logging.getLogger(__name__)


class ReviewExtractor:
    """
    Extracts reviews from Google Play Store.
    """
    
    # Play Store review page URL pattern
    REVIEWS_URL_TEMPLATE = "https://play.google.com/store/apps/details?id={app_id}&hl=en&showAllReviews=true"
    
    # Default settings
    DEFAULT_TIMEOUT = 30000  # 30 seconds
    DEFAULT_WAIT_TIME = 2  # seconds to wait for content to load
    MAX_SCROLL_ATTEMPTS = 10
    SCROLL_PAUSE = 1  # seconds between scrolls
    
    # Sampling settings
    SAMPLES_PER_RATING = 15
    
    def __init__(
        self,
        timeout: int = None,
        headless: bool = True,
        wait_time: int = None,
        max_retries: int = 3,
        enable_cleaning: bool = True,
        duplicate_threshold: int = None
    ):
        """
        Initialize the review extractor.
        
        Args:
            timeout: Page load timeout in milliseconds (default: 30000)
            headless: Run browser in headless mode (default: True)
            wait_time: Time to wait for content to load in seconds (default: 2)
            max_retries: Maximum number of retries for failed requests (default: 3)
            enable_cleaning: Enable text cleaning and PII scrubbing (default: True)
            duplicate_threshold: Fuzzy duplicate threshold 0-100 (default: 90)
        """
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.headless = headless
        self.wait_time = wait_time or self.DEFAULT_WAIT_TIME
        self.max_retries = max_retries
        self.enable_cleaning = enable_cleaning
        self.cleaning_service = CleaningService(duplicate_threshold=duplicate_threshold) if enable_cleaning else None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    def _init_browser(self):
        """Initialize Playwright browser"""
        if self.browser is None:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
    
    def _close_browser(self):
        """Close browser and cleanup"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
        self.browser = None
        self.context = None
    
    def extract_reviews(
        self,
        app_id: str,
        start_date: date,
        end_date: date,
        samples_per_rating: int = None
    ) -> List[Review]:
        """
        Extract reviews for an app within a date range.
        
        Args:
            app_id: App package name (e.g., 'com.whatsapp')
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            samples_per_rating: Number of reviews to sample per rating (default: 15)
            
        Returns:
            List of Review objects sorted by newest first
        """
        samples_per_rating = samples_per_rating or self.SAMPLES_PER_RATING

        logger.info(
            f"Extracting reviews for {app_id} from {start_date} to {end_date} "
            f"using google-play-scraper backend"
        )

        # Use API-based scraper instead of Playwright for reliability
        return self.extract_reviews_with_google_play_scraper(
            app_id=app_id,
            start_date=start_date,
            end_date=end_date,
            samples_per_rating=samples_per_rating,
        )

    def extract_reviews_with_google_play_scraper(
        self,
        app_id: str,
        start_date: date,
        end_date: date,
        samples_per_rating: int = 15,
        lang: str = "en",
        country: str = "in",
    ) -> List[Review]:
        """
        Extract reviews using google-play-scraper instead of Playwright.

        This bypasses the browser and calls Google's internal API via the
        google_play_scraper library, returning Review objects compatible
        with the existing pipeline.
        """
        rating_buckets: Dict[int, List[Review]] = {i: [] for i in range(1, 6)}

        continuation_token = None

        while True:
            batch, continuation_token = gp_reviews(
                app_id,
                lang=lang,
                country=country,
                sort=Sort.NEWEST,
                count=200,
                continuation_token=continuation_token,
            )

            if not batch:
                break

            for r in batch:
                dt = r.get("at")
                if not isinstance(dt, datetime):
                    continue

                review_date = dt.date()

                if review_date < start_date or review_date > end_date:
                    continue

                rating = int(r.get("score", 0) or 0)
                if rating not in rating_buckets:
                    continue

                if len(rating_buckets[rating]) >= samples_per_rating:
                    continue

                text = (r.get("content") or "").strip()
                if not text or len(text) < 15:
                    continue

                title = (r.get("title") or "").strip() or None
                review_id = str(r.get("reviewId") or "")

                review = Review(
                    rating=rating,
                    text=text,
                    title=title,
                    date=review_date,
                    review_id=review_id,
                    author=None,
                )

                rating_buckets[rating].append(review)

            if all(len(bucket) >= samples_per_rating for bucket in rating_buckets.values()):
                break

            if continuation_token is None:
                break

        all_reviews: List[Review] = [
            r for bucket in rating_buckets.values() for r in bucket
        ]
        all_reviews.sort(key=lambda r: r.date, reverse=True)

        logger.info(f"Extracted {len(all_reviews)} reviews via google-play-scraper")
        return all_reviews
    
    def _scroll_to_load_reviews(self, page: Page):
        """Scroll the page to trigger lazy loading of reviews"""
        logger.info("Scrolling to load more reviews...")
        
        for attempt in range(self.MAX_SCROLL_ATTEMPTS):
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(self.SCROLL_PAUSE)
            
            # Check if "Show more" button exists and click it
            try:
                show_more_selectors = [
                    'button:has-text("Show more")',
                    'button:has-text("See more reviews")',
                    '[aria-label*="Show more"]',
                    '[data-testid*="show-more"]',
                ]
                
                for selector in show_more_selectors:
                    try:
                        button = page.query_selector(selector)
                        if button and button.is_visible():
                            button.click()
                            time.sleep(self.SCROLL_PAUSE)
                            logger.info(f"Clicked 'Show more' button (attempt {attempt + 1})")
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Could not find/click 'Show more' button: {e}")
            
            # Scroll up a bit and back down to trigger lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.8)")
            time.sleep(self.SCROLL_PAUSE)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(self.SCROLL_PAUSE)
    
    def _extract_reviews_from_page(self, page: Page, start_date: date, end_date: date) -> List[Review]:
        """Extract reviews from the main page"""
        reviews = []
        
        # Multiple selectors to find review containers (Play Store structure can vary)
        review_selectors = [
            'div[data-review-id]',
            'div[jsname]',  # Reviews often have jsname attributes
            'div.review',
            '[itemprop="review"]',
            'div[class*="review"]',
        ]
        
        review_elements = []
        for selector in review_selectors:
            elements = page.query_selector_all(selector)
            if elements:
                review_elements = elements
                logger.info(f"Found {len(elements)} review elements using selector: {selector}")
                break
        
        if not review_elements:
            # Fallback: try to find by structure
            review_elements = page.query_selector_all('div:has(span[aria-label*="star"])')
            logger.info(f"Found {len(review_elements)} review elements using fallback selector")
        
        for element in review_elements:
            try:
                review = self._parse_review_element(element)
                if review:
                    reviews.append(review)
            except Exception as e:
                logger.debug(f"Error parsing review element: {e}")
                continue
        
        return reviews
    
    def _extract_reviews_from_modals(self, page: Page, start_date: date, end_date: date) -> List[Review]:
        """Extract reviews that are shown in modal/popup components"""
        reviews = []
        
        # Find all clickable elements that might open review modals
        modal_triggers = []
        selectors = [
            'button[aria-label*="review"]',
            'a[href*="review"]',
            'div[role="button"]',
            'span:has-text("See all")',
        ]
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                modal_triggers.extend(elements)
            except:
                continue
        
        logger.info(f"Found {len(modal_triggers)} potential modal triggers")
        
        for trigger in modal_triggers[:10]:  # Limit to first 10 to avoid too many modals
            try:
                if not trigger.is_visible():
                    continue
                
                # Click to open modal
                trigger.click()
                time.sleep(1)  # Wait for modal to open
                
                # Find modal content
                modal_selectors = [
                    '[role="dialog"]',
                    'div[class*="modal"]',
                    'div[class*="popup"]',
                    'div[class*="dialog"]',
                ]
                
                modal = None
                for selector in modal_selectors:
                    modal = page.query_selector(selector)
                    if modal and modal.is_visible():
                        break
                
                if modal:
                    # Extract reviews from modal
                    modal_reviews = self._extract_reviews_from_element(modal, start_date, end_date)
                    reviews.extend(modal_reviews)
                    
                    # Close modal (press Escape or click outside)
                    page.keyboard.press('Escape')
                    time.sleep(0.5)
                
            except Exception as e:
                logger.debug(f"Error extracting from modal: {e}")
                # Try to close modal if still open
                try:
                    page.keyboard.press('Escape')
                except:
                    pass
                continue
        
        return reviews
    
    def _extract_reviews_from_element(self, element, start_date: date, end_date: date) -> List[Review]:
        """Extract reviews from a specific element (page or modal)"""
        reviews = []
        
        selectors = [
            'div[data-review-id]',
            'div[jsname]',
            'div.review',
            '[itemprop="review"]',
        ]
        
        review_elements = []
        for selector in selectors:
            try:
                elements = element.query_selector_all(selector)
                if elements:
                    review_elements = elements
                    break
            except:
                continue
        
        for review_element in review_elements:
            try:
                review = self._parse_review_element(review_element)
                if review:
                    reviews.append(review)
            except Exception as e:
                logger.debug(f"Error parsing review from element: {e}")
                continue
        
        return reviews
    
    def _parse_review_element(self, element) -> Optional[Review]:
        """
        Parse a single review element into a Review object.
        Reviews with text < 15 characters are filtered out here to avoid
        creating invalid Review objects.
        """
        try:
            # Extract rating
            rating = self._extract_rating(element)
            if not rating:
                return None
            
            # Extract text
            text = self._extract_text(element)
            # Filter out reviews with less than 15 characters at parse time
            if not text or len(text.strip()) < 15:
                logger.debug(f"Skipping review with text < 15 characters: {text[:20] if text else 'None'}...")
                return None
            
            # Extract title (optional)
            title = self._extract_title(element)
            
            # Extract date
            review_date = self._extract_date(element)
            if not review_date:
                return None
            
            # Extract review ID if available
            review_id = element.get_attribute('data-review-id') or element.get_attribute('id')
            
            return Review(
                rating=rating,
                title=title,
                text=text,
                date=review_date,
                review_id=review_id
            )
            
        except Exception as e:
            logger.debug(f"Error parsing review element: {e}")
            return None
    
    def _extract_rating(self, element) -> Optional[int]:
        """Extract rating (1-5 stars) from review element"""
        # Try multiple methods to find rating
        
        # Method 1: aria-label with star rating
        aria_label = element.get_attribute('aria-label') or ''
        if 'star' in aria_label.lower():
            for i in range(5, 0, -1):
                if f'{i} star' in aria_label.lower():
                    return i
        
        # Method 2: Find elements with star ratings
        star_selectors = [
            'span[aria-label*="star"]',
            'div[aria-label*="star"]',
            '[class*="star"]',
        ]
        
        for selector in star_selectors:
            star_elements = element.query_selector_all(selector)
            for star_elem in star_elements:
                aria_label = star_elem.get_attribute('aria-label') or ''
                for i in range(5, 0, -1):
                    if f'{i} star' in aria_label.lower():
                        return i
        
        # Method 3: Look for numeric rating in text
        text_content = element.inner_text().lower()
        for i in range(5, 0, -1):
            if f'{i}-star' in text_content or f'{i} star' in text_content:
                return i
        
        # Method 4: Check for filled stars (visual indicator)
        filled_stars = element.query_selector_all('[class*="filled"], [class*="active"]')
        if filled_stars:
            # Count filled stars
            count = len([s for s in filled_stars if 'star' in (s.get_attribute('class') or '').lower()])
            if 1 <= count <= 5:
                return count
        
        return None
    
    def _extract_text(self, element) -> Optional[str]:
        """Extract review text from element"""
        # Try to find review text in common locations
        text_selectors = [
            'span[jsname="bN97Pc"]',  # Common Play Store selector
            'div[jsname="bN97Pc"]',
            '[itemprop="reviewBody"]',
            'div[class*="review-text"]',
            'span[class*="review-text"]',
            'div[class*="comment"]',
        ]
        
        for selector in text_selectors:
            text_elem = element.query_selector(selector)
            if text_elem:
                text = text_elem.inner_text().strip()
                if text and len(text) >= 15:
                    return text
        
        # Fallback: get all text and try to extract review content
        full_text = element.inner_text()
        # Remove rating and date info, keep review text
        lines = full_text.split('\n')
        # Filter out lines that look like dates or ratings
        review_lines = [
            line for line in lines
            if not any(word in line.lower() for word in ['star', 'rating', 'ago', 'day', 'month', 'year', 'reviewed'])
            and len(line.strip()) > 10
        ]
        
        if review_lines:
            return ' '.join(review_lines).strip()
        
        return None
    
    def _extract_title(self, element) -> Optional[str]:
        """Extract review title if available"""
        title_selectors = [
            'span[jsname="bN97Pc"]:first-child',
            'div[class*="review-title"]',
            'h3',
            'h4',
        ]
        
        for selector in title_selectors:
            title_elem = element.query_selector(selector)
            if title_elem:
                title = title_elem.inner_text().strip()
                if title and len(title) > 0:
                    return title
        
        return None
    
    def _extract_date(self, element) -> Optional[date]:
        """Extract review date from element"""
        # Try to find date elements
        date_selectors = [
            'span[jsname="bN97Pc"]:last-child',
            'span[class*="date"]',
            'time[datetime]',
            '[itemprop="datePublished"]',
        ]
        
        for selector in date_selectors:
            date_elem = element.query_selector(selector)
            if date_elem:
                # Try datetime attribute first
                datetime_attr = date_elem.get_attribute('datetime')
                if datetime_attr:
                    try:
                        parsed_date = dateparser.parse(datetime_attr)
                        if parsed_date:
                            return parsed_date.date()
                    except:
                        pass
                
                # Try parsing text content
                date_text = date_elem.inner_text().strip()
                if date_text:
                    parsed_date = self._parse_date_string(date_text)
                    if parsed_date:
                        return parsed_date
        
        # Fallback: search in all text
        full_text = element.inner_text()
        parsed_date = self._parse_date_string(full_text)
        if parsed_date:
            return parsed_date
        
        return None
    
    def _parse_date_string(self, date_string: str) -> Optional[date]:
        """Parse date string into date object"""
        if not date_string:
            return None
        
        # Try dateparser first
        try:
            parsed = dateparser.parse(date_string, settings={'RELATIVE_BASE': datetime.now()})
            if parsed:
                return parsed.date()
        except:
            pass
        
        # Try common patterns
        date_string_lower = date_string.lower()
        
        # "X days ago", "X months ago", etc.
        if 'ago' in date_string_lower:
            try:
                parsed = dateparser.parse(date_string, settings={'RELATIVE_BASE': datetime.now()})
                if parsed:
                    return parsed.date()
            except:
                pass
        
        # Try ISO format
        try:
            return datetime.fromisoformat(date_string.split('T')[0]).date()
        except:
            pass
        
        return None
    
    def _filter_by_date_range(self, reviews: List[Review], start_date: date, end_date: date) -> List[Review]:
        """Filter reviews by date range"""
        filtered = [
            review for review in reviews
            if start_date <= review.date <= end_date
        ]
        logger.info(f"Filtered {len(reviews)} reviews to {len(filtered)} within date range")
        return filtered
    
    def _filter_by_min_length(self, reviews: List[Review], min_length: int = 15) -> List[Review]:
        """
        Filter out reviews with text shorter than minimum length.
        
        Args:
            reviews: List of reviews to filter
            min_length: Minimum character length (default: 15)
            
        Returns:
            List of reviews with text length >= min_length
        """
        filtered = [
            review for review in reviews
            if review.text and len(review.text.strip()) >= min_length
        ]
        removed_count = len(reviews) - len(filtered)
        if removed_count > 0:
            logger.info(f"Filtered out {removed_count} reviews with text < {min_length} characters")
        return filtered
    
    def _sample_by_rating(self, reviews: List[Review], samples_per_rating: int) -> List[Review]:
        """
        Sample reviews by rating (N per rating).
        Only includes reviews that have already passed length filtering.
        
        Args:
            reviews: List of reviews (should already be filtered by length)
            samples_per_rating: Number of reviews to sample per rating
            
        Returns:
            List of sampled reviews (up to samples_per_rating per rating)
        """
        sampled = []
        
        for rating in range(1, 6):
            # Get reviews for this rating (already filtered by length)
            rating_reviews = [r for r in reviews if r.rating == rating]
            
            # Take up to samples_per_rating reviews
            count = min(len(rating_reviews), samples_per_rating)
            sampled.extend(rating_reviews[:samples_per_rating])
            
            logger.info(
                f"Sampled {count} reviews with {rating} stars "
                f"(available: {len(rating_reviews)}, requested: {samples_per_rating})"
            )
        
        return sampled
    
    def _clean_and_scrub_reviews(self, reviews: List[Review]) -> List[Review]:
        """
        Clean and scrub PII from review texts.
        Creates new Review objects with cleaned text.
        """
        if not self.cleaning_service:
            return reviews
        
        cleaned_reviews = []
        pii_count = 0
        
        for review in reviews:
            if not review.text:
                continue
            
            # Clean and scrub PII
            cleaned_text, had_pii = self.cleaning_service.clean_and_scrub(review.text)
            
            if had_pii:
                pii_count += 1
            
            # Skip if text becomes too short after cleaning
            if len(cleaned_text.strip()) < 15:
                continue
            
            # Create new review with cleaned text
            cleaned_review = Review(
                rating=review.rating,
                title=review.title,  # Title is optional, keep as is
                text=cleaned_text,
                date=review.date,
                review_id=review.review_id,
                author=None  # Never store author
            )
            cleaned_reviews.append(cleaned_review)
        
        if pii_count > 0:
            logger.info(f"Scrubbed PII from {pii_count} reviews")
        
        logger.info(f"Cleaned {len(reviews)} reviews to {len(cleaned_reviews)} valid reviews")
        return cleaned_reviews
    
    def _deduplicate_reviews(self, reviews: List[Review]) -> List[Review]:
        """Remove duplicate reviews based on exact text matching (fallback when cleaning disabled)"""
        seen_texts = set()
        unique_reviews = []
        
        for review in reviews:
            # Normalize text for comparison
            normalized_text = review.text.lower().strip()
            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_reviews.append(review)
        
        logger.info(f"Deduplicated {len(reviews)} reviews to {len(unique_reviews)} unique reviews")
        return unique_reviews


def extract_reviews(
    app_id: str,
    start_date: date,
    end_date: date,
    samples_per_rating: int = 40
) -> List[Review]:
    """
    Convenience function to extract reviews.
    
    Args:
        app_id: App package name
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        samples_per_rating: Number of reviews per rating (default: 15)
        
    Returns:
        List of Review objects
    """
    extractor = ReviewExtractor()
    return extractor.extract_reviews(app_id, start_date, end_date, samples_per_rating)

