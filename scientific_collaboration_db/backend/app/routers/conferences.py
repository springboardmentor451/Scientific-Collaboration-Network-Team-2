from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.deps import require_roles
from app.database import get_db
from app.models import Conference, User, UserRole
from app.schemas.common import ConferenceOut
from app.schemas.conference import ConferenceCreate, ConferenceUpdate

router = APIRouter(prefix="/conferences", tags=["conferences-write"])
admin_only = require_roles("system_admin", "institution_admin")


@router.post("", response_model=ConferenceOut, status_code=status.HTTP_201_CREATED)
def create_conference(payload: ConferenceCreate, db: Session = Depends(get_db), current_user: User = Depends(admin_only)):
    data = payload.model_dump()

    if current_user.role == UserRole.INSTITUTION_ADMIN:
        # An Institution Admin can only ever create a conference under their
        # own institution — whatever institution_id they sent is ignored in
        # favor of their own, same pattern used for onboarding researchers.
        if not current_user.effective_institution_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account isn't linked to an institution yet")
        data["institution_id"] = current_user.effective_institution_id

    conference = Conference(**data)
    db.add(conference)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create conference")
    db.refresh(conference)
    log_action(db, current_user.id, "CREATE", "Conference", conference.id, {"name": conference.name})
    return conference


@router.put("/{conference_id}", response_model=ConferenceOut)
def update_conference(conference_id: str, payload: ConferenceUpdate, db: Session = Depends(get_db), current_user: User = Depends(admin_only)):
    conference = db.get(Conference, conference_id)
    if not conference:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conference not found")

    changed = payload.model_dump(exclude_unset=True)

    if current_user.role == UserRole.INSTITUTION_ADMIN:
        # Institution Admins may only edit conferences that belong to their
        # own institution — never another institution's conference, and
        # never a platform-wide (no-institution) one created by a System
        # Admin. They also can't reassign a conference to a different
        # institution.
        admin_inst = current_user.effective_institution_id
        if not admin_inst or conference.institution_id != admin_inst:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit conferences that belong to your own institution")
        changed.pop("institution_id", None)

    for field, value in changed.items():
        setattr(conference, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not update conference")
    db.refresh(conference)
    log_action(db, current_user.id, "UPDATE", "Conference", conference.id, {"fields": list(changed.keys())})
    return conference


@router.delete("/{conference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conference(conference_id: str, db: Session = Depends(get_db), current_user=Depends(require_roles("system_admin"))):
    conference = db.get(Conference, conference_id)
    if not conference:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conference not found")
    name = conference.name
    db.delete(conference)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not delete conference")
    log_action(db, current_user.id, "DELETE", "Conference", conference_id, {"name": name})
