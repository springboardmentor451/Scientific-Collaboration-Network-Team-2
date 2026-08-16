# Scientific Collaboration Network Analyzer — Connected Build

This package contains your original FastAPI backend, wired up to the
`ResearchSphere` frontend, plus a ready-to-restore seeded database.

```
final_package/
├── backend/                 FastAPI app (unchanged except a few additions, see below)
├── frontend/
│   └── ResearchSphere.html  The connected frontend — open this in a browser
├── database/
│   └── scientific_collab_db_seed.sql   pg_dump of a working, seeded database
└── README.md                 you are here
```

---

## 1. Set up PostgreSQL

You need a local PostgreSQL server (v14+). If you don't have one:

- **Windows/Mac:** install from https://www.postgresql.org/download/
- **Docker (easiest):** the backend already ships a `docker-compose.yml`. From
  `backend/`, run:
  ```
  docker compose up -d db
  ```
  This starts Postgres on `localhost:5432` with user `scan_user` /
  password `scan_password`, database `scientific_collab_db` — matching the
  `.env` file already in `backend/`.

If you're not using Docker, create the same database/user manually:
```sql
CREATE USER scan_user WITH PASSWORD 'scan_password';
CREATE DATABASE scientific_collab_db OWNER scan_user;
```

## 2. Load the seeded database

Restore the included dump so you start with real, working data instead of an
empty schema:

```bash
psql -h localhost -U scan_user -d scientific_collab_db -f database/scientific_collab_db_seed.sql
```

This gives you:
- 6 institutions, 20 researchers, 30 publications, 8 projects, 6 conferences,
  39 citation records
- **Demo login accounts** (password for all: `Password123!`):
  | Email | Role |
  |---|---|
  | `admin@researchsphere.dev` | System Admin |
  | `institution.admin@researchsphere.dev` | Institution Admin |
  | `reviewer@researchsphere.dev` | Reviewer |
  | `researcher@researchsphere.dev` | Researcher |

  (There are also 19 other randomly-generated researcher accounts from the
  original `seed.py` — same password, emails visible via `SELECT email FROM
  users;` if you want to try more.)

If you'd rather start from a clean, empty schema instead of the seed dump,
skip step 2 and instead run, from `backend/`:
```bash
python -m alembic upgrade head
python seed.py
python add_demo_accounts.py   # adds the 4 memorable demo logins above
```

## 3. Run the backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Check it's alive: open http://localhost:8000/health — should show
`{"status":"ok","database":"connected"}`. Interactive API docs are at
http://localhost:8000/docs.

## 4. Open the frontend

Just open `frontend/ResearchSphere.html` directly in your browser (double-click
it, or drag it into a browser tab). No build step, no server needed for the
frontend itself — it's a single HTML file that talks to the API at
`http://localhost:8000` over `fetch()`.

Log in with any of the demo accounts above (2-step verification is a cosmetic
UI step — the code is echoed as a toast + the browser console, just click
through it). You should see real data: real researchers, real publications,
real projects, etc., not the placeholder data from before.

If your backend runs somewhere other than `localhost:8000`, change this one
line near the top of the `<script>` block in `ResearchSphere.html`:
```js
const API_BASE_URL = 'http://localhost:8000';
```

---

## What's actually connected now

Previously, `ResearchSphere.html` was 100% mock data — a hardcoded in-memory
`DB` object and a fake login flow that never touched a server. It now:

- **Logs in for real** against `POST /auth/login-json`, and registers new
  accounts against `POST /auth/register` (self-registration always creates a
  Researcher account — that's how the backend is written).
- **Loads real data** for Researchers, Publications, Projects, Conferences,
  and Citations from the API on every login, replacing the mock arrays.
- **Persists your session** — refreshing the page keeps you logged in via a
  saved JWT token, and logging out clears it.
- **Creates real records** — the "Upload publication," "New project,"
  "Register for conference," and "Link citation" modals now `POST` to the
  backend instead of just showing a toast.
- **Saves real profile edits** — the Profile page's "Save changes" calls
  `PUT /researchers/me`.
- **Shows real admin data** — the Users and Audit & Compliance pages (System
  Admin role) pull from `GET /admin/users` and `GET /admin/audit-logs`.

## Known limitations (backend gaps, not frontend bugs)

A few things in the original mock UI don't have a matching backend capability
yet. These are documented in the code (search `ResearchSphere.html` for
comments near each) rather than silently faked:

- **"Add researcher" modal** is still cosmetic. The backend has no endpoint
  to create a bare researcher profile without a full user account — the only
  way to create a researcher is via `/auth/register`.
- **Password change** isn't exposed by the API, so that section of the
  Profile page is disabled.
- **Institution Admins aren't linked to a specific institution** in the
  current backend schema (only `Researcher` rows have an `institution_id`).
  The frontend falls back to showing the first institution in the system for
  that role — a real fix would add an `institution_id` to institution-admin
  users.
- **Project "progress %"** isn't tracked by the backend, so it's approximated
  from the project's status (planned/active/completed) rather than a real
  number.
- **Skills/research-interest tags** on researcher cards are empty — the
  `GET /researchers` list endpoint doesn't include them (the `Tag` model
  exists in the database but isn't wired into that response yet).
- Two small backend additions were made to support the frontend properly:
  `auth.py` now auto-verifies new accounts when SMTP isn't configured (so
  registration doesn't get stuck waiting on an email that can't be sent in a
  local dev setup), and `ProjectOut` now includes `lead_researcher_name` and
  `member_names` (the original response had no way to show a project's team).

## Files changed from your original upload

- `backend/app/routers/auth.py` — dev-mode auto-verification on register
- `backend/app/models/project.py`, `backend/app/schemas/common.py`,
  `backend/app/main.py` — added `lead_researcher_name`/`member_names` to
  project responses
- `backend/add_demo_accounts.py` — new, optional helper script
- `frontend/ResearchSphere.html` — real API integration throughout (was 100%
  mock before)

Everything else — models, migrations, all other routers, schemas — is
unchanged from what you uploaded.
