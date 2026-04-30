"""
VYUHA Email Tool
SMTP-based email sending utility for transactional emails
Supports both Gmail SMTP and SendGrid API
"""

import smtplib
import requests
from email.message import EmailMessage
import os
from typing import Optional


def send_via_sendgrid(to_email: str, subject: str, body: str, from_email: str, from_name: str) -> bool:
    """Send email via SendGrid API"""
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key or api_key.startswith("SG."):
        return False
    
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email, "name": from_name},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        return response.status_code in [200, 202, 201]
    except Exception as e:
        print(f"SendGrid API error: {e}")
        return False


def create_email_message(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> EmailMessage:
    """
    Create a properly formatted email message.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Plain text body
        html_body: Optional HTML-formatted body

    Returns:
        EmailMessage object ready for sending
    """
    msg = EmailMessage()
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["From"] = os.getenv("SMTP_FROM_EMAIL", "noreply@institution.edu")

    if html_body:
        msg.set_content(body)
        msg.add_alternative(html_body, subtype="html")
    else:
        msg.set_content(body)

    return msg

def send_email(
    smtp_user: str,
    smtp_pass: str,
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """
    Send an email via SendGrid API (preferred) or SMTP server.
    Returns:
        True if sent successfully, False otherwise
    """
    from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@institution.edu")
    from_name = os.getenv("SMTP_FROM_NAME", "VYUHA Academy")
    
    sendgrid_key = os.getenv("SENDGRID_API_KEY", "").strip()
    
    # Try SendGrid first if API key is available
    if sendgrid_key and sendgrid_key.startswith("SG."):
        if send_via_sendgrid(to_email, subject, body, from_email, from_name):
            return True
        # If SendGrid fails, fall through to SMTP
    
    # Fallback to SMTP
    msg = create_email_message(to_email, subject, body, html_body)

    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Email send failed: {str(e)}")
        return False

def generate_verification_email(to_email: str, verification_url: str) -> tuple:
    """
    Generate email content for user verification.

    Args:
        to_email: Recipient email
        verification_url: URL for email verification link

    Returns:
        (subject, body) tuple for email sending
    """
    verification_link = f"{verification_url}?token=verify_email"
    subject = "Email Verification Required"
    body = f"""
    Dear User,

    Please verify your email address by clicking the link below:
    {verification_link}

    If you did not request this, please ignore this email.

    Best regards,
    VYUHA Team
    """
    return subject, body

def generate_welcome_email(to_email: str, user_name: str) -> tuple:
    """
    Generate welcome email content for new users.

    Args:
        to_email: Recipient email
        user_name: Recipient's name

    Returns:
        (subject, body) tuple for email sending
    """
    subject = "Welcome to VYUHA Academy!"
    body = f"""
    Hello {user_name},

    Welcome to VYUHA Academy! We're excited to have you join our community of learners.

    Here's what you need to know:
    • Access your student dashboard at: {os.getenv('APP_URL', 'https://vyuha.edu')}/dashboard
    • Check your upcoming classes and schedules
    • Receive announcements and important updates

    If you have any questions, reply to this email or contact support.

    Best regards,
    VYUHA Team
    """
    return subject, body