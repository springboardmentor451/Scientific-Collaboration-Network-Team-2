"""
Sends real email via SMTP (e.g. a Gmail account with an App Password).

If SMTP_USERNAME isn't configured (local/dev use), we don't fail the request —
we log the message to the console instead, so the app is still fully usable
without a real mail account during development.
"""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("app.email")
settings = get_settings()


def _smtp_configured() -> bool:
    return bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD and settings.SMTP_FROM_EMAIL)


def send_email(to_email: str, subject: str, body_text: str) -> None:
    if not _smtp_configured():
        logger.warning(
            "SMTP not configured — logging email instead of sending it.\n"
            "TO: %s\nSUBJECT: %s\nBODY:\n%s",
            to_email, subject, body_text,
        )
        return

    message = EmailMessage()
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body_text)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)


# def send_verification_email(to_email: str, verification_link: str) -> None:

def send_otp_email(to_email: str, code: str) -> None:
    subject = "Your sign-in code — Scientific Collaboration Network Analyzer"
    body = (
        f"Hi,\n\n"
        f"Your 2-step verification code is: {code}\n\n"
        f"This code expires in 10 minutes. If you didn't try to sign in, "
        f"you can safely ignore this email.\n"
    )
    send_email(to_email, subject, body)


def send_verification_email(to_email: str, verification_link: str) -> None:
    # ------------
    subject = "Verify your email — Scientific Collaboration Network Analyzer"
    body = (
        f"Hi,\n\n"
        f"Thanks for registering. Please verify your email address by opening this link:\n\n"
        f"{verification_link}\n\n"
        f"This link expires in {settings.EMAIL_VERIFICATION_EXPIRE_MINUTES // 60} hours.\n\n"
        f"If you didn't create this account, you can ignore this email."
    )
    send_email(to_email, subject, body)
