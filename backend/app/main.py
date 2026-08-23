from fastapi import FastAPI

from app.db.database import Base, engine
from app.models.researcher import Researcher
from app.models.institution import Institution
from app.models.publication import Publication
from app.models.user import User
from app.models.project import ResearchProject
from app.models.conference import Conference, ConferenceParticipation
from app.models.citation import Citation
from app.models.audit import AuditLog
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.researcher import router as researcher_router
from app.api.institution import institution_router
from app.api.publication import router as publication_router
from app.api.project import router as project_router, collaboration_router
from app.api.conference import router as conference_router
from app.api.citation import router as citation_router
from app.api.report import router as report_router
from app.api.audit import router as audit_router
from app.middleware.audit_middleware import AuditLogMiddleware


app = FastAPI()

app.add_middleware(AuditLogMiddleware)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(researcher_router)
app.include_router(institution_router)
app.include_router(publication_router)
app.include_router(project_router)
app.include_router(collaboration_router)
app.include_router(conference_router)
app.include_router(citation_router)
app.include_router(report_router)
app.include_router(audit_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Scientific Collaboration Network Analyzer"
    }