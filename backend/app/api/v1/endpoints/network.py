from typing import Any, Dict
import networkx as nx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.researchers import Researcher
from backend.app.models.publication_authors import PublicationAuthor
from backend.app.models.collaborations import Collaboration
from backend.app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/network/graph")
def get_collaboration_network(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Constructs and returns the co-authorship & collaboration network graph.
    Nodes represent researchers, and weighted edges represent collaborations.
    """
    # 1. Initialize NetworkX undirected Graph
    G = nx.Graph()

    # 2. Fetch all researchers and add as nodes
    researchers = db.query(Researcher).all()
    # Pre-populate researcher details map
    res_map = {}
    for r in researchers:
        res_map[r.id] = r
        # Size of node proportional to number of publications + 5 base size
        pub_count = len(r.publication_relations)
        label = r.full_name
        dept_name = r.department.name if r.department else "No Dept"
        inst_name = r.institution.name if r.institution else "No Institution"
        title_hover = f"{r.full_name}<br>{dept_name}, {inst_name}<br>Interests: {', '.join(r.research_interests or [])}"
        
        G.add_node(
            r.id,
            id=r.id,
            label=label,
            title=title_hover,
            value=pub_count + 5,  # vis.js uses 'value' for scaling node size
            group=r.institution_id or 0 # Color nodes based on institution
        )

    # 3. Add co-authorship edges (from publication_authors)
    # Group author relations by publication_id
    pub_authors_list = db.query(PublicationAuthor).all()
    pub_to_authors = {}
    for relation in pub_authors_list:
        pub_id = relation.publication_id
        res_id = relation.researcher_id
        if pub_id not in pub_to_authors:
            pub_to_authors[pub_id] = []
        pub_to_authors[pub_id].append(res_id)

    # Add weighted edges for co-authorship
    for pub_id, author_ids in pub_to_authors.items():
        # Add edges between all pairs of co-authors
        n = len(author_ids)
        for i in range(n):
            for j in range(i + 1, n):
                u, v = author_ids[i], author_ids[j]
                if G.has_node(u) and G.has_node(v):
                    if G.has_edge(u, v):
                        G[u][v]["weight"] += 1
                        G[u][v]["title"] = f"{G[u][v]['weight']} shared publications"
                    else:
                        G.add_edge(u, v, weight=1, title="1 shared publication")

    # 4. Add other explicit collaborations (from collaborations table)
    collaborations = db.query(Collaboration).all()
    for col in collaborations:
        u, v = col.researcher_id_1, col.researcher_id_2
        if u and v and G.has_node(u) and G.has_node(v):
            if G.has_edge(u, v):
                G[u][v]["weight"] += 1.5  # Project / Institutional gets slightly higher weight bump
                G[u][v]["title"] = f"{G[u][v]['weight']:.1f} collaboration strength (Co-authored / Projects)"
            else:
                G.add_edge(u, v, weight=1.5, title=f"Collaboration ({col.collaboration_type.value})")

    # 5. Extract nodes and edges in Vis.js format
    nodes_data = []
    for node, attrs in G.nodes(data=True):
        nodes_data.append(attrs)

    edges_data = []
    for u, v, attrs in G.edges(data=True):
        edges_data.append({
            "from": u,
            "to": v,
            "value": attrs["weight"], # vis.js edge thickness
            "title": attrs["title"]
        })

    return {
        "nodes": nodes_data,
        "edges": edges_data
    }
