from fastapi import APIRouter,Depends,HTTPException,Query,Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user,require_admin
from app.models.user import User
from app.models.institution import Institution
from app.models.researcher import Researcher
from app.models.publication import Publication
from app.models.project import Project
from app.Schemas.institution import InstitutionCreate,InstitutionResponse,InstitutionUpdate
from app.Crud.audit import log_action

router=APIRouter(prefix="/institutions",tags=["Institutions"])
def result(item,db):
    data={key:getattr(item,key) for key in ["id","name","short_name","location","description","research_areas","website","source","source_url"]};data["researcher_count"]=db.query(Researcher).filter(Researcher.institution_id==item.id).count();data["publication_count"]=db.query(Publication).join(User,Publication.owner_id==User.id).filter(User.institution_id==item.id).count();return data
@router.get("",response_model=list[InstitutionResponse])
def list_institutions(search:str|None=Query(default=None),skip:int=Query(default=0,ge=0),limit:int=Query(default=100,ge=1,le=200),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    query=db.query(Institution)
    if user.role == "Institution Admin":
        if not user.institution_id: raise HTTPException(403,"Your account is not assigned to an institution.")
        query=query.filter(Institution.id==user.institution_id)
    if search: query=query.filter(or_(Institution.name.ilike(f"%{search}%"),Institution.location.ilike(f"%{search}%")))
    return[result(item,db) for item in query.order_by(Institution.name).offset(skip).limit(limit).all()]
@router.get("/{item_id}",response_model=InstitutionResponse)
def get_institution(item_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=db.query(Institution).filter(Institution.id==item_id).first()
    if not item:raise HTTPException(404,"Institution not found.")
    if user.role == "Institution Admin" and user.institution_id != item.id: raise HTTPException(403,"You can only view your institution.")
    return result(item,db)
@router.get("/{item_id}/report")
def institution_report(item_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=db.query(Institution).filter(Institution.id==item_id).first()
    if not item:raise HTTPException(404,"Institution not found.")
    if user.role == "Institution Admin" and user.institution_id != item.id: raise HTTPException(403,"You can only view your institution report.")
    publications=db.query(Publication).join(User,Publication.owner_id==User.id).filter(User.institution_id==item.id)
    return {**result(item,db),"project_count":db.query(Project).join(User,Project.owner_id==User.id).filter(User.institution_id==item.id).count(),"publication_trends":[{"year":year,"count":count} for year,count in publications.with_entities(Publication.publication_year,func.count(Publication.id)).group_by(Publication.publication_year).order_by(Publication.publication_year).all()]}
@router.post("",response_model=InstitutionResponse,status_code=201)
def create(data:InstitutionCreate,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    if db.query(Institution).filter(Institution.name==data.name).first():raise HTTPException(400,"Institution already exists.")
    item=Institution(**data.model_dump());db.add(item);db.flush();db.query(User).filter(func.lower(User.institution)==item.name.lower()).update({User.institution_id:item.id},synchronize_session=False);db.query(Researcher).filter(func.lower(Researcher.institution)==item.name.lower()).update({Researcher.institution_id:item.id},synchronize_session=False);log_action(db,"INSTITUTION_CREATED",admin.id,"Institution",item.id,item.name);db.commit();db.refresh(item);return result(item,db)
@router.put("/{item_id}",response_model=InstitutionResponse)
def update(item_id:int,data:InstitutionUpdate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=db.query(Institution).filter(Institution.id==item_id).first()
    if not item:raise HTTPException(404,"Institution not found.")
    if user.role not in {"Admin","System Admin","Institution Admin"}: raise HTTPException(403,"Administrator access required.")
    if user.role == "Institution Admin" and user.institution_id != item.id: raise HTTPException(403,"You can only update your institution.")
    for field,value in data.model_dump(exclude_unset=True).items():setattr(item,field,value)
    db.commit();db.refresh(item);return result(item,db)
@router.delete("/{item_id}",status_code=204)
def delete(item_id:int,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    item=db.query(Institution).filter(Institution.id==item_id).first()
    if not item:raise HTTPException(404,"Institution not found.")
    log_action(db,"INSTITUTION_DELETED",admin.id,"Institution",item.id,item.name);db.delete(item);db.commit();return Response(status_code=204)
