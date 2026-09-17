# How to Run This in VS Code (after unzipping)

## 1. Unzip and open the folder

1. Right-click `ResearchSphere_Ready.zip` → **Extract All...**
2. Pick a location, e.g. `C:\Users\Ishika\Downloads\ResearchSphere_Ready`
3. Open VS Code
4. **File → Open Folder...** → select that extracted folder
   (the one that directly contains `backend`, `frontend`, `database`,
   `README.md`)

You should see this in the Explorer sidebar (left panel):
```
ResearchSphere_Ready/
├── backend/
├── frontend/
├── database/
├── README.md
└── YOUR_SETUP_GUIDE.md
```

## 2. Open THREE terminals in VS Code

You need three things running at once: the database (Docker), the backend
(FastAPI), and the frontend (a static file server). Each needs its own
terminal tab so you can see all of them and leave them running.

Open a terminal: **Terminal → New Terminal** (or `` Ctrl+` ``).
To open more, click the **+** icon in the terminal panel's top-right, or
repeat **Terminal → New Terminal**. You'll end up with 3 tabs at the bottom
of the terminal panel — click between them to switch.

Every new terminal opens already inside your project root folder — confirm
with `pwd`, it should show the `ResearchSphere_Ready` path.

---

### Terminal 1 — Database (Docker)

```powershell
cd backend
docker compose up -d
```

Check it started:
```powershell
docker ps
```
You should see `scan_postgres` and `scan_pgadmin` listed as running.

This terminal can be left as-is (no continuous output) — the containers
run in the background even after this command finishes.

---

### Terminal 2 — Backend (FastAPI)

First time only — set up the Python environment:
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Every time after that, just:
```powershell
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

Leave this terminal running — you'll see request logs appear here as you
use the app. Look for:
```
INFO:     Uvicorn running on http://127.0.0.1:8001
```

Verify: open http://127.0.0.1:8001/health in a browser — should return
`{"status":"ok","database":"connected"}`.

---

### Terminal 3 — Frontend (static server)

```powershell
cd frontend
python -m http.server 5501
```

(Port 5500 is often already taken by VS Code's own Live Server / internal
tooling on this machine — use 5501 to avoid the conflict.)

Leave this terminal running too.

Open in your browser: **http://127.0.0.1:5501/ResearchSphere.html**

---

## 3. Everyday workflow after the first setup

Once the venv and `npm`/`pip` installs are done once, starting the project
next time is just 3 commands, one per terminal tab:

| Terminal | Command |
|---|---|
| 1 (db) | `cd backend && docker compose up -d` |
| 2 (backend) | `cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --port 8001` |
| 3 (frontend) | `cd frontend && python -m http.server 5501` |

To stop everything: `Ctrl+C` in terminals 2 and 3, and
`cd backend && docker compose stop` in terminal 1 (use `stop`, not `down`,
so your data isn't touched).

## 4. Quick sanity checklist if something doesn't load

- [ ] `docker ps` shows `scan_postgres` running
- [ ] http://127.0.0.1:8001/health returns `{"status":"ok",...}`
- [ ] Terminal 2 shows no red error text
- [ ] You're opening `http://127.0.0.1:5501/ResearchSphere.html` (not 5500)

See `YOUR_SETUP_GUIDE.md` in this same folder for deeper troubleshooting
(wrong Postgres port, CORS errors, etc.) — it's based on issues already
solved on this exact machine.
