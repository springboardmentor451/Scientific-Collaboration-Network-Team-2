from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.auth.oauth2 import get_current_user
from backend.app.database.session import get_db

from backend.app.models.collaborations import Collaboration
from backend.app.models.researchers import Researcher
from backend.app.models.institutions import Institution
from backend.app.models.users import User

from backend.app.schemas.collaboration import (
    CollaborationCreate,
    CollaborationUpdate,
    CollaborationResponse,
    CollaborationStatsResponse
)


router = APIRouter(
    prefix="/collaborations",
    tags=["Collaborations"]
)


# ============================================================
# HELPERS
# ============================================================

def get_researcher(
    db: Session,
    researcher_id: int
):

    return (
        db.query(Researcher)
        .filter(
            Researcher.id == researcher_id
        )
        .first()
    )


def get_researcher_name(
    db: Session,
    researcher
):

    if not researcher:
        return None

    # Try researcher.full_name first
    full_name = getattr(
        researcher,
        "full_name",
        None
    )

    if full_name:
        return full_name

    # Otherwise get name from User
    user_id = getattr(
        researcher,
        "user_id",
        None
    )

    if user_id:

        user = (
            db.query(User)
            .filter(
                User.id == user_id
            )
            .first()
        )

        if user:

            return getattr(
                user,
                "full_name",
                None
            )

    return None


def get_institution_name(
    db: Session,
    researcher
):

    if not researcher:
        return None

    institution_id = getattr(
        researcher,
        "institution_id",
        None
    )

    if not institution_id:
        return None

    institution = (
        db.query(Institution)
        .filter(
            Institution.id == institution_id
        )
        .first()
    )

    if institution:
        return institution.name

    return None


# ============================================================
# BUILD RESPONSE
# ============================================================

def build_collaboration_response(
    collaboration: Collaboration,
    db: Session
):

    researcher_1 = get_researcher(
        db,
        collaboration.researcher_id_1
    )

    researcher_2 = get_researcher(
        db,
        collaboration.researcher_id_2
    )

    return {

        "id": collaboration.id,

        "researcher_id_1":
            collaboration.researcher_id_1,

        "researcher_id_2":
            collaboration.researcher_id_2,

        "researcher_1_name":
            get_researcher_name(
                db,
                researcher_1
            ),

        "researcher_2_name":
            get_researcher_name(
                db,
                researcher_2
            ),

        "institution_1":
            get_institution_name(
                db,
                researcher_1
            ),

        "institution_2":
            get_institution_name(
                db,
                researcher_2
            ),

        "collaboration_type":
            collaboration.collaboration_type,

        "description":
            collaboration.description,

        "start_date":
            collaboration.start_date,

        "end_date":
            collaboration.end_date,

        "status":
            collaboration.status,

        "created_at":
            collaboration.created_at
    }


# ============================================================
# STATISTICS
# ============================================================

@router.get(
    "/stats",
    response_model=CollaborationStatsResponse
)
def get_collaboration_stats(

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    collaborations = (
        db.query(Collaboration)
        .all()
    )

    active = 0
    completed = 0
    pending = 0
    cancelled = 0

    for collaboration in collaborations:

        status = str(
            collaboration.status or ""
        ).strip().lower()

        if status == "active":
            active += 1

        elif status == "completed":
            completed += 1

        elif status == "pending":
            pending += 1

        elif status == "cancelled":
            cancelled += 1

    return {

        "total_collaborations":
            len(collaborations),

        "active":
            active,

        "completed":
            completed,

        "pending":
            pending,

        "cancelled":
            cancelled
    }


# ============================================================
# GET ALL COLLABORATIONS
# ============================================================

@router.get(
    "/",
    response_model=list[CollaborationResponse]
)
def get_collaborations(

    search: str | None = Query(
        default=None
    ),

    collaboration_type: str | None = Query(
        default=None
    ),

    status: str | None = Query(
        default=None
    ),

    sort: str = Query(
        default="date_desc"
    ),

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    query = db.query(
        Collaboration
    )

    # --------------------------------------------------------
    # Collaboration type filter
    # --------------------------------------------------------

    if (
        collaboration_type
        and collaboration_type.lower() != "all"
    ):

        query = query.filter(
            Collaboration.collaboration_type
            == collaboration_type
        )

    # --------------------------------------------------------
    # Status filter
    # --------------------------------------------------------

    if (
        status
        and status.lower() != "all"
    ):

        query = query.filter(
            Collaboration.status
            == status
        )

    # --------------------------------------------------------
    # Sorting
    # --------------------------------------------------------

    if sort == "date_asc":

        query = query.order_by(
            Collaboration.start_date
            .asc()
            .nullslast()
        )

    elif sort == "date_desc":

        query = query.order_by(
            Collaboration.start_date
            .desc()
            .nullslast(),
            Collaboration.id.desc()
        )

    elif sort == "id_asc":

        query = query.order_by(
            Collaboration.id.asc()
        )

    elif sort == "id_desc":

        query = query.order_by(
            Collaboration.id.desc()
        )

    else:

        query = query.order_by(
            Collaboration.start_date
            .desc()
            .nullslast()
        )

    rows = query.all()

    results = []

    for collaboration in rows:

        result = build_collaboration_response(
            collaboration,
            db
        )

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        if search:

            search_text = search.strip().lower()

            searchable_values = [

                result["researcher_1_name"],

                result["researcher_2_name"],

                result["institution_1"],

                result["institution_2"],

                result["collaboration_type"],

                result["description"],

                result["status"]
            ]

            combined_text = " ".join(

                str(value or "")

                for value
                in searchable_values

            ).lower()

            if search_text not in combined_text:
                continue

        results.append(result)

    return results


# ============================================================
# GET ONE COLLABORATION
# ============================================================

@router.get(
    "/{collaboration_id}",
    response_model=CollaborationResponse
)
def get_collaboration(

    collaboration_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    collaboration = (
        db.query(Collaboration)
        .filter(
            Collaboration.id
            == collaboration_id
        )
        .first()
    )

    if not collaboration:

        raise HTTPException(
            status_code=404,
            detail="Collaboration not found."
        )

    return build_collaboration_response(
        collaboration,
        db
    )


# ============================================================
# CREATE COLLABORATION
# ============================================================

@router.post(
    "/",
    response_model=CollaborationResponse,
    status_code=201
)
def create_collaboration(

    collaboration_data: CollaborationCreate,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    researcher_1_id = (
        collaboration_data.researcher_id_1
    )

    researcher_2_id = (
        collaboration_data.researcher_id_2
    )

    # --------------------------------------------------------
    # Prevent self collaboration
    # --------------------------------------------------------

    if researcher_1_id == researcher_2_id:

        raise HTTPException(
            status_code=400,
            detail=(
                "A researcher cannot "
                "collaborate with themselves."
            )
        )

    # --------------------------------------------------------
    # Check researcher 1
    # --------------------------------------------------------

    researcher_1 = get_researcher(
        db,
        researcher_1_id
    )

    if not researcher_1:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Researcher "
                f"{researcher_1_id} not found."
            )
        )

    # --------------------------------------------------------
    # Check researcher 2
    # --------------------------------------------------------

    researcher_2 = get_researcher(
        db,
        researcher_2_id
    )

    if not researcher_2:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Researcher "
                f"{researcher_2_id} not found."
            )
        )

    # --------------------------------------------------------
    # Check duplicate pair
    # --------------------------------------------------------

    existing = (

        db.query(Collaboration)

        .filter(

            (
                (
                    Collaboration.researcher_id_1
                    == researcher_1_id
                )

                &

                (
                    Collaboration.researcher_id_2
                    == researcher_2_id
                )
            )

            |

            (
                (
                    Collaboration.researcher_id_1
                    == researcher_2_id
                )

                &

                (
                    Collaboration.researcher_id_2
                    == researcher_1_id
                )
            )
        )

        .first()
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail=(
                "This researcher pair "
                "already has a collaboration record."
            )
        )

    institution_1 = get_or_create_institution(
        db,
        collaboration_data.institution_1_name,
    )
    institution_2 = get_or_create_institution(
        db,
        collaboration_data.institution_2_name,
    )

    if institution_1:
        researcher_1.institution_id = institution_1.id
    if institution_2:
        researcher_2.institution_id = institution_2.id

    # --------------------------------------------------------
    # Create collaboration
    # --------------------------------------------------------

    collaboration = Collaboration(

        researcher_id_1=
            researcher_1_id,

        researcher_id_2=
            researcher_2_id,

        collaboration_type=
            collaboration_data.collaboration_type,

        description=
            collaboration_data.description,

        start_date=
            collaboration_data.start_date,

        end_date=
            collaboration_data.end_date,

        status=
            collaboration_data.status or "Pending"
    )

    db.add(
        collaboration
    )

    db.commit()

    db.refresh(
        collaboration
    )

    return build_collaboration_response(
        collaboration,
        db
    )


# ============================================================
# UPDATE COLLABORATION
# ============================================================

@router.put(
    "/{collaboration_id}",
    response_model=CollaborationResponse
)
def update_collaboration(

    collaboration_id: int,

    collaboration_data: CollaborationUpdate,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    collaboration = (
        db.query(Collaboration)
        .filter(
            Collaboration.id
            == collaboration_id
        )
        .first()
    )

    if not collaboration:

        raise HTTPException(
            status_code=404,
            detail="Collaboration not found."
        )

    values = (
        collaboration_data
        .model_dump(
            exclude_unset=True
        )
    )

    researcher_1_id = values.get(
        "researcher_id_1",
        collaboration.researcher_id_1
    )

    researcher_2_id = values.get(
        "researcher_id_2",
        collaboration.researcher_id_2
    )

    # --------------------------------------------------------
    # Prevent self collaboration
    # --------------------------------------------------------

    if researcher_1_id == researcher_2_id:

        raise HTTPException(
            status_code=400,
            detail=(
                "A researcher cannot "
                "collaborate with themselves."
            )
        )

    # --------------------------------------------------------
    # Validate researchers
    # --------------------------------------------------------

    if not get_researcher(
        db,
        researcher_1_id
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                f"Researcher "
                f"{researcher_1_id} not found."
            )
        )

    if not get_researcher(
        db,
        researcher_2_id
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                f"Researcher "
                f"{researcher_2_id} not found."
            )
        )

    # --------------------------------------------------------
    # Apply changes
    # --------------------------------------------------------

    for key, value in values.items():

        setattr(
            collaboration,
            key,
            value
        )

    db.commit()

    db.refresh(
        collaboration
    )

    return build_collaboration_response(
        collaboration,
        db
    )


# ============================================================
# DELETE COLLABORATION
# ============================================================

@router.delete(
    "/{collaboration_id}",
    status_code=204
)
def delete_collaboration(

    collaboration_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    collaboration = (
        db.query(Collaboration)
        .filter(
            Collaboration.id
            == collaboration_id
        )
        .first()
    )

    if not collaboration:

        raise HTTPException(
            status_code=404,
            detail="Collaboration not found."
        )

    db.delete(
        collaboration
    )

    db.commit()

    return None


def get_or_create_institution(db: Session, name: str | None):
    institution_name = (name or "").strip()
    if not institution_name:
        return None

    institution = db.query(Institution).filter(
        func.lower(Institution.name) == institution_name.lower()
    ).first()
    if institution:
        return institution

    institution = Institution(name=institution_name)
    db.add(institution)
    db.flush()
    return institution