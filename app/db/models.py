"""
SQLAlchemy ORM Models for App Review Insights Analyzer

Schema:
- apps: App metadata
- subscriptions: Email subscriptions for apps
- weekly_batches: Weekly processing batches
- reviews: Individual reviews
- theme_summaries: Theme analysis results
- weekly_pulse_notes: Final weekly pulse artifacts
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    JSON,
    Boolean,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class App(Base):
    """App metadata table"""
    __tablename__ = "apps"

    id = Column(Integer, primary_key=True, index=True)
    playstore_app_id = Column(String(255), unique=True, nullable=False, index=True)
    app_name = Column(String(255), nullable=False)
    app_url = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="app", cascade="all, delete-orphan")
    weekly_batches = relationship("WeeklyBatch", back_populates="app", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<App(id={self.id}, playstore_app_id='{self.playstore_app_id}', name='{self.app_name}')>"


class Subscription(Base):
    """Email subscriptions for apps"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("apps.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    app = relationship("App", back_populates="subscriptions")

    __table_args__ = (
        Index("idx_subscription_app_email", "app_id", "email"),
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, app_id={self.app_id}, email='{self.email}', active={self.is_active})>"


class WeeklyBatch(Base):
    """Weekly processing batches"""
    __tablename__ = "weekly_batches"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("apps.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        # Check constraint for status values
    )
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    app = relationship("App", back_populates="weekly_batches")
    reviews = relationship("Review", back_populates="weekly_batch", cascade="all, delete-orphan")
    theme_summaries = relationship("ThemeSummary", back_populates="weekly_batch", cascade="all, delete-orphan")
    weekly_pulse_note = relationship("WeeklyPulseNote", back_populates="weekly_batch", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("app_id", "week_start_date", name="uq_app_week_start"),
        Index("idx_batch_app_week", "app_id", "week_start_date"),
        Index("idx_batch_status", "status"),
        CheckConstraint("status IN ('pending', 'processed', 'failed')", name="chk_batch_status"),
    )

    def __repr__(self) -> str:
        return f"<WeeklyBatch(id={self.id}, app_id={self.app_id}, week={self.week_start_date}, status='{self.status}')>"


class Review(Base):
    """Individual reviews"""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("apps.id", ondelete="CASCADE"), nullable=False, index=True)
    weekly_batch_id = Column(Integer, ForeignKey("weekly_batches.id", ondelete="CASCADE"), nullable=True, index=True)
    rating = Column(Integer, nullable=False)
    title = Column(String(512), nullable=True)
    text = Column(Text, nullable=False)
    review_date = Column(Date, nullable=False, index=True)
    review_hash = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    app = relationship("App")
    weekly_batch = relationship("WeeklyBatch", back_populates="reviews")

    __table_args__ = (
        Index("idx_review_app_date", "app_id", "review_date"),
        Index("idx_review_batch", "weekly_batch_id"),
        Index("idx_review_rating", "rating"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_review_rating"),
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, app_id={self.app_id}, rating={self.rating}, date={self.review_date})>"


class ThemeSummary(Base):
    """Theme analysis results for a weekly batch"""
    __tablename__ = "theme_summaries"

    id = Column(Integer, primary_key=True, index=True)
    weekly_batch_id = Column(Integer, ForeignKey("weekly_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    theme_name = Column(String(255), nullable=False)
    key_points = Column(JSON, nullable=False)  # List of strings
    candidate_quotes = Column(JSON, nullable=False)  # List of strings
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    weekly_batch = relationship("WeeklyBatch", back_populates="theme_summaries")

    __table_args__ = (
        Index("idx_theme_batch", "weekly_batch_id"),
    )

    def __repr__(self) -> str:
        return f"<ThemeSummary(id={self.id}, batch_id={self.weekly_batch_id}, theme='{self.theme_name}')>"


class WeeklyPulseNote(Base):
    """Final weekly pulse artifacts"""
    __tablename__ = "weekly_pulse_notes"

    id = Column(Integer, primary_key=True, index=True)
    weekly_batch_id = Column(Integer, ForeignKey("weekly_batches.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    overview = Column(Text, nullable=False)
    themes = Column(JSON, nullable=False)  # List of {"name": str, "summary": str}
    quotes = Column(JSON, nullable=False)  # List of strings
    actions = Column(JSON, nullable=False)  # List of strings
    word_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    weekly_batch = relationship("WeeklyBatch", back_populates="weekly_pulse_note")

    __table_args__ = (
        Index("idx_pulse_batch", "weekly_batch_id"),
    )

    def __repr__(self) -> str:
        return f"<WeeklyPulseNote(id={self.id}, batch_id={self.weekly_batch_id}, title='{self.title}')>"








