from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models import SupportMessage, User, UserRole
from app.schemas.support import SupportMessageCreate, SupportMessageOut, SupportThreadOut

router = APIRouter(prefix="/support", tags=["support"])
system_admin_only = require_roles("system_admin")


def _display_name(user: User) -> str:
    if user.researcher and user.researcher.full_name:
        return user.researcher.full_name
    return user.email.split("@")[0]


def _serialize(msg: SupportMessage, db: Session) -> SupportMessageOut:
    sender = db.get(User, msg.sender_id)
    return SupportMessageOut(
        id=msg.id,
        thread_user_id=msg.thread_user_id,
        sender_id=msg.sender_id,
        sender_name=_display_name(sender) if sender else "Unknown",
        sender_role=sender.role.value if sender else "unknown",
        body=msg.body,
        is_from_admin=msg.is_from_admin,
        is_read=msg.is_read,
        created_at=msg.created_at,
    )


@router.post("/messages", response_model=SupportMessageOut, status_code=status.HTTP_201_CREATED)
def send_support_message(
    payload: SupportMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Researchers, Reviewers and Institution Admins send a message into their
    own single conversation thread with the System Admin team. A System
    Admin uses the same endpoint to reply — but must specify which user's
    thread (thread_user_id) they're replying to.
    """
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message can't be empty")

    if current_user.role == UserRole.SYSTEM_ADMIN:
        if not payload.thread_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="thread_user_id is required when replying as System Admin")
        target = db.get(User, payload.thread_user_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That user/thread was not found")
        thread_user_id = target.id
        is_from_admin = True
    else:
        thread_user_id = current_user.id
        is_from_admin = False

    msg = SupportMessage(
        thread_user_id=thread_user_id,
        sender_id=current_user.id,
        body=body,
        is_from_admin=is_from_admin,
        is_read=False,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    log_action(db, current_user.id, "CREATE", "SupportMessage", msg.id, {"thread_user_id": str(thread_user_id)})
    return _serialize(msg, db)


@router.get("/messages", response_model=list[SupportMessageOut])
def get_my_support_thread(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Your own conversation with the System Admin (Researcher / Reviewer /
    Institution Admin only — a System Admin has no thread of their own and
    should use GET /support/threads instead).
    """
    if current_user.role == UserRole.SYSTEM_ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System Admins should use GET /support/threads")

    msgs = (
        db.query(SupportMessage)
        .filter(SupportMessage.thread_user_id == current_user.id)
        .order_by(SupportMessage.created_at.asc())
        .all()
    )
    # Viewing the thread marks the admin's replies as read.
    unread = [m for m in msgs if m.is_from_admin and not m.is_read]
    for m in unread:
        m.is_read = True
    if unread:
        db.commit()
    return [_serialize(m, db) for m in msgs]


@router.get("/threads", response_model=list[SupportThreadOut])
def list_support_threads(db: Session = Depends(get_db), current_user: User = Depends(system_admin_only)):
    """System Admin inbox: every user who has an open support conversation, most recently active first."""
    thread_user_ids = [row[0] for row in db.query(SupportMessage.thread_user_id).distinct().all()]
    threads: list[SupportThreadOut] = []
    for uid in thread_user_ids:
        user = db.get(User, uid)
        if not user:
            continue
        msgs = (
            db.query(SupportMessage)
            .filter(SupportMessage.thread_user_id == uid)
            .order_by(SupportMessage.created_at.asc())
            .all()
        )
        if not msgs:
            continue
        last = msgs[-1]
        unread_count = sum(1 for m in msgs if not m.is_from_admin and not m.is_read)
        inst = user.institution.name if user.institution else (user.researcher.institution.name if user.researcher and user.researcher.institution else None)
        threads.append(SupportThreadOut(
            user_id=uid,
            user_name=_display_name(user),
            user_email=user.email,
            user_role=user.role.value,
            institution_name=inst,
            last_message=last.body,
            last_message_at=last.created_at,
            unread_count=unread_count,
        ))
    threads.sort(key=lambda t: t.last_message_at, reverse=True)
    return threads


@router.get("/threads/{user_id}", response_model=list[SupportMessageOut])
def get_support_thread(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(system_admin_only)):
    """System Admin: read one user's full conversation, marking their unread messages as seen."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    msgs = (
        db.query(SupportMessage)
        .filter(SupportMessage.thread_user_id == user_id)
        .order_by(SupportMessage.created_at.asc())
        .all()
    )
    unread = [m for m in msgs if not m.is_from_admin and not m.is_read]
    for m in unread:
        m.is_read = True
    if unread:
        db.commit()
    return [_serialize(m, db) for m in msgs]
