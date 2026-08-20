import re
from typing import Any, Dict, Optional

ORCID_REGEX = re.compile(r"^.{10}$")

def validate_orcid(orcid_id: str) -> bool:
    """Validate format of ORCID ID (e.g. 0000-0002-1825-0097)"""
    if not orcid_id:
        return False
    return bool(ORCID_REGEX.match(orcid_id))

def get_orcid_profile(orcid_id: str) -> Optional[Dict[str, Any]]:
    """Mock query for ORCID user profiles"""
    if not validate_orcid(orcid_id):
        return None
    return {
        "orcid_id": orcid_id,
        "full_name": "Dr. Academic Collaborator",
        "biography": "Researcher focusing on graph databases and social networks.",
        "skills": ["Python", "NetworkX", "Graph Databases"]
    }
