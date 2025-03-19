"""
jwt generation for MagicLink login
"""

import os
import uuid
from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string


def generate_token():
    """Generate JWT token for user authentication"""
    token = uuid.uuid4()
    return token


def send_magic_link_email(email, token, user_type):
    """Send magic link email to user"""
    magic_link_url = (
        f"{settings.FRONTEND_URL}/api/auth/magic-link/callback?token={token}"
    )

    context = {
        "magic_link_url": magic_link_url,
        "user_type": user_type,
        "expiry_hours": 24,
    }

    email_html = render_to_string(
        "authentication/magic_link_email.html", context
    )

    subject = "Your Magic Link for Authentication"
    recipient_list = [email]
    from_email = "onboarding@resend.dev"
    message = email_html
    with get_connection(
        host=settings.RESEND_SMTP_HOST,
        port=settings.RESEND_SMTP_PORT,
        username=settings.RESEND_SMTP_USERNAME,
        password=os.getenv("RESEND_API_KEY"),
        use_tls=True,
    ) as connection:
        r = EmailMessage(
            subject=subject,
            body=message,
            to=recipient_list,
            from_email=from_email,
            connection=connection,
        ).send()
    return r
