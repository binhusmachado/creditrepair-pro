from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from models import Dispute, User, Notification, Client
from services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Automated notification and reminder system"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    def run_daily_checks(self) -> Dict:
        """Run all daily notification checks"""
        results = {
            "follow_up_reminders": [],
            "deadline_violations": [],
            "monthly_reports": []
        }
        
        # Check for follow-ups needed
        results["follow_up_reminders"] = self.check_follow_up_reminders()
        
        # Check for deadline violations
        results["deadline_violations"] = self.check_deadline_violations()
        
        # Send monthly progress reports
        results["monthly_reports"] = self.send_monthly_reports()
        
        return results
    
    def check_follow_up_reminders(self) -> List[Dict]:
        """Check for disputes needing follow-up (25+ days since sent)"""
        cutoff_date = datetime.utcnow() - timedelta(days=25)
        
        disputes = self.db.query(Dispute).filter(
            Dispute.status == "sent",
            Dispute.sent_date <= cutoff_date,
            Dispute.follow_up_date.is_(None)
        ).all()
        
        reminders = []
        for dispute in disputes:
            client = self.db.query(Client).get(dispute.client_id)
            user = self.db.query(User).filter_by(client_id=client.id).first()
            
            if user and client:
                days_sent = (datetime.utcnow() - dispute.sent_date).days
                
                # Send reminder
                self.email_service.send_follow_up_reminder(
                    user.email,
                    client.full_name,
                    dispute.bureau,
                    days_sent
                )
                
                # Update follow-up date
                dispute.follow_up_date = datetime.utcnow()
                
                # Create notification
                self.create_notification(
                    user.id,
                    "Follow-Up Reminder",
                    f"Your {dispute.bureau.title()} dispute from {days_sent} days ago needs follow-up.",
                    "dispute_update"
                )
                
                reminders.append({
                    "dispute_id": dispute.id,
                    "client": client.full_name,
                    "bureau": dispute.bureau,
                    "days_sent": days_sent
                })
        
        self.db.commit()
        logger.info(f"Sent {len(reminders)} follow-up reminders")
        return reminders
    
    def check_deadline_violations(self) -> List[Dict]:
        """Check for disputes past the 30-day response deadline"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        disputes = self.db.query(Dispute).filter(
            Dispute.status == "sent",
            Dispute.sent_date <= cutoff_date,
            Dispute.response_type.is_(None)
        ).all()
        
        violations = []
        for dispute in disputes:
            client = self.db.query(Client).get(dispute.client_id)
            user = self.db.query(User).filter_by(client_id=client.id).first()
            
            if user:
                days_overdue = (datetime.utcnow() - dispute.sent_date).days - 30
                
                # Create notification
                self.create_notification(
                    user.id,
                    "Response Deadline Violation",
                    f"{dispute.bureau.title()} has not responded to your dispute ({days_overdue} days overdue). Consider filing a CFPB complaint.",
                    "dispute_update"
                )
                
                violations.append({
                    "dispute_id": dispute.id,
                    "client": client.full_name,
                    "bureau": dispute.bureau,
                    "days_overdue": days_overdue
                })
        
        logger.info(f"Found {len(violations)} deadline violations")
        return violations
    
    def send_monthly_reports(self) -> List[Dict]:
        """Send monthly progress reports to active clients"""
        # Get active subscriptions
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        
        active_clients = self.db.query(Client).join(User).filter(
            User.is_active == True
        ).all()
        
        reports = []
        for client in active_clients:
            user = self.db.query(User).filter_by(client_id=client.id).first()
            if not user:
                continue
            
            # Get last month's disputes
            monthly_disputes = self.db.query(Dispute).filter(
                Dispute.client_id == client.id,
                Dispute.created_date >= one_month_ago
            ).all()
            
            if monthly_disputes:
                # Count outcomes
                deleted = sum(1 for d in monthly_disputes if d.response_type == "deleted")
                updated = sum(1 for d in monthly_disputes if d.response_type == "updated")
                verified = sum(1 for d in monthly_disputes if d.response_type == "verified")
                pending = sum(1 for d in monthly_disputes if d.status == "sent")
                
                # Send monthly report email
                subject = "Your Monthly Credit Repair Progress Report"
                
                html_body = f"""
                <!DOCTYPE html>
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Monthly Progress Report</h2>
                    
                    <p>Hi {client.full_name},</p>
                    
                    <p>Here's your credit repair progress for the past month:</p>
                    
                    <ul>
                        <li>✅ Items Deleted: {deleted}</li>
                        <li>📝 Items Updated: {updated}</li>
                        <li>🔍 Items Verified: {verified}</li>
                        <li>⏳ Pending: {pending}</li>
                    </ul>
                    
                    <p>Keep up the great work! Log in to see your full progress.</p>
                </body>
                </html>
                """
                
                self.email_service.send_email(
                    user.email,
                    subject,
                    f"Monthly progress: {deleted} deleted, {updated} updated, {verified} verified, {pending} pending",
                    html_body
                )
                
                reports.append({
                    "client_id": client.id,
                    "name": client.full_name,
                    "disputes_sent": len(monthly_disputes)
                })
        
        logger.info(f"Sent {len(reports)} monthly reports")
        return reports
    
    def create_notification(self, user_id: int, title: str, message: str, 
                           notification_type: str, link: str = None) -> Notification:
        """Create a notification for a user"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
        
        self.db.add(notification)
        self.db.commit()
        
        return notification
    
    def get_unread_notifications(self, user_id: int) -> List[Notification]:
        """Get unread notifications for a user"""
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).order_by(Notification.created_at.desc()).all()
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark a notification as read"""
        notification = self.db.query(Notification).get(notification_id)
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.db.commit()
            return True
        return False