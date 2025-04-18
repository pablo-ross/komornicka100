import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from ..core.config import settings


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    cc_emails: Optional[List[str]] = None,
    bcc_emails: Optional[List[str]] = None,
) -> bool:
    """
    Send an email using the configured SMTP server.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content of the email
        cc_emails: Optional list of CC email addresses
        bcc_emails: Optional list of BCC email addresses
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Create message container
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USERNAME
    msg["To"] = to_email
    
    # Add CC recipients if provided
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)
        
    # Set recipients list for sending
    recipients = [to_email]
    if cc_emails:
        recipients.extend(cc_emails)
    if bcc_emails:
        recipients.extend(bcc_emails)
        
    # Attach HTML part
    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)
    
    # Create secure SSL context
    context = ssl.create_default_context()
    
    try:
        # Connect to server and send email
        if settings.SMTP_PORT == 1025:  # For Mailpit testing (no auth, no SSL/TLS)
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.sendmail(settings.SMTP_USERNAME, recipients, msg.as_string())
        elif settings.SMTP_PORT == 465:  # For SSL connections
            with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=context) as server:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USERNAME, recipients, msg.as_string())
        else:  # For TLS connections (usually port 587)
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USERNAME, recipients, msg.as_string())
        return True
    except Exception as e:
        # Log the error
        print(f"Error sending email: {e}")
        return False


def send_activity_verification_email(
    to_email: str,
    first_name: str,
    activity_name: str,
    activity_date: str,
    source_gpx_name: str,
) -> bool:
    """
    Send an email notification about a verified activity.
    
    Args:
        to_email: User's email address
        first_name: User's first name
        activity_name: Name of the verified Strava activity
        activity_date: Date of the verified activity
        source_gpx_name: Name of the matched source GPX route
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = f"{settings.PROJECT_NAME} - Activity Verified!"
    content = f"""
    <html>
    <body>
        <h1>Hello {first_name},</h1>
        <p>Good news! Your activity has been verified for the {settings.PROJECT_NAME}.</p>
        <p><strong>Activity:</strong> {activity_name}</p>
        <p><strong>Date:</strong> {activity_date}</p>
        <p><strong>Route:</strong> {source_gpx_name}</p>
        <p>This activity has been added to your contest profile. Keep up the great work!</p>
        <p>Best regards,<br>KMTB Team</p>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, content)


def send_strava_connected_email(
    to_email: str,
    first_name: str,
) -> bool:
    """
    Send an email notification that Strava has been successfully connected.
    
    Args:
        to_email: User's email address
        first_name: User's first name
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = f"{settings.PROJECT_NAME} - Strava Account Connected"
    content = f"""
    <html>
    <body>
        <h1>Hello {first_name},</h1>
        <p>Congratulations! Your Strava account has been successfully connected to the {settings.PROJECT_NAME}.</p>
        <p>We'll now automatically check your Strava activities for matching routes. When we find a match, you'll receive a notification.</p>
        <p>Thank you for participating in the contest!</p>
        <p>Best regards,<br>KMTB Team</p>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, content)