# Scientific Collaboration Network Analyzer — Database Layer

PostgreSQL database + SQLAlchemy models + Alembic migrations + a FastAPI
layer (read endpoints, JWT authentication, and validated write endpoints)
for the Scientific Collaboration Network Analyzer project. Covers
users/roles, institutions, researchers, publications & co-authorship,
projects, institutional collaborations, conferences, citations, and audit
logs — matching the modules in the project spec.

## What's new in this version
- **Authentication** — register, login (JWT), and "who am I" endpoints
- **Real email verification** — registration checks that the email's domain
  actually has mail servers (a live DNS lookup, not just format), then sends
  a real verification email with a click-to-verify link. Login is blocked
  until the link is clicked. Works with a real Gmail account, or falls back
  to logging the link to the console for local development without one.
- **Validated write endpoints** — create/update Publications and Projects,
  update your own Researcher profile
- **Ownership & role checks** — only the corresponding author (or a system
  admin) can edit a publication; only the lead researcher, an institution
  admin, or a system admin can edit a project
- **Business-rule validation** — DOI/ORCID format checks, password
  strength, publication status workflow (draft → submitted → published →
  archived), project end_date can't precede start_date, budget can't be
  negative, and more

## Stack
- PostgreSQL 16 (via Docker)
- SQLAlchemy 2.0 (ORM models)
- Alembic (migrations)
- FastAPI + Uvicorn (sample read API to prove the DB layer works)
- Faker (realistic seed data)

## Folder structure
```
app/
  core/config.py     # settings from .env
  database.py         # engine, session, Base
  models/              # one file per entity (User, Researcher, Publication, ...)
  schemas/             # Pydantic response models
  main.py              # FastAPI app with a few demo endpoints
alembic/               # migration environment
seed.py                 # populates sample data
docker-compose.yml      # Postgres + pgAdmin
requirements.txt
.env.example
```

## 1. Open in VS Code
Unzip the folder and open it in VS Code:
```bash
code scientific_collaboration_db
```

## 2. Create a virtual environment
```bash
cd scientific_collaboration_db
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

## 3. Install dependencies
```bash
pip install -r requirements.txt
```

## 4. Configure environment variables
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
The defaults in `.env.example` already match `docker-compose.yml`, so you
normally don't need to edit anything for local development.

## 5. Start PostgreSQL (Docker)
```bash
docker compose up -d db
```
This also starts **pgAdmin** at http://localhost:5050 (login:
`admin@example.com` / `admin`) if you want a GUI to browse the database.

Check the container is healthy:
```bash
docker compose ps
```

## 6. Generate and run the first migration
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```
This creates every table (users, institutions, researchers, publications,
publication_authors, projects, project_members, collaborations, conferences,
conference_participations, citations, audit_logs) directly from the
SQLAlchemy models.

## 7. Seed sample data
```bash
python seed.py
```
Populates institutions, researchers/users, publications with co-authorship,
funded projects, conferences, citations (internal + external), and
institutional collaborations. Re-run with a full reset any time:
```bash
python seed.py --reset
```

## 8. (Optional) Set up real email sending
By default (no SMTP configured), verification links are printed to your
terminal instead of emailed — so you can test the whole flow without a real
mail account. To actually send real emails through a Gmail account:

1. On the Google account you'll send from: enable **2-Step Verification**.
2. Create an **App Password** at https://myaccount.google.com/apppasswords
3. In your `.env` file, fill in:
```
SMTP_USERNAME=youraccount@gmail.com
SMTP_PASSWORD=<the 16-character App Password, not your normal password>
SMTP_FROM_EMAIL=youraccount@gmail.com
```
That's it — no other code changes needed.

## 9. Run the API
```bash
uvicorn app.main:app --reload
```
Open http://localhost:8001/docs for interactive Swagger docs.

### Read-only endpoints (no login needed)
- `GET /health` — confirms the API can reach PostgreSQL
- `GET /institutions`
- `GET /researchers`
- `GET /publications`
- `GET /projects`
- `GET /conferences`
- `GET /researchers/{id}/collaboration-network` — co-author graph for one researcher

### Authentication & email verification
- `POST /auth/register` — create an account + linked researcher profile.
  Validates: email format **and deliverability** (a live DNS check that the
  domain actually has mail servers — fake domains are rejected immediately),
  email uniqueness, password strength (8+ chars, at least one letter and one
  digit), ORCID format if provided. The account starts **unverified** and a
  verification email is sent (or logged to the console in dev mode).
- `GET /auth/verify-email?token=...` — the link from that email; marks the
  account verified.
- `POST /auth/login` — **blocked with a 403 until the email is verified.**
  OAuth2-compatible (use the **Authorize** button, top-right of the Swagger
  page — enter your email as the "username"). Once authorized, Swagger
  automatically attaches your token to every subsequent request in the docs UI.
- `POST /auth/login-json` — plain JSON login alternative (`{"email": ..., "password": ...}`),
  for non-Swagger clients such as a future frontend.
- `GET /auth/me` — returns the currently logged-in user.

> Note: accounts created by `seed.py` are marked pre-verified (they're demo
> data, not real signups), so you can log into them immediately without
> going through email verification.

### Write endpoints (require login — click Authorize first)
- `PUT /researchers/me` — update your own researcher profile (partial update)
- `POST /publications` — create a publication; you're automatically added
  as the corresponding author; add co-authors via `co_author_ids`
- `PUT /publications/{id}` — update a publication. Only the corresponding
  author or a system admin can edit it. Status changes must follow
  `draft → submitted → published → archived` (no skipping steps)
- `POST /projects` — create a project; defaults you as the lead researcher
- `PUT /projects/{id}` — update a project. Only the lead researcher, an
  institution admin, or a system admin can edit it

### Peer review workflow (System Admin / Institution Admin / Reviewer)
- `GET /reviews/reviewers` — reviewer accounts eligible to be assigned.
  System Admin sees everyone; Institution Admin sees only their own
  institution's reviewers.
- `POST /reviews` — assign a reviewer to a publication (`publication_id`,
  `reviewer_id`, optional `note`). Institution Admin can only assign within
  their own institution (both the publication's authors and the reviewer
  must belong to it) — a mismatch on either side is a 403.
- `GET /reviews` — list review assignments, scoped the same way as above.
  Optional `?status=pending|approved|changes_requested|rejected` filter.
- `DELETE /reviews/{id}` — cancel a still-pending assignment.
- `GET /reviews/mine` — the logged-in Reviewer's own queue + history.
- `POST /reviews/{id}/decision` — a Reviewer submits their decision
  (`status`: `approved` / `changes_requested` / `rejected`, optional
  `comments`). Approving a submitted publication publishes it; rejecting one
  sends it back to draft. Both the assigned reviewer and the affected
  author get an email (or a console log in dev mode).

### Account & role management (System Admin / Institution Admin)
- `POST /admin/researchers` — onboard a new Researcher account (System Admin:
  any institution; Institution Admin: their own institution only). Emails a
  password-reset link so the new researcher sets their own password.
- `POST /admin/staff` — onboard a Reviewer or (System Admin only) another
  Institution Admin account directly, with no Researcher profile attached.
- `GET /admin/users` — System Admin sees every account; Institution Admin
  sees only accounts belonging to their own institution.
- `PATCH /admin/users/{id}` — update role / active status / institution.
  System Admin can change anything. Institution Admin is restricted to:
  accounts already in their own institution, switching **only** between
  Researcher and Reviewer (never promoting to Institution Admin/System
  Admin), and toggling active status — institution reassignment is always
  System Admin only.
- `DELETE /admin/users/{id}` — System Admin only.
- `GET /admin/audit-logs` — System Admin sees every action on the platform;
  Institution Admin sees only actions performed by accounts in their own
  institution (themselves, their researchers, their reviewers).

## Making schema changes later
1. Edit/add a model in `app/models/`.
2. Import it in `app/models/__init__.py` if it's a new file.
3. Generate a migration: `alembic revision --autogenerate -m "describe change"`
4. Apply it: `alembic upgrade head`

## Notes
- All primary keys are UUIDs — safe for merging data from multiple
  institutions/sources without collisions.
- `PublicationAuthor`, `ProjectMember`, and `ConferenceParticipation` are
  modeled as full association tables (not plain many-to-many) so they can
  carry extra fields like author order, corresponding-author flag, project
  role, and participation role.
- `Citation` supports citing either another publication already in the
  system, or an external work via `external_title` / `external_doi` /
  `external_authors`, so reference lists aren't limited to what's stored
  locally.
- Passwords are hashed with bcrypt via `passlib` in the seed script — swap
  in real registration/login logic when you build the auth module.
- This repo intentionally ships only the database layer plus a minimal
  read-only API to prove it end-to-end. Build the write endpoints,
  authentication/JWT, dashboards, and reports on top of `app/models` and
  `app/database.get_db`.
