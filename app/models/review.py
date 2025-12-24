"""
Review data model
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Review:
    """
    Represents a single app review from Google Play Store.
    """
    rating: int  # 1-5 stars
    title: Optional[str]
    text: str
    date: date
    review_id: Optional[str] = None  # Unique identifier if available
    author: Optional[str] = None  # Will be scrubbed later, stored temporarily
    
    def __post_init__(self):
        """Validate review data"""
        if not (1 <= self.rating <= 5):
            raise ValueError(f"Rating must be between 1 and 5, got {self.rating}")
        
        if not self.text or len(self.text.strip()) == 0:
            raise ValueError("Review text cannot be empty")
        
        if not isinstance(self.date, date):
            raise ValueError(f"Date must be a date object, got {type(self.date)}")
    
    def to_dict(self) -> dict:
        """Convert review to dictionary"""
        return {
            'rating': self.rating,
            'title': self.title,
            'text': self.text,
            'date': self.date.isoformat(),
            'review_id': self.review_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Review':
        """Create review from dictionary"""
        from datetime import datetime
        
        date_obj = data['date']
        if isinstance(date_obj, str):
            date_obj = datetime.fromisoformat(date_obj).date()
        
        return cls(
            rating=data['rating'],
            title=data.get('title'),
            text=data['text'],
            date=date_obj,
            review_id=data.get('review_id'),
        )

