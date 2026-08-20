from backend.app.db.base_class import Base
from backend.app.models.users import User, UserRole
from backend.app.models.institutions import Institution
from backend.app.models.departments import Department
from backend.app.models.researchers import Researcher
from backend.app.models.publications import Publication, PublicationType, PublicationStatus
from backend.app.models.publication_authors import PublicationAuthor
from backend.app.models.projects import Project, ProjectStatus
from backend.app.models.project_assignments import ProjectAssignment
from backend.app.models.collaborations import Collaboration, CollaborationType
from backend.app.models.conferences import Conference
from backend.app.models.conference_participation import ConferenceParticipation, ParticipationRole
from backend.app.models.citations import Citation
from backend.app.models.references import Reference
from backend.app.models.audit_logs import AuditLog
from backend.app.models.notifications import Notification, NotificationChannel, NotificationStatus
