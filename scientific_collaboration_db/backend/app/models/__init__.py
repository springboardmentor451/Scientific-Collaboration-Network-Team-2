"""
Import every model here so:
  1. `Base.metadata` is fully populated for Alembic autogenerate.
  2. Other modules can do `from app.models import User, Publication, ...`.
"""
from app.database import Base  # noqa: F401

# from app.models.user import User, UserRole  # noqa: F401

from app.models.user import User, UserRole  # noqa: F401
from app.models.login_otp import LoginOtp  # noqa: F401
from app.models.institution import Institution  # noqa: F401
from app.models.tag import Tag, TagCategory, researcher_tags  # noqa: F401
from app.models.researcher import Researcher  # noqa: F401
from app.models.publication import (  # noqa: F401
    Publication,
    PublicationType,
    PublicationStatus,
    PublicationAuthor,
)
from app.models.project import Project, ProjectStatus, ProjectMember  # noqa: F401
from app.models.collaboration import Collaboration, CollaborationType  # noqa: F401
from app.models.conference import (  # noqa: F401
    Conference,
    ConferenceParticipation,
    ParticipationRole,
)
from app.models.citation import Citation  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401

__all__ = [
    "Base",
    # "User",
    # "UserRole",
    "User",
    "UserRole",
    "LoginOtp",
    "Institution",
    "Tag",
    "TagCategory",
    "researcher_tags",
    "Researcher",
    "Publication",
    "PublicationType",
    "PublicationStatus",
    "PublicationAuthor",
    "Project",
    "ProjectStatus",
    "ProjectMember",
    "Collaboration",
    "CollaborationType",
    "Conference",
    "ConferenceParticipation",
    "ParticipationRole",
    "Citation",
    "AuditLog",
]
