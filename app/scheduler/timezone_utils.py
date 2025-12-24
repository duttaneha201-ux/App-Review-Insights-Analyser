"""
Timezone utilities for scheduler

Handles conversion between IST (Asia/Kolkata) and UTC for scheduling.
IST is the source of truth for business logic (Monday 8 AM IST).
"""

from datetime import datetime, time, timedelta, date
from typing import Optional
import pytz

# IST timezone (Asia/Kolkata)
IST = pytz.timezone('Asia/Kolkata')
UTC = pytz.UTC


def get_ist_now() -> datetime:
    """
    Get current time in IST timezone.
    
    Returns:
        datetime object with IST timezone
    """
    return datetime.now(IST)


def get_utc_now() -> datetime:
    """
    Get current time in UTC timezone.
    
    Returns:
        datetime object with UTC timezone
    """
    return datetime.now(UTC)


def ist_to_utc(ist_datetime: datetime) -> datetime:
    """
    Convert IST datetime to UTC.
    
    Args:
        ist_datetime: datetime object (assumed to be in IST if naive)
        
    Returns:
        datetime object in UTC timezone
    """
    if ist_datetime.tzinfo is None:
        # Assume naive datetime is in IST
        ist_datetime = IST.localize(ist_datetime)
    elif ist_datetime.tzinfo != IST:
        # Convert to IST first
        ist_datetime = ist_datetime.astimezone(IST)
    
    return ist_datetime.astimezone(UTC)


def utc_to_ist(utc_datetime: datetime) -> datetime:
    """
    Convert UTC datetime to IST.
    
    Args:
        utc_datetime: datetime object (assumed to be in UTC if naive)
        
    Returns:
        datetime object in IST timezone
    """
    if utc_datetime.tzinfo is None:
        # Assume naive datetime is in UTC
        utc_datetime = UTC.localize(utc_datetime)
    elif utc_datetime.tzinfo != UTC:
        # Convert to UTC first
        utc_datetime = utc_datetime.astimezone(UTC)
    
    return utc_datetime.astimezone(IST)


def get_next_monday_8am_ist() -> datetime:
    """
    Get the next Monday at 8:00 AM IST.
    
    Returns:
        datetime object for next Monday 8 AM IST
    """
    now_ist = get_ist_now()
    
    # Calculate days until next Monday
    days_until_monday = (7 - now_ist.weekday()) % 7
    if days_until_monday == 0:
        # Today is Monday, check if it's before 8 AM
        if now_ist.time() < time(8, 0):
            # Today at 8 AM
            next_monday = now_ist.replace(hour=8, minute=0, second=0, microsecond=0)
        else:
            # Next Monday at 8 AM
            next_monday = now_ist + timedelta(days=7)
            next_monday = next_monday.replace(hour=8, minute=0, second=0, microsecond=0)
    else:
        # Next Monday at 8 AM
        next_monday = now_ist + timedelta(days=days_until_monday)
        next_monday = next_monday.replace(hour=8, minute=0, second=0, microsecond=0)
    
    return next_monday


def get_monday_8am_ist_for_week(week_start_date) -> datetime:
    """
    Get Monday 8 AM IST for a specific week.
    
    Args:
        week_start_date: date object representing the start of the week
        
    Returns:
        datetime object for Monday 8 AM IST of that week
    """
    # Ensure week_start_date is a Monday
    if week_start_date.weekday() != 0:
        # Adjust to Monday
        days_to_monday = week_start_date.weekday()
        week_start_date = week_start_date - timedelta(days=days_to_monday)
    
    # Create datetime at 8 AM IST
    monday_8am = IST.localize(
        datetime.combine(week_start_date, time(8, 0))
    )
    
    return monday_8am


def get_week_start_date(reference_date: Optional[date] = None) -> date:
    """
    Get the Monday (week start) for a given date.
    
    Args:
        reference_date: date object (defaults to today in IST)
        
    Returns:
        date object for Monday of that week
    """
    if reference_date is None:
        reference_date = get_ist_now().date()
    
    # Calculate days to subtract to get to Monday
    days_to_monday = reference_date.weekday()
    monday = reference_date - timedelta(days=days_to_monday)
    
    return monday


def get_week_end_date(reference_date: Optional[date] = None) -> date:
    """
    Get the Sunday (week end) for a given date.
    
    Args:
        reference_date: date object (defaults to today in IST)
        
    Returns:
        date object for Sunday of that week
    """
    week_start = get_week_start_date(reference_date)
    week_end = week_start + timedelta(days=6)
    return week_end

