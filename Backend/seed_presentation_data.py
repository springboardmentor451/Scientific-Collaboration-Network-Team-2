"""Create linked SCNA presentation accounts and records in the configured PostgreSQL database.

These are clearly labelled presentation identities, not real people's personal accounts.
Run only against the intended Supabase project.
"""
from datetime import datetime, timezone
from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.institution import Institution
from app.models.researcher import Researcher
from app.models.publication import Publication
from app.models.collaboration import CollaborationRequest
from app.models.conference import Conference
from app.models.citation import Citation
from app.models.project import Project
from app.models.conference import conference_participants
from app.Utils.auth import hash_password

Base.metadata.create_all(bind=engine)

ACCOUNTS = [
    ("admin@scna.demo", "SCNA Presentation Admin", "System Admin", "SCNA_Admin@2026"),
    ("asha.researcher@scna.demo", "Asha Mehta", "Researcher", "Asha_Research@2026"),
    ("rohan.faculty@scna.demo", "Rohan Kulkarni", "Institution Admin", "Rohan_Faculty@2026"),
    ("meera.student@scna.demo", "Meera Shah", "Reviewer", "Meera_Student@2026"),
    ("kabir.collaborator@scna.demo", "Kabir Joshi", "Publisher", "Kabir_Collab@2026"),
]

def account(db, email, name, role, password):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
    user.full_name, user.role, user.password, user.approval_status, user.is_active = name, role, hash_password(password), "Approved", True
    return user

db = SessionLocal()
try:
    users = {email: account(db, email, name, role, password) for email, name, role, password in ACCOUNTS}
    db.flush()

    institutions = {}
    for name, short_name, location, areas in [
        ("National Institute of Technology Pune", "NITP", "Pune, India", ["Artificial Intelligence", "Network Science"]),
        ("Western Research University", "WRU", "Mumbai, India", ["Healthcare Analytics", "Data Engineering"]),
    ]:
        item = db.query(Institution).filter(Institution.name == name).first() or Institution(name=name, short_name=short_name, location=location, research_areas=areas, description=f"Research institution focused on {', '.join(areas)}.")
        db.add(item) if item.id is None else None
        institutions[short_name] = item
    db.flush()
    users["asha.researcher@scna.demo"].institution = institutions["NITP"].name; users["asha.researcher@scna.demo"].institution_id = institutions["NITP"].id; users["asha.researcher@scna.demo"].department = "Computer Science"; users["asha.researcher@scna.demo"].research_interests = ["Artificial Intelligence", "Network Science"]; users["asha.researcher@scna.demo"].skills = ["Python", "Graph Analytics"]
    users["rohan.faculty@scna.demo"].institution = institutions["WRU"].name; users["rohan.faculty@scna.demo"].institution_id = institutions["WRU"].id; users["rohan.faculty@scna.demo"].department = "Information Systems"; users["rohan.faculty@scna.demo"].research_interests = ["Healthcare Analytics"]; users["rohan.faculty@scna.demo"].skills = ["SQL", "Machine Learning"]
    db.flush()

    researcher_data = [
        (users["asha.researcher@scna.demo"], institutions["NITP"], "Artificial Intelligence", ["Python", "Graph Analytics"]),
        (users["rohan.faculty@scna.demo"], institutions["WRU"], "Healthcare Analytics", ["SQL", "Machine Learning"]),
    ]
    researchers = {}
    for user, institution, field, skills in researcher_data:
        item = db.query(Researcher).filter(Researcher.user_id == user.id).first() or Researcher(user_id=user.id, name=user.full_name, email=user.email, department=user.department, institution=institution.name, institution_id=institution.id, field=field, skills=skills, research_interests=user.research_interests)
        db.add(item) if item.id is None else None
        researchers[user.email] = item
    db.flush()

    pubs = []
    for user, title, area, venue, year in [
        (users["asha.researcher@scna.demo"], "Graph-Based Discovery of Research Collaborators", "Network Science", "SCNA Journal", 2025),
        (users["rohan.faculty@scna.demo"], "Privacy-Aware Healthcare Research Networks", "Healthcare Analytics", "Data Systems Conference", 2026),
    ]:
        item = db.query(Publication).filter(Publication.owner_id == user.id, Publication.title == title).first() or Publication(owner_id=user.id, title=title, authors=user.full_name, abstract=f"A presentation research record owned by {user.full_name}.", research_area=area, venue=venue, publication_year=year, publication_type="Journal Article")
        db.add(item) if item.id is None else None; pubs.append(item)
    db.flush()

    for user, title, area in [(users["asha.researcher@scna.demo"], "Cross-Institution Research Graph", "Network Science"), (users["rohan.faculty@scna.demo"], "Collaborative Health Data Project", "Healthcare Analytics"), (users["kabir.collaborator@scna.demo"], "Open Research Partnership", "Research Collaboration")]:
        if not db.query(Project).filter(Project.owner_id == user.id, Project.title == title).first(): db.add(Project(owner_id=user.id, title=title, description=f"Active project owned by {user.full_name} and managed through SCNA.", research_area=area, status="Active", start_date=datetime(2026, 1, 15, tzinfo=timezone.utc)))
    db.flush()

    if not db.query(CollaborationRequest).filter(CollaborationRequest.requester_id == users["asha.researcher@scna.demo"].id, CollaborationRequest.recipient_id == users["rohan.faculty@scna.demo"].id).first(): db.add(CollaborationRequest(requester_id=users["asha.researcher@scna.demo"].id, recipient_id=users["rohan.faculty@scna.demo"].id, message="Let us collaborate on cross-institution research networks.", status="Accepted"))
    db.flush()
    for pub in pubs:
        if not db.query(Citation).filter(Citation.owner_id == pub.owner_id, Citation.publication_id == pub.id).first(): db.add(Citation(owner_id=pub.owner_id, publication_id=pub.id, cited_title="SCNA Research Methods Reference", cited_authors="SCNA Presentation Research Group", cited_url="https://example.org/scna-reference", notes="Reference record created through the citation module."))

    conferences = []
    for title, topic, location, starts in [("SCNA Collaboration Summit 2026", "Scientific Network Collaboration", "Pune, India", datetime(2026, 11, 12, 9, tzinfo=timezone.utc)), ("Applied Healthcare Analytics Forum", "Healthcare Analytics", "Mumbai, India", datetime(2027, 2, 18, 10, tzinfo=timezone.utc))]:
        item = db.query(Conference).filter(Conference.title == title).first() or Conference(title=title, topic=topic, location=location, starts_at=starts, description=f"Presentation conference record for {topic}.", is_open=True)
        db.add(item) if item.id is None else None; conferences.append(item)
    db.flush()
    for conference, user in [(conferences[0], users["asha.researcher@scna.demo"]), (conferences[0], users["rohan.faculty@scna.demo"]), (conferences[1], users["kabir.collaborator@scna.demo"])]:
        if not db.execute(conference_participants.select().where(conference_participants.c.conference_id == conference.id, conference_participants.c.user_id == user.id)).first(): db.execute(conference_participants.insert().values(conference_id=conference.id, user_id=user.id))
    db.commit()
    print("Presentation dataset created in the configured Supabase database.")
    for email, name, role, password in ACCOUNTS: print(f"{role}: {name} | {email} | {password}")
finally:
    db.close()
