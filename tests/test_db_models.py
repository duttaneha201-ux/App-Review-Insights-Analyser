"""
Unit tests for Database Models

Tests cover:
- Model creation and validation
- Relationships
- Foreign key integrity
- JSON field serialization/deserialization
"""

import pytest
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    App,
    Subscription,
    WeeklyBatch,
    Review,
    ThemeSummary,
    WeeklyPulseNote,
)
from app.db.database import get_test_db_session


class TestAppModel:
    """Test App model"""

    def test_create_app(self):
        """Test creating an app"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.commit()

            assert app.id is not None
            assert app.playstore_app_id == "com.whatsapp"
            assert app.app_name == "WhatsApp"

    def test_app_unique_playstore_id(self):
        """Test that playstore_app_id must be unique"""
        with get_test_db_session() as session:
            app1 = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app1)
            session.commit()

            app2 = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp Duplicate",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app2)

            with pytest.raises(IntegrityError):
                session.commit()


class TestSubscriptionModel:
    """Test Subscription model"""

    def test_create_subscription(self):
        """Test creating a subscription"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            subscription = Subscription(
                app_id=app.id,
                email="test@example.com",
                start_date=date.today(),
                is_active=True,
            )
            session.add(subscription)
            session.commit()

            assert subscription.id is not None
            assert subscription.email == "test@example.com"
            assert subscription.is_active is True

    def test_subscription_foreign_key(self):
        """Test that subscription requires valid app_id"""
        with get_test_db_session() as session:
            subscription = Subscription(
                app_id=99999,  # Non-existent app
                email="test@example.com",
                start_date=date.today(),
            )
            session.add(subscription)

            with pytest.raises(IntegrityError):
                session.commit()


class TestWeeklyBatchModel:
    """Test WeeklyBatch model"""

    def test_create_weekly_batch(self):
        """Test creating a weekly batch"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            batch = WeeklyBatch(
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                status="pending",
            )
            session.add(batch)
            session.commit()

            assert batch.id is not None
            assert batch.status == "pending"

    def test_weekly_batch_unique_constraint(self):
        """Test that app_id + week_start_date must be unique"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            batch1 = WeeklyBatch(
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                status="pending",
            )
            session.add(batch1)
            session.commit()

            batch2 = WeeklyBatch(
                app_id=app.id,
                week_start_date=date(2024, 1, 1),  # Same week
                week_end_date=date(2024, 1, 7),
                status="pending",
            )
            session.add(batch2)

            with pytest.raises(IntegrityError):
                session.commit()


class TestReviewModel:
    """Test Review model"""

    def test_create_review(self):
        """Test creating a review"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            review = Review(
                app_id=app.id,
                rating=5,
                title="Great app!",
                text="This is a great app.",
                review_date=date.today(),
                review_hash="abc123",
            )
            session.add(review)
            session.commit()

            assert review.id is not None
            assert review.rating == 5

    def test_review_rating_constraint(self):
        """Test that rating must be between 1 and 5"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            # SQLite enforces CHECK constraints, so this should fail
            review = Review(
                app_id=app.id,
                rating=6,  # Invalid rating
                title="Test",
                text="Test review",
                review_date=date.today(),
                review_hash="test123",
            )
            session.add(review)
            # Should raise IntegrityError due to CHECK constraint
            with pytest.raises(IntegrityError):
                session.commit()

    def test_review_unique_hash(self):
        """Test that review_hash must be unique"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            review1 = Review(
                app_id=app.id,
                rating=5,
                title="Test",
                text="Test review",
                review_date=date.today(),
                review_hash="duplicate_hash",
            )
            session.add(review1)
            session.commit()

            review2 = Review(
                app_id=app.id,
                rating=4,
                title="Test 2",
                text="Test review 2",
                review_date=date.today(),
                review_hash="duplicate_hash",  # Same hash
            )
            session.add(review2)

            with pytest.raises(IntegrityError):
                session.commit()


class TestThemeSummaryModel:
    """Test ThemeSummary model"""

    def test_create_theme_summary(self):
        """Test creating a theme summary with JSON fields"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            batch = WeeklyBatch(
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                status="processed",
            )
            session.add(batch)
            session.flush()

            theme = ThemeSummary(
                weekly_batch_id=batch.id,
                theme_name="Performance Issues",
                key_points=["Slow loading", "Crashes frequently"],
                candidate_quotes=["App is very slow", "Crashes all the time"],
            )
            session.add(theme)
            session.commit()

            assert theme.id is not None
            assert isinstance(theme.key_points, list)
            assert len(theme.key_points) == 2
            assert isinstance(theme.candidate_quotes, list)


class TestWeeklyPulseNoteModel:
    """Test WeeklyPulseNote model"""

    def test_create_weekly_pulse_note(self):
        """Test creating a weekly pulse note with JSON fields"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            batch = WeeklyBatch(
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                status="processed",
            )
            session.add(batch)
            session.flush()

            pulse = WeeklyPulseNote(
                weekly_batch_id=batch.id,
                title="Weekly Product Pulse",
                overview="This week's insights",
                themes=[{"name": "Theme 1", "summary": "Summary 1"}],
                quotes=["Quote 1", "Quote 2"],
                actions=["Action 1", "Action 2"],
                word_count=150,
            )
            session.add(pulse)
            session.commit()

            assert pulse.id is not None
            assert isinstance(pulse.themes, list)
            assert isinstance(pulse.quotes, list)
            assert isinstance(pulse.actions, list)
            assert pulse.word_count == 150

    def test_weekly_pulse_note_unique_batch(self):
        """Test that weekly_batch_id must be unique"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            batch = WeeklyBatch(
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                status="processed",
            )
            session.add(batch)
            session.flush()

            pulse1 = WeeklyPulseNote(
                weekly_batch_id=batch.id,
                title="Pulse 1",
                overview="Overview",
                themes=[],
                quotes=[],
                actions=[],
                word_count=100,
            )
            session.add(pulse1)
            session.commit()

            pulse2 = WeeklyPulseNote(
                weekly_batch_id=batch.id,  # Same batch
                title="Pulse 2",
                overview="Overview 2",
                themes=[],
                quotes=[],
                actions=[],
                word_count=100,
            )
            session.add(pulse2)

            with pytest.raises(IntegrityError):
                session.commit()


class TestRelationships:
    """Test model relationships"""

    def test_app_subscriptions_relationship(self):
        """Test App-Subscription relationship"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            sub1 = Subscription(
                app_id=app.id,
                email="user1@example.com",
                start_date=date.today(),
            )
            sub2 = Subscription(
                app_id=app.id,
                email="user2@example.com",
                start_date=date.today(),
            )
            session.add_all([sub1, sub2])
            session.commit()

            # Test relationship
            assert len(app.subscriptions) == 2
            assert app.subscriptions[0].email in ["user1@example.com", "user2@example.com"]

    def test_batch_reviews_relationship(self):
        """Test WeeklyBatch-Review relationship"""
        with get_test_db_session() as session:
            app = App(
                playstore_app_id="com.whatsapp",
                app_name="WhatsApp",
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
            )
            session.add(app)
            session.flush()

            batch = WeeklyBatch(
                app_id=app.id,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                status="processed",
            )
            session.add(batch)
            session.flush()

            review1 = Review(
                app_id=app.id,
                weekly_batch_id=batch.id,
                rating=5,
                title="Review 1",
                text="Text 1",
                review_date=date.today(),
                review_hash="hash1",
            )
            review2 = Review(
                app_id=app.id,
                weekly_batch_id=batch.id,
                rating=4,
                title="Review 2",
                text="Text 2",
                review_date=date.today(),
                review_hash="hash2",
            )
            session.add_all([review1, review2])
            session.commit()

            assert len(batch.reviews) == 2
            assert batch.reviews[0].rating in [4, 5]

