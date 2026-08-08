# SciCollab - Entity Relationship Diagram

## Database Tables

1. users
2. researchers
3. institutions
4. publications
5. publication_authors
6. conferences
7. conference_participants
8. projects
9. project_members
10. collaborations
11. research_interests
12. researcher_interests
13. funding
14. institution_partnerships

USERS
  │
  │ 1 : 1
  ↓
RESEARCHERS
  │
  ├──────── N : 1 ──────── INSTITUTIONS
  │
  ├──────── 1 : N ──────── PUBLICATION_AUTHORS
  │                              │
  │                              │ N : 1
  │                              ↓
  │                         PUBLICATIONS
  │
  ├──────── 1 : N ──────── PROJECT_MEMBERS
  │                              │
  │                              │ N : 1
  │                              ↓
  │                           PROJECTS
  │
  ├──────── 1 : N ──────── CONFERENCE_PARTICIPANTS
  │                              │
  │                              │ N : 1
  │                              ↓
  │                         CONFERENCES
  │
  ├──────── 1 : N ──────── RESEARCHER_INTERESTS
  │                              │
  │                              │ N : 1
  │                              ↓
  │                       RESEARCH_INTERESTS
  │
  └──────── 1 : N ──────── COLLABORATIONS
                                 ↑
                                 │ N : 1
                                 │
                             RESEARCHERS


PROJECTS
   │
   │ 1 : N
   ↓
FUNDING


INSTITUTIONS
     │
     │ 1 : N
     ↓
INSTITUTION_PARTNERSHIPS
     ↑
     │ N : 1
     │
INSTITUTIONS