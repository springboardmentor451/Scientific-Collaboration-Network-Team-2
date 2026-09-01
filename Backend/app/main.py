from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import Base, engine
from app.core.migrations import apply_compatibility_migrations
from app.models.user import User
from app.models.researcher import Researcher
from app.models.publication import Publication, publication_authors
from app.models.collaboration import CollaborationRequest
from app.models.audit import AuditLog
from app.models.institution import Institution
from app.models.conference import Conference
from app.models.citation import Citation
from app.models.project import Project, project_researchers
from app.models.notification import Notification
from app.models.review import Review
from app.models.generated_report import GeneratedReport
from app.Routes.user import router as user_router
from app.Routes.researcher import router as researcher_router
from app.Routes.publication import router as publication_router
from app.Routes.collaboration import router as collaboration_router
from app.Routes.dashboard import router as dashboard_router
from app.Routes.admin import router as admin_router
from app.Routes.audit import router as audit_router
from app.Routes.institution import router as institution_router
from app.Routes.conference import router as conference_router
from app.Routes.report import router as report_router
from app.Routes.citation import router as citation_router
from app.Routes.project import router as project_router
from app.Routes.notification import router as notification_router
from app.Routes.network import router as network_router
from app.Routes.review import router as review_router
from app.Routes.assistant import router as assistant_router

Base.metadata.create_all(bind=engine)
apply_compatibility_migrations(engine)

app = FastAPI(title="Scientific Collaboration Network Analyzer")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request, exc: RequestValidationError):
    """Keep Pydantic validation errors clear and renderable by the React UI."""
    first_error = exc.errors()[0]
    field_name = str(first_error.get("loc", ("field",))[-1]).replace("_", " ").title()
    message = first_error.get("msg", "Invalid request.")

    if first_error.get("type") == "missing":
        message = f"{field_name} is required."
    elif message.startswith("Value error, "):
        message = message.removeprefix("Value error, ")

    return JSONResponse(status_code=422, content={"detail": message})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(researcher_router)
app.include_router(publication_router)
app.include_router(collaboration_router)
app.include_router(dashboard_router)
app.include_router(admin_router)
app.include_router(audit_router)
app.include_router(institution_router)
app.include_router(conference_router)
app.include_router(report_router)
app.include_router(citation_router)
app.include_router(project_router)
app.include_router(notification_router)
app.include_router(network_router)
app.include_router(review_router)
app.include_router(assistant_router)


@app.get("/")
def home():
    return {"message": "Backend is working"}
