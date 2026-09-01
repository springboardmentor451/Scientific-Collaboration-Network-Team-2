from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.core.email import send_announcement_email
from app.Crud.audit import log_action
from app.models.user import User
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class AnnouncementCreate(BaseModel):
    subject: str = Field(min_length=2, max_length=200)
    message: str = Field(min_length=2, max_length=5000)
    recipient_role: str | None = Field(default=None, max_length=30)
    send_email: bool = False

@router.get("/my")
def my_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return [{"id": item.id, "title": item.title, "description": item.message, "link": item.link, "read": item.is_read, "time": item.created_at.isoformat()} for item in items]

@router.put("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user.id).first()
    if not item: raise HTTPException(404, "Notification not found.")
    item.is_read = True; db.commit()
    return {"message": "Notification marked as read."}

@router.put("/read-all")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read.is_(False)).update({Notification.is_read: True}, synchronize_session=False); db.commit(); return {"message": "Notifications marked as read."}

@router.post("/announcement", status_code=201)
def send_announcement(data: AnnouncementCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    recipients = db.query(User).filter(User.is_active.is_(True), User.approval_status == "Approved")
    if data.recipient_role: recipients = recipients.filter(User.role == data.recipient_role)
    users = recipients.all()
    if not users: raise HTTPException(400, "No active recipients match this announcement.")
    db.add_all([Notification(user_id=item.id, title=data.subject, message=data.message, link="/notifications") for item in users])
    email_sent = 0
    email_failed = 0
    if data.send_email:
        for recipient in users:
            if not recipient.email_verified:
                email_failed += 1
                continue
            try:
                send_announcement_email(recipient.email, recipient.full_name, data.subject, data.message)
                email_sent += 1
            except Exception:
                # Keep in-app delivery available if an individual email cannot be delivered.
                email_failed += 1
    channel = "in-app and email" if data.send_email else "in-app"
    log_action(db, "ANNOUNCEMENT_SENT", admin.id, "Notification", None, f"Recipients: {len(users)}; channel: {channel}; email sent: {email_sent}; email failed: {email_failed}")
    db.commit()
    return {"message": "Announcement sent.", "recipient_count": len(users), "email_sent_count": email_sent, "email_failed_count": email_failed}
