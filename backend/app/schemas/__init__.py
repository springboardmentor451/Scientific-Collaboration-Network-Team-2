from backend.app.schemas.users import UserBase, UserCreate, UserUpdate, UserOut, Token, TokenPayload
from backend.app.schemas.institutions import InstitutionBase, InstitutionCreate, InstitutionUpdate, InstitutionOut
from backend.app.schemas.departments import DepartmentBase, DepartmentCreate, DepartmentUpdate, DepartmentOut
from backend.app.schemas.researchers import ResearcherBase, ResearcherCreate, ResearcherUpdate, ResearcherOut
from backend.app.schemas.publications import PublicationBase, PublicationCreate, PublicationUpdate, PublicationOut
from backend.app.schemas.publication_authors import PublicationAuthorBase, PublicationAuthorCreate, PublicationAuthorUpdate, PublicationAuthorOut
from backend.app.schemas.projects import ProjectBase, ProjectCreate, ProjectUpdate, ProjectOut
from backend.app.schemas.project_assignments import ProjectAssignmentBase, ProjectAssignmentCreate, ProjectAssignmentUpdate, ProjectAssignmentOut
from backend.app.schemas.collaborations import CollaborationBase, CollaborationCreate, CollaborationUpdate, CollaborationOut
from backend.app.schemas.conferences import ConferenceBase, ConferenceCreate, ConferenceUpdate, ConferenceOut
from backend.app.schemas.conference_participation import ConferenceParticipationBase, ConferenceParticipationCreate, ConferenceParticipationUpdate, ConferenceParticipationOut
from backend.app.schemas.citations import CitationBase, CitationCreate, CitationUpdate, CitationOut
from backend.app.schemas.references import ReferenceBase, ReferenceCreate, ReferenceUpdate, ReferenceOut
from backend.app.schemas.audit_logs import AuditLogBase, AuditLogCreate, AuditLogOut
from backend.app.schemas.notifications import NotificationBase, NotificationCreate, NotificationOut
