import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional, Dict
from config import settings
import os
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Handle email sending for disputes and notifications"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST") or "smtp.gmail.com"
        smtp_port_str = os.getenv("SMTP_PORT") or "587"
        self.smtp_port = int(smtp_port_str) if smtp_port_str else 587
        self.smtp_user = os.getenv("SMTP_USER") or ""
        self.smtp_password = os.getenv("SMTP_PASSWORD") or ""
        self.from_email = os.getenv("FROM_EMAIL") or "noreply@creditrepairpro.com"
        self.from_name = os.getenv("FROM_NAME") or "CreditRepair Pro"
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   html_body: str = None, attachments: List[str] = None) -> bool:
        """Send a generic email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            attachment = MIMEApplication(f.read())
                            attachment.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=os.path.basename(file_path)
                            )
                            msg.attach(attachment)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Email send failed: {str(e)}")
            return False
    
    def send_welcome(self, to_email: str, client_name: str) -> bool:
        """Send welcome email"""
        subject = "Welcome to CreditRepair Pro!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9fafb; padding: 30px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                .btn {{ background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to CreditRepair Pro!</h1>
                </div>
                <div class="content">
                    <h2>Hi {client_name},</h2>
                    <p>Thank you for choosing CreditRepair Pro! We're excited to help you on your journey to better credit.</p>
                    
                    <h3>Next Steps:</h3>
                    <ul>
                        <li>Complete your profile</li>
                        <li>Upload your credit reports</li>
                        <li>Review our error analysis</li>
                        <li>Approve your dispute letters</li>
                    </ul>
                    
                    <p>If you have any questions, reply to this email or contact us at {os.getenv('COMPANY_PHONE', '(305) 747-3973')}.</p>
                    
                    <p><a href="{os.getenv('COMPANY_URL', '')}/client/dashboard" class="btn">Go to Dashboard</a></p>
                </div>
                <div class="footer">
                    <p>© 2025 CreditRepair Pro. All rights reserved.</p>
                    <p>{os.getenv('COMPANY_ADDRESS', 'Miami, FL')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""Welcome to CreditRepair Pro!

Hi {client_name},

Thank you for choosing CreditRepair Pro! We're excited to help you on your journey to better credit.

Next Steps:
1. Complete your profile
2. Upload your credit reports
3. Review our error analysis
4. Approve your dispute letters

If you have any questions, contact us at {os.getenv('COMPANY_PHONE', '(305) 747-3973')}.

Best regards,
CreditRepair Pro Team
"""
        
        return self.send_email(to_email, subject, plain_body, html_body)
    
    def send_analysis_complete(self, to_email: str, client_name: str, 
                               error_count: int, dispute_count: int) -> bool:
        """Send analysis completion email"""
        subject = "Your Credit Report Analysis is Complete"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #059669; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9fafb; padding: 30px; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; }}
                .stat-number {{ font-size: 36px; font-weight: bold; color: #dc2626; }}
                .btn {{ background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Analysis Complete! 🎉</h1>
                </div>
                <div class="content">
                    <p>Hi {client_name},</p>
                    <p>We've completed the analysis of your credit report. Here's what we found:</p>
                    
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-number">{error_count}</div>
                            <div>Errors Found</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">{dispute_count}</div>
                            <div>Disputes Recommended</div>
                        </div>
                    </div>
                    
                    <p>Log in to your dashboard to review the detailed analysis and approve your dispute letters.</p>
                    
                    <a href="{os.getenv('COMPANY_URL', '')}/client/dashboard" class="btn">View Analysis</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""Analysis Complete!

Hi {client_name},

We've completed the analysis of your credit report.

Results:
- Errors Found: {error_count}
- Disputes Recommended: {dispute_count}

Log in to your dashboard to review the detailed analysis.

{os.getenv('COMPANY_URL', '')}/client/dashboard
"""
        
        return self.send_email(to_email, subject, plain_body, html_body)
    
    def send_letters_ready(self, to_email: str, client_name: str, letter_count: int) -> bool:
        """Send letters ready notification"""
        subject = "Your Dispute Letters Are Ready"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Your Dispute Letters Are Ready, {client_name}!</h2>
            
            <p>We've generated {letter_count} customized dispute letters for you.</p>
            
            <p><strong>Important:</strong> Send these letters via certified mail with return receipt requested.</p>
            
            <p><a href="{os.getenv('COMPANY_URL', '')}/client/letters" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Download Letters</a></p>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, "Your dispute letters are ready. Download them from your dashboard.", html_body)
    
    def send_follow_up_reminder(self, to_email: str, client_name: str, 
                                 bureau: str, days_overdue: int) -> bool:
        """Send follow-up reminder"""
        subject = f"Action Required: {bureau.title()} Dispute Follow-Up"
        
        body = f"""Hi {client_name},

This is a reminder that {bureau.title()} has not responded to your dispute sent {days_overdue} days ago.

Under the Fair Credit Reporting Act, credit bureaus must respond within 30 days.

Recommended Actions:
1. Send a follow-up letter
2. Document the violation
3. Consider filing a CFPB complaint

Log in to your dashboard for the follow-up letter template.

Best regards,
CreditRepair Pro Team
"""
        return self.send_email(to_email, subject, body)
    
    def send_payment_receipt(self, to_email: str, client_name: str, 
                             amount: float, description: str) -> bool:
        """Send payment receipt"""
        subject = "Payment Receipt - CreditRepair Pro"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Payment Receipt</h2>
            
            <p>Hi {client_name},</p>
            
            <p>Thank you for your payment!</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Description:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{description}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Amount:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">${amount:.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Date:</strong></td>
                    <td style="padding: 10px;">{datetime.utcnow().strftime('%B %d, %Y')}</td>
                </tr>
            </table>
            
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, f"Payment of ${amount:.2f} received. Thank you!", html_body)
    
    def send_password_reset(self, to_email: str, reset_link: str) -> bool:
        """Send password reset email"""
        subject = "Password Reset Request"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Password Reset</h2>
            
            <p>You requested a password reset. Click the link below to reset your password:</p>
            
            <p><a href="{reset_link}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
            
            <p style="color: #666; font-size: 12px;">This link expires in 1 hour. If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, f"Reset your password: {reset_link}", html_body)