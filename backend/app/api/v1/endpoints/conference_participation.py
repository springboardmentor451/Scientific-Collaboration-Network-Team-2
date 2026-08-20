from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.researchers import Researcher
from backend.app.models.conference_participation import ConferenceParticipation
from backend.app.schemas.conference_participation import ConferenceParticipationCreate, ConferenceParticipationUpdate, ConferenceParticipationOut
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/conference-participation/", response_model=List[ConferenceParticipationOut])
def read_conference_participations(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    conference_id: Optional[int] = None,
    researcher_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve conference participations list.
    """
    query = db.query(ConferenceParticipation)
    if conference_id:
        query = query.filter(ConferenceParticipation.conference_id == conference_id)
    if researcher_id:
        query = query.filter(ConferenceParticipation.researcher_id == researcher_id)
    return query.offset(skip).limit(limit).all()

@router.get("/conference-participation/{id}", response_model=ConferenceParticipationOut)
def read_conference_participation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get conference participation by id.
    """
    part = db.query(ConferenceParticipation).filter(ConferenceParticipation.id == id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Participation record not found")
    return part

@router.post("/conference-participation/", response_model=ConferenceParticipationOut, status_code=status.HTTP_201_CREATED)
def create_conference_participation(
    *,
    db: Session = Depends(get_db),
    part_in: ConferenceParticipationCreate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Register participation.
    """
    # Fetch corresponding researcher profile
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if part_in.researcher_id != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot register participation details for another researcher profile"
        )
        
    # Check duplicate
    existing = db.query(ConferenceParticipation).filter(
        ConferenceParticipation.conference_id == part_in.conference_id,
        ConferenceParticipation.researcher_id == part_in.researcher_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="This researcher is already registered for this conference.")
        
    db_part = ConferenceParticipation(
        conference_id=part_in.conference_id,
        researcher_id=part_in.researcher_id,
        participation_role=part_in.participation_role,
        presentation_title=part_in.presentation_title,
        registration_date=part_in.registration_date
    )
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="register_participation",
        entity_type="conference_participation",
        entity_id=db_part.id,
        ip_address=request.client.host if request.client else None
    )
    return db_part

@router.put("/conference-participation/{id}", response_model=ConferenceParticipationOut)
def update_conference_participation(
    *,
    db: Session = Depends(get_db),
    id: int,
    part_in: ConferenceParticipationUpdate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Update participation details.
    """
    db_part = db.query(ConferenceParticipation).filter(ConferenceParticipation.id == id).first()
    if not db_part:
        raise HTTPException(status_code=404, detail="Participation record not found")
        
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if db_part.researcher_id != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this participation record"
        )
        
    update_data = part_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(db_part, field, update_data[field])
        
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update_participation",
        entity_type="conference_participation",
        entity_id=db_part.id,
        ip_address=request.client.host if request.client else None
    )
    return db_part

@router.delete("/conference-participation/{id}")
def delete_conference_participation(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Delete participation registration.
    """
    db_part = db.query(ConferenceParticipation).filter(ConferenceParticipation.id == id).first()
    if not db_part:
        raise HTTPException(status_code=404, detail="Participation record not found")
        
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if db_part.researcher_id != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this participation record"
        )
        
    db.delete(db_part)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete_participation",
        entity_type="conference_participation",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Participation record deleted successfully"}
