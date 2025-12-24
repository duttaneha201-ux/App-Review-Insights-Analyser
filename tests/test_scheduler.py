"""
Unit tests for scheduler module

Tests:
- Timezone conversion (IST to UTC)
- Immediate job triggering
- Weekly job scheduling
- Idempotency checks
- Failure handling
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytz

from app.scheduler.timezone_utils import (
    get_ist_now,
    get_utc_now,
    ist_to_utc,
    utc_to_ist,
    get_next_monday_8am_ist,
    get_week_start_date,
    get_week_end_date,
)
from app.scheduler.config import SchedulerConfig
from app.scheduler.jobs import trigger_immediate_analysis, run_weekly_job
from app.scheduler.scheduler import SchedulerManager


class TestTimezoneUtils:
    """Test timezone conversion utilities"""
    
    def test_ist_to_utc_conversion(self):
        """Test IST to UTC conversion"""
        # IST is UTC+5:30
        ist_time = datetime(2024, 1, 15, 8, 0, 0)  # 8 AM IST
        ist_time = pytz.timezone('Asia/Kolkata').localize(ist_time)
        
        utc_time = ist_to_utc(ist_time)
        
        # 8 AM IST = 2:30 AM UTC
        assert utc_time.hour == 2
        assert utc_time.minute == 30
        assert utc_time.tzinfo == pytz.UTC
    
    def test_utc_to_ist_conversion(self):
        """Test UTC to IST conversion"""
        utc_time = datetime(2024, 1, 15, 2, 30, 0)  # 2:30 AM UTC
        utc_time = pytz.UTC.localize(utc_time)
        
        ist_time = utc_to_ist(utc_time)
        
        # 2:30 AM UTC = 8:00 AM IST
        assert ist_time.hour == 8
        assert ist_time.minute == 0
        assert ist_time.tzinfo == pytz.timezone('Asia/Kolkata')
    
    def test_get_next_monday_8am_ist(self):
        """Test getting next Monday 8 AM IST"""
        # Mock current time to be a Wednesday
        mock_now = datetime(2024, 1, 17, 10, 0, 0)  # Wednesday 10 AM
        mock_now = pytz.timezone('Asia/Kolkata').localize(mock_now)
        
        with patch('app.scheduler.timezone_utils.get_ist_now', return_value=mock_now):
            next_monday = get_next_monday_8am_ist()
            
            # Should be next Monday (Jan 22) at 8 AM IST
            assert next_monday.weekday() == 0  # Monday
            assert next_monday.hour == 8
            assert next_monday.minute == 0
    
    def test_get_next_monday_8am_ist_same_day(self):
        """Test getting Monday 8 AM when it's Monday before 8 AM"""
        # Mock current time to be Monday 7 AM
        mock_now = datetime(2024, 1, 15, 7, 0, 0)  # Monday 7 AM
        mock_now = pytz.timezone('Asia/Kolkata').localize(mock_now)
        
        with patch('app.scheduler.timezone_utils.get_ist_now', return_value=mock_now):
            next_monday = get_next_monday_8am_ist()
            
            # Should be today at 8 AM IST
            assert next_monday.date() == mock_now.date()
            assert next_monday.hour == 8
            assert next_monday.minute == 0
    
    def test_get_week_start_date(self):
        """Test getting week start (Monday)"""
        # Wednesday
        test_date = date(2024, 1, 17)
        week_start = get_week_start_date(test_date)
        
        # Should be Monday (Jan 15)
        assert week_start.weekday() == 0
        assert week_start == date(2024, 1, 15)
    
    def test_get_week_end_date(self):
        """Test getting week end (Sunday)"""
        # Wednesday
        test_date = date(2024, 1, 17)
        week_end = get_week_end_date(test_date)
        
        # Should be Sunday (Jan 21)
        assert week_end.weekday() == 6
        assert week_end == date(2024, 1, 21)


class TestSchedulerConfig:
    """Test scheduler configuration"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        assert SchedulerConfig.WEEKLY_JOB_DAY == 0  # Monday
        assert SchedulerConfig.WEEKLY_JOB_HOUR == 8  # 8 AM
        assert SchedulerConfig.WEEKLY_JOB_MINUTE == 0
    
    def test_get_weekly_cron_time(self):
        """Test getting weekly cron configuration"""
        cron_config = SchedulerConfig.get_weekly_cron_time()
        
        assert 'day_of_week' in cron_config
        assert 'hour' in cron_config
        assert 'minute' in cron_config
        assert cron_config['day_of_week'] == 0


class TestImmediateAnalysisJob:
    """Test immediate analysis job"""
    
    @patch('app.scheduler.jobs.get_db_session')
    @patch('app.scheduler.jobs._process_weekly_batch')
    def test_trigger_immediate_analysis_success(self, mock_process, mock_db_session):
        """Test successful immediate analysis"""
        # Mock database session
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        
        # Mock subscription
        mock_subscription = Mock()
        mock_subscription.id = 1
        mock_subscription.app_id = 1
        mock_subscription.email = "test@example.com"
        mock_subscription.is_active = True
        
        # Mock app
        mock_app = Mock()
        mock_app.id = 1
        mock_app.app_url = "https://play.google.com/store/apps/details?id=com.test"
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_subscription
        
        # Mock AppRepository
        with patch('app.scheduler.jobs.AppRepository.get_by_id', return_value=mock_app):
            # Mock timezone utils
            with patch('app.scheduler.jobs.get_ist_now') as mock_now:
                mock_now.return_value.date.return_value = date(2024, 1, 17)  # Wednesday
                
                # Mock process result
                mock_process.return_value = {
                    'success': True,
                    'execution_time': 10.5,
                }
                
                result = trigger_immediate_analysis(1)
                
                assert result['success'] is True
                mock_process.assert_called_once()
    
    @patch('app.scheduler.jobs.get_db_session')
    def test_trigger_immediate_analysis_subscription_not_found(self, mock_db_session):
        """Test immediate analysis with non-existent subscription"""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = trigger_immediate_analysis(999)
        
        assert result['success'] is False
        assert 'error' in result


class TestWeeklyJob:
    """Test weekly recurring job"""
    
    @patch('app.scheduler.jobs.get_db_session')
    @patch('app.scheduler.jobs.SubscriptionRepository.get_active_subscriptions')
    @patch('app.scheduler.jobs._process_weekly_batch')
    def test_run_weekly_job_success(self, mock_process, mock_get_subs, mock_db_session):
        """Test successful weekly job execution"""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        
        # Mock subscriptions
        mock_subscription = Mock()
        mock_subscription.id = 1
        mock_subscription.app_id = 1
        mock_subscription.email = "test@example.com"
        mock_get_subs.return_value = [mock_subscription]
        
        # Mock app
        mock_app = Mock()
        mock_app.id = 1
        mock_app.app_url = "https://play.google.com/store/apps/details?id=com.test"
        
        with patch('app.scheduler.jobs.AppRepository.get_by_id', return_value=mock_app):
            with patch('app.scheduler.jobs.get_ist_now') as mock_now:
                mock_now.return_value.date.return_value = date(2024, 1, 17)  # Wednesday
                
                mock_process.return_value = {
                    'success': True,
                    'execution_time': 15.0,
                }
                
                result = run_weekly_job()
                
                assert result['success'] is True
                assert result['processed_count'] == 1
                assert result['error_count'] == 0
    
    @patch('app.scheduler.jobs.get_db_session')
    @patch('app.scheduler.jobs.SubscriptionRepository.get_active_subscriptions')
    def test_run_weekly_job_no_subscriptions(self, mock_get_subs, mock_db_session):
        """Test weekly job with no active subscriptions"""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_get_subs.return_value = []
        
        result = run_weekly_job()
        
        assert result['success'] is True
        assert result['processed_count'] == 0


class TestSchedulerManager:
    """Test scheduler manager"""
    
    def test_scheduler_manager_initialization(self):
        """Test scheduler manager initialization"""
        manager = SchedulerManager()
        assert manager.scheduler is None
        assert manager._initialized is False
    
    @patch('app.scheduler.scheduler.SchedulerConfig.is_enabled', return_value=False)
    def test_scheduler_manager_disabled(self, mock_enabled):
        """Test scheduler manager when disabled"""
        manager = SchedulerManager()
        result = manager.initialize()
        
        assert result is False
        assert manager.scheduler is None
    
    @patch('app.scheduler.scheduler.SchedulerConfig.is_enabled', return_value=True)
    @patch('app.scheduler.scheduler.BackgroundScheduler')
    @patch('app.scheduler.scheduler.SQLAlchemyJobStore')
    @patch('os.makedirs')
    def test_scheduler_manager_initialize(self, mock_makedirs, mock_store, mock_scheduler_class, mock_enabled):
        """Test scheduler manager initialization"""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        manager = SchedulerManager()
        result = manager.initialize()
        
        assert result is True
        assert manager._initialized is True
        mock_scheduler_class.assert_called_once()
    
    def test_add_immediate_job_not_running(self):
        """Test adding immediate job when scheduler not running"""
        manager = SchedulerManager()
        result = manager.add_immediate_job(1)
        
        assert result is False


class TestIdempotency:
    """Test idempotency checks"""
    
    @patch('app.scheduler.jobs.get_db_session')
    @patch('app.scheduler.jobs.WeeklyBatchRepository.get_by_app_and_week')
    @patch('app.scheduler.jobs.WeeklyPulseNoteRepository.get_by_week')
    def test_process_weekly_batch_already_processed(self, mock_get_pulse, mock_get_batch, mock_db_session):
        """Test that already processed batches are skipped"""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        
        # Mock existing processed batch
        mock_batch = Mock()
        mock_batch.id = 1
        mock_batch.status = 'processed'
        mock_get_batch.return_value = mock_batch
        
        # Mock pulse note exists
        mock_pulse = Mock()
        mock_get_pulse.return_value = mock_pulse
        
        from app.scheduler.jobs import _process_weekly_batch
        
        result = _process_weekly_batch(
            subscription_id=1,
            app_id=1,
            week_start=date(2024, 1, 15),
            week_end=date(2024, 1, 21),
            app_url="https://play.google.com/store/apps/details?id=com.test",
            email="test@example.com",
        )
        
        assert result['success'] is True
        assert result['skipped'] is True
        assert result['message'] == 'Batch already processed'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



