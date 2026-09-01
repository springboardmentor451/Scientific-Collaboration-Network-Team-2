from fastapi import APIRouter,Depends,HTTPException,Query,Response
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user,require_admin
from app.models.user import User
from app.models.conference import Conference
from app.models.researcher import Researcher
from app.Schemas.conference import ConferenceCreate,ConferenceResponse,ConferenceUpdate
from app.Crud.audit import log_action

router=APIRouter(prefix="/conferences",tags=["Conferences"])
def result(item,user):
    data={key:getattr(item,key) for key in ["id","title","topic","description","location","starts_at","ends_at","registration_url","is_open"]};data["participant_count"]=len(item.participants);data["is_registered"]=any(person.id==user.id for person in item.participants);return data
@router.get("",response_model=list[ConferenceResponse])
def list_conferences(search:str|None=Query(default=None),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    query=db.query(Conference)
    if search:query=query.filter(or_(Conference.title.ilike(f"%{search}%"),Conference.topic.ilike(f"%{search}%"),Conference.location.ilike(f"%{search}%")))
    return[result(item,user) for item in query.order_by(Conference.starts_at).all()]
@router.get("/{item_id}",response_model=ConferenceResponse)
def get_conference(item_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=db.query(Conference).filter(Conference.id==item_id).first()
    if not item:raise HTTPException(404,"Conference not found.")
    return result(item,user)
@router.post("",response_model=ConferenceResponse,status_code=201)
def create(data:ConferenceCreate,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    item=Conference(**data.model_dump());db.add(item);db.flush();log_action(db,"CONFERENCE_CREATED",admin.id,"Conference",item.id,item.title);db.commit();db.refresh(item);return result(item,admin)
@router.put("/{item_id}",response_model=ConferenceResponse)
def update(item_id:int,data:ConferenceUpdate,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    item=db.query(Conference).filter(Conference.id==item_id).first()
    if not item:raise HTTPException(404,"Conference not found.")
    for field,value in data.model_dump(exclude_unset=True).items():setattr(item,field,value)
    db.commit();db.refresh(item);return result(item,admin)
@router.delete("/{item_id}",status_code=204)
def delete(item_id:int,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    item=db.query(Conference).filter(Conference.id==item_id).first()
    if not item:raise HTTPException(404,"Conference not found.")
    log_action(db,"CONFERENCE_DELETED",admin.id,"Conference",item.id,item.title);db.delete(item);db.commit();return Response(status_code=204)
@router.post("/{item_id}/register",response_model=ConferenceResponse)
def register(item_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=db.query(Conference).filter(Conference.id==item_id).first()
    if not item:raise HTTPException(404,"Conference not found.")
    if not item.is_open:raise HTTPException(400,"Conference registration is closed.")
    if user not in item.participants:
        item.participants.append(user);log_action(db,"CONFERENCE_REGISTERED",user.id,"Conference",item.id,item.title);db.commit();db.refresh(item)
    return result(item,user)
@router.delete("/{item_id}/register",response_model=ConferenceResponse)
def unregister(item_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=db.query(Conference).filter(Conference.id==item_id).first()
    if not item:raise HTTPException(404,"Conference not found.")
    if user in item.participants:
        item.participants.remove(user);log_action(db,"CONFERENCE_UNREGISTERED",user.id,"Conference",item.id,item.title);db.commit();db.refresh(item)
    return result(item,user)

@router.get("/{item_id}/participants")
def participants(item_id:int,db:Session=Depends(get_db),_user:User=Depends(get_current_user)):
    item=db.query(Conference).filter(Conference.id==item_id).first()
    if not item: raise HTTPException(404,"Conference not found.")
    return [{"id":person.id,"full_name":person.full_name,"email":person.email,"institution":person.institution,"department":person.department,"role":person.role} for person in item.participants]

@router.get("/researcher/{researcher_id}",response_model=list[ConferenceResponse])
def researcher_history(researcher_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    researcher=db.query(Researcher).filter(Researcher.id==researcher_id).first()
    if not researcher or not researcher.user_id: raise HTTPException(404,"Researcher not found.")
    if user.role == "Institution Admin" and researcher.institution_id != user.institution_id: raise HTTPException(403,"You can only view participation from your institution.")
    if researcher.user_id != user.id and user.role not in {"Admin","System Admin","Institution Admin"}: raise HTTPException(403,"You cannot view this participation history.")
    items=db.query(Conference).filter(Conference.participants.any(id=researcher.user_id)).order_by(Conference.starts_at.desc()).all()
    return [result(item,user) for item in items]
