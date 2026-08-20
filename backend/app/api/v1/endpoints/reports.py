from io import BytesIO
from typing import Any, Dict, List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from backend.app.db.session import get_db
from backend.app.models.users import User
from backend.app.models.researchers import Researcher
from backend.app.models.publications import Publication
from backend.app.models.projects import Project
from backend.app.models.collaborations import Collaboration
from backend.app.models.institutions import Institution
from backend.app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/reports/publications")
def get_publication_report_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Get metadata statistics grouped by publication type."""
    data = db.query(
        Publication.type,
        Publication.status,
        func.count(Publication.id)
    ).group_by(Publication.type, Publication.status).all()
    
    return [
        {"type": r[0].value, "status": r[1].value, "count": r[2]}
        for r in data
    ]

# We need to import 'func' to perform the group_by query above.
from sqlalchemy import func

@router.get("/reports/collaborations")
def get_collaboration_report_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Get count of collaborations grouped by type."""
    data = db.query(
        Collaboration.collaboration_type,
        func.count(Collaboration.id)
    ).group_by(Collaboration.collaboration_type).all()
    
    return [
        {"collaboration_type": r[0].value, "count": r[1]}
        for r in data
    ]

@router.get("/reports/institutions")
def get_institution_report_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Get count of researchers per institution."""
    data = db.query(
        Institution.name,
        func.count(Researcher.id)
    ).join(Researcher, isouter=True).group_by(Institution.name).all()
    
    return [
        {"institution_name": r[0], "researcher_count": r[1]}
        for r in data
    ]

@router.get("/reports/export")
def export_reports(
    format: str = Query(..., pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    institution_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export research database tables with filters applied.
    """
    from backend.app.models.publication_authors import PublicationAuthor
    
    res_query = db.query(Researcher)
    pub_query = db.query(Publication)
    proj_query = db.query(Project)
    collab_query = db.query(Collaboration)

    if institution_id:
        res_query = res_query.filter(Researcher.institution_id == institution_id)
        # Filter publications written by researchers of this institution
        inst_researchers = db.query(Researcher.id).filter(Researcher.institution_id == institution_id).subquery()
        pub_ids = db.query(PublicationAuthor.publication_id).filter(PublicationAuthor.researcher_id.in_(inst_researchers)).subquery()
        pub_query = pub_query.filter(Publication.id.in_(pub_ids))
        proj_query = proj_query.filter(Project.institution_id == institution_id)
        collab_query = collab_query.filter((Collaboration.institution_id_1 == institution_id) | (Collaboration.institution_id_2 == institution_id))

    if start_date:
        pub_query = pub_query.filter(Publication.publication_date >= start_date)
        proj_query = proj_query.filter(Project.start_date >= start_date)
    if end_date:
        pub_query = pub_query.filter(Publication.publication_date <= end_date)
        proj_query = proj_query.filter(Project.end_date <= end_date)

    researchers = res_query.all()
    publications = pub_query.all()
    projects = proj_query.all()
    collaborations = collab_query.all()

    if format == "xlsx":
        output = BytesIO()
        wb = Workbook()
        
        # 1. Researchers sheet
        ws_res = wb.active
        ws_res.title = "Researchers"
        ws_res.append(["ID", "Name", "ORCID ID", "Institution", "Department", "Interests", "Skills"])
        for r in researchers:
            inst = r.institution.name if r.institution else "None"
            dept = r.department.name if r.department else "None"
            interests = ", ".join(r.research_interests or [])
            skills = ", ".join(r.skills or [])
            ws_res.append([r.id, r.full_name, r.orcid_id or "", inst, dept, interests, skills])

        # 2. Publications sheet
        ws_pub = wb.create_sheet(title="Publications")
        ws_pub.append(["ID", "Title", "Type", "Status", "DOI", "Venue", "Publication Date", "Creator ID"])
        for p in publications:
            ws_pub.append([p.id, p.title, p.type.value, p.status.value, p.doi or "", p.venue or "", str(p.publication_date or ""), p.created_by or ""])

        # 3. Projects sheet
        ws_proj = wb.create_sheet(title="Projects")
        ws_proj.append(["ID", "Title", "Funding Source", "Funding Amount", "Status", "Start Date", "End Date"])
        for pr in projects:
            ws_proj.append([pr.id, pr.title, pr.funding_source or "", float(pr.funding_amount or 0), pr.status.value, str(pr.start_date or ""), str(pr.end_date or "")])

        # 4. Collaborations sheet
        ws_collab = wb.create_sheet(title="Collaborations")
        ws_collab.append(["ID", "Type", "Researcher 1", "Researcher 2", "Project ID", "Publication ID", "Created At"])
        for c in collaborations:
            r1 = c.researcher_1.full_name if c.researcher_1 else ""
            r2 = c.researcher_2.full_name if c.researcher_2 else ""
            ws_collab.append([c.id, c.collaboration_type.value, r1, r2, c.project_id or "", c.publication_id or "", str(c.created_at)])

        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=collaboration_report.xlsx"}
        )

    elif format == "pdf":
        output = BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=letter,
            rightMargin=36, leftMargin=36,
            topMargin=36, bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=colors.HexColor("#1A252C"),
            spaceAfter=15
        )
        h2_style = ParagraphStyle(
            name="H2Style",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=colors.HexColor("#2C3E50"),
            spaceBefore=15,
            spaceAfter=8
        )
        body_style = ParagraphStyle(
            name="BodyStyle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#34495E")
        )

        story = []
        
        # Title & Description
        story.append(Paragraph("Scientific Collaboration Network Report", title_style))
        story.append(Paragraph(f"Generated on {date.today().strftime('%B %d, %Y')}", body_style))
        story.append(Spacer(1, 15))
        
        # Metrics Table
        story.append(Paragraph("System Aggregates", h2_style))
        metrics_data = [
            ["Metric", "Count"],
            ["Total Researchers", str(len(researchers))],
            ["Total Publications", str(len(publications))],
            ["Total Funding Projects", str(len(projects))],
            ["Total Collaborations", str(len(collaborations))]
        ]
        t_metrics = Table(metrics_data, colWidths=[200, 100])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(t_metrics)
        story.append(Spacer(1, 15))
        
        # Recent Publications Table
        story.append(Paragraph("Recent Publications", h2_style))
        pub_headers = [["ID", "Title", "Venue", "Status", "Date"]]
        for p in publications[:5]:
            # Limit title text for rendering
            title_text = p.title[:50] + "..." if len(p.title) > 50 else p.title
            pub_headers.append([
                str(p.id),
                title_text,
                p.venue or "None",
                p.status.value,
                str(p.publication_date or "")
            ])
        
        t_pub = Table(pub_headers, colWidths=[30, 240, 110, 70, 70])
        t_pub.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#16A085")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ]))
        story.append(t_pub)
        
        doc.build(story)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=collaboration_report.pdf"}
        )
