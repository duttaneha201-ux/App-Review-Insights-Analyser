"""
Theme Chunking Engine

This module provides functionality to:
- Chunk reviews by week
- Identify themes using LLM (Groq)
- Extract key points per theme
- Select candidate quotes
- Aggregate themes across chunks
"""

import logging
import json
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

from app.models.review import Review
from app.services.llm_orchestrator import LLMOrchestrator, LLMConfig

logger = logging.getLogger(__name__)


@dataclass
class ThemeChunk:
    """
    Represents a theme chunk for a specific week.
    """
    theme: str
    key_points: List[str]
    candidate_quotes: List[str]
    week_start: date
    week_end: date
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "theme": self.theme,
            "key_points": self.key_points,
            "candidate_quotes": self.candidate_quotes,
            "week_start": self.week_start.isoformat(),
            "week_end": self.week_end.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThemeChunk':
        """Create from dictionary"""
        week_start = datetime.fromisoformat(data['week_start']).date() if isinstance(data.get('week_start'), str) else data.get('week_start')
        week_end = datetime.fromisoformat(data['week_end']).date() if isinstance(data.get('week_end'), str) else data.get('week_end')
        
        return cls(
            theme=data['theme'],
            key_points=data.get('key_points', []),
            candidate_quotes=data.get('candidate_quotes', []),
            week_start=week_start,
            week_end=week_end
        )


@dataclass
class AggregatedTheme:
    """
    Represents an aggregated theme across multiple weeks.
    """
    theme: str
    key_points: List[str]
    candidate_quotes: List[str]
    frequency: int  # Number of weeks this theme appeared
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "theme": self.theme,
            "key_points": self.key_points,
            "candidate_quotes": self.candidate_quotes,
            "frequency": self.frequency
        }


class ThemeChunker:
    """
    Chunks reviews by week and identifies themes using LLM.
    """
    
    # Groq model options (free and fast)
    # Available models: llama-3.1-8b-instant, llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
    DEFAULT_MODEL = "llama-3.1-8b-instant"
    
    # Max themes per chunk
    MAX_THEMES_PER_CHUNK = 5
    
    # Max themes total (after aggregation)
    MAX_THEMES_TOTAL = 5
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = None,
        temperature: float = 0.3,
        orchestrator: Optional[LLMOrchestrator] = None
    ):
        """
        Initialize the theme chunker.
        
        Args:
            api_key: Groq API key (if None, will try to get from environment)
            model: Groq model name (default: llama-3.1-8b-instant)
            temperature: LLM temperature (default: 0.3 for more deterministic)
            orchestrator: Optional LLMOrchestrator instance (for testing or shared instance)
        """
        self.model = model or self.DEFAULT_MODEL
        self.temperature = temperature
        
        # Use provided orchestrator or create new one
        if orchestrator is not None:
            self.orchestrator = orchestrator
            # Update model if different from default
            if model and model != orchestrator.config.model:
                config = LLMConfig(model=model, temperature=temperature)
                self.orchestrator = LLMOrchestrator(api_key=orchestrator.api_key, config=config)
        else:
            config = LLMConfig(
                model=self.model,
                temperature=temperature,
                max_tokens=2000,
                max_retries=3,
                backoff_seconds=1.0
            )
            self.orchestrator = LLMOrchestrator(api_key=api_key, config=config)
        
        logger.info(f"Initialized ThemeChunker with model: {self.model}")
    
    def chunk_reviews_by_week(
        self,
        reviews: List[Review],
        start_date: date,
        end_date: date
    ) -> Dict[str, List[Review]]:
        """
        Chunk reviews by week.
        
        Args:
            reviews: List of Review objects
            start_date: Start date of the period
            end_date: End date of the period
            
        Returns:
            Dictionary mapping week identifier (YYYY-WW) to list of reviews
        """
        week_chunks: Dict[str, List[Review]] = defaultdict(list)
        
        for review in reviews:
            # Get ISO week number
            week_key = self._get_week_key(review.date)
            
            # Only include reviews within the date range
            if start_date <= review.date <= end_date:
                week_chunks[week_key].append(review)
        
        # Sort reviews within each week by date (newest first)
        for week_key in week_chunks:
            week_chunks[week_key].sort(key=lambda r: r.date, reverse=True)
        
        logger.info(f"Chunked {len(reviews)} reviews into {len(week_chunks)} weeks")
        return dict(week_chunks)
    
    def _get_week_key(self, review_date: date) -> str:
        """
        Get week identifier in format YYYY-WW.
        
        Args:
            review_date: Date of the review
            
        Returns:
            Week key string (e.g., "2024-15")
        """
        # Use ISO week
        year, week, _ = review_date.isocalendar()
        return f"{year}-W{week:02d}"
    
    def _get_week_dates(self, week_key: str) -> tuple[date, date]:
        """
        Get start and end dates for a week key.
        
        Args:
            week_key: Week key in format YYYY-WW
            
        Returns:
            Tuple of (start_date, end_date)
        """
        year, week = week_key.split('-W')
        year = int(year)
        week = int(week)
        
        # Get first day of the week (Monday)
        jan1 = date(year, 1, 1)
        days_offset = (week - 1) * 7
        week_start = jan1 + timedelta(days=days_offset - jan1.weekday())
        
        # Get last day of the week (Sunday)
        week_end = week_start + timedelta(days=6)
        
        return week_start, week_end
    
    def identify_themes_for_chunk(
        self,
        reviews: List[Review],
        week_start: date,
        week_end: date
    ) -> List[ThemeChunk]:
        """
        Identify themes for a chunk of reviews using LLM.
        
        Args:
            reviews: List of reviews for this week
            week_start: Start date of the week
            week_end: End date of the week
            
        Returns:
            List of ThemeChunk objects (max 5 themes)
        """
        if not reviews:
            return []
        
        # Prepare review text for LLM
        review_texts = []
        for i, review in enumerate(reviews[:50], 1):  # Limit to 50 reviews per chunk
            rating_stars = "⭐" * review.rating
            review_texts.append(f"Review {i} ({rating_stars}): {review.text}")
        
        reviews_text = "\n\n".join(review_texts)
        
        # Create prompt
        prompt = self._create_theme_identification_prompt(reviews_text, len(reviews))
        
        # Call LLM
        try:
            response = self._call_llm(prompt)
            themes = self._parse_theme_response(response, week_start, week_end)
            
            # Limit to max themes
            themes = themes[:self.MAX_THEMES_PER_CHUNK]
            
            logger.info(f"Identified {len(themes)} themes for week {week_start} to {week_end}")
            return themes
            
        except Exception as e:
            logger.error(f"Error identifying themes: {e}", exc_info=True)
            return []
    
    def _create_theme_identification_prompt(self, reviews_text: str, num_reviews: int) -> str:
        """
        Create prompt for theme identification.
        
        Args:
            reviews_text: Formatted review texts
            num_reviews: Total number of reviews
            
        Returns:
            Prompt string
        """
        prompt = f"""You are analyzing {num_reviews} app reviews to identify common themes.

REVIEWS:
{reviews_text}

TASK:
Identify up to 5 main themes from these reviews. For each theme:
1. Provide a concise theme name (2-4 words)
2. List 2-4 key points that summarize the theme
3. Select 2-3 representative quotes from the reviews

RULES:
- Keep everything concise and factual
- NO marketing language or fluff
- Focus on user experiences and feedback
- Themes should be specific and actionable
- Quotes must be exact from the reviews (or very close paraphrases)

OUTPUT FORMAT (JSON array):
[
  {{
    "theme": "Theme name",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "candidate_quotes": ["Quote 1", "Quote 2"]
  }},
  ...
]

Return ONLY valid JSON. No markdown, no explanations, just the JSON array."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM via orchestrator.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Response text from LLM
        """
        system_prompt = "You are a helpful assistant that analyzes user reviews and identifies themes. Always respond with valid JSON only."
        
        try:
            response = self.orchestrator.chat_json(
                system_prompt=system_prompt,
                user_prompt=prompt,
                max_tokens=2000
            )
            logger.debug(f"LLM response: {response[:200]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error calling LLM via orchestrator: {e}")
            raise
    
    def _parse_theme_response(
        self,
        response: str,
        week_start: date,
        week_end: date
    ) -> List[ThemeChunk]:
        """
        Parse LLM response into ThemeChunk objects.
        
        Args:
            response: LLM response text
            week_start: Week start date
            week_end: Week end date
            
        Returns:
            List of ThemeChunk objects
        """
        themes = []
        
        try:
            # Use orchestrator's robust JSON parsing
            data = self.orchestrator.parse_json_response(response)
            
            # Handle different response formats
            if isinstance(data, dict):
                # Single theme object
                if "theme" in data:
                    themes_data = [data]
                # Wrapped in a key
                elif "themes" in data:
                    themes_data = data["themes"]
                else:
                    # Try to find array in any key
                    themes_data = next((v for v in data.values() if isinstance(v, list)), [])
            elif isinstance(data, list):
                themes_data = data
            else:
                logger.warning(f"Unexpected response format: {type(data)}")
                return []
            
            # Create ThemeChunk objects
            for theme_data in themes_data:
                if not isinstance(theme_data, dict):
                    continue
                
                theme = theme_data.get("theme", "").strip()
                if not theme:
                    continue
                
                key_points = theme_data.get("key_points", [])
                if isinstance(key_points, str):
                    key_points = [key_points]
                key_points = [kp.strip() for kp in key_points if kp.strip()]
                
                candidate_quotes = theme_data.get("candidate_quotes", [])
                if isinstance(candidate_quotes, str):
                    candidate_quotes = [candidate_quotes]
                candidate_quotes = [cq.strip() for cq in candidate_quotes if cq.strip()]
                
                if theme and (key_points or candidate_quotes):
                    themes.append(ThemeChunk(
                        theme=theme,
                        key_points=key_points[:4],  # Limit to 4
                        candidate_quotes=candidate_quotes[:3],  # Limit to 3
                        week_start=week_start,
                        week_end=week_end
                    ))
            
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response[:500]}")
        except Exception as e:
            logger.error(f"Error parsing theme response: {e}", exc_info=True)
        
        return themes
    
    def aggregate_themes(
        self,
        theme_chunks: List[ThemeChunk]
    ) -> List[AggregatedTheme]:
        """
        Aggregate themes across multiple weeks.
        
        Args:
            theme_chunks: List of ThemeChunk objects from all weeks
            
        Returns:
            List of AggregatedTheme objects (max 5 themes)
        """
        # Group themes by similarity
        theme_groups: Dict[str, List[ThemeChunk]] = defaultdict(list)
        
        for chunk in theme_chunks:
            # Simple grouping by exact theme name match
            # In production, you might want fuzzy matching here
            theme_key = chunk.theme.lower().strip()
            theme_groups[theme_key].append(chunk)
        
        # Create aggregated themes
        aggregated = []
        
        for theme_key, chunks in theme_groups.items():
            # Use the most common theme name
            theme_name = max(set(c.theme for c in chunks), key=lambda t: sum(1 for c in chunks if c.theme == t))
            
            # Aggregate key points (deduplicate and limit)
            all_key_points = []
            for chunk in chunks:
                all_key_points.extend(chunk.key_points)
            
            # Remove duplicates while preserving order
            seen_points = set()
            unique_key_points = []
            for point in all_key_points:
                point_lower = point.lower().strip()
                if point_lower not in seen_points and len(point_lower) > 3:  # Allow shorter points
                    seen_points.add(point_lower)
                    unique_key_points.append(point)
            
            # Aggregate candidate quotes (deduplicate and limit)
            all_quotes = []
            for chunk in chunks:
                all_quotes.extend(chunk.candidate_quotes)
            
            # Remove duplicates while preserving order
            seen_quotes = set()
            unique_quotes = []
            for quote in all_quotes:
                quote_lower = quote.lower().strip()
                if quote_lower not in seen_quotes and len(quote_lower) > 15:
                    seen_quotes.add(quote_lower)
                    unique_quotes.append(quote)
            
            aggregated.append(AggregatedTheme(
                theme=theme_name,
                key_points=unique_key_points[:5],  # Limit to 5 key points
                candidate_quotes=unique_quotes[:5],  # Limit to 5 quotes
                frequency=len(chunks)
            ))
        
        # Sort by frequency (most common first)
        aggregated.sort(key=lambda t: t.frequency, reverse=True)
        
        # Limit to max themes
        aggregated = aggregated[:self.MAX_THEMES_TOTAL]
        
        logger.info(f"Aggregated {len(theme_chunks)} theme chunks into {len(aggregated)} themes")
        return aggregated
    
    def process_reviews(
        self,
        reviews: List[Review],
        start_date: date,
        end_date: date
    ) -> List[AggregatedTheme]:
        """
        Complete pipeline: chunk reviews, identify themes, and aggregate.
        
        Args:
            reviews: List of Review objects
            start_date: Start date of the period
            end_date: End date of the period
            
        Returns:
            List of AggregatedTheme objects
        """
        # Step 1: Chunk by week
        week_chunks = self.chunk_reviews_by_week(reviews, start_date, end_date)
        
        # Step 2: Identify themes for each week
        all_theme_chunks = []
        for week_key, week_reviews in week_chunks.items():
            week_start, week_end = self._get_week_dates(week_key)
            themes = self.identify_themes_for_chunk(week_reviews, week_start, week_end)
            all_theme_chunks.extend(themes)
        
        # Step 3: Aggregate themes across weeks
        aggregated = self.aggregate_themes(all_theme_chunks)
        
        return aggregated


def chunk_reviews_by_week(
    reviews: List[Review],
    start_date: date,
    end_date: date
) -> Dict[str, List[Review]]:
    """
    Convenience function to chunk reviews by week.
    
    Args:
        reviews: List of Review objects
        start_date: Start date
        end_date: End date
        
    Returns:
        Dictionary mapping week keys to reviews
    """
    chunker = ThemeChunker.__new__(ThemeChunker)  # Create without __init__
    chunker.chunk_reviews_by_week = ThemeChunker.chunk_reviews_by_week.__get__(chunker, ThemeChunker)
    chunker._get_week_key = ThemeChunker._get_week_key.__get__(chunker, ThemeChunker)
    return chunker.chunk_reviews_by_week(reviews, start_date, end_date)

