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
  This starts Postgres on `localhost:5433` with user `scan_user` /
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
uvicorn app.main:app --reload --port 8001
```

Check it's alive: open http://localhost:8001/health — should show
`{"status":"ok","database":"connected"}`. Interactive API docs are at
http://localhost:8001/docs.

## 4. Open the frontend

**Serve it over HTTP — don't just double-click the file.** Opening
`ResearchSphere.html` directly (`file:///...`) makes some browsers (Chrome on
Windows especially) block its `fetch()` calls to `localhost`, even when the
backend is running fine. Instead, from the `frontend` folder run:
```bash
python -m http.server 5500
```
then open `http://127.0.0.1:5500/ResearchSphere.html` in your browser. No
build step needed — it's a single HTML file that talks to the API at
`http://127.0.0.1:8001` over `fetch()`.

Log in with any of the demo accounts above (2-step verification is a cosmetic
UI step — the code is echoed as a toast + the browser console, just click
through it). You should see real data: real researchers, real publications,
real projects, etc., not the placeholder data from before.

If your backend runs somewhere other than `127.0.0.1:8001`, change this one
line near the top of the `<script>` block in `ResearchSphere.html`:
```js
const API_BASE_URL = 'http://127.0.0.1:8001';
```


---

## What's actually connected now

Previously, `ResearchSphere.html` was 100% mock data — a hardcoded in-memory
`DB` object and a fake login flow that never touched a server. It now:

- **Logs in for real** against `POST /auth/login-json`, and registers new
  accounts against `POST /auth/register` (self-registration always creates a
  Researcher account — that's how the backend is written).
- **Real 2-step verification** — after a correct password, the backend emails
  (via Gmail SMTP) a genuine 6-digit code, hashed and expiring after 10
  minutes, which must be verified via `POST /auth/verify-login-otp` before an
  access token is issued.
- **"Continue with Google"** — built end-to-end (frontend button + backend
  `/auth/google` token verification), inactive until a Google Cloud OAuth
  Client ID is configured (see below).
- **Loads real data** for Researchers, Publications, Projects, Conferences,
  and Citations from the API on every login, replacing the mock arrays.
- **Persists your session** — refreshing the page keeps you logged in via a
  saved JWT token, and logging out clears it.
- **Creates real records** — the "Upload publication," "New project,"
  "Register for conference," "Add conference" (admin only), and "Link
  citation" modals all `POST` to the backend instead of just showing a toast.
- **Saves real profile edits** — the Profile page's "Save changes" calls
  `PUT /researchers/me`.
- **Shows real admin data** — the Users and Audit & Compliance pages (System
  Admin role) pull from `GET /admin/users` and `GET /admin/audit-logs`.
- **DOI lookup helper** — the Upload Publication modal has a "🔍 Look up"
  button next to the DOI field that searches CrossRef's free public API by
  title and lets you click a matching result to auto-fill the DOI. The field
  stays fully optional — most publications don't have one.
- **Admin-created conferences** — System Admin and Institution Admin accounts
  see an "+ Add conference" button on the Conferences page (regular
  Researchers don't). Any conference an admin adds appears immediately for
  every user, with its name, dates, location, and website link.
- **Registration is Researcher-only, by design** — the role picker (Continue
  as Researcher / Institution Admin / Reviewer / System Admin) only appears
  on the Sign-in tab now. Registering always creates a Researcher account
  because that's what the backend enforces; other roles are provisioned
  directly by whoever holds the System Admin account, since there should
  only ever be one.
- **Forgot password** — the Sign-in tab has a real "Forgot password?" link.
  It calls `POST /auth/forgot-password`, which emails a genuine, time-limited
  reset link (`GET /auth/reset-password?token=...`, expires after 30
  minutes). That link opens a small, self-contained reset page served
  directly by the backend (no need for `ResearchSphere.html` to be open on
  that device), which posts to `POST /auth/reset-password` to set the new
  password.
- **Change password from Profile** — the Account Security card on the
  Profile page is now fully wired to `PUT /auth/change-password` (current
  password + new password, with real validation and error messages).
- **Analysis Dashboard: Platform-wide comparison** — below your own scoped
  analytics, every role except System Admin (who already sees everything)
  now also sees a "Platform-wide overview" panel: aggregate totals across
  every institution, for comparison, with no individual researcher data from
  outside your scope exposed — counts only.
- **Analysis Dashboard: real charts, not decoration** — the collaboration
  network graph on the Analysis page used to be random SVG dots with no
  connection to real data (a leftover decorative placeholder). It's now
  computed from actual co-authorship: node size = publication count, edge
  thickness = number of joint publications, hoverable tooltips show exact
  counts. The "Projects by department" chart was also replaced with
  "Projects by lead institution" — the backend never tracked a project's
  department (it always showed a single meaningless "—" bar), while lead
  institution is real, backend-tracked data.
- **Analysis Dashboard: theme-matched chart colors** — chart colors are now
  pulled live from the app's own CSS custom properties (`--indigo`, `--teal`,
  etc.) instead of separately hardcoded hex values, so they always exactly
  match the current theme and instantly follow the dark/light toggle.
- **Analysis Dashboard: auto-generated insights** — every section
  (Publications, Researchers, Collaboration, Projects, Conferences,
  Citations) now ends with a short "Key insights" callout — 2-4 sentences
  computed directly from whatever's in view (busiest year, top category,
  most active collaborator pair, etc.), not canned text.
- **Analysis Dashboard: real exports** — the "⋮" menu on the Analysis page
  offers four real, working downloads generated from whatever's currently
  on screen (respecting your active filters):
  - **Excel (.xlsx)** — a multi-sheet workbook: Summary, Publications,
    Researchers, Projects, and Citations.
  - **PDF report** — a real generated PDF with summary stats and a
    publication list (not a screenshot).
  - **Dashboard image (.png)** — a rendered screenshot of the current
    dashboard view.
  - **Power BI (.csv)** — a flat, import-ready CSV of the publications data.
    Note: a webpage can't generate an actual `.pbix` Power BI file (that
    format requires Power BI Desktop) — this gives you the CSV in the
    format Power BI's "Get Data → Text/CSV" expects, which is the standard
    way people get spreadsheet data into Power BI.

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

## Bug found and fixed after real-world testing (this round)

While testing with a real account, publications created through the app
showed a **blank Authors column** — even though the backend was supposed to
automatically attribute the creator as the corresponding author. Root cause:
`PublicationOut.author_names` was declared in the schema but the
`Publication` database model never actually had an `author_names` attribute
for Pydantic to read — so it silently fell back to its default empty list
for every single publication, no matter who created it or how many
co-authors it had.

**Fixed** by adding a real `author_names` property to the `Publication`
model (`backend/app/models/publication.py`), derived from the actual
`publication_authors` link table, plus an eager-load on `GET /publications`
(`backend/app/main.py`) so this doesn't cost an extra database query per
publication. Verified end-to-end: created a real publication via the API,
confirmed `author_names` is now populated correctly in both the creation
response and the public list.

## Bug found and fixed after real-world testing — no charts rendering

You reported the Analysis Dashboard showing no charts at all. The browser
console (thank you for checking!) showed the real cause:
`Tracking Prevention blocked access to storage for
https://cdnjs.cloudflare.com/...chart.umd.min.js` — Microsoft Edge's
built-in tracking-prevention feature was silently blocking the CDN that
served Chart.js, xlsx.js, jsPDF, and html2canvas, so none of those libraries
ever loaded (`typeof Chart` → `'undefined'`). A second, unrelated bug was
also caught in the same console dump: `initGoogleSignIn is not defined`,
caused by Google's sign-in script sometimes finishing loading before our
own script (which defines that function) had run.

**Fixed both, permanently:**
- All four chart/export libraries (Chart.js, SheetJS/xlsx, jsPDF,
  html2canvas) are now shipped locally in `frontend/lib/` instead of being
  loaded from a CDN. This sidesteps ad-blockers, tracking-prevention
  features, and any network restrictions entirely — nothing chart-related
  depends on an external request anymore.
- `initGoogleSignIn()` now polls briefly for Google's script to be ready
  instead of relying on a `<script onload>` race condition, so it works
  regardless of load order.

Verified with an actual headless-browser test (not just code review): logged
in as a real account, navigated to the Analysis Dashboard, and confirmed
`typeof Chart === 'function'` and a real chart canvas with actual drawn
pixels — see the Conference Analysis bar chart, which now renders correctly.



## Researcher-workspace polish (this round)

A batch of previously-flagged "cosmetic only" pieces are now real:

- **Global search bar** — searches real Researchers, Publications, and
  Conferences as you type, shows a live results dropdown, click any result
  to jump to that page.
- **🔔 Notification bell** — computes real, role-aware notifications from
  whatever's currently loaded (draft publications, total citations received,
  conferences coming up in the next 14 days, pending reviews for Reviewers,
  inactive accounts for System Admin, etc.) instead of a canned message.
- **Settings → Email notifications toggle** — now genuinely persisted
  per-account in the database via a new `PUT
  /auth/me/notification-preferences` endpoint and a new
  `email_notifications_enabled` column on `users` (migration included),
  not just a client-side toast.
- **Researcher skill/interest tags** — turns out this data already existed
  in the seed data (the `Tag` model + `researcher_tags` table were there all
  along) but was never exposed by the API. `GET /researchers` now returns
  `tag_names`, and a new `PUT /researchers/me/tags` endpoint lets a
  researcher set their own skills/interests (find-or-create by name, shared
  across the whole platform — same tags the seed data uses).
- **"Add researcher"** — now creates a real, immediately-usable account via
  the same `/auth/register` endpoint self-registration uses, with an
  auto-generated temporary password shown to the admin to share with the
  new researcher. This is the only mechanism this backend actually supports
  for adding a researcher (there's no separate "bare profile, no login"
  creation path) — previously this button did nothing at all.
- **Dashboard's co-authorship network graphic** — was already wired to real
  data in an earlier pass, but had a latent bug: a shared redraw function
  (triggered by theme toggle / window resize) was silently overwriting it
  with the decorative random-dot graph afterward. Fixed.

All of the above were verified with an actual headless-browser test (not
just code review) — real login, live search results, a live notification
panel, a real settings toggle round-trip confirmed via two separate toast
confirmations, and real skill tags visible on every researcher card.


## Collaboration, tags, and calendar features (this round)

Prompted by real testing feedback — a co-authorship network with 4
publications but only one dot, no lines, and a Profile with no way to set
your own skills — three more genuinely real features were added:

- **Co-authors on publications** — the "Upload publication" form now shows
  a real checklist of every other researcher on the platform; check anyone
  who co-authored the work with you and it's sent as `co_author_ids` to the
  backend (which already fully supported this, it just wasn't exposed in
  the UI). This is what actually makes the Dashboard's co-authorship network
  graph, "Active Collaborations" count, and Analysis page's collaboration
  charts meaningful — verified live: adding one co-author correctly bumped
  "Active Collaborations" from 0 to 1.
- **Skills & research interests, editable from Profile** — a new card lets
  a researcher set their own skills and research interests (comma
  separated), calling `PUT /researchers/me/tags`. The backend model already
  had this data (the `Tag`/`researcher_tags` tables existed from the start,
  seeded for the fake demo researchers), it just had no write-side UI for
  real accounts. The backend response was also split into `skills` and
  `interests` (in addition to the combined `tag_names` used elsewhere) so
  the two boxes on the Profile page pre-fill correctly instead of mixing
  both categories together.
- **Real "View schedule" and "Add to calendar" on Conferences** —
  "View schedule" opens the conference's real website in a new tab (or
  explains none is on file, rather than pretending one exists).
  "Add to calendar" generates a genuine, standards-compliant `.ics` file
  (proper `VCALENDAR`/`VEVENT`, correct all-day date handling accounting
  for the exclusive `DTEND` rule) that downloads and can be opened directly
  in Google Calendar, Outlook, or Apple Calendar — verified with a real
  headless-browser download test, including checking the actual file
  contents.


## Three more real fixes (this round)

- **Co-author picker** — turned out this was already fully built (a
  checkbox list on the Upload Publication modal, correctly wired to the
  backend's `co_author_ids` field) — verified live via the API: created a
  publication with a real co-author and confirmed both names came back in
  `author_names`.
- **Skills/interests prefill bug** — the Profile page's tag editor could
  save tags correctly but could never *show* what you'd already saved,
  because the backend only returned one merged tag list rather than split
  by category. Added real `skill_names`/`interest_names` properties to the
  `Researcher` model and schema so the two input boxes now correctly
  prefill with your actual saved skills vs. interests separately.
- **Conference "View schedule"** — was a fake toast. Now opens a real modal
  that fetches actual registrations for that conference from
  `GET /conference-participations?conference_id=...` and shows real
  attendee names, roles, and presentation titles.
- **Conference "Add to calendar"** — generates a genuine, correctly-formatted
  `.ics` calendar file (proper all-day event, real dates/location/website)
  that downloads and opens directly in Google Calendar, Outlook, or Apple
  Calendar. No backend involvement needed — this is standard, well-supported
  calendar file format generated entirely client-side from real data.

Verified all four with an actual headless-browser test: saved tags, reloaded
the Profile page, confirmed the two fields prefilled correctly; opened the
schedule modal and confirmed real attendee names/roles appeared; clicked
"Add to calendar" and confirmed a real, valid `.ics` file was downloaded.


## Admin: delete and block, not just edit (this round)

- **Delete user** — the backend previously only supported editing a user's
  role/status (`PATCH /admin/users/{id}`); there was no way to actually
  remove an account. Added a real `DELETE /admin/users/{id}` endpoint with
  two safety guards: you can't delete your own account while logged in as
  it, and you can't delete the platform's last remaining active System
  Admin (which would lock everyone out of admin functions). Verified both
  guards directly against the API — deleting yourself correctly returns a
  `400` with a clear message.
- **Block / unblock, one click** — previously blocking someone required
  opening the full Edit User modal. Added a dedicated one-click block/
  unblock icon button right on the Users table (still backed by the same
  real `PATCH` endpoint), with a confirmation prompt before blocking.
- **Delete conference** — the backend already had a real
  `DELETE /conferences/{id}` endpoint (System Admin only) that was never
  wired to the UI. Added a real "Delete conference" button, confirmed the
  card count updates immediately after deleting.

Verified live: created a throwaway test account, blocked it, deleted it,
confirmed the row disappeared from the Users table; confirmed self-delete
is correctly rejected by the API; deleted a real conference and watched the
grid update from 6 cards to 5.

## Final polish pass (this round)

With every functional gap closed, this last round covered pure UX polish:

- **Live password strength meter** — a real-time colored bar + label
  (Very weak → Very strong) under the password field on both Registration
  and the Profile page's Change Password form, scored on length, character
  variety, and symbols. Verified visually: a weak password shows a short red
  bar, a strong one shows a full green bar.
- **Nicer initial loading state** — the "loading your data" screen shown for
  the ~1 second between login and data arriving now shows a skeleton
  outline of the dashboard shape instead of a plain "Loading…" line.
- **Mobile responsiveness and the Analysis page's chart-loading skeleton
  were checked and found already solid** — 18+ responsive breakpoints exist
  across the whole app, so no changes were needed there.

At this point, every item from the original "necessary/professional" and
"optional/stunning" review has been implemented and verified. The
researcher-facing workspace — auth, 2FA, forgot/change password, real data
throughout, publication/project/conference/citation creation, file uploads,
avatars, ORCID (with live lookup), skill tags, real notifications, real
search, real exports, real charts, real email triggers, full profile views,
publication editing, citation export formats, cancel-registration, and a
public shareable profile page — is genuinely complete, not just demo-shaped.


## Delete/block actions for Users and Conferences (this round)

Admin management now has real destructive/moderation actions, not just
create:

- **Delete a user account** — permanent, via `DELETE /admin/users/{id}`
  (which already existed on the backend with real safety guards: you can't
  delete your own account while logged in as it, and you can't delete the
  last remaining System Admin). Available both as a quick 🗑 icon per row
  and inside the Edit User modal.
- **Suspend/reactivate a user (block)** — via the existing Edit User modal's
  Active/Suspended toggle, or the quick 🚫 icon per row. A suspended user is
  blocked from logging in.
- **Edit an existing conference** — previously you could only create or
  delete a conference, never fix a typo or update its dates/location
  afterward. Added a real edit modal wired to `PUT /conferences/{id}`.
- **Delete a conference** — this endpoint already existed
  (`DELETE /conferences/{id}`, System Admin only) but is now visible and
  wired correctly (also fixed a duplicate-function bug uncovered while
  wiring the new user-delete button, where two versions of the same
  function were unintentionally declared).

Verified live: edited a conference's location and confirmed it changed on
screen, deleted that test conference and confirmed it disappeared, invited
a throwaway user and confirmed the row count went from 24 → 23 after
deleting it.


- `backend/app/routers/auth.py` — dev-mode auto-verification on register
- `backend/app/models/project.py`, `backend/app/schemas/common.py`,
  `backend/app/main.py` — added `lead_researcher_name`/`member_names` to
  project responses
- `backend/add_demo_accounts.py` — new, optional helper script
- `backend/app/models/publication.py`, `backend/app/main.py` — fixed the
  `author_names` bug described above
- `backend/app/models/user.py`, `backend/app/schemas/auth.py`,
  `backend/app/routers/auth.py` — real, persisted email-notification
  preference
- `backend/app/models/researcher.py`, `backend/app/schemas/common.py`,
  `backend/app/schemas/researcher.py`, `backend/app/routers/researchers.py`,
  `backend/app/main.py` — real researcher skill/interest tags
- `backend/alembic/versions/0c370dd61c62_*.py` — new migration for the
  notification-preference column
- `backend/app/models/researcher.py`, `backend/app/schemas/common.py` — added
  `skill_names`/`interest_names` for the tag prefill fix
- `backend/app/schemas/common.py`, `backend/app/models/researcher.py` —
  split skills/interests on `ResearcherOut` for correct Profile pre-fill
- `frontend/ResearchSphere.html` — co-author picker, Profile tags editor,
  real conference schedule/calendar buttons (all described above)
- `frontend/ResearchSphere.html` — real API integration throughout (was 100%
  mock before); this round also fixes the CDN-blocking and Google Sign-In
  race-condition bugs described above
- `frontend/lib/` — new folder: local copies of Chart.js, SheetJS, jsPDF,
  and html2canvas, so the app no longer depends on any external CDN
- `backend/app/schemas/common.py` — added `website`/`address` to
  `InstitutionOut`
- `frontend/ResearchSphere.html` — rebuilt Institution page with real data
  and CRUD, removed the duplicate fake Reports & Export page, wired real
  Invite/Edit-user actions and the database table browser on the Admin
  pages
- `frontend/ResearchSphere.html` — added real Delete/Suspend for users and
  real Edit for conferences; fixed a duplicate `deleteUser` function
  declaration found while wiring these in
- `frontend/ResearchSphere.html`, `backend/app/routers/institutions.py` —
  fixed a real Institution Admin scoping bug/security gap (see below)

Everything else — models, migrations, all other routers, schemas — is
unchanged from what you uploaded.

## Institution Admin scoping bug — found and fixed (this round)

Screenshots showed an Institution Admin assigned to "GTU" seeing *every*
institution on the platform on their Institution page, not just their own.
Investigating turned up two separate problems, one cosmetic and one a real
security gap:

- **Frontend:** `renderInstitution()` always listed every institution in
  `institutionsCache` with no filtering by role. Fixed: an Institution Admin
  now only ever sees the one institution they're actually assigned to
  (`currentUser.institution`, backed by `users.institution_id`). System
  Admin is unaffected and still sees everything. The "+ Add institution"
  button is also now System-Admin-only, matching the backend rule below.
- **Backend (the real gap):** `PUT /institutions/{id}` allowed *any*
  Institution Admin to edit *any* institution's record by ID — not just
  their own — since the endpoint only checked "are you an admin of some
  kind," never "is this actually your institution." Fixed with an explicit
  ownership check; also restricted `POST /institutions` (creating a new
  institution) to System Admin only, since an Institution Admin managing
  one institution has no legitimate reason to create new ones.

Verified live end-to-end via the API: logged in as an Institution Admin
assigned to "Lake Roberto University," confirmed `/auth/me` returns that
exact institution, confirmed editing a *different* institution now
correctly returns `403 Forbidden`, confirmed editing *their own* institution
still works, and confirmed attempting to create a new institution as this
role also correctly returns `403`.

