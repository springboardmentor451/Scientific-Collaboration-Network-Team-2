from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.researcher import Researcher
from app.models.collaboration import CollaborationRequest
from app.models.publication import Publication

router = APIRouter(prefix="/network", tags=["Collaboration Network"])

@router.get("/graph")
def graph(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    researchers = db.query(Researcher).filter(Researcher.user_id.isnot(None)).all()
    ids = {item.user_id for item in researchers}
    nodes = [{"id": item.user_id, "researcher_id": item.id, "label": item.name, "institution": item.institution, "field": item.field, "publications": db.query(Publication).filter(Publication.owner_id == item.user_id).count()} for item in researchers]
    requests = db.query(CollaborationRequest).filter(CollaborationRequest.status == "Accepted", or_(CollaborationRequest.requester_id.in_(ids), CollaborationRequest.recipient_id.in_(ids))).all()
    edges = [{"source": item.requester_id, "target": item.recipient_id, "status": item.status} for item in requests]
    return {"nodes": nodes, "edges": edges}
