from io import BytesIO
from fastapi import APIRouter,Depends,HTTPException,Response
from sqlalchemy import func,or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.publication import Publication
from app.models.collaboration import CollaborationRequest
from app.models.conference import Conference,conference_participants
from app.models.institution import Institution
from app.models.generated_report import GeneratedReport
from app.models.project import Project
from app.Crud.audit import log_action
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

router=APIRouter(prefix="/reports",tags=["Reports"])
@router.get("/my")
def my_report(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    publications=db.query(Publication).filter(Publication.owner_id==user.id)
    trends=[{"year":year,"count":count} for year,count in publications.with_entities(Publication.publication_year,func.count(Publication.id)).group_by(Publication.publication_year).order_by(Publication.publication_year).all()]
    requests=db.query(CollaborationRequest).filter(or_(CollaborationRequest.requester_id==user.id,CollaborationRequest.recipient_id==user.id))
    return{"user":{"full_name":user.full_name,"role":user.role,"institution":user.institution,"department":user.department},"publication_count":publications.count(),"collaboration_count":requests.filter(CollaborationRequest.status=="Accepted").count(),"pending_received":requests.filter(CollaborationRequest.recipient_id==user.id,CollaborationRequest.status=="Pending").count(),"pending_sent":requests.filter(CollaborationRequest.requester_id==user.id,CollaborationRequest.status=="Pending").count(),"conference_registrations":db.query(conference_participants).filter(conference_participants.c.user_id==user.id).count(),"interests":user.research_interests or [],"skills":user.skills or [],"publication_trends":trends}

def institution_payload(db, institution):
    users = db.query(User).filter(User.institution_id == institution.id)
    publications = db.query(Publication).join(User, Publication.owner_id == User.id).filter(User.institution_id == institution.id)
    projects = db.query(Project).join(User, Project.owner_id == User.id).filter(User.institution_id == institution.id)
    return {"institution": institution.name, "researchers": users.count(), "publications": publications.count(), "projects": projects.count(), "publication_years": [{"year": year, "count": count} for year, count in publications.with_entities(Publication.publication_year, func.count(Publication.id)).group_by(Publication.publication_year).order_by(Publication.publication_year).all()]}

@router.post("/generated/{institution_id}")
def generate_institution_report(institution_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution: raise HTTPException(404, "Institution not found.")
    if user.role not in {"Admin", "System Admin", "Institution Admin"}: raise HTTPException(403, "You cannot generate institution reports.")
    if user.role == "Institution Admin" and user.institution_id != institution.id: raise HTTPException(403, "You can only report on your own institution.")
    item = GeneratedReport(created_by_id=user.id, institution_id=institution.id, report_type="Institution", payload=institution_payload(db, institution))
    db.add(item); db.flush(); log_action(db, "REPORT_GENERATED", user.id, "GeneratedReport", item.id, institution.name); db.commit(); db.refresh(item)
    return {"id":item.id,"report_type":item.report_type,"institution_id":item.institution_id,"payload":item.payload,"created_at":item.created_at}

@router.get("/generated")
def generated_reports(db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    query = db.query(GeneratedReport)
    if user.role not in {"Admin", "System Admin"}: query = query.filter(GeneratedReport.created_by_id == user.id)
    return [{"id":item.id,"report_type":item.report_type,"institution_id":item.institution_id,"payload":item.payload,"created_at":item.created_at,"created_by":item.created_by.full_name} for item in query.order_by(GeneratedReport.created_at.desc()).all()]

@router.get("/generated/{report_id}")
def generated_report(report_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    item=db.query(GeneratedReport).filter(GeneratedReport.id==report_id).first()
    if not item: raise HTTPException(404,"Report not found.")
    if item.created_by_id != user.id and user.role not in {"Admin","System Admin"}: raise HTTPException(403,"You cannot view this report.")
    return {"id":item.id,"report_type":item.report_type,"institution_id":item.institution_id,"payload":item.payload,"created_at":item.created_at}

@router.delete("/generated/{report_id}",status_code=204)
def delete_generated_report(report_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=db.query(GeneratedReport).filter(GeneratedReport.id==report_id).first()
    if not item: raise HTTPException(404,"Report not found.")
    if item.created_by_id != user.id and user.role not in {"Admin","System Admin"}: raise HTTPException(403,"You cannot delete this report.")
    db.delete(item);db.commit();return Response(status_code=204)

def exportable_report(report_id, db, user):
    item=db.query(GeneratedReport).filter(GeneratedReport.id==report_id).first()
    if not item: raise HTTPException(404,"Report not found.")
    if item.created_by_id != user.id and user.role not in {"Admin","System Admin"}: raise HTTPException(403,"You cannot export this report.")
    return item

@router.get("/generated/{report_id}/export.xlsx")
def export_excel(report_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=exportable_report(report_id,db,user); workbook=Workbook(); sheet=workbook.active; sheet.title="SCNA Report"; sheet.append(["Metric","Value"])
    for key,value in item.payload.items():
        if isinstance(value,(list,dict)): value=str(value)
        sheet.append([key.replace("_"," ").title(),value])
    output=BytesIO();workbook.save(output)
    return Response(output.getvalue(),media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":f'attachment; filename="scna-report-{item.id}.xlsx"'})

@router.get("/generated/{report_id}/export.pdf")
def export_pdf(report_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=exportable_report(report_id,db,user);output=BytesIO();pdf=canvas.Canvas(output,pagesize=A4);text=pdf.beginText(48,790);text.setFont("Helvetica",12);text.textLine(f"SCNA {item.report_type} Report")
    for key,value in item.payload.items():
        if text.getY() < 60: pdf.drawText(text);pdf.showPage();text=pdf.beginText(48,790);text.setFont("Helvetica",10)
        text.textLine(f"{key.replace('_',' ').title()}: {value}")
    pdf.drawText(text);pdf.save()
    return Response(output.getvalue(),media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="scna-report-{item.id}.pdf"'})
