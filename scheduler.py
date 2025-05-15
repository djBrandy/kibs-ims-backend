import requests
import time
import schedule
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def send_notifications():
    """Send notifications for low stock and expiring products"""
    try:
        logger.info("Sending notifications...")
        response = requests.post('http://localhost:5000/api/alerts/send-notifications')
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully sent {data.get('notifications_sent', 0)} notifications")
        else:
            logger.error(f"Failed to send notifications: {response.status_code} - {response.text}")
    
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")

def run_scheduler():
    """Run the scheduler to send notifications every 6 hours"""
    logger.info("Starting notification scheduler...")
    
    # Schedule the notification job to run every 6 hours
    schedule.every(6).hours.do(send_notifications)
    
    # Also run once at startup
    send_notifications()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    run_scheduler()