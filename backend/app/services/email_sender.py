import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.config import settings
from app.services.tokens import generate_unsubscribe_token

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def _get_access_token() -> str:
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
            "refresh_token": settings.gmail_refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def send_newsletter_email(to_email: str, subject: str, html_content: str) -> bool:
    unsubscribe_token = generate_unsubscribe_token(to_email)
    unsubscribe_link = f"http://localhost:8000/members/unsubscribe?token={unsubscribe_token}"

    full_html = (
        f"{html_content}"
        f"<hr>"
        f'<p style="font-size: 12px; color: #888;">'
        f'You\'re receiving this because you\'re a member of the Cybersecurity & AI Club at York College. '
        f'<a href="{unsubscribe_link}">Unsubscribe</a></p>'
    )

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.gmail_address
    message["To"] = to_email
    message.attach(MIMEText(full_html, "html"))

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    try:
        access_token = _get_access_token()
        response = httpx.post(
            GMAIL_SEND_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": raw_message},
            timeout=15,
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send to {to_email}: {e}")
        return False


def send_newsletter_to_members(member_emails: list, subject: str, html_content: str) -> dict:
    sent = 0
    failed = 0

    for email in member_emails:
        success = send_newsletter_email(email, subject, html_content)
        if success:
            sent += 1
        else:
            failed += 1

    return {"sent": sent, "failed": failed}
