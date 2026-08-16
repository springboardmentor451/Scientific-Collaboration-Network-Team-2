from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.deps import require_roles
from app.database import get_db
from app.models import Institution
from app.schemas.common import InstitutionOut
from app.schemas.institution import InstitutionCreate, InstitutionUpdate

router = APIRouter(prefix="/institutions", tags=["institutions-write"])
admin_only = require_roles("system_admin", "institution_admin")


@router.post("", response_model=InstitutionOut, status_code=status.HTTP_201_CREATED)
def create_institution(payload: InstitutionCreate, db: Session = Depends(get_db), current_user=Depends(admin_only)):
    institution = Institution(**payload.model_dump())
    db.add(institution)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create institution")
    db.refresh(institution)
    log_action(db, current_user.id, "CREATE", "Institution", institution.id, {"name": institution.name})
    return institution


@router.put("/{institution_id}", response_model=InstitutionOut)
def update_institution(institution_id: str, payload: InstitutionUpdate, db: Session = Depends(get_db), current_user=Depends(admin_only)):
    institution = db.get(Institution, institution_id)
    if not institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    changed = payload.model_dump(exclude_unset=True)
    for field, value in changed.items():
        setattr(institution, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not update institution")
    db.refresh(institution)
    log_action(db, current_user.id, "UPDATE", "Institution", institution.id, {"fields": list(changed.keys())})
    return institution


@router.delete("/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_institution(institution_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("system_admin"))):
    institution = db.get(Institution, institution_id)
    if not institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    name = institution.name
    db.delete(institution)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not delete institution — researchers or projects still reference it",
        )
    log_action(db, current_user.id, "DELETE", "Institution", institution_id, {"name": name})