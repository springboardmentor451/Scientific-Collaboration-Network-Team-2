# Database Schema 

# Scienctific Network Collaboration Anlayzier


## USERS 

| Column        | Type     | Key    | Nullable |
| ------------- | -------- | ------ | -------- |
| id            | Integer  | PK     | No       |
| full_name     | String   |        | No       |
| email         | String   | UNIQUE | No       |
| password_hash | String   |        | No       |
| role          | String   |        | No       |
| is_active     | Boolean  |        | No       |
| created_at    | DateTime |        | No       |
| updated_at    | DateTime |        | Yes      |

## RESEARCHERS

| Column         | Type     | Key                  | Nullable |
| -------------- | -------- | -------------------- | -------- |
| id             | Integer  | PK                   | No       |
| user_id        | Integer  | FK → users.id        | No       |
| institution_id | Integer  | FK → institutions.id | Yes      |
| designation    | String   |                      | Yes      |
| department     | String   |                      | Yes      |
| orcid          | String   | UNIQUE               | Yes      |
| bio            | Text     |                      | Yes      |
| profile_image  | String   |                      | Yes      |
| created_at     | DateTime |                      | No       |
| updated_at     | DateTime |                      | Yes      |


## INSTITUTIONS

| Column     | Type     | Key | Nullable |
| ---------- | -------- | --- | -------- |
| id         | Integer  | PK  | No       |
| name       | String   |     | No       |
| type       | String   |     | Yes      |
| department | String   |     | Yes      |
| city       | String   |     | Yes      |
| state      | String   |     | Yes      |
| country    | String   |     | Yes      |
| website    | String   |     | Yes      |
| email      | String   |     | Yes      |
| created_at | DateTime |     | No       |
| updated_at | DateTime |     | Yes      |


## PUBLICATIONOS 

| Column           | Type     | Key           | Nullable |
| ---------------- | -------- | ------------- | -------- |
| id               | Integer  | PK            | No       |
| title            | String   |               | No       |
| abstract         | Text     |               | Yes      |
| doi              | String   | UNIQUE        | Yes      |
| publication_type | String   |               | Yes      |
| journal          | String   |               | Yes      |
| publisher        | String   |               | Yes      |
| publication_year | Integer  |               | Yes      |
| publication_date | Date     |               | Yes      |
| citation_count   | Integer  |               | Yes      |
| url              | String   |               | Yes      |
| created_by       | Integer  | FK → users.id | No       |
| created_at       | DateTime |               | No       |
| updated_at       | DateTime |               | Yes      |


## PUBLICATION_AUTHORS

| Column         | Type    | Key                 | Nullable |
| -------------- | ------- | ---                 | -------- |
| id             | Integer | PK                  | No       |
| publication_id | Integer | FK->publications.id | No       |
| researcher_id  | Integer | FK->researchers.id  | No       |
| author_order   | Integer |                     | Yes      |
| author_role    | String  |                     | Yes      |

researchers N ─── publication_authors ─── N publications

## CONFERENCES

| Column          | Type     | Key |
| --------------- | -------- | --- |
| id              | Integer  | PK  |
| name            | String   |     |
| description     | Text     |     |
| organizer       | String   |     |
| location        | String   |     |
| start_date      | Date     |     |
| end_date        | Date     |     |
| website         | String   |     |
| conference_type | String   |     |
| created_at      | DateTime |     |
| updated_at      | DateTime |     |


International Conference on AI
Organizer: ABC University
Location: Hyderabad
Start date: ...
End date: ...

## CONFERENCE_PARTICIPANTS

| Column             | Type     | Key                 |
| ------------------ | -------- | ------------------- |
| id                 | Integer  | PK                  |
| conference_id      | Integer  | FK → conferences.id |
| researcher_id      | Integer  | FK → researchers.id |
| participation_type | String   |                     |
| presentation_title | String   |                     |
| presentation_url   | String   |                     |
| attended           | Boolean  |                     |
| created_at         | DateTime |                     |


researchers N
       │
       ▼
conference_participants
       ▲
       │
conferences N

## PROJECTS

| Column        | Type     | Key           |
| ------------- | -------- | ------------- |
| id            | Integer  | PK            |
| title         | String   |               |
| description   | Text     |               |
| research_area | String   |               |
| status        | String   |               |
| start_date    | Date     |               |
| end_date      | Date     |               |
| project_url   | String   |               |
| created_by    | Integer  | FK → users.id |
| created_at    | DateTime |               |
| updated_at    | DateTime |               |

status like..

planned
ongoing
completed
cancelled

## PROJECT_MEMBERS

| Column        | Type     | Key                 |
| ------------- | -------- | ------------------- |
| id            | Integer  | PK                  |
| project_id    | Integer  | FK → projects.id    |
| researcher_id | Integer  | FK → researchers.id |
| role          | String   |                     |
| joined_date   | Date     |                     |
| left_date     | Date     |                     |
| created_at    | DateTime |                     |


researchers N
       │
       ▼
project_members
       ▲
       │
projects N

ex: Project: AI Research Project

Researcher A → Principal Investigator
Researcher B → Researcher
Researcher C → Research Assistant

## COLLABORATIONS

| Column              | Type     | Key                 |
| ------------------- | -------- | ------------------- |
| id                  | Integer  | PK                  |
| researcher_id_1     | Integer  | FK → researchers.id |
| researcher_id_2     | Integer  | FK → researchers.id |
| collaboration_type  | String   |                     |
| collaboration_count | Integer  |                     |
| first_collaboration | Date     |                     |
| last_collaboration  | Date     |                     |
| status              | String   |                     |
| created_at          | DateTime |                     |

Researcher A
     │
     │ collaboration
     ▼
Researcher B

## RESEARCH_INTERESTS

| Column      | Type     | Key    |
| ----------- | -------- | ------ |
| id          | Integer  | PK     |
| name        | String   | UNIQUE |
| description | Text     |        |
| created_at  | DateTime |        |


Artificial Intelligence
Machine Learning
Computer Vision
Cybersecurity
Data Science
IoT
Natural Language Processing


## RESEARCHER_INTERESTS

| Column              | Type     | Key                        |
| ------------------- | -------- | -------------------------- |
| id                  | Integer  | PK                         |
| researcher_id       | Integer  | FK → researchers.id        |
| interest_id         | Integer  | FK → research_interests.id |
| expertise_level     | String   |                            |
| years_of_experience | Integer  |                            |
| created_at          | DateTime |                            |


researchers N
       │
       ▼
researcher_interests
       ▲
       │
research_interests N

Researcher A
 ├── Artificial Intelligence
 ├── Computer Vision
 └── Machine Learning

 ## FUNDING

 | Column         | Type     | Key              |
| -------------- | -------- | ---------------- |
| id             | Integer  | PK               |
| project_id     | Integer  | FK → projects.id |
| funding_agency | String   |                  |
| grant_number   | String   |                  |
| amount         | Numeric  |                  |
| currency       | String   |                  |
| start_date     | Date     |                  |
| end_date       | Date     |                  |
| status         | String   |                  |
| description    | Text     |                  |
| created_at     | DateTime |                  |
| updated_at     | DateTime |                  |

projects 1 ───── N funding

## INSTITUTION_PARTNERSHIPS

| Column           | Type     | Key                  |
| ---------------- | -------- | -------------------- |
| id               | Integer  | PK                   |
| institution_id_1 | Integer  | FK → institutions.id |
| institution_id_2 | Integer  | FK → institutions.id |
| partnership_type | String   |                      |
| start_date       | Date     |                      |
| end_date         | Date     |                      |
| status           | String   |                      |
| description      | Text     |                      |
| created_at       | DateTime |                      |
| updated_at       | DateTime |                      |

University A
      │
      │ Research Partnership
      ▼
University B



