import smtplib
from email.mime.text import MIMEText
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.notifications import Notification, NotificationChannel, NotificationStatus

def send_notification(
    db: Session,
    user_id: int,
    subject: str,
    body: str,
    channel: NotificationChannel = NotificationChannel.email
) -> Notification:
    """
    Log notification to database and trigger channel dispatch.
    """
    db_notification = Notification(
        user_id=user_id,
        channel=channel,
        subject=subject,
        body=body,
        status=NotificationStatus.pending
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    # If channel is email, attempt to send SMTP
    if channel == NotificationChannel.email and settings.SMTP_HOST:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = settings.EMAILS_FROM_EMAIL
            # Fetch user email
            from backend.app.models.users import User
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.email:
                msg["To"] = user.email
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.starttls()
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                db_notification.status = NotificationStatus.sent
            else:
                db_notification.status = NotificationStatus.failed
        except Exception:
            db_notification.status = NotificationStatus.failed
    else:
        # For SMS, Push, In-App or SMTP not configured
        # Auto-resolve in-app / push notifications to sent
        if channel in [NotificationChannel.in_app, NotificationChannel.push]:
            db_notification.status = NotificationStatus.sent
        else:
            db_notification.status = NotificationStatus.failed

    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification
