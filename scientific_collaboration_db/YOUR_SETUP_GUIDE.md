# ResearchSphere — Your Working Setup Guide

This guide reflects the exact setup confirmed working on your machine. Follow
it in order every time you start the project fresh.

## The two databases — read this first

Your PC has TWO separate PostgreSQL installs. Only ONE of them has your real
data. Do not mix them up:

| | Native PostgreSQL 18 | Docker PostgreSQL (this project) |
|---|---|---|
| Port | 5432 | **5433** |
| Has your data? | No — empty/unrelated | **Yes — your real data lives here** |
| Managed by | Windows install | `docker-compose.yml` in `backend/` |

The backend's `.env` file (already included in this zip, in `backend/.env`)
is pre-configured to talk to port **5433**. Don't change this unless you know
what you're doing.

If you ever use `psql` or `pg_dump` manually, always add `-p 5433`:
```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5433 -U scan_user -d scientific_collab_db
```

## Step 1 — Start the database + pgAdmin (Docker)

```powershell
cd backend
docker compose up -d
```

This starts two containers:
- `scan_postgres` — Postgres, exposed on host port **5433**
- `scan_pgadmin` — pgAdmin web UI, exposed on host port **5050**

Check they're running:
```powershell
docker ps
```

pgAdmin is at: **http://localhost:5050**
Login: `admin@example.com` / `admin`

Inside pgAdmin, when adding/checking the server connection, use:
- Host: `scan_postgres` (Docker's internal network name — only works from
  inside pgAdmin's container, NOT from PowerShell)
- Port: `5432` (Docker's *internal* port — different from the 5433 you use
  from Windows!)

## Step 2 — Set up the database schema (first time only)

If this is a brand new Docker volume (no data yet):
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
python seed.py
python add_demo_accounts.py
```

If you already have data (your existing Docker volume), skip this — your
data persists across `docker compose up`/`down` automatically as long as you
don't run `docker compose down -v` (the `-v` deletes the data volume).

⚠️ **Never run `python seed.py --reset`** unless you've backed up first — it
drops and recreates every table.

## Step 3 — Back up your real data (do this regularly)

```powershell
cd backend
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h localhost -p 5433 -U scan_user -d scientific_collab_db -f my_real_data_backup.sql
```
Password when prompted: `scan_password`

Keep `my_real_data_backup.sql` somewhere safe. To restore it later onto a
fresh database:
```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5433 -U scan_user -d scientific_collab_db -f my_real_data_backup.sql
```

## Step 4 — Start the backend

In a terminal, with the venv active:
```powershell
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```
Leave this window open. Verify it's alive: http://127.0.0.1:8001/health
should return `{"status":"ok","database":"connected"}`.

## Step 5 — Start the frontend

In a **separate** terminal (port 5500 is often taken by VS Code's own
server on this machine — use 5501 instead):
```powershell
cd frontend
python -m http.server 5501
```
Leave this window open too.

Open in your browser: **http://127.0.0.1:5501/ResearchSphere.html**

## Step 6 — Log in

Demo accounts (password for all: `Password123!`):

| Email | Role |
|---|---|
| admin@researchsphere.dev | System Admin |
| institution.admin@researchsphere.dev | Institution Admin |
| reviewer@researchsphere.dev | Reviewer |
| researcher@researchsphere.dev | Researcher |

Or use **Create account** to register your own email (e.g. your Gmail) —
this calls the backend's `/auth/register` endpoint and adds a real row to
the `users` table.

## Quick troubleshooting

- **"No account found with this email"** → that email isn't in the
  database yet. Use Create account, or one of the demo accounts above.
- **"Could not reach the API" / Failed to fetch** → the backend (Step 4)
  isn't running, crashed, or you're hitting a CORS/browser issue. Check the
  backend terminal for errors, and check http://127.0.0.1:8001/health.
- **"password authentication failed for user scan_user"** → you forgot
  `-p 5433` and are accidentally hitting the native Postgres install on
  5432 instead of the Docker one.
- **"Cannot GET /ResearchSphere.html"** → you're not in the `frontend`
  folder, or something else (like VS Code) is already using that port.
