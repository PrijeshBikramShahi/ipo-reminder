from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging
import db
from notification_service import NotificationService

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """Scheduler for automated IPO notifications"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.notification_service = NotificationService()
    
    def start(self):
        """Start the scheduler"""
        # Check for IPO notifications every day at 8:00 AM Nepal Time (2:15 AM UTC)
        self.scheduler.add_job(
            self.send_daily_notifications,
            CronTrigger(hour=2, minute=15),  # 8:00 AM NPT
            id='daily_ipo_check',
            name='Daily IPO Notification Check',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Notification scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Notification scheduler stopped")
    
    def send_daily_notifications(self):
        """Check IPOs and send notifications"""
        logger.info("Running daily IPO notification check...")
        
        try:
            # Get all active FCM tokens
            tokens = db.get_all_active_tokens()
            
            if not tokens:
                logger.warning("No active FCM tokens found")
                return
            
            # Get upcoming IPOs
            ipos = db.get_upcoming_ipos()
            
            if not ipos:
                logger.info("No upcoming IPOs found")
                return
            
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            notifications_sent = 0
            
            for ipo in ipos:
                start_date = datetime.fromisoformat(ipo['startDate']).date()
                
                # IPO opens today
                if start_date == today:
                    logger.info(f"Sending opening notifications for {ipo['company']}")
                    for token in tokens:
                        success = self.notification_service.send_ipo_opening_notification(token, ipo)
                        if success:
                            notifications_sent += 1
                
                # IPO opens tomorrow
                elif start_date == tomorrow:
                    logger.info(f"Sending reminder for {ipo['company']}")
                    for token in tokens:
                        success = self.notification_service.send_ipo_reminder_notification(token, ipo, 1)
                        if success:
                            notifications_sent += 1
            
            logger.info(f"Sent {notifications_sent} notifications successfully")
            
        except Exception as e:
            logger.error(f"Error in daily notification check: {e}", exc_info=True)
    
    def send_test_notification(self, token: str):
        """Send a test notification"""
        test_ipo = {
            'company': 'Test Company Limited',
            'startDate': datetime.now().isoformat()[:10],
            'endDate': (datetime.now() + timedelta(days=5)).isoformat()[:10]
        }
        
        return self.notification_service.send_ipo_opening_notification(token, test_ipo)