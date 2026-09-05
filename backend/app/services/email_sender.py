import base64
import os
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

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


def _attach_file(message: MIMEMultipart, filepath: str):
    if not os.path.exists(filepath):
        return

    filename = os.path.basename(filepath)
    content_type, encoding = mimetypes.guess_type(filepath)
    if content_type is None:
        content_type = "application/octet-stream"

    main_type, sub_type = content_type.split("/", 1)

    with open(filepath, "rb") as f:
        part = MIMEBase(main_type, sub_type)
        part.set_payload(f.read())

    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    message.attach(part)


def send_newsletter_email(to_email: str, subject: str, html_content: str, attachment_paths: list = None) -> bool:
    unsubscribe_token = generate_unsubscribe_token(to_email)
    unsubscribe_link = f"http://localhost:8000/members/unsubscribe?token={unsubscribe_token}"

    full_html = (
        f"{html_content}"
        f"<hr>"
        f'<p style="font-size: 12px; color: #888;">'
        f'You\'re receiving this because you\'re a member of the Cybersecurity & AI Club at York College. '
        f'<a href="{unsubscribe_link}">Unsubscribe</a></p>'
    )

    message = MIMEMultipart("mixed")
    message["Subject"] = subject
    message["From"] = settings.gmail_address
    message["To"] = to_email

    body = MIMEMultipart("alternative")
    body.attach(MIMEText(full_html, "html"))
    message.attach(body)

    for path in (attachment_paths or []):
        _attach_file(message, path)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    try:
        access_token = _get_access_token()
        response = httpx.post(
            GMAIL_SEND_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": raw_message},
            timeout=30,
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send to {to_email}: {e}")
        return False


def send_newsletter_to_members(member_emails: list, subject: str, html_content: str, attachment_paths: list = None) -> dict:
    sent = 0
    failed = 0

    for email in member_emails:
        success = send_newsletter_email(email, subject, html_content, attachment_paths)
        if success:
            sent += 1
        else:
            failed += 1

    return {"sent": sent, "failed": failed}
