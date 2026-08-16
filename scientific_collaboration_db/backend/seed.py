"""
Populates the database with realistic sample data so the schema, relationships,
and API can be demonstrated immediately after migrating.

Usage:
    python seed.py            # adds sample data
    python seed.py --reset    # wipes all rows first, then reseeds
"""
import argparse
import random
import uuid
from datetime import date, timedelta

from faker import Faker
from passlib.hash import bcrypt

from app.database import Base, SessionLocal, engine
from app.models import (
    Citation,
    Collaboration,
    CollaborationType,
    Conference,
    ConferenceParticipation,
    Institution,
    ParticipationRole,
    Project,
    ProjectMember,
    ProjectStatus,
    Publication,
    PublicationAuthor,
    PublicationStatus,
    PublicationType,
    Researcher,
    Tag,
    TagCategory,
    User,
    UserRole,
)

fake = Faker()
Faker.seed(42)
random.seed(42)

INSTITUTION_TYPES = ["university", "research_institute", "government_lab", "publisher", "funding_organization"]
SKILLS = ["Machine Learning", "Data Engineering", "Bioinformatics", "Robotics", "Cryptography",
          "Materials Science", "Climate Modeling", "Statistics", "NLP", "Computer Vision"]
INTERESTS = ["Renewable Energy", "Genomics", "Quantum Computing", "Public Health", "Neuroscience",
             "Astrophysics", "Cybersecurity", "Sustainable Agriculture", "Urban Planning", "Ethics in AI"]


def reset_db():
    print("Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed(session):
    # --- Institutions ---
    institutions = []
    for _ in range(6):
        inst = Institution(
            name=f"{fake.city()} {random.choice(['University', 'Institute of Technology', 'Research Center'])}",
            country=fake.country(),
            address=fake.address(),
            website=fake.url(),
            institution_type=random.choice(INSTITUTION_TYPES),
        )
        institutions.append(inst)
    session.add_all(institutions)
    session.flush()

    # --- Tags (skills + interests) ---
    tags = [Tag(name=s, category=TagCategory.SKILL) for s in SKILLS]
    tags += [Tag(name=i, category=TagCategory.RESEARCH_INTEREST) for i in INTERESTS]
    session.add_all(tags)
    session.flush()
    skill_tags = [t for t in tags if t.category == TagCategory.SKILL]
    interest_tags = [t for t in tags if t.category == TagCategory.RESEARCH_INTEREST]

    # --- Users + Researchers ---
    roles = [UserRole.RESEARCHER] * 16 + [UserRole.INSTITUTION_ADMIN, UserRole.REVIEWER, UserRole.SYSTEM_ADMIN]
    researchers = []
    for i, role in enumerate(roles):
        user = User(
            email=fake.unique.email(),
            hashed_password=bcrypt.hash("Password123!"),
            role=role,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        session.flush()

        researcher = Researcher(
            user_id=user.id,
            institution_id=random.choice(institutions).id,
            full_name=fake.name(),
            department=random.choice(["Computer Science", "Physics", "Biology", "Chemistry", "Mathematics", "Engineering"]),
            academic_title=random.choice(["Professor", "Associate Professor", "Postdoctoral Researcher", "PhD Candidate", "Research Scientist"]),
            orcid_id=f"0000-000{random.randint(1,3)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            bio=fake.text(max_nb_chars=200),
        )
        researcher.tags = random.sample(skill_tags, k=2) + random.sample(interest_tags, k=2)
        researchers.append(researcher)
        session.add(researcher)
    session.flush()

    # --- Projects ---
    projects = []
    for _ in range(8):
        start = fake.date_between(start_date="-3y", end_date="-6m")
        proj = Project(
            title=fake.catch_phrase() + " Research Initiative",
            description=fake.text(max_nb_chars=300),
            funding_source=random.choice(["National Science Foundation", "EU Horizon", "Internal Grant", "Industry Partner", "DARPA"]),
            budget=random.randint(50_000, 2_000_000),
            status=random.choice(list(ProjectStatus)),
            start_date=start,
            end_date=start + timedelta(days=random.randint(180, 900)),
            lead_institution_id=random.choice(institutions).id,
            lead_researcher_id=random.choice(researchers).id,
        )
        projects.append(proj)
    session.add_all(projects)
    session.flush()

    for proj in projects:
        for researcher in random.sample(researchers, k=random.randint(3, 6)):
            session.add(ProjectMember(
                project_id=proj.id,
                researcher_id=researcher.id,
                role=random.choice(["Principal Investigator", "Co-Investigator", "Research Assistant", "Contributor"]),
            ))
    session.flush()

    # --- Publications + Authors ---
    publications = []
    for _ in range(30):
        pub_type = random.choice(list(PublicationType))
        status = random.choices(
            list(PublicationStatus), weights=[1, 2, 5, 2]
        )[0]
        pub = Publication(
            title=fake.sentence(nb_words=8).rstrip("."),
            abstract=fake.text(max_nb_chars=400),
            publication_type=pub_type,
            status=status,
            doi=f"10.{random.randint(1000,9999)}/{uuid.uuid4().hex[:10]}" if status == PublicationStatus.PUBLISHED else None,
            journal_or_venue=fake.catch_phrase() + " Journal",
            volume=str(random.randint(1, 40)),
            issue=str(random.randint(1, 4)),
            pages=f"{random.randint(1,300)}-{random.randint(301,600)}",
            publication_date=fake.date_between(start_date="-4y", end_date="today") if status in (
                PublicationStatus.PUBLISHED, PublicationStatus.ARCHIVED
            ) else None,
            project_id=random.choice(projects).id if random.random() < 0.6 else None,
        )
        publications.append(pub)
    session.add_all(publications)
    session.flush()

    for pub in publications:
        authors = random.sample(researchers, k=random.randint(1, 5))
        for order, researcher in enumerate(authors, start=1):
            session.add(PublicationAuthor(
                publication_id=pub.id,
                researcher_id=researcher.id,
                author_order=order,
                is_corresponding=(order == 1),
            ))
    session.flush()

    # --- Citations (internal + external) ---
    published = [p for p in publications if p.status in (PublicationStatus.PUBLISHED, PublicationStatus.ARCHIVED)]
    for pub in published:
        for _ in range(random.randint(0, 3)):
            if published and random.random() < 0.6:
                target = random.choice([p for p in published if p.id != pub.id]) if len(published) > 1 else None
                if target:
                    session.add(Citation(citing_publication_id=pub.id, cited_publication_id=target.id))
            else:
                session.add(Citation(
                    citing_publication_id=pub.id,
                    external_title=fake.sentence(nb_words=10).rstrip("."),
                    external_doi=f"10.{random.randint(1000,9999)}/{uuid.uuid4().hex[:8]}",
                    external_authors=fake.name(),
                ))
    session.flush()

    # --- Conferences + Participation ---
    conferences = []
    for _ in range(6):
        start = fake.date_between(start_date="-2y", end_date="+1y")
        conferences.append(Conference(
            name=f"International Conference on {fake.bs().title()}",
            location=f"{fake.city()}, {fake.country()}",
            website=fake.url(),
            start_date=start,
            end_date=start + timedelta(days=random.randint(1, 4)),
        ))
    session.add_all(conferences)
    session.flush()

    for conf in conferences:
        for researcher in random.sample(researchers, k=random.randint(4, 10)):
            role = random.choice(list(ParticipationRole))
            session.add(ConferenceParticipation(
                conference_id=conf.id,
                researcher_id=researcher.id,
                publication_id=random.choice(publications).id if role == ParticipationRole.PRESENTER else None,
                role=role,
                presentation_title=fake.sentence(nb_words=6).rstrip(".") if role == ParticipationRole.PRESENTER else None,
            ))
    session.flush()

    # --- Institutional Collaborations ---
    for _ in range(10):
        a, b = random.sample(institutions, k=2)
        start = fake.date_between(start_date="-3y", end_date="today")
        session.add(Collaboration(
            collaboration_type=random.choice(list(CollaborationType)),
            institution_a_id=a.id,
            institution_b_id=b.id,
            project_id=random.choice(projects).id if random.random() < 0.5 else None,
            start_date=start,
            end_date=start + timedelta(days=random.randint(90, 700)) if random.random() < 0.5 else None,
            notes=fake.sentence(),
        ))

    session.commit()
    print(f"Seeded: {len(institutions)} institutions, {len(researchers)} researchers, "
          f"{len(projects)} projects, {len(publications)} publications, "
          f"{len(conferences)} conferences.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables before seeding")
    args = parser.parse_args()

    if args.reset:
        reset_db()

    session = SessionLocal()
    try:
        seed(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
