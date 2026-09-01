"""Import public scholarly directory records from OpenAlex without creating SCNA accounts.

The imported records are public catalogue profiles only.  They have no password,
no login access, and preserve an OpenAlex source URL for attribution.
"""

from __future__ import annotations

import re

import requests

from app.core.database import SessionLocal, engine
from app.core.migrations import apply_compatibility_migrations
from app.models.institution import Institution
from app.models.researcher import Researcher
from app.models.user import User  # Ensures Researcher's mapped User relationship is registered.

OPENALEX = "https://api.openalex.org"
HEADERS = {"User-Agent": "SCNA public-research-catalogue/1.0 (mailto:scna.network@gmail.com)"}


def clean_short_name(name: str) -> str:
    initials = "".join(part[0] for part in re.findall(r"[A-Za-z0-9]+", name)[:8])
    return (initials or name[:30])[:30]


def upsert_institution(db, item: dict, topic: str = "Research") -> Institution | None:
    source_id = item.get("id")
    name = item.get("display_name")
    if not source_id or not name:
        return None
    institution = db.query(Institution).filter(Institution.source_id == source_id).first()
    if institution:
        return institution
    geo = item.get("geo") or {}
    location = geo.get("country") or item.get("country_code") or "International"
    institution = Institution(
        name=name[:200], short_name=clean_short_name(name), location=location[:200],
        description="Public institution record imported from OpenAlex.",
        research_areas=[topic], website=item.get("homepage_url"),
        source="OpenAlex", source_id=source_id, source_url=source_id,
    )
    db.add(institution)
    db.flush()
    return institution


def main() -> None:
    apply_compatibility_migrations(engine)
    db = SessionLocal()
    try:
        institutions_payload = requests.get(
            f"{OPENALEX}/institutions", params={"search": "university", "per-page": 15}, headers=HEADERS, timeout=30
        ).json()
        institution_count = 0
        for item in institutions_payload.get("results", []):
            if institution_count >= 7:
                break
            if upsert_institution(db, item):
                institution_count += 1

        authors_payload = requests.get(
            f"{OPENALEX}/authors", params={"search": "computer science", "per-page": 25}, headers=HEADERS, timeout=30
        ).json()
        imported_researchers = 0
        seen_author_ids: set[str] = set()
        for author in authors_payload.get("results", []):
            if imported_researchers >= 15:
                break
            author_id = author.get("id")
            author_name = author.get("display_name")
            affiliations = author.get("last_known_institutions") or []
            topics = author.get("topics") or []
            topic = ((topics[0] if topics else {}).get("display_name")) or "Computer Science"
            if not author_id or not author_name or not affiliations or author_id in seen_author_ids:
                continue
            seen_author_ids.add(author_id)
            source_id = f"openalex:{author_id.rsplit('/', 1)[-1]}"
            if db.query(Researcher).filter(Researcher.source_id == source_id).first():
                continue
            institution = upsert_institution(db, affiliations[0], topic)
            if not institution:
                continue
            author_key = re.sub(r"[^a-z0-9]", "", source_id.lower())
            researcher = Researcher(
                user_id=None, institution_id=institution.id, name=author_name[:150],
                email=f"{author_key}@public.scna.invalid", department="Public scholarly profile",
                institution=institution.name, field=topic[:200], skills=[topic],
                research_interests=[topic], affiliation=institution.name,
                source="OpenAlex", source_id=source_id, source_url=author_id,
            )
            db.add(researcher)
            imported_researchers += 1
        db.commit()
        print({"public_institutions_available": db.query(Institution).filter(Institution.source == "OpenAlex").count(), "public_researchers_available": db.query(Researcher).filter(Researcher.source == "OpenAlex").count()})
    except requests.RequestException as exc:
        db.rollback()
        raise SystemExit(f"OpenAlex request failed: {exc}") from exc
    finally:
        db.close()


if __name__ == "__main__":
    main()
