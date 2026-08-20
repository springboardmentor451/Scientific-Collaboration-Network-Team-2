from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.conferences import Conference
from backend.app.schemas.conferences import ConferenceCreate, ConferenceUpdate, ConferenceOut
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/conferences/", response_model=List[ConferenceOut])
def read_conferences(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve conferences.
    """
    query = db.query(Conference)
    if search:
        query = query.filter(Conference.name.ilike(f"%{search}%"))
    conferences = query.offset(skip).limit(limit).all()
    return conferences

@router.get("/conferences/{id}", response_model=ConferenceOut)
def read_conference(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get conference details.
    """
    conf = db.query(Conference).filter(Conference.id == id).first()
    if not conf:
        raise HTTPException(status_code=404, detail="Conference not found")
    return conf

@router.post("/conferences/", response_model=ConferenceOut, status_code=status.HTTP_201_CREATED)
def create_conference(
    *,
    db: Session = Depends(get_db),
    conf_in: ConferenceCreate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.reviewer, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Register a conference.
    """
    db_conf = Conference(
        name=conf_in.name,
        location=conf_in.location,
        start_date=conf_in.start_date,
        end_date=conf_in.end_date,
        website=conf_in.website,
        description=conf_in.description
    )
    db.add(db_conf)
    db.commit()
    db.refresh(db_conf)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="conference",
        entity_id=db_conf.id,
        ip_address=request.client.host if request.client else None
    )
    return db_conf

@router.put("/conferences/{id}", response_model=ConferenceOut)
def update_conference(
    *,
    db: Session = Depends(get_db),
    id: int,
    conf_in: ConferenceUpdate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.reviewer, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Update conference details.
    """
    conf = db.query(Conference).filter(Conference.id == id).first()
    if not conf:
        raise HTTPException(status_code=404, detail="Conference not found")
        
    update_data = conf_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(conf, field, update_data[field])
        
    db.add(conf)
    db.commit()
    db.refresh(conf)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="conference",
        entity_id=conf.id,
        ip_address=request.client.host if request.client else None
    )
    return conf

@router.delete("/conferences/{id}")
def delete_conference(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(RoleChecker([UserRole.system_admin])),
    request: Request
) -> Any:
    """
    Delete a conference entry.
    """
    conf = db.query(Conference).filter(Conference.id == id).first()
    if not conf:
        raise HTTPException(status_code=404, detail="Conference not found")
    db.delete(conf)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="conference",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Conference deleted successfully"}
