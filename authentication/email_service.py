"""
Passwordless authentication Email Service
"""

import requests
from django.template.loader import render_to_string
from django.conf import settings


class EmailService:
    @staticmethod
    def send_magic_link(email, token, user_type):
        """Send magic link email using Resend API"""
        api_key = settings.RESEND_API_KEY
        base_url = settings.FRONTEND_URL

        # Create magic link URL
        magic_link = (
            f"{base_url}/auth/magic-link-verify?token={token}&"
            f"email={email}&type={user_type}"
        )

        # Render HTML template
        context = {
            "magic_link": magic_link,
            "user_type": user_type,
            "expiry_hours": 24,
        }
        email_html = render_to_string(
            "authentication/magic_link.html", context
        )

        # Send email with Resend
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": "noreply@updates.deccanlabs.in",
            "to": email,
            "subject": "Login to InfluenceAI",
            "html": email_html,
        }

        response = requests.post(
            "https://api.resend.com/emails", json=payload, headers=headers
        )

        return {"response": response.json(), "status": response.status_code}
