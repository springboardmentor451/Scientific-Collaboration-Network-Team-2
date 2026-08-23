from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.report import (
    AdminDashboard,
    CollaborationReport,
    InstitutionDashboard,
    InstitutionReport,
    PublicationReport,
    ResearcherDashboard,
)
from app.services import report as report_service

router = APIRouter(tags=["Reports & Dashboards"])


@router.get("/reports/publications", response_model=PublicationReport)
def read_publication_report(db: Session = Depends(get_db)):
    return report_service.publication_report(db)


@router.get("/reports/institutions", response_model=InstitutionReport)
def read_institution_report(db: Session = Depends(get_db)):
    return report_service.institution_report(db)


@router.get("/reports/collaborations", response_model=CollaborationReport)
def read_collaboration_report(db: Session = Depends(get_db)):
    return report_service.collaboration_report(db)


@router.get("/reports/publications/export")
def export_publications(db: Session = Depends(get_db)):
    from app.utils.excel_export import publications_to_excel

    buffer = publications_to_excel(db)
    headers = {"Content-Disposition": "attachment; filename=publications_report.xlsx"}
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/dashboard/researcher/{researcher_id}", response_model=ResearcherDashboard)
def read_researcher_dashboard(researcher_id: int, db: Session = Depends(get_db)):
    try:
        return report_service.researcher_dashboard(db, researcher_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/dashboard/institution/{institution_id}", response_model=InstitutionDashboard)
def read_institution_dashboard(institution_id: int, db: Session = Depends(get_db)):
    try:
        return report_service.institution_dashboard(db, institution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/dashboard/admin", response_model=AdminDashboard)
def read_admin_dashboard(db: Session = Depends(get_db)):
    return report_service.admin_dashboard(db)
