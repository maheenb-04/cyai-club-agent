import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings
from app.services.tokens import generate_unsubscribe_token

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


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

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(settings.gmail_address, settings.gmail_app_password)
            server.sendmail(settings.gmail_address, to_email, message.as_string())
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