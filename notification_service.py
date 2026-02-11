import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
from typing import List, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending FCM notifications"""
    
    def __init__(self, credentials_path: str = "firebase-credentials.json"):
        """
        Initialize Firebase Admin SDK
        
        Args:
            credentials_path: Path to Firebase service account JSON file
        """
        self.initialized = False
        
        if os.path.exists(credentials_path):
            try:
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)
                self.initialized = True
                logger.info("Firebase Admin SDK initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")
        else:
            logger.warning(f"Firebase credentials not found at {credentials_path}")
    
    def send_ipo_opening_notification(self, token: str, ipo: Dict) -> bool:
        """
        Send notification for IPO opening today
        
        Args:
            token: FCM device token
            ipo: IPO dictionary with company, startDate, endDate
        
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            logger.error("Firebase not initialized")
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title='🔔 IPO Opening Today!',
                    body=f"{ipo['company']} IPO opens today until {ipo['endDate']}"
                ),
                data={
                    'type': 'ipo_opening',
                    'company': ipo['company'],
                    'startDate': ipo['startDate'],
                    'endDate': ipo['endDate'],
                    'timestamp': datetime.now().isoformat()
                },
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='ic_notification',
                        color='#4CAF50',
                        sound='default'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent notification: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def send_ipo_reminder_notification(self, token: str, ipo: Dict, days_until: int) -> bool:
        """
        Send reminder notification for upcoming IPO
        
        Args:
            token: FCM device token
            ipo: IPO dictionary
            days_until: Number of days until IPO opens
        
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            return False
        
        try:
            day_text = "tomorrow" if days_until == 1 else f"in {days_until} days"
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title='📅 Upcoming IPO Reminder',
                    body=f"{ipo['company']} IPO opens {day_text}"
                ),
                data={
                    'type': 'ipo_reminder',
                    'company': ipo['company'],
                    'startDate': ipo['startDate'],
                    'endDate': ipo['endDate'],
                    'daysUntil': str(days_until),
                    'timestamp': datetime.now().isoformat()
                },
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='ic_notification',
                        color='#2196F3',
                        sound='default'
                    )
                )
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent reminder: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
            return False
    
    def send_bulk_notification(self, tokens: List[str], title: str, body: str, 
                              data: Dict = None) -> Dict:
        """
        Send notification to multiple devices
        
        Args:
            tokens: List of FCM tokens
            title: Notification title
            body: Notification body
            data: Optional data payload
        
        Returns:
            Dictionary with success/failure counts
        """
        if not self.initialized or not tokens:
            return {'success': 0, 'failure': 0}
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_multicast(message)
            
            logger.info(f"Sent {response.success_count} notifications successfully")
            if response.failure_count > 0:
                logger.warning(f"Failed to send {response.failure_count} notifications")
            
            return {
                'success': response.success_count,
                'failure': response.failure_count
            }
            
        except Exception as e:
            logger.error(f"Bulk notification failed: {e}")
            return {'success': 0, 'failure': len(tokens)}