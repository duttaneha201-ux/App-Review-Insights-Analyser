"""
Unit tests for Backup and Export Utilities

Tests cover:
- Export reviews to JSON/CSV
- Export weekly pulse notes to JSON/CSV
- Backup database
"""

import json
import csv
import tempfile
from pathlib import Path
from datetime import date

import pytest

from app.db.database import get_test_db_session
from app.db.repository import (
    AppRepository,
    WeeklyBatchRepository,
    ReviewRepository,
    WeeklyPulseNoteRepository,
)
from app.db.backup import (
    export_reviews_to_json,
    export_reviews_to_csv,
    export_pulse_notes_to_json,
    export_pulse_notes_to_csv,
)
from app.models.review import Review as ReviewDataClass


class TestExportReviews:
    """Test review export functions"""

    def test_export_reviews_to_json(self):
        """Test exporting reviews to JSON"""
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

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "reviews.json"
                count = export_reviews_to_json(session, output_path, app_id=app.id)
                
                assert count == 2
                assert output_path.exists()
                
                with open(output_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    assert len(data) == 2
                    assert data[0]["rating"] in [4, 5]

    def test_export_reviews_to_csv(self):
        """Test exporting reviews to CSV"""
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
            ]

            ReviewRepository.bulk_insert_with_deduplication(
                session,
                app_id=app.id,
                weekly_batch_id=None,
                reviews=reviews,
            )
            session.commit()

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "reviews.csv"
                count = export_reviews_to_csv(session, output_path, app_id=app.id)
                
                assert count == 1
                assert output_path.exists()
                
                with open(output_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 1
                    assert rows[0]["rating"] == "5"


class TestExportPulseNotes:
    """Test pulse note export functions"""

    def test_export_pulse_notes_to_json(self):
        """Test exporting pulse notes to JSON"""
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
                title="Test Pulse",
                overview="Overview",
                themes=[{"name": "Theme", "summary": "Summary"}],
                quotes=["Quote"],
                actions=["Action"],
                word_count=50,
            )
            session.commit()

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "pulses.json"
                count = export_pulse_notes_to_json(session, output_path, app_id=app.id)
                
                assert count == 1
                assert output_path.exists()
                
                with open(output_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    assert len(data) == 1
                    assert data[0]["title"] == "Test Pulse"
                    assert isinstance(data[0]["themes"], list)

    def test_export_pulse_notes_to_csv(self):
        """Test exporting pulse notes to CSV"""
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
                title="Test Pulse",
                overview="Overview",
                themes=[],
                quotes=[],
                actions=[],
                word_count=50,
            )
            session.commit()

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "pulses.csv"
                count = export_pulse_notes_to_csv(session, output_path, app_id=app.id)
                
                assert count == 1
                assert output_path.exists()
                
                with open(output_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 1
                    assert rows[0]["title"] == "Test Pulse"








