"""
Weekly Synthesis Engine

This module provides functionality to:
- Synthesize aggregated themes into a Weekly Product Pulse
- Generate executive-friendly summaries (≤250 words)
- Auto-compress if word count exceeds limit
- Select top 3 themes based on frequency & impact
"""

import logging
import json
import re
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

from app.services.theme_chunker import AggregatedTheme
from app.services.llm_orchestrator import LLMOrchestrator, LLMConfig

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class WeeklyPulse:
    """
    Represents a Weekly Product Pulse.
    """
    title: str
    overview: str
    themes: List[Dict[str, str]]  # [{"name": "...", "summary": "..."}]
    quotes: List[str]
    actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "overview": self.overview,
            "themes": self.themes,
            "quotes": self.quotes,
            "actions": self.actions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeeklyPulse':
        """Create from dictionary"""
        return cls(
            title=data.get("title", ""),
            overview=data.get("overview", ""),
            themes=data.get("themes", []),
            quotes=data.get("quotes", []),
            actions=data.get("actions", [])
        )
    
    def word_count(self) -> int:
        """Calculate total word count"""
        text = f"{self.title} {self.overview} "
        for theme in self.themes:
            text += f"{theme.get('name', '')} {theme.get('summary', '')} "
        text += " ".join(self.quotes) + " "
        text += " ".join(self.actions)
        return len(text.split())


class WeeklySynthesisEngine:
    """
    Synthesizes aggregated themes into a Weekly Product Pulse.
    """
    
    # Groq model (same as theme chunker)
    DEFAULT_MODEL = "llama-3.1-8b-instant"
    
    # Word count limits
    MAX_WORDS = 250
    MAX_THEMES = 3
    MAX_QUOTES = 3
    MAX_ACTIONS = 3
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = None,
        temperature: float = 0.3,
        orchestrator: Optional[LLMOrchestrator] = None
    ):
        """
        Initialize the synthesis engine.
        
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
                max_tokens=1000,
                max_retries=3,
                backoff_seconds=1.0
            )
            self.orchestrator = LLMOrchestrator(api_key=api_key, config=config)
        
        logger.info(f"Initialized WeeklySynthesisEngine with model: {self.model}")
    
    def synthesize_weekly_pulse(
        self,
        aggregated_themes: List[AggregatedTheme],
        app_name: Optional[str] = None
    ) -> WeeklyPulse:
        """
        Synthesize aggregated themes into a Weekly Product Pulse.
        
        Args:
            aggregated_themes: List of AggregatedTheme objects (from Module 4)
            app_name: Optional app name for context
            
        Returns:
            WeeklyPulse object
        """
        if not aggregated_themes:
            logger.warning("No themes provided for synthesis")
            return WeeklyPulse(
                title="No Themes Identified",
                overview="No significant themes were identified from the reviews.",
                themes=[],
                quotes=[],
                actions=[]
            )
        
        # Select top 3 themes based on frequency & impact
        top_themes = self._select_top_themes(aggregated_themes, max_themes=self.MAX_THEMES)
        
        # Create synthesis prompt
        prompt = self._create_synthesis_prompt(top_themes, app_name)
        
        # Call LLM to generate pulse
        try:
            response = self._call_llm(prompt)
            pulse = self._parse_pulse_response(response)
            
            # Validate and compress if needed
            pulse = self._validate_and_compress(pulse)
            
            logger.info(f"Generated weekly pulse: {pulse.title} ({pulse.word_count()} words)")
            return pulse
            
        except Exception as e:
            logger.error(f"Error synthesizing weekly pulse: {e}", exc_info=True)
            # Return fallback pulse
            return self._create_fallback_pulse(top_themes)
    
    def _select_top_themes(
        self,
        themes: List[AggregatedTheme],
        max_themes: int = 3
    ) -> List[AggregatedTheme]:
        """
        Select top themes based on frequency and impact.
        
        Args:
            themes: List of aggregated themes
            max_themes: Maximum number of themes to select
            
        Returns:
            List of top themes (sorted by frequency, then by number of key points)
        """
        # Sort by frequency (most common first), then by number of key points
        sorted_themes = sorted(
            themes,
            key=lambda t: (t.frequency, len(t.key_points), len(t.candidate_quotes)),
            reverse=True
        )
        
        # Limit to max themes
        top_themes = sorted_themes[:max_themes]
        
        logger.info(f"Selected top {len(top_themes)} themes from {len(themes)} total")
        return top_themes
    
    def _create_synthesis_prompt(
        self,
        themes: List[AggregatedTheme],
        app_name: Optional[str] = None
    ) -> str:
        """
        Create prompt for weekly pulse synthesis.
        
        Args:
            themes: List of top themes
            app_name: Optional app name
            
        Returns:
            Prompt string
        """
        # Format themes for prompt
        themes_text = []
        for i, theme in enumerate(themes, 1):
            theme_text = f"Theme {i}: {theme.theme}\n"
            theme_text += f"  Frequency: {theme.frequency} week(s)\n"
            if theme.key_points:
                theme_text += f"  Key Points: {', '.join(theme.key_points[:3])}\n"
            if theme.candidate_quotes:
                theme_text += f"  Sample Quotes: {', '.join(theme.candidate_quotes[:2])}\n"
            themes_text.append(theme_text)
        
        themes_section = "\n".join(themes_text)
        
        app_context = f" for {app_name}" if app_name else ""
        
        prompt = f"""You are creating a Weekly Product Pulse{app_context} based on user reviews.

THEMES IDENTIFIED:
{themes_section}

TASK:
Create a concise, executive-friendly Weekly Product Pulse that synthesizes these themes.

REQUIREMENTS:
- Total output MUST be ≤ 250 words
- Executive-friendly, neutral tone (no marketing language)
- Focus on actionable insights
- No PII (personal information already removed)
- Be factual and data-driven

OUTPUT FORMAT (JSON):
{{
  "title": "Concise title (5-10 words)",
  "overview": "Brief overview (2-3 sentences, ~30-40 words)",
  "themes": [
    {{"name": "Theme name", "summary": "Brief summary (1-2 sentences)"}},
    ...
  ],
  "quotes": ["Representative quote 1", "Quote 2", "Quote 3"],
  "actions": ["Actionable insight 1", "Action 2", "Action 3"]
}}

CONSTRAINTS:
- Maximum 3 themes (select most impactful)
- Maximum 3 quotes (most representative)
- Maximum 3 actions (most actionable)
- Total word count: ≤ 250 words
- Keep everything concise and factual

Return ONLY valid JSON. No markdown, no explanations, just the JSON object."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM via orchestrator.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Response text from LLM
        """
        system_prompt = "You are a helpful assistant that creates executive summaries. Always respond with valid JSON only."
        
        try:
            response = self.orchestrator.chat_json(
                system_prompt=system_prompt,
                user_prompt=prompt,
                max_tokens=1000
            )
            logger.debug(f"LLM response: {response[:200]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error calling LLM via orchestrator: {e}")
            raise
    
    def _parse_pulse_response(self, response: str) -> WeeklyPulse:
        """
        Parse LLM response into WeeklyPulse object.
        
        Args:
            response: LLM response text
            
        Returns:
            WeeklyPulse object
        """
        try:
            # Use orchestrator's robust JSON parsing
            data = self.orchestrator.parse_json_response(response)
            
            # Validate and create WeeklyPulse
            pulse = WeeklyPulse.from_dict(data)
            
            # Ensure limits
            pulse.themes = pulse.themes[:self.MAX_THEMES]
            pulse.quotes = pulse.quotes[:self.MAX_QUOTES]
            pulse.actions = pulse.actions[:self.MAX_ACTIONS]
            
            return pulse
            
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        except Exception as e:
            logger.error(f"Error parsing pulse response: {e}", exc_info=True)
            raise
    
    def _validate_and_compress(self, pulse: WeeklyPulse) -> WeeklyPulse:
        """
        Validate word count and compress if needed.
        
        Args:
            pulse: WeeklyPulse object
            
        Returns:
            Compressed WeeklyPulse if needed
        """
        word_count = pulse.word_count()
        
        if word_count <= self.MAX_WORDS:
            logger.debug(f"Pulse word count ({word_count}) is within limit")
            return pulse
        
        logger.info(f"Pulse word count ({word_count}) exceeds limit ({self.MAX_WORDS}), compressing...")
        
        # Compression pass
        compressed = self._compress_pulse(pulse)
        
        # Verify compression worked
        new_word_count = compressed.word_count()
        if new_word_count > self.MAX_WORDS:
            logger.warning(f"Compression still exceeds limit ({new_word_count} words), applying aggressive compression")
            compressed = self._aggressive_compress(compressed)
        
        logger.info(f"Compressed to {compressed.word_count()} words")
        return compressed
    
    def _compress_pulse(self, pulse: WeeklyPulse) -> WeeklyPulse:
        """
        Compress pulse while preserving key elements.
        
        Strategy:
        - Keep top 3 themes (already limited)
        - Keep top 3 quotes (already limited)
        - Keep top 3 actions (already limited)
        - Shorten overview
        - Shorten theme summaries
        - Shorten quotes if needed
        """
        compressed = WeeklyPulse(
            title=pulse.title[:60],  # Limit title length
            overview=self._compress_text(pulse.overview, target_words=40),
            themes=[],
            quotes=pulse.quotes[:self.MAX_QUOTES],
            actions=pulse.actions[:self.MAX_ACTIONS]
        )
        
        # Compress theme summaries
        for theme in pulse.themes[:self.MAX_THEMES]:
            theme_name = theme.get('name', '')[:30]
            theme_summary = self._compress_text(theme.get('summary', ''), target_words=20)
            compressed.themes.append({
                'name': theme_name,
                'summary': theme_summary
            })
        
        # Compress quotes if still too long
        if compressed.word_count() > self.MAX_WORDS:
            compressed.quotes = [
                self._compress_text(q, target_words=15) for q in compressed.quotes[:self.MAX_QUOTES]
            ]
        
        return compressed
    
    def _aggressive_compress(self, pulse: WeeklyPulse) -> WeeklyPulse:
        """
        Aggressively compress pulse to meet word limit.
        
        Args:
            pulse: WeeklyPulse object
            
        Returns:
            Heavily compressed WeeklyPulse
        """
        return WeeklyPulse(
            title=pulse.title[:50],
            overview=self._compress_text(pulse.overview, target_words=30),
            themes=[
                {
                    'name': theme.get('name', '')[:25],
                    'summary': self._compress_text(theme.get('summary', ''), target_words=15)
                }
                for theme in pulse.themes[:self.MAX_THEMES]
            ],
            quotes=[
                self._compress_text(q, target_words=12) for q in pulse.quotes[:self.MAX_QUOTES]
            ],
            actions=[
                self._compress_text(a, target_words=10) for a in pulse.actions[:self.MAX_ACTIONS]
            ]
        )
    
    def _compress_text(self, text: str, target_words: int) -> str:
        """
        Compress text to approximately target word count.
        
        Args:
            text: Text to compress
            target_words: Target word count
            
        Returns:
            Compressed text
        """
        if not text:
            return ""
        
        words = text.split()
        if len(words) <= target_words:
            return text
        
        # Take first target_words words
        compressed_words = words[:target_words]
        
        # Ensure it ends properly (remove trailing punctuation issues)
        result = " ".join(compressed_words)
        
        # Add ellipsis if truncated
        if len(words) > target_words:
            result = result.rstrip('.,;:') + "..."
        
        return result
    
    def _create_fallback_pulse(self, themes: List[AggregatedTheme]) -> WeeklyPulse:
        """
        Create a fallback pulse if LLM fails.
        
        Args:
            themes: List of themes
            
        Returns:
            Basic WeeklyPulse object
        """
        if not themes:
            return WeeklyPulse(
                title="Weekly Product Pulse",
                overview="No themes identified this week.",
                themes=[],
                quotes=[],
                actions=[]
            )
        
        # Create simple pulse from themes
        theme_summaries = []
        quotes = []
        
        for theme in themes[:self.MAX_THEMES]:
            theme_summaries.append({
                'name': theme.theme,
                'summary': '. '.join(theme.key_points[:2]) if theme.key_points else "No summary available."
            })
            if theme.candidate_quotes:
                quotes.extend(theme.candidate_quotes[:1])
        
        return WeeklyPulse(
            title="Weekly Product Pulse",
            overview=f"Identified {len(themes)} key themes from user reviews.",
            themes=theme_summaries[:self.MAX_THEMES],
            quotes=quotes[:self.MAX_QUOTES],
            actions=["Review theme details", "Prioritize improvements", "Monitor trends"]
        )


def synthesize_weekly_pulse(
    aggregated_themes: List[AggregatedTheme],
    app_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> WeeklyPulse:
    """
    Convenience function to synthesize weekly pulse.
    
    Args:
        aggregated_themes: List of AggregatedTheme objects
        app_name: Optional app name
        api_key: Optional Groq API key (uses env var if not provided)
        
    Returns:
        WeeklyPulse object
    """
    engine = WeeklySynthesisEngine(api_key=api_key)
    return engine.synthesize_weekly_pulse(aggregated_themes, app_name)

