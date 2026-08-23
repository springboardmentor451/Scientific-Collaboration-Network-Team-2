import enum

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.db.database import Base


class ParticipationRole(str, enum.Enum):
    PRESENTER = "presenter"
    ATTENDEE = "attendee"
    ORGANIZER = "organizer"
    REVIEWER = "reviewer"


class Conference(Base):
    __tablename__ = "conferences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    website = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    participations = relationship(
        "ConferenceParticipation", back_populates="conference", cascade="all, delete-orphan"
    )


class ConferenceParticipation(Base):
    __tablename__ = "conference_participations"

    id = Column(Integer, primary_key=True, index=True)
    conference_id = Column(Integer, ForeignKey("conferences.id"), nullable=False)
    researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    # Optional link to the paper presented at this conference.
    publication_id = Column(Integer, ForeignKey("publications.id"), nullable=True)
    role = Column(Enum(ParticipationRole), default=ParticipationRole.ATTENDEE, nullable=False)
    presentation_title = Column(String, nullable=True)

    conference = relationship("Conference", back_populates="participations")
    researcher = relationship("Researcher")
    publication = relationship("Publication")
