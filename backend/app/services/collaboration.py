from collections import defaultdict
from itertools import combinations

from sqlalchemy.orm import Session

from app.models.project import ResearchProject
from app.models.publication import Publication
from app.models.researcher import Researcher
from app.schemas.project import CollaborationEdge, CollaborationNetwork


def build_collaboration_network(db: Session) -> CollaborationNetwork:
    """
    Builds a researcher-to-researcher collaboration graph.

    Two researchers are linked if they co-authored a publication together
    and/or are members of the same research project. Edge weight is broken
    down into shared_publications / shared_projects so the caller can decide
    how to visualize or weight it.
    """
    pair_pub_counts: dict[tuple[int, int], int] = defaultdict(int)
    pair_project_counts: dict[tuple[int, int], int] = defaultdict(int)
    involved_ids: set[int] = set()

    publications = db.query(Publication).all()
    for pub in publications:
        author_ids = sorted({a.id for a in pub.authors})
        involved_ids.update(author_ids)
        for a, b in combinations(author_ids, 2):
            pair_pub_counts[(a, b)] += 1

    projects = db.query(ResearchProject).all()
    for project in projects:
        member_ids = sorted({m.id for m in project.members})
        involved_ids.update(member_ids)
        for a, b in combinations(member_ids, 2):
            pair_project_counts[(a, b)] += 1

    all_pairs = set(pair_pub_counts) | set(pair_project_counts)
    if not all_pairs:
        return CollaborationNetwork(nodes=[], edges=[])

    researchers = {
        r.id: r
        for r in db.query(Researcher).filter(Researcher.id.in_(involved_ids)).all()
    }

    edges = []
    for a, b in sorted(all_pairs):
        if a not in researchers or b not in researchers:
            continue
        edges.append(
            CollaborationEdge(
                researcher_a_id=a,
                researcher_a_name=researchers[a].name,
                researcher_b_id=b,
                researcher_b_name=researchers[b].name,
                shared_publications=pair_pub_counts.get((a, b), 0),
                shared_projects=pair_project_counts.get((a, b), 0),
            )
        )

    return CollaborationNetwork(nodes=list(researchers.values()), edges=edges)


def get_researcher_collaborators(db: Session, researcher_id: int):
    """Returns the direct collaborators (co-authors + co-project-members) of one researcher."""
    network = build_collaboration_network(db)
    collaborators = {}
    for edge in network.edges:
        if edge.researcher_a_id == researcher_id:
            collaborators[edge.researcher_b_id] = edge
        elif edge.researcher_b_id == researcher_id:
            collaborators[edge.researcher_a_id] = edge
    return list(collaborators.values())
