"""
Demo data seeder for the Scientific Collaboration Network Analyzer.

Populates every module with realistic, cross-linked sample data so the
collaboration network, dashboards, and reports have something meaningful
to show in a demo/presentation:

  - Institutions
  - Researchers (spread across institutions)
  - User accounts (login credentials for a few of the above)
  - Publications (various types/statuses/years, multi-author)
  - Research projects (with members + institutional partners)
  - Conferences + participation records
  - Citations (internal + external)

USAGE
-----
Run from the `backend/` directory, with your virtualenv active and
dependencies installed:

    python seed_demo_data.py

It runs against whatever database app/db/database.py is configured for
(your real scientific_network.db by default). It is safe to run more than
once - anything that already exists (matched by unique name/email) is
skipped rather than duplicated, so re-running just fills in anything new.

DEMO LOGIN CREDENTIALS (all use the same password)
----------------------------------------------------
    Password for every seeded user: Demo@1234

    admin@scna.demo            System Admin
    iisc.admin@scna.demo       Institution Admin (IISc)
    mit.admin@scna.demo        Institution Admin (MIT)
    reviewer@scna.demo         Reviewer
    ananya.rao@iisc.demo       Researcher
    sarah.johnson@mit.demo     Researcher
"""

import datetime as dt

from app.core.security import hash_password
from app.db.database import Base, Sessionlocal, engine
from app.models.citation import Citation
from app.models.conference import Conference, ConferenceParticipation, ParticipationRole
from app.models.institution import Institution
from app.models.project import ProjectStatus, ResearchProject
from app.models.publication import Publication, PublicationStatus, PublicationType
from app.models.researcher import Researcher
from app.models.user import User, UserRole

DEMO_PASSWORD = "Demo@1234"


def get_or_create(db, model, defaults=None, **lookup):
    """Fetch a row matching `lookup`, or create it with `lookup` + `defaults`."""
    instance = db.query(model).filter_by(**lookup).first()
    if instance:
        return instance, False
    params = {**lookup, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance, True


def seed():
    Base.metadata.create_all(bind=engine)
    db = Sessionlocal()
    created_counts = {}

    try:
        # ------------------------------------------------------------------
        # 1. Institutions
        # ------------------------------------------------------------------
        institutions_data = [
            {"name": "Indian Institute of Science (IISc)", "type": "University", "country": "India"},
            {"name": "Massachusetts Institute of Technology (MIT)", "type": "University", "country": "USA"},
            {"name": "National Institute of Standards and Technology (NIST)", "type": "Government Laboratory", "country": "USA"},
            {"name": "Springer Nature", "type": "Academic Publisher", "country": "Germany"},
            {"name": "National Science Foundation (NSF)", "type": "Funding Organization", "country": "USA"},
        ]
        institutions = {}
        created = 0
        for data in institutions_data:
            inst, was_created = get_or_create(
                db, Institution, name=data["name"],
                defaults={"type": data["type"], "country": data["country"]},
            )
            institutions[data["name"]] = inst
            created += was_created
        created_counts["institutions"] = created

        iisc = institutions["Indian Institute of Science (IISc)"]
        mit = institutions["Massachusetts Institute of Technology (MIT)"]
        nist = institutions["National Institute of Standards and Technology (NIST)"]
        springer = institutions["Springer Nature"]
        nsf = institutions["National Science Foundation (NSF)"]

        # ------------------------------------------------------------------
        # 2. Researchers
        # ------------------------------------------------------------------
        researchers_data = [
            ("Ananya Rao", "ananya.rao@iisc.demo", "Computer Science", "Professor", iisc),
            ("Vikram Nair", "vikram.nair@iisc.demo", "Computer Science", "Associate Professor", iisc),
            ("Priya Menon", "priya.menon@iisc.demo", "Electrical Engineering", "PhD Researcher", iisc),
            ("Arjun Das", "arjun.das@iisc.demo", "Physics", "Postdoctoral Fellow", iisc),
            ("Meera Iyer", "meera.iyer@iisc.demo", "Electrical Engineering", "Assistant Professor", iisc),
            ("Sophia Lee", "sophia.lee@iisc.demo", "Computer Science", "PhD Researcher", iisc),
            ("Sarah Johnson", "sarah.johnson@mit.demo", "Artificial Intelligence", "Professor", mit),
            ("David Chen", "david.chen@mit.demo", "Robotics", "Associate Professor", mit),
            ("Emily Zhang", "emily.zhang@mit.demo", "Machine Learning", "PhD Researcher", mit),
            ("Michael Brown", "michael.brown@mit.demo", "Computer Science", "Postdoctoral Fellow", mit),
            ("Carlos Fernandez", "carlos.fernandez@mit.demo", "Data Science", "Associate Professor", mit),
            ("Robert Wilson", "robert.wilson@nist.demo", "Cybersecurity", "Senior Researcher", nist),
            ("Laura Kim", "laura.kim@nist.demo", "Data Science", "Researcher", nist),
            ("Daniel Kim", "daniel.kim@nist.demo", "Artificial Intelligence", "Researcher", nist),
            ("James Cooper", "james.cooper@springer.demo", "Editorial", "Managing Editor", springer),
            ("Anna Fischer", "anna.fischer@springer.demo", "Editorial", "Reviewer Coordinator", springer),
            ("Thomas Green", "thomas.green@nsf.demo", "Program Office", "Program Director", nsf),
            ("Rachel Adams", "rachel.adams@nsf.demo", "Program Office", "Program Officer", nsf),
        ]
        researchers = {}
        created = 0
        for name, email, dept, designation, inst in researchers_data:
            r, was_created = get_or_create(
                db, Researcher, email=email,
                defaults={
                    "name": name,
                    "department": dept,
                    "designation": designation,
                    "institution_id": inst.id,
                },
            )
            researchers[name] = r
            created += was_created
        created_counts["researchers"] = created

        # ------------------------------------------------------------------
        # 3. User accounts (login credentials)
        # ------------------------------------------------------------------
        users_data = [
            ("System Admin", "admin@scna.demo", UserRole.SYSTEM_ADMIN, None, None),
            ("IISc Admin", "iisc.admin@scna.demo", UserRole.INSTITUTION_ADMIN, None, iisc.id),
            ("MIT Admin", "mit.admin@scna.demo", UserRole.INSTITUTION_ADMIN, None, mit.id),
            ("Anna Fischer", "reviewer@scna.demo", UserRole.REVIEWER, researchers["Anna Fischer"].id, springer.id),
            ("Ananya Rao", "ananya.rao@iisc.demo", UserRole.RESEARCHER, researchers["Ananya Rao"].id, iisc.id),
            ("Sarah Johnson", "sarah.johnson@mit.demo", UserRole.RESEARCHER, researchers["Sarah Johnson"].id, mit.id),
        ]
        created = 0
        for name, email, role, researcher_id, institution_id in users_data:
            _, was_created = get_or_create(
                db, User, email=email,
                defaults={
                    "name": name,
                    "hashed_password": hash_password(DEMO_PASSWORD),
                    "role": role,
                    "is_active": True,
                    "researcher_id": researcher_id,
                    "institution_id": institution_id,
                },
            )
            created += was_created
        created_counts["users"] = created

        # ------------------------------------------------------------------
        # 4. Publications
        # ------------------------------------------------------------------
        R = researchers
        publications_data = [
            ("Federated Learning for Cross-Institutional Research Data", PublicationType.JOURNAL_PAPER, PublicationStatus.PUBLISHED, 2024, "Nature Machine Intelligence", "10.1038/s42256-024-0001", [R["Ananya Rao"], R["Sarah Johnson"]]),
            ("Efficient Graph Neural Networks for Co-authorship Prediction", PublicationType.CONFERENCE_PAPER, PublicationStatus.PUBLISHED, 2024, "NeurIPS 2024", "10.5555/neurips.2024.0142", [R["Emily Zhang"], R["Vikram Nair"], R["Sophia Lee"]]),
            ("A Survey of Secure Multi-Party Computation in Research Collaboration", PublicationType.JOURNAL_PAPER, PublicationStatus.PUBLISHED, 2023, "ACM Computing Surveys", "10.1145/3567890", [R["Robert Wilson"], R["Laura Kim"]]),
            ("Low-Power VLSI Design for Edge AI Accelerators", PublicationType.CONFERENCE_PAPER, PublicationStatus.PUBLISHED, 2025, "IEEE VLSI Symposium 2025", "10.1109/vlsi.2025.0091", [R["Priya Menon"], R["Meera Iyer"], R["David Chen"]]),
            ("Robotic Swarm Coordination Using Reinforcement Learning", PublicationType.JOURNAL_PAPER, PublicationStatus.SUBMITTED, 2026, "Journal of Field Robotics", None, [R["David Chen"], R["Michael Brown"]]),
            ("Explainable AI Methods for Clinical Decision Support", PublicationType.JOURNAL_PAPER, PublicationStatus.DRAFT, 2026, None, None, [R["Sarah Johnson"], R["Daniel Kim"]]),
            ("Quantum-Resistant Cryptographic Protocols: A Practical Guide", PublicationType.BOOK, PublicationStatus.PUBLISHED, 2023, "Springer Nature", "10.1007/978-3-031-00001", [R["Robert Wilson"], R["James Cooper"]]),
            ("Adaptive Sampling for Large-Scale Materials Simulation", PublicationType.CONFERENCE_PAPER, PublicationStatus.PUBLISHED, 2025, "Asia Pacific Conf. on Materials Science 2025", "10.1109/apcms.2025.0027", [R["Arjun Das"], R["Carlos Fernandez"]]),
            ("Method and System for Adaptive Neural Compression", PublicationType.PATENT, PublicationStatus.PUBLISHED, 2024, "US Patent Office", "US11987654B2", [R["Emily Zhang"], R["Michael Brown"]]),
            ("Benchmarking Distributed Training Infrastructure for Foundation Models", PublicationType.TECHNICAL_REPORT, PublicationStatus.PUBLISHED, 2025, "NIST Technical Report Series", "10.6028/nist.tr.9001", [R["Laura Kim"], R["Daniel Kim"]]),
            ("Cross-Border Data Governance in Collaborative Research Networks", PublicationType.JOURNAL_PAPER, PublicationStatus.ARCHIVED, 2021, "Science and Public Policy", "10.1093/scipol.2021.0088", [R["Thomas Green"], R["Rachel Adams"]]),
            ("Scalable Co-authorship Network Visualization Techniques", PublicationType.CONFERENCE_PAPER, PublicationStatus.PUBLISHED, 2024, "IEEE VIS 2024", "10.1109/vis.2024.0056", [R["Vikram Nair"], R["Sophia Lee"], R["Ananya Rao"]]),
            ("Energy-Efficient Wireless Sensor Networks for Smart Campuses", PublicationType.JOURNAL_PAPER, PublicationStatus.PUBLISHED, 2022, "IEEE Sensors Journal", "10.1109/jsen.2022.0134", [R["Priya Menon"], R["Meera Iyer"]]),
            ("Trends in Open-Access Scientific Publishing 2020-2025", PublicationType.TECHNICAL_REPORT, PublicationStatus.PUBLISHED, 2025, "Springer Nature", "10.1007/report.2025.0012", [R["James Cooper"], R["Anna Fischer"]]),
            ("Multi-Agent Simulation Framework for Climate Policy Research", PublicationType.CONFERENCE_PAPER, PublicationStatus.SUBMITTED, 2026, "AAMAS 2026", None, [R["Carlos Fernandez"], R["Arjun Das"], R["Daniel Kim"]]),
        ]
        publications = []
        created = 0
        for title, ptype, status, year, venue, doi, authors in publications_data:
            pub, was_created = get_or_create(
                db, Publication, title=title,
                defaults={
                    "publication_type": ptype,
                    "status": status,
                    "year": year,
                    "venue": venue,
                    "doi": doi,
                    "abstract": f"Demo abstract for '{title}'.",
                },
            )
            if was_created:
                pub.authors = authors
                created += 1
            publications.append(pub)
        created_counts["publications"] = created
        db.flush()

        pub_by_title = {p.title: p for p in publications}

        # ------------------------------------------------------------------
        # 5. Research projects
        # ------------------------------------------------------------------
        projects_data = [
            (
                "Global Federated Learning Consortium",
                "Cross-institutional consortium building privacy-preserving federated learning "
                "infrastructure for joint research on sensitive datasets.",
                ProjectStatus.ACTIVE, dt.date(2024, 1, 1), dt.date(2026, 12, 31),
                "National Science Foundation", 1250000.0,
                [iisc, mit], [R["Ananya Rao"], R["Sarah Johnson"], R["Emily Zhang"]],
            ),
            (
                "Secure Edge AI for Critical Infrastructure",
                "Developing low-power, tamper-resistant AI accelerators for deployment in "
                "national critical infrastructure systems.",
                ProjectStatus.ACTIVE, dt.date(2025, 3, 1), dt.date(2027, 3, 1),
                "NIST", 890000.0,
                [nist, iisc], [R["Robert Wilson"], R["Priya Menon"], R["Meera Iyer"]],
            ),
            (
                "Autonomous Swarm Robotics Initiative",
                "Multi-robot coordination for search-and-rescue and environmental monitoring "
                "applications using reinforcement learning.",
                ProjectStatus.PLANNED, dt.date(2026, 9, 1), None,
                "MIT Robotics Lab Internal Grant", 400000.0,
                [mit], [R["David Chen"], R["Michael Brown"]],
            ),
            (
                "Quantum-Resistant Cryptography for Research Networks",
                "Practical migration paths to post-quantum cryptographic protocols for "
                "inter-institutional data exchange.",
                ProjectStatus.COMPLETED, dt.date(2022, 1, 1), dt.date(2023, 12, 31),
                "NSF", 610000.0,
                [nist, springer], [R["Robert Wilson"], R["James Cooper"]],
            ),
            (
                "Open Science Publishing Trends Observatory",
                "Longitudinal study tracking open-access adoption, publication trends, and "
                "collaboration patterns across major publishers.",
                ProjectStatus.ON_HOLD, dt.date(2023, 6, 1), dt.date(2025, 6, 1),
                "Springer Nature Foundation", 150000.0,
                [springer, nsf], [R["James Cooper"], R["Anna Fischer"], R["Thomas Green"]],
            ),
            (
                "Materials Simulation at Scale",
                "High-performance adaptive sampling methods for large-scale materials "
                "science simulations on next-generation HPC clusters.",
                ProjectStatus.ACTIVE, dt.date(2025, 1, 15), dt.date(2027, 1, 15),
                "NSF", 975000.0,
                [iisc, mit], [R["Arjun Das"], R["Carlos Fernandez"]],
            ),
        ]
        created = 0
        for title, desc, status, start, end, agency, amount, insts, members in projects_data:
            proj, was_created = get_or_create(
                db, ResearchProject, title=title,
                defaults={
                    "description": desc,
                    "status": status,
                    "start_date": start,
                    "end_date": end,
                    "funding_agency": agency,
                    "funding_amount": amount,
                },
            )
            if was_created:
                proj.institutions = insts
                proj.members = members
                created += 1
        created_counts["projects"] = created
        db.flush()

        # ------------------------------------------------------------------
        # 6. Conferences + participation records
        # ------------------------------------------------------------------
        conferences_data = [
            ("NeurIPS 2024", "Vancouver, Canada", "https://neurips.cc/2024", dt.date(2024, 12, 9), dt.date(2024, 12, 15)),
            ("IEEE VLSI Symposium 2025", "Kyoto, Japan", "https://vlsisymposium.org", dt.date(2025, 6, 9), dt.date(2025, 6, 13)),
            ("Asia Pacific Conf. on Materials Science 2025", "Singapore", "https://apcms.example.org", dt.date(2025, 8, 20), dt.date(2025, 8, 23)),
            ("IEEE VIS 2024", "St. Pete Beach, USA", "https://ieeevis.org/2024", dt.date(2024, 10, 13), dt.date(2024, 10, 18)),
            ("AAMAS 2026", "Auckland, New Zealand", "https://aamas2026.org", dt.date(2026, 5, 4), dt.date(2026, 5, 8)),
        ]
        conferences = {}
        created = 0
        for name, location, website, start, end in conferences_data:
            conf, was_created = get_or_create(
                db, Conference, name=name,
                defaults={"location": location, "website": website, "start_date": start, "end_date": end},
            )
            conferences[name] = conf
            created += was_created
        created_counts["conferences"] = created
        db.flush()

        participations_data = [
            ("NeurIPS 2024", "Emily Zhang", ParticipationRole.PRESENTER, "Efficient Graph Neural Networks for Co-authorship Prediction", "Efficient Graph Neural Networks for Co-authorship Prediction"),
            ("NeurIPS 2024", "Vikram Nair", ParticipationRole.ATTENDEE, None, None),
            ("IEEE VLSI Symposium 2025", "Priya Menon", ParticipationRole.PRESENTER, "Low-Power VLSI Design for Edge AI Accelerators", "Low-Power VLSI Design for Edge AI Accelerators"),
            ("IEEE VLSI Symposium 2025", "David Chen", ParticipationRole.ATTENDEE, None, None),
            ("Asia Pacific Conf. on Materials Science 2025", "Arjun Das", ParticipationRole.PRESENTER, "Adaptive Sampling for Large-Scale Materials Simulation", "Adaptive Sampling for Large-Scale Materials Simulation"),
            ("Asia Pacific Conf. on Materials Science 2025", "Carlos Fernandez", ParticipationRole.ORGANIZER, None, None),
            ("IEEE VIS 2024", "Sophia Lee", ParticipationRole.PRESENTER, "Scalable Co-authorship Network Visualization Techniques", "Scalable Co-authorship Network Visualization Techniques"),
            ("IEEE VIS 2024", "Ananya Rao", ParticipationRole.ORGANIZER, None, None),
            ("AAMAS 2026", "Daniel Kim", ParticipationRole.ATTENDEE, None, None),
            ("AAMAS 2026", "Carlos Fernandez", ParticipationRole.PRESENTER, "Multi-Agent Simulation Framework for Climate Policy Research", "Multi-Agent Simulation Framework for Climate Policy Research"),
        ]
        created = 0
        for conf_name, researcher_name, role, pub_title, pres_title in participations_data:
            conf = conferences[conf_name]
            researcher = researchers[researcher_name]
            pub = pub_by_title.get(pub_title) if pub_title else None
            exists = (
                db.query(ConferenceParticipation)
                .filter_by(conference_id=conf.id, researcher_id=researcher.id, role=role)
                .first()
            )
            if not exists:
                db.add(
                    ConferenceParticipation(
                        conference_id=conf.id,
                        researcher_id=researcher.id,
                        publication_id=pub.id if pub else None,
                        role=role,
                        presentation_title=pres_title,
                    )
                )
                created += 1
        created_counts["conference_participations"] = created
        db.flush()

        # ------------------------------------------------------------------
        # 7. Citations (internal + external references)
        # ------------------------------------------------------------------
        citations_data = [
            ("Efficient Graph Neural Networks for Co-authorship Prediction",
             "Federated Learning for Cross-Institutional Research Data", None, None),
            ("Scalable Co-authorship Network Visualization Techniques",
             "Efficient Graph Neural Networks for Co-authorship Prediction", None, None),
            ("Low-Power VLSI Design for Edge AI Accelerators",
             None, "Chen, L. et al., 'Deep Learning Hardware Survey', IEEE TCAD, 2021", "10.1109/tcad.2021.0099"),
            ("Robotic Swarm Coordination Using Reinforcement Learning",
             None, "Sutton, R. & Barto, A., 'Reinforcement Learning: An Introduction', MIT Press, 2018", None),
            ("Explainable AI Methods for Clinical Decision Support",
             None, "Ribeiro, M. et al., 'Why Should I Trust You?', KDD 2016", "10.1145/2939672.2939778"),
            ("Adaptive Sampling for Large-Scale Materials Simulation",
             "Federated Learning for Cross-Institutional Research Data", None, None),
            ("Benchmarking Distributed Training Infrastructure for Foundation Models",
             "Method and System for Adaptive Neural Compression", None, None),
            ("Multi-Agent Simulation Framework for Climate Policy Research",
             "Adaptive Sampling for Large-Scale Materials Simulation", None, None),
            ("Quantum-Resistant Cryptographic Protocols: A Practical Guide",
             "A Survey of Secure Multi-Party Computation in Research Collaboration", None, None),
            ("Trends in Open-Access Scientific Publishing 2020-2025",
             None, "Piwowar, H. et al., 'The State of OA', PeerJ, 2018", "10.7717/peerj.4375"),
            ("Cross-Border Data Governance in Collaborative Research Networks",
             None, "OECD, 'Data Governance in the Digital Age', 2019", None),
            ("Energy-Efficient Wireless Sensor Networks for Smart Campuses",
             "Low-Power VLSI Design for Edge AI Accelerators", None, None),
        ]
        created = 0
        for citing_title, cited_title, ext_ref, ext_doi in citations_data:
            citing_pub = pub_by_title[citing_title]
            cited_pub = pub_by_title.get(cited_title) if cited_title else None
            exists = (
                db.query(Citation)
                .filter_by(
                    citing_publication_id=citing_pub.id,
                    cited_publication_id=cited_pub.id if cited_pub else None,
                    external_reference=ext_ref,
                )
                .first()
            )
            if not exists:
                db.add(
                    Citation(
                        citing_publication_id=citing_pub.id,
                        cited_publication_id=cited_pub.id if cited_pub else None,
                        external_reference=ext_ref,
                        doi=ext_doi,
                    )
                )
                created += 1
        created_counts["citations"] = created

        db.commit()

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("Demo data seeded successfully.\n")
    print("Newly created records this run:")
    for key, count in created_counts.items():
        print(f"  {key:28s} {count}")
    print("\nDemo login credentials (password for all: Demo@1234):")
    print("  admin@scna.demo          System Admin")
    print("  iisc.admin@scna.demo     Institution Admin (IISc)")
    print("  mit.admin@scna.demo      Institution Admin (MIT)")
    print("  reviewer@scna.demo       Reviewer")
    print("  ananya.rao@iisc.demo     Researcher")
    print("  sarah.johnson@mit.demo   Researcher")


if __name__ == "__main__":
    seed()
