"""
Repository/Data Access Layer for App Review Insights Analyzer

Provides clean, testable methods for database operations.
All database access should go through this layer.
"""

import hashlib
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.db.models import (
    App,
    Subscription,
    WeeklyBatch,
    Review as ReviewModel,
    ThemeSummary,
    WeeklyPulseNote,
)
from app.models.review import Review as ReviewDataClass


class AppRepository:
    """Repository for App operations"""

    @staticmethod
    def get_or_create_by_playstore_id(
        session: Session,
        playstore_app_id: str,
        app_name: str,
        app_url: str,
    ) -> App:
        """
        Get existing app or create new one by Play Store ID.
        
        Args:
            session: Database session
            playstore_app_id: Google Play Store app ID (e.g., "com.whatsapp")
            app_name: App name
            app_url: App URL
            
        Returns:
            App instance
        """
        app = session.query(App).filter(
            App.playstore_app_id == playstore_app_id
        ).first()
        
        if app:
            # Update name/URL if changed
            if app.app_name != app_name or app.app_url != app_url:
                app.app_name = app_name
                app.app_url = app_url
        else:
            app = App(
                playstore_app_id=playstore_app_id,
                app_name=app_name,
                app_url=app_url,
            )
            session.add(app)
            session.flush()
        
        return app

    @staticmethod
    def get_by_id(session: Session, app_id: int) -> Optional[App]:
        """Get app by ID"""
        return session.query(App).filter(App.id == app_id).first()

    @staticmethod
    def get_by_playstore_id(session: Session, playstore_app_id: str) -> Optional[App]:
        """Get app by Play Store ID"""
        return session.query(App).filter(
            App.playstore_app_id == playstore_app_id
        ).first()

    @staticmethod
    def list_all(session: Session) -> List[App]:
        """List all apps"""
        return session.query(App).all()


class SubscriptionRepository:
    """Repository for Subscription operations"""

    @staticmethod
    def create(
        session: Session,
        app_id: int,
        email: str,
        start_date: date,
        end_date: Optional[date] = None,
        is_active: bool = True,
    ) -> Subscription:
        """
        Create a new subscription.
        
        Args:
            session: Database session
            app_id: App ID
            email: Email address
            start_date: Subscription start date
            end_date: Optional end date
            is_active: Whether subscription is active
            
        Returns:
            Subscription instance
        """
        subscription = Subscription(
            app_id=app_id,
            email=email,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
        )
        session.add(subscription)
        session.flush()
        return subscription

    @staticmethod
    def get_active_subscriptions(
        session: Session,
        app_id: Optional[int] = None,
    ) -> List[Subscription]:
        """
        Get active subscriptions, optionally filtered by app.
        
        Args:
            session: Database session
            app_id: Optional app ID filter
            
        Returns:
            List of active subscriptions
        """
        query = session.query(Subscription).filter(Subscription.is_active == True)
        
        if app_id:
            query = query.filter(Subscription.app_id == app_id)
        
        return query.all()

    @staticmethod
    def deactivate(session: Session, subscription_id: int) -> None:
        """Deactivate a subscription"""
        subscription = session.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        if subscription:
            subscription.is_active = False


class WeeklyBatchRepository:
    """Repository for WeeklyBatch operations"""

    @staticmethod
    def get_or_create(
        session: Session,
        app_id: int,
        week_start_date: date,
        week_end_date: date,
    ) -> WeeklyBatch:
        """
        Get existing batch or create new one (idempotent).
        
        Args:
            session: Database session
            app_id: App ID
            week_start_date: Week start date
            week_end_date: Week end date
            
        Returns:
            WeeklyBatch instance
        """
        batch = session.query(WeeklyBatch).filter(
            and_(
                WeeklyBatch.app_id == app_id,
                WeeklyBatch.week_start_date == week_start_date,
            )
        ).first()
        
        if not batch:
            batch = WeeklyBatch(
                app_id=app_id,
                week_start_date=week_start_date,
                week_end_date=week_end_date,
                status="pending",
            )
            session.add(batch)
            session.flush()
        
        return batch

    @staticmethod
    def get_by_id(session: Session, batch_id: int) -> Optional[WeeklyBatch]:
        """Get batch by ID"""
        return session.query(WeeklyBatch).filter(WeeklyBatch.id == batch_id).first()

    @staticmethod
    def update_status(
        session: Session,
        batch_id: int,
        status: str,
    ) -> None:
        """
        Update batch status.
        
        Args:
            session: Database session
            batch_id: Batch ID
            status: New status ('pending', 'processed', 'failed')
        """
        batch = session.query(WeeklyBatch).filter(WeeklyBatch.id == batch_id).first()
        if batch:
            batch.status = status
            batch.updated_at = datetime.now()

    @staticmethod
    def get_pending_batches(session: Session) -> List[WeeklyBatch]:
        """Get all pending batches"""
        return session.query(WeeklyBatch).filter(
            WeeklyBatch.status == "pending"
        ).all()

    @staticmethod
    def get_by_app_and_week(
        session: Session,
        app_id: int,
        week_start_date: date,
    ) -> Optional[WeeklyBatch]:
        """Get batch by app and week"""
        return session.query(WeeklyBatch).filter(
            and_(
                WeeklyBatch.app_id == app_id,
                WeeklyBatch.week_start_date == week_start_date,
            )
        ).first()


class ReviewRepository:
    """Repository for Review operations"""

    @staticmethod
    def _compute_review_hash(review: ReviewDataClass) -> str:
        """
        Compute hash for review deduplication.
        
        Uses rating + text + date to create unique hash.
        """
        content = f"{review.rating}|{review.text.strip()}|{review.date.isoformat()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def bulk_insert_with_deduplication(
        session: Session,
        app_id: int,
        weekly_batch_id: Optional[int],
        reviews: List[ReviewDataClass],
    ) -> int:
        """
        Bulk insert reviews with duplicate protection.
        
        Args:
            session: Database session
            app_id: App ID
            weekly_batch_id: Optional weekly batch ID
            reviews: List of Review objects
            
        Returns:
            Number of reviews actually inserted (excluding duplicates)
        """
        inserted_count = 0
        seen_hashes = set()  # Track hashes in current batch to avoid duplicates within batch
        
        for review in reviews:
            review_hash = ReviewRepository._compute_review_hash(review)
            
            # Skip if already seen in this batch
            if review_hash in seen_hashes:
                continue
            
            # Check if review already exists in database
            existing = session.query(ReviewModel).filter(
                ReviewModel.review_hash == review_hash
            ).first()
            
            if not existing:
                db_review = ReviewModel(
                    app_id=app_id,
                    weekly_batch_id=weekly_batch_id,
                    rating=review.rating,
                    title=review.title,
                    text=review.text,
                    review_date=review.date,
                    review_hash=review_hash,
                )
                session.add(db_review)
                inserted_count += 1
                seen_hashes.add(review_hash)
        
        session.flush()
        return inserted_count

    @staticmethod
    def get_by_app(
        session: Session,
        app_id: int,
        limit: Optional[int] = None,
    ) -> List[ReviewModel]:
        """Get reviews by app"""
        query = session.query(ReviewModel).filter(ReviewModel.app_id == app_id)
        query = query.order_by(ReviewModel.review_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()

    @staticmethod
    def get_by_week(
        session: Session,
        weekly_batch_id: int,
    ) -> List[ReviewModel]:
        """Get reviews by weekly batch"""
        return session.query(ReviewModel).filter(
            ReviewModel.weekly_batch_id == weekly_batch_id
        ).order_by(ReviewModel.review_date.desc()).all()

    @staticmethod
    def get_by_rating(
        session: Session,
        app_id: int,
        rating: int,
        limit: Optional[int] = None,
    ) -> List[ReviewModel]:
        """Get reviews by rating"""
        query = session.query(ReviewModel).filter(
            and_(
                ReviewModel.app_id == app_id,
                ReviewModel.rating == rating,
            )
        ).order_by(ReviewModel.review_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()

    @staticmethod
    def get_by_date_range(
        session: Session,
        app_id: int,
        start_date: date,
        end_date: date,
    ) -> List[ReviewModel]:
        """Get reviews by date range"""
        return session.query(ReviewModel).filter(
            and_(
                ReviewModel.app_id == app_id,
                ReviewModel.review_date >= start_date,
                ReviewModel.review_date <= end_date,
            )
        ).order_by(ReviewModel.review_date.desc()).all()


class ThemeSummaryRepository:
    """Repository for ThemeSummary operations"""

    @staticmethod
    def bulk_insert(
        session: Session,
        weekly_batch_id: int,
        themes: List[Dict[str, Any]],
    ) -> List[ThemeSummary]:
        """
        Bulk insert theme summaries.
        
        Args:
            session: Database session
            weekly_batch_id: Weekly batch ID
            themes: List of theme dicts with keys: theme_name, key_points, candidate_quotes
            
        Returns:
            List of created ThemeSummary instances
        """
        summaries = []
        
        for theme in themes:
            summary = ThemeSummary(
                weekly_batch_id=weekly_batch_id,
                theme_name=theme["theme_name"],
                key_points=theme.get("key_points", []),
                candidate_quotes=theme.get("candidate_quotes", []),
            )
            session.add(summary)
            summaries.append(summary)
        
        session.flush()
        return summaries

    @staticmethod
    def get_by_week(
        session: Session,
        weekly_batch_id: int,
    ) -> List[ThemeSummary]:
        """Get theme summaries for a weekly batch"""
        return session.query(ThemeSummary).filter(
            ThemeSummary.weekly_batch_id == weekly_batch_id
        ).all()


class WeeklyPulseNoteRepository:
    """Repository for WeeklyPulseNote operations"""

    @staticmethod
    def create_or_update(
        session: Session,
        weekly_batch_id: int,
        title: str,
        overview: str,
        themes: List[Dict[str, str]],
        quotes: List[str],
        actions: List[str],
        word_count: int,
    ) -> WeeklyPulseNote:
        """
        Create or update weekly pulse note (idempotent).
        
        Args:
            session: Database session
            weekly_batch_id: Weekly batch ID
            title: Pulse title
            overview: Overview text
            themes: List of theme dicts with 'name' and 'summary'
            quotes: List of quote strings
            actions: List of action strings
            word_count: Total word count
            
        Returns:
            WeeklyPulseNote instance
        """
        pulse = session.query(WeeklyPulseNote).filter(
            WeeklyPulseNote.weekly_batch_id == weekly_batch_id
        ).first()
        
        if pulse:
            # Update existing
            pulse.title = title
            pulse.overview = overview
            pulse.themes = themes
            pulse.quotes = quotes
            pulse.actions = actions
            pulse.word_count = word_count
        else:
            # Create new
            pulse = WeeklyPulseNote(
                weekly_batch_id=weekly_batch_id,
                title=title,
                overview=overview,
                themes=themes,
                quotes=quotes,
                actions=actions,
                word_count=word_count,
            )
            session.add(pulse)
        
        session.flush()
        return pulse

    @staticmethod
    def get_by_week(
        session: Session,
        weekly_batch_id: int,
    ) -> Optional[WeeklyPulseNote]:
        """Get weekly pulse note by batch ID"""
        return session.query(WeeklyPulseNote).filter(
            WeeklyPulseNote.weekly_batch_id == weekly_batch_id
        ).first()

    @staticmethod
    def get_by_app(
        session: Session,
        app_id: int,
        limit: Optional[int] = None,
    ) -> List[WeeklyPulseNote]:
        """Get weekly pulse notes for an app"""
        query = session.query(WeeklyPulseNote).join(WeeklyBatch).filter(
            WeeklyBatch.app_id == app_id
        ).order_by(WeeklyPulseNote.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()

