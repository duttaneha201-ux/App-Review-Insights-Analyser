"""
Backup and Export Utilities for App Review Insights Analyzer

Provides functions to:
- Export reviews to JSON/CSV
- Export weekly pulse notes to JSON/CSV
- Backup full SQLite database
"""

import json
import csv
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.models import Review, WeeklyPulseNote, App, WeeklyBatch
from app.db.database import DB_URL


def export_reviews_to_json(
    session: Session,
    output_path: Path,
    app_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> int:
    """
    Export reviews to JSON file.
    
    Args:
        session: Database session
        output_path: Output file path
        app_id: Optional app ID filter
        start_date: Optional start date filter (ISO format)
        end_date: Optional end date filter (ISO format)
        
    Returns:
        Number of reviews exported
    """
    from datetime import date as date_type
    
    query = session.query(Review)
    
    if app_id:
        query = query.filter(Review.app_id == app_id)
    
    if start_date:
        start = date_type.fromisoformat(start_date)
        query = query.filter(Review.review_date >= start)
    
    if end_date:
        end = date_type.fromisoformat(end_date)
        query = query.filter(Review.review_date <= end)
    
    reviews = query.order_by(Review.review_date.desc()).all()
    
    data = []
    for review in reviews:
        data.append({
            "id": review.id,
            "app_id": review.app_id,
            "weekly_batch_id": review.weekly_batch_id,
            "rating": review.rating,
            "title": review.title,
            "text": review.text,
            "review_date": review.review_date.isoformat(),
            "created_at": review.created_at.isoformat(),
        })
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return len(data)


def export_reviews_to_csv(
    session: Session,
    output_path: Path,
    app_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> int:
    """
    Export reviews to CSV file.
    
    Args:
        session: Database session
        output_path: Output file path
        app_id: Optional app ID filter
        start_date: Optional start date filter (ISO format)
        end_date: Optional end date filter (ISO format)
        
    Returns:
        Number of reviews exported
    """
    from datetime import date as date_type
    
    query = session.query(Review)
    
    if app_id:
        query = query.filter(Review.app_id == app_id)
    
    if start_date:
        start = date_type.fromisoformat(start_date)
        query = query.filter(Review.review_date >= start)
    
    if end_date:
        end = date_type.fromisoformat(end_date)
        query = query.filter(Review.review_date <= end)
    
    reviews = query.order_by(Review.review_date.desc()).all()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "app_id",
                "weekly_batch_id",
                "rating",
                "title",
                "text",
                "review_date",
                "created_at",
            ],
        )
        writer.writeheader()
        
        for review in reviews:
            writer.writerow({
                "id": review.id,
                "app_id": review.app_id,
                "weekly_batch_id": review.weekly_batch_id,
                "rating": review.rating,
                "title": review.title or "",
                "text": review.text,
                "review_date": review.review_date.isoformat(),
                "created_at": review.created_at.isoformat(),
            })
    
    return len(reviews)


def export_pulse_notes_to_json(
    session: Session,
    output_path: Path,
    app_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> int:
    """
    Export weekly pulse notes to JSON file.
    
    Args:
        session: Database session
        output_path: Output file path
        app_id: Optional app ID filter
        limit: Optional limit on number of notes
        
    Returns:
        Number of pulse notes exported
    """
    query = session.query(WeeklyPulseNote).join(WeeklyBatch)
    
    if app_id:
        query = query.filter(WeeklyBatch.app_id == app_id)
    
    query = query.order_by(WeeklyPulseNote.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    pulse_notes = query.all()
    
    data = []
    for note in pulse_notes:
        data.append({
            "id": note.id,
            "weekly_batch_id": note.weekly_batch_id,
            "title": note.title,
            "overview": note.overview,
            "themes": note.themes,
            "quotes": note.quotes,
            "actions": note.actions,
            "word_count": note.word_count,
            "created_at": note.created_at.isoformat(),
        })
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return len(data)


def export_pulse_notes_to_csv(
    session: Session,
    output_path: Path,
    app_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> int:
    """
    Export weekly pulse notes to CSV file.
    
    Note: JSON fields (themes, quotes, actions) are serialized as JSON strings.
    
    Args:
        session: Database session
        output_path: Output file path
        app_id: Optional app ID filter
        limit: Optional limit on number of notes
        
    Returns:
        Number of pulse notes exported
    """
    query = session.query(WeeklyPulseNote).join(WeeklyBatch)
    
    if app_id:
        query = query.filter(WeeklyBatch.app_id == app_id)
    
    query = query.order_by(WeeklyPulseNote.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    pulse_notes = query.all()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "weekly_batch_id",
                "title",
                "overview",
                "themes",
                "quotes",
                "actions",
                "word_count",
                "created_at",
            ],
        )
        writer.writeheader()
        
        for note in pulse_notes:
            writer.writerow({
                "id": note.id,
                "weekly_batch_id": note.weekly_batch_id,
                "title": note.title,
                "overview": note.overview,
                "themes": json.dumps(note.themes),
                "quotes": json.dumps(note.quotes),
                "actions": json.dumps(note.actions),
                "word_count": note.word_count,
                "created_at": note.created_at.isoformat(),
            })
    
    return len(pulse_notes)


def backup_database(backup_dir: Path = Path("backups")) -> Path:
    """
    Backup full SQLite database with timestamped filename.
    
    Args:
        backup_dir: Directory to store backup
        
    Returns:
        Path to backup file
    """
    # Extract database path from DB_URL
    # DB_URL format: sqlite:///path/to/db.db
    db_path_str = DB_URL.replace("sqlite:///", "")
    db_path = Path(db_path_str)
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    # Create backup directory
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"reviews_backup_{timestamp}.db"
    backup_path = backup_dir / backup_filename
    
    # Copy database file
    shutil.copy2(db_path, backup_path)
    
    return backup_path








