from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.researcher import Researcher
from app.models.collaboration import CollaborationRequest
from app.Schemas.collaboration import CollaborationRequestCreate, CollaborationRequestResponse
from app.Crud.audit import log_action
from app.models.notification import Notification

router = APIRouter(prefix="/collaborations", tags=["Collaborations"])

@router.post("/request", response_model=CollaborationRequestResponse, status_code=201)
def send_request(data: CollaborationRequestCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"Researcher", "Faculty", "Collaborator", "Admin", "System Admin"}:
        raise HTTPException(403, "Your role cannot send collaboration requests.")
    target = db.query(Researcher).filter(Researcher.id == data.researcher_id).first()
    if not target or not target.user_id: raise HTTPException(404, "Researcher does not have a connected user account.")
    if target.user_id == user.id: raise HTTPException(400, "You cannot collaborate with yourself.")
    duplicate = db.query(CollaborationRequest).filter(CollaborationRequest.requester_id == user.id, CollaborationRequest.recipient_id == target.user_id, CollaborationRequest.status == "Pending").first()
    if duplicate: raise HTTPException(400, "A pending request already exists.")
    request = CollaborationRequest(requester_id=user.id, recipient_id=target.user_id, message=data.message)
    db.add(request); db.flush(); db.add(Notification(user_id=target.user_id, title="New collaboration request", message=f"{user.full_name} sent you a collaboration request.", link="/collaborations")); log_action(db, "COLLABORATION_REQUESTED", user.id, "CollaborationRequest", request.id, f"Recipient: {target.user_id}"); db.commit(); db.refresh(request); return request

@router.get("/requests/sent", response_model=list[CollaborationRequestResponse])
def sent(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(CollaborationRequest).filter(CollaborationRequest.requester_id == user.id).order_by(CollaborationRequest.created_at.desc()).all()

@router.get("/requests/received", response_model=list[CollaborationRequestResponse])
def received(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(CollaborationRequest).filter(CollaborationRequest.recipient_id == user.id).order_by(CollaborationRequest.created_at.desc()).all()

def decide(request_id, decision, db, user):
    item = db.query(CollaborationRequest).filter(CollaborationRequest.id == request_id).first()
    if not item: raise HTTPException(404, "Collaboration request not found.")
    if item.recipient_id != user.id: raise HTTPException(403, "Only the recipient can respond to this request.")
    if item.status != "Pending": raise HTTPException(400, "This request has already been processed.")
    item.status = decision
    db.add(Notification(
        user_id=item.requester_id,
        title=f"Collaboration request {decision.lower()}",
        message=f"{user.full_name} {decision.lower()} your collaboration request.",
        link="/collaborations",
    ))
    log_action(db, f"COLLABORATION_{decision.upper()}", user.id, "CollaborationRequest", item.id)
    db.commit(); db.refresh(item); return item

@router.put("/requests/{request_id}/accept", response_model=CollaborationRequestResponse)
def accept(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)): return decide(request_id, "Accepted", db, user)

@router.put("/requests/{request_id}/reject", response_model=CollaborationRequestResponse)
def reject(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)): return decide(request_id, "Rejected", db, user)

@router.put("/requests/{request_id}/cancel", response_model=CollaborationRequestResponse)
def cancel(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(CollaborationRequest).filter(CollaborationRequest.id == request_id).first()
    if not item: raise HTTPException(404, "Collaboration request not found.")
    if item.requester_id != user.id: raise HTTPException(403, "Only the sender can cancel this request.")
    if item.status != "Pending": raise HTTPException(400, "Only pending requests can be cancelled.")
    item.status = "Cancelled"
    db.add(Notification(user_id=item.recipient_id, title="Collaboration request cancelled", message=f"{user.full_name} cancelled a collaboration request.", link="/collaborations"))
    log_action(db, "COLLABORATION_CANCELLED", user.id, "CollaborationRequest", item.id)
    db.commit(); db.refresh(item); return item

@router.get("/my", response_model=list[CollaborationRequestResponse])
def my_collaborations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(CollaborationRequest).filter(or_(CollaborationRequest.requester_id == user.id, CollaborationRequest.recipient_id == user.id), CollaborationRequest.status == "Accepted").all()
