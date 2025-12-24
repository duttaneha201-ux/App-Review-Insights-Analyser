"""
Unit tests for Repository/Data Access Layer

Tests cover:
- CRUD operations for each table
- Deduplication logic using review_hash
- Foreign key integrity
- JSON field serialization/deserialization
"""

import pytest
from datetime import date, timedelta
from app.db.database import get_test_db_session
from app.db.repository import (
    AppRepository,
    SubscriptionRepository,
    WeeklyBatchRepository,
    ReviewRepository,
    ThemeSummaryRepository,
    WeeklyPulseNoteRepository,
)
from app.models.review import Review as ReviewDataClass


class TestAppRepository:
    """Test AppRepository"""

    def test_get_or_create_by_playstore_id_new(self):
        """Test creating a new app"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.commit()

            assert app.id is not None
            assert app.playstore_app_id == "com.whatsapp"

    def test_get_or_create_by_playstore_id_existing(self):
        """Test getting existing app"""
        with get_test_db_session() as session:
            # Create first
            app1 = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.commit()
            app1_id = app1.id

            # Get existing
            app2 = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp Updated",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.commit()

            assert app2.id == app1_id
            assert app2.app_name == "WhatsApp Updated"  # Updated

    def test_get_by_id(self):
        """Test getting app by ID"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.commit()

            found = AppRepository.get_by_id(session, app.id)
            assert found is not None
            assert found.playstore_app_id == "com.whatsapp"


class TestSubscriptionRepository:
    """Test SubscriptionRepository"""

    def test_create_subscription(self):
        """Test creating a subscription"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            subscription = SubscriptionRepository.create(
                session,
                app_id=app.id,
                email="test@example.com",
                start_date=date.today(),
            )
            session.commit()

            assert subscription.id is not None
            assert subscription.email == "test@example.com"

    def test_get_active_subscriptions(self):
        """Test getting active subscriptions"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            sub1 = SubscriptionRepository.create(
                session,
                app_id=app.id,
                email="active@example.com",
                start_date=date.today(),
                is_active=True,
            )
            sub2 = SubscriptionRepository.create(
                session,
                app_id=app.id,
                email="inactive@example.com",
                start_date=date.today(),
                is_active=False,
            )
            session.commit()

            active = SubscriptionRepository.get_active_subscriptions(session, app_id=app.id)
            assert len(active) == 1
            assert active[0].email == "active@example.com"


class TestWeeklyBatchRepository:
    """Test WeeklyBatchRepository"""

    def test_get_or_create_new(self):
        """Test creating a new batch"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            batch = WeeklyBatchRepository.get_or_create(
                session,
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
            )
            session.commit()

            assert batch.id is not None
            assert batch.status == "pending"

    def test_get_or_create_existing(self):
        """Test getting existing batch (idempotent)"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            batch1 = WeeklyBatchRepository.get_or_create(
                session,
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
            )
            session.commit()
            batch1_id = batch1.id

            batch2 = WeeklyBatchRepository.get_or_create(
                session,
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
            )
            session.commit()

            assert batch2.id == batch1_id  # Same batch

    def test_update_status(self):
        """Test updating batch status"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            batch = WeeklyBatchRepository.get_or_create(
                session,
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
            )
            session.commit()

            WeeklyBatchRepository.update_status(session, batch.id, "processed")
            session.commit()

            updated = WeeklyBatchRepository.get_by_id(session, batch.id)
            assert updated.status == "processed"


class TestReviewRepository:
    """Test ReviewRepository"""

    def test_bulk_insert_with_deduplication(self):
        """Test bulk insert with duplicate protection"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            reviews = [
                ReviewDataClass(
                    rating=5,
                    title="Great",
                    text="Great app!",
                    date=date.today(),
                ),
                ReviewDataClass(
                    rating=4,
                    title="Good",
                    text="Good app",
                    date=date.today(),
                ),
                ReviewDataClass(
                    rating=5,
                    title="Great",
                    text="Great app!",  # Duplicate
                    date=date.today(),
                ),
            ]

            inserted = ReviewRepository.bulk_insert_with_deduplication(
                session,
                app_id=app.id,
                weekly_batch_id=None,
                reviews=reviews,
            )
            session.commit()

            assert inserted == 2  # Only 2 unique reviews

    def test_get_by_app(self):
        """Test getting reviews by app"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            reviews = [
                ReviewDataClass(rating=5, title="R1", text="Text 1", date=date.today()),
                ReviewDataClass(rating=4, title="R2", text="Text 2", date=date.today()),
            ]

            ReviewRepository.bulk_insert_with_deduplication(
                session,
                app_id=app.id,
                weekly_batch_id=None,
                reviews=reviews,
            )
            session.commit()

            found = ReviewRepository.get_by_app(session, app.id)
            assert len(found) == 2

    def test_get_by_rating(self):
        """Test getting reviews by rating"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            reviews = [
                ReviewDataClass(rating=5, title="R1", text="Text 1", date=date.today()),
                ReviewDataClass(rating=5, title="R2", text="Text 2", date=date.today()),
                ReviewDataClass(rating=4, title="R3", text="Text 3", date=date.today()),
            ]

            ReviewRepository.bulk_insert_with_deduplication(
                session,
                app_id=app.id,
                weekly_batch_id=None,
                reviews=reviews,
            )
            session.commit()

            five_star = ReviewRepository.get_by_rating(session, app.id, rating=5)
            assert len(five_star) == 2


class TestThemeSummaryRepository:
    """Test ThemeSummaryRepository"""

    def test_bulk_insert(self):
        """Test bulk inserting theme summaries"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            batch = WeeklyBatchRepository.get_or_create(
                session,
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
            )
            session.flush()

            themes = [
                {
                    "theme_name": "Performance",
                    "key_points": ["Slow", "Crashes"],
                    "candidate_quotes": ["Very slow"],
                },
                {
                    "theme_name": "UI",
                    "key_points": ["Confusing"],
                    "candidate_quotes": ["Hard to use"],
                },
            ]

            summaries = ThemeSummaryRepository.bulk_insert(
                session,
                weekly_batch_id=batch.id,
                themes=themes,
            )
            session.commit()

            assert len(summaries) == 2
            assert summaries[0].theme_name == "Performance"


class TestWeeklyPulseNoteRepository:
    """Test WeeklyPulseNoteRepository"""

    def test_create_or_update_new(self):
        """Test creating a new pulse note"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            batch = WeeklyBatchRepository.get_or_create(
                session,
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
            )
            session.flush()

            pulse = WeeklyPulseNoteRepository.create_or_update(
                session,
                weekly_batch_id=batch.id,
                title="Weekly Pulse",
                overview="Overview text",
                themes=[{"name": "Theme 1", "summary": "Summary 1"}],
                quotes=["Quote 1"],
                actions=["Action 1"],
                word_count=100,
            )
            session.commit()

            assert pulse.id is not None
            assert pulse.title == "Weekly Pulse"

    def test_create_or_update_existing(self):
        """Test updating existing pulse note (idempotent)"""
        with get_test_db_session() as session:
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.flush()

            batch = WeeklyBatchRepository.get_or_create(
                session,
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
            )
            session.flush()

            pulse1 = WeeklyPulseNoteRepository.create_or_update(
                session,
                weekly_batch_id=batch.id,
                title="Original Title",
                overview="Original overview",
                themes=[],
                quotes=[],
                actions=[],
                word_count=50,
            )
            session.commit()
            pulse1_id = pulse1.id

            pulse2 = WeeklyPulseNoteRepository.create_or_update(
                session,
                weekly_batch_id=batch.id,
                title="Updated Title",
                overview="Updated overview",
                themes=[],
                quotes=[],
                actions=[],
                word_count=100,
            )
            session.commit()

            assert pulse2.id == pulse1_id  # Same record
            assert pulse2.title == "Updated Title"  # Updated








