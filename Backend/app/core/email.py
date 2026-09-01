"""Minimal SMTP mail delivery for production email verification.

Credentials are read only from environment variables.  This works with the
free Brevo SMTP plan and can also be used with another SMTP provider.
"""
import os
import smtplib
from email.message import EmailMessage


def send_verification_email(recipient: str, full_name: str, code: str) -> None:
    # Automated tests never contact an external mail service.
    if os.getenv("EMAIL_DELIVERY_MODE") == "test":
        return
    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM_EMAIL")
    port = int(os.getenv("SMTP_PORT", "587"))
    if not all((host, username, password, sender)):
        raise RuntimeError("Email delivery is not configured. Add SMTP credentials to Backend/.env.")

    message = EmailMessage()
    message["Subject"] = "Verify your SCNA email address"
    message["From"] = f'{os.getenv("SMTP_FROM_NAME", "SCNA")} <{sender}>'
    message["To"] = recipient
    message.set_content(
        f"Hello {full_name},\n\nYour Scientific Collaboration Network Analyzer verification code is: {code}\n\n"
        "This code expires in 10 minutes. If you did not create an SCNA account, you can ignore this email.\n"
    )
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)


def send_password_reset_email(recipient: str, full_name: str, code: str) -> None:
    host = os.getenv("SMTP_HOST"); username = os.getenv("SMTP_USERNAME"); password = os.getenv("SMTP_PASSWORD"); sender = os.getenv("SMTP_FROM_EMAIL")
    if os.getenv("EMAIL_DELIVERY_MODE") == "test": return
    if not all((host, username, password, sender)): raise RuntimeError("Email delivery is not configured. Add SMTP credentials to Backend/.env.")
    message = EmailMessage(); message["Subject"] = "Reset your SCNA password"; message["From"] = f'{os.getenv("SMTP_FROM_NAME", "SCNA")} <{sender}>'; message["To"] = recipient
    message.set_content(f"Hello {full_name},\n\nYour SCNA password reset code is: {code}\n\nThis code expires in 10 minutes. If you did not request a password reset, ignore this email.\n")
    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=20) as smtp:
        smtp.starttls(); smtp.login(username, password); smtp.send_message(message)


def send_announcement_email(recipient: str, full_name: str, subject: str, body: str) -> None:
    """Deliver an administrator announcement through the configured SMTP provider."""
    if os.getenv("EMAIL_DELIVERY_MODE") == "test":
        return
    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM_EMAIL")
    port = int(os.getenv("SMTP_PORT", "587"))
    if not all((host, username, password, sender)):
        raise RuntimeError("Email delivery is not configured. Add SMTP credentials to Backend/.env.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f'{os.getenv("SMTP_FROM_NAME", "SCNA")} <{sender}>'
    message["To"] = recipient
    message.set_content(f"Hello {full_name},\n\n{body}\n\nThis announcement was sent by the Scientific Collaboration Network Analyzer.")
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)
