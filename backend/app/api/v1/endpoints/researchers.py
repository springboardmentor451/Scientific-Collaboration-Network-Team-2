from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.researchers import Researcher
from backend.app.schemas.researchers import ResearcherCreate, ResearcherUpdate, ResearcherOut
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/researchers/", response_model=List[ResearcherOut])
def read_researchers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    institution_id: Optional[int] = None,
    department_id: Optional[int] = None,
    gender: Optional[str] = None,
    nationality: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    skill: Optional[str] = None,
    interest: Optional[str] = None
) -> Any:
    """
    Retrieve researcher profiles with advanced filtering.
    """
    from sqlalchemy import String, cast
    query = db.query(Researcher)
    if search:
        query = query.filter(
            (Researcher.full_name.ilike(f"%{search}%")) |
            (Researcher.bio.ilike(f"%{search}%"))
        )
    if institution_id:
        query = query.filter(Researcher.institution_id == institution_id)
    if department_id:
        query = query.filter(Researcher.department_id == department_id)
    if gender:
        query = query.filter(Researcher.gender == gender)
    if nationality:
        query = query.filter(Researcher.nationality.ilike(nationality))
    if country:
        query = query.filter(Researcher.country.ilike(country))
    if city:
        query = query.filter(Researcher.city.ilike(city))
    if skill:
        query = query.filter(cast(Researcher.skills, String).ilike(f"%{skill}%"))
    if interest:
        query = query.filter(cast(Researcher.research_interests, String).ilike(f"%{interest}%"))
        
    researchers = query.offset(skip).limit(limit).all()
    return researchers

@router.get("/researchers/{id}", response_model=ResearcherOut)
def read_researcher(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get researcher profile by id.
    """
    researcher = db.query(Researcher).filter(Researcher.id == id).first()
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher profile not found")
    return researcher

@router.post("/researchers/", response_model=ResearcherOut, status_code=status.HTTP_201_CREATED)
def create_researcher(
    *,
    db: Session = Depends(get_db),
    researcher_in: ResearcherCreate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Create researcher profile. (Admin or the user matching user_id)
    """
    if current_user.id != researcher_in.user_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges to create a profile for another user"
        )
        
    # Check if profile already exists for user
    existing = db.query(Researcher).filter(Researcher.user_id == researcher_in.user_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A researcher profile already exists for this user."
        )
        
    inst_id = researcher_in.institution_id
    if not inst_id and researcher_in.institution_name:
        from backend.app.models.institutions import Institution
        inst_name = researcher_in.institution_name.strip()
        institution = db.query(Institution).filter(Institution.name.ilike(inst_name)).first()
        if not institution:
            institution = Institution(name=inst_name)
            db.add(institution)
            db.commit()
            db.refresh(institution)
        inst_id = institution.id

    dept_id = researcher_in.department_id
    if not dept_id and researcher_in.department_name and inst_id:
        from backend.app.models.departments import Department
        dept_name = researcher_in.department_name.strip()
        department = db.query(Department).filter(
            Department.name.ilike(dept_name),
            Department.institution_id == inst_id
        ).first()
        if not department:
            department = Department(name=dept_name, institution_id=inst_id)
            db.add(department)
            db.commit()
            db.refresh(department)
        dept_id = department.id

    db_researcher = Researcher(
        user_id=researcher_in.user_id,
        full_name=researcher_in.full_name,
        institution_id=inst_id,
        department_id=dept_id,
        gender=researcher_in.gender,
        gender_other=researcher_in.gender_other,
        nationality=researcher_in.nationality,
        country=researcher_in.country,
        city=researcher_in.city,
        mobile_number=researcher_in.mobile_number,
        designation=researcher_in.designation,
        highest_qualification=researcher_in.highest_qualification,
        year_highest_qualification=researcher_in.year_highest_qualification,
        orcid_id=researcher_in.orcid_id,
        google_scholar_url=researcher_in.google_scholar_url,
        researchgate_url=researcher_in.researchgate_url,
        scopus_id=researcher_in.scopus_id,
        wos_id=researcher_in.wos_id,
        research_interests=researcher_in.research_interests or [],
        skills=researcher_in.skills or [],
        affiliations=researcher_in.affiliations,
        bio=researcher_in.bio,
        profile_photo_url=researcher_in.profile_photo_url
    )
    db.add(db_researcher)
    db.commit()
    db.refresh(db_researcher)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="researcher",
        entity_id=db_researcher.id,
        ip_address=request.client.host if request.client else None
    )
    return db_researcher

@router.get("/researchers/{id}/completion-status")
def get_completion_status(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Calculate deterministic profile completion percentage and missing fields list.
    """
    researcher = db.query(Researcher).filter(Researcher.id == id).first()
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher profile not found")

    score = 0
    missing = []

    if researcher.full_name:
        score += 10
    else:
        missing.append("Add full name")

    if researcher.user and researcher.user.is_verified:
        score += 15
    else:
        missing.append("Verify email address")

    if researcher.mobile_number and len(researcher.mobile_number) == 10:
        score += 10
    else:
        missing.append("Add 10-digit mobile number")

    if researcher.gender and researcher.nationality:
        score += 10
    else:
        missing.append("Specify gender and nationality")

    if researcher.country and researcher.city:
        score += 10
    else:
        missing.append("Add country and city")

    if researcher.institution_id or researcher.department_id:
        score += 15
    else:
        missing.append("Select institution / department")

    if researcher.research_interests or researcher.skills:
        score += 15
    else:
        missing.append("Add research interests or skills")

    if researcher.profile_photo_url or researcher.bio:
        score += 15
    else:
        missing.append("Upload profile photo or add biography")

    return {
        "researcher_id": id,
        "completion_percentage": min(score, 100),
        "is_complete": score >= 100,
        "missing_fields": missing
    }

@router.put("/researchers/{id}", response_model=ResearcherOut)
def update_researcher(
    *,
    db: Session = Depends(get_db),
    id: int,
    researcher_in: ResearcherUpdate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Update researcher profile. (Admin, or the profile owner)
    """
    researcher = db.query(Researcher).filter(Researcher.id == id).first()
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher profile not found")
        
    if current_user.id != researcher.user_id and current_user.role not in [UserRole.system_admin, UserRole.institution_admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this profile"
        )
        
    update_data = researcher_in.model_dump(exclude_unset=True)
    inst_id = update_data.get("institution_id")
    inst_name = update_data.pop("institution_name", None)
    if not inst_id and inst_name:
        from backend.app.models.institutions import Institution
        inst_name_stripped = inst_name.strip()
        institution = db.query(Institution).filter(Institution.name.ilike(inst_name_stripped)).first()
        if not institution:
            institution = Institution(name=inst_name_stripped)
            db.add(institution)
            db.commit()
            db.refresh(institution)
        update_data["institution_id"] = institution.id
        inst_id = institution.id
        
    dept_id = update_data.get("department_id")
    dept_name = update_data.pop("department_name", None)
    resolved_inst_id = inst_id or researcher.institution_id
    if not dept_id and dept_name and resolved_inst_id:
        from backend.app.models.departments import Department
        dept_name_stripped = dept_name.strip()
        department = db.query(Department).filter(
            Department.name.ilike(dept_name_stripped),
            Department.institution_id == resolved_inst_id
        ).first()
        if not department:
            department = Department(name=dept_name_stripped, institution_id=resolved_inst_id)
            db.add(department)
            db.commit()
            db.refresh(department)
        update_data["department_id"] = department.id

    # If the user is a researcher, they cannot change their registration/signup identity fields.
    if current_user.role == UserRole.researcher:
        import enum
        signup_fields = {
            "full_name": "Full Name",
            "orcid_id": "ORCID Identifier",
            "mobile_number": "Mobile Number",
            "gender": "Gender",
            "gender_other": "Specify Gender",
            "nationality": "Nationality",
            "country": "Country",
            "city": "City",
            "institution_id": "Institution",
            "department_id": "Department",
            "research_interests": "Research Interests"
        }
        for field, label in signup_fields.items():
            if field in update_data:
                current_val = getattr(researcher, field)
                new_val = update_data[field]
                if field == "research_interests":
                    if sorted(current_val or []) != sorted(new_val or []):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Researchers are not permitted to edit their registration info: {label}"
                        )
                elif field == "gender" and isinstance(new_val, enum.Enum):
                    if current_val != new_val:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Researchers are not permitted to edit their registration info: {label}"
                        )
                else:
                    c_str = str(current_val or "").strip()
                    n_str = str(new_val or "").strip()
                    if c_str != n_str:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Researchers are not permitted to edit their registration info: {label}"
                        )

    for field in update_data:
        setattr(researcher, field, update_data[field])
        
    db.add(researcher)
    db.commit()
    db.refresh(researcher)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="researcher",
        entity_id=researcher.id,
        ip_address=request.client.host if request.client else None
    )
    return researcher

@router.delete("/researchers/{id}")
def delete_researcher(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Delete researcher profile. (Admin only)
    """
    researcher = db.query(Researcher).filter(Researcher.id == id).first()
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher profile not found")
        
    db.delete(researcher)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="researcher",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Researcher profile deleted successfully"}
