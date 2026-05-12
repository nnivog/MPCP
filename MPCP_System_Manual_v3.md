# MPCP Management System — Complete Technical Manual v3.0
### Managing Point & Checking Point Control System
**Sipradi Trading Pvt. Ltd.**
*Author: Govinda Upadhyay | Stack: Flask 3.x + SQLite + Vanilla JS | Last Updated: May 2026*

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [File Structure](#3-file-structure)
4. [Database Design](#4-database-design)
5. [Authentication & Access Control](#5-authentication--access-control)
6. [API Reference](#6-api-reference)
7. [Frontend Architecture](#7-frontend-architecture)
8. [Core Modules](#8-core-modules)
9. [Reports & Analytics](#9-reports--analytics)
10. [Audit Log System](#10-audit-log-system)
11. [Data Flow Diagrams](#11-data-flow-diagrams)
12. [User Manual](#12-user-manual)
13. [Deployment Guide](#13-deployment-guide)
14. [Master Prompt](#14-master-prompt)

---

## 1. System Overview

MPCP is a multi-department KPI compliance tracking system for Sipradi Trading Pvt. Ltd. It tracks whether employees meet their assigned Managing Points (MPs) and Checking Points (CPs) each month using the Nepali Bikram Sambat (BS) calendar.

### What It Tracks

**Managing Points (MPs)** are top-level KPI categories assigned to a department or role (e.g., "Vehicle Border Tracking", "Goods SLA Delivery"). Each MP has a reference code, target, and frequency.

**Checking Points (CPs)** are specific measurable sub-indicators under each MP (e.g., "CC within 3 Days", "Registration within 15 Days"). Each CP links to one MP and carries a numeric target, unit, and frequency.

**Performance Records** are monthly actual-vs-target entries per employee per CP, recorded in BS calendar months. Each record stores total, compliant count, NC count, percentages, unit, status, and location.

**Compliance Status** — Each record is either Compliant (C) or Non-Compliant (NC) based on actual vs. target logic. Lower-is-better metrics (Days, Hours) use ≤ 105% of target; higher-is-better use ≥ 95% of target.

### Key Metrics

- Compliance % per employee, MP, CP, location, sector
- YoY comparison across fiscal years (format: 2081-82, 2082-83)
- Exception tracking (non-compliant records and repeat failures)
- KPI trend charts per employee across BS months
- Department-level isolation — each department has its own database

### Business Rules

- Nepali fiscal year runs Shrawan → Ashadh (approx. July 16 → July 15)
- Compliance threshold: ≥ 95% = Compliant (green), 80–94% = amber, < 80% = red
- FY can be locked to prevent backdated edits
- One performance record per employee per CP per month per FY (duplicate guard)
- master_admin sees all departments; dept users are locked to their own department

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Browser (Client)                       │
│   index.html — Single file, ~297KB                           │
│   Vanilla JS (~230+ functions), no framework, no build step  │
│   Chart.js 4.4 (CDN) for trend/bar charts                    │
│   State object S{} holds all loaded data in memory           │
└─────────────────────────────┬────────────────────────────────┘
                              │ HTTP/JSON REST API
┌─────────────────────────────▼────────────────────────────────┐
│                    Flask App (app.py)                          │
│   ~3,500 lines, 85+ routes, Python 3.11+                     │
│   Session-based auth (before_request guard)                   │
│   Custom BS calendar logic (FY_MAP, BS_Q, BS_MONTHS)         │
│   openpyxl for Excel I/O, custom _xl_sheet() for .xlsx gen   │
│   log_audit() called at 19 event points                       │
└──────────┬─────────────────────────┬────────────────────────┘
           │                         │
┌──────────▼──────────┐   ┌──────────▼──────────────────────┐
│     master.db        │   │      {dept_code}.db              │
│  (global/shared)     │   │  (one per department)            │
│                      │   │                                  │
│  ● users             │   │  ● employees                     │
│  ● departments       │   │  ● mps (Managing Points)         │
│  ● audit_log         │   │  ● cps (Checking Points)         │
│                      │   │  ● roles                         │
│                      │   │  ● perf (performance records)    │
│                      │   │  ● perf_cache (FY summaries)     │
│                      │   │  ● locations                     │
│                      │   │  ● sectors                       │
│                      │   │  ● cascade_links                 │
│                      │   │  ── Junction tables ──           │
│                      │   │  ● emp_roles                     │
│                      │   │  ● emp_mps / emp_cps             │
│                      │   │  ● mp_owners / cp_owners         │
│                      │   │  ● emp_sectors                   │
│                      │   │  ● emp_locations                 │
│                      │   │  ● role_mps / role_cps           │
└──────────────────────┘   └──────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | Flask 3.x (Python) | Lightweight, zero-config, fast to develop |
| Database | SQLite | File-based, portable, zero admin overhead |
| Frontend | Vanilla JS (ES6+) | No build step, instant load, full control |
| Charts | Chart.js 4.4 (CDN) | Rich visualizations, free |
| Excel I/O | openpyxl (read) + custom _xl_sheet() (write) | Full xlsx support without pandas |
| Calendar | Custom BS logic | Nepali Bikram Sambat calendar support |
| Auth | Flask sessions + PBKDF2 | Secure, stateless, simple |
| Audit | log_audit() + audit_log table | 19-event tamper-evident trail |

---

## 3. File Structure

```
mpcp/
├── app.py                          # All backend — ~3,500 lines, 85+ routes
├── index.html                      # Entire frontend — ~297KB, single file
├── data/
│   ├── secret.key                  # Flask session key (auto-generated once)
│   ├── master.db                   # Users, departments, audit log
│   ├── logistics.db                # Logistics & SCM department data
│   └── salesmarketing.db           # Sales & Marketing department data
├── MPCP_System_Manual.md           # This document
├── Sample_Employees.xlsx           # Employee import template
├── Sample_ManagingPoints.xlsx      # MP import template
├── Sample_CheckingPoints.xlsx      # CP import template
├── Sample_Performance.csv          # Performance import template
└── MPCP_Perf_Template.csv          # Quick perf upload template
```

### Key Files Explained

**app.py** contains everything: DB init, auth, all API routes, HTML templates (LOGIN_HTML, CHANGE_PW_HTML, ADMIN_HTML) as Python string variables, and utility functions. There is intentionally no separate templates/ folder.

**index.html** is the entire single-page application. It contains inline CSS, inline JS, all tab panels as hidden divs, and communicates with the backend exclusively via the `api` object (get/post/put/del wrappers around fetch).

**data/** holds all SQLite databases. The master.db is always present. Each department gets its own `{dept_code}.db` created automatically when the department is first created.

---

## 4. Database Design

### master.db — Global Shared Database

#### `users`
```sql
CREATE TABLE users(
  id          TEXT PRIMARY KEY,       -- Random 8-char alphanumeric UUID
  username    TEXT UNIQUE NOT NULL,   -- Login handle (lowercase)
  password_hash TEXT NOT NULL,        -- PBKDF2-SHA256: "salt:hash"
  full_name   TEXT NOT NULL,
  role        TEXT DEFAULT 'user',    -- master_admin|dept_admin|moderator|user
  dept_code   TEXT DEFAULT NULL,      -- NULL = master-level user
  emp_code    TEXT DEFAULT '',        -- Linked employee code
  active      INTEGER DEFAULT 1,      -- 0 = disabled
  created_at  TEXT DEFAULT ''         -- ISO timestamp
);
```

#### `departments`
```sql
CREATE TABLE departments(
  id         TEXT PRIMARY KEY,
  code       TEXT UNIQUE NOT NULL,   -- e.g. "logistics", "salesmarketing"
  name       TEXT NOT NULL,           -- e.g. "Logistics & SCM"
  active     INTEGER DEFAULT 1,
  created_at TEXT DEFAULT ''
);
```

#### `audit_log`
```sql
CREATE TABLE audit_log(
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ts          TEXT NOT NULL,          -- UTC timestamp: "2026-05-11 04:33:30"
  actor_id    TEXT,                   -- User ID who acted
  actor_name  TEXT,                   -- Display name
  action      TEXT NOT NULL,          -- Event code: LOGIN, EMP_UPDATE, etc.
  target_type TEXT,                   -- "employee", "mp", "cp", "user", "perf"
  target_id   TEXT,                   -- Affected record ID
  detail      TEXT,                   -- Human-readable change description
  ip          TEXT                    -- Client IP address
);
```

---

### {dept_code}.db — Per Department Database

#### `employees`
```sql
CREATE TABLE employees(
  id         TEXT PRIMARY KEY,
  emp_code   TEXT UNIQUE,             -- "EMP000105"
  name       TEXT NOT NULL,
  role       TEXT DEFAULT '',         -- Job title/designation
  level      INTEGER DEFAULT 3,       -- 1=HOD, 2=Supervisor, 3=Operations
  dept       TEXT DEFAULT 'Ops',      -- Sub-department/sector label
  manager_id TEXT,                    -- FK → employees.id (self-referential)
  email      TEXT DEFAULT '',
  photo      TEXT DEFAULT ''          -- Base64 photo or URL
);
```

#### `mps` — Managing Points
```sql
CREATE TABLE mps(
  id        TEXT PRIMARY KEY,
  ref       TEXT NOT NULL,            -- "HOD-MP-1", "LM-VEH-1"
  title     TEXT NOT NULL,            -- "Vehicle Border Tracking"
  target    TEXT DEFAULT '',          -- "100%" or "15 Days"
  freq      TEXT DEFAULT 'Monthly',   -- Daily|Weekly|Monthly|Quarterly
  kpi_c     INTEGER DEFAULT 0,        -- KPI weight compliant
  kpi_nc    INTEGER DEFAULT 0,        -- KPI weight non-compliant
  kpi_total INTEGER DEFAULT 0         -- Total KPI weight
);
```

#### `cps` — Checking Points
```sql
CREATE TABLE cps(
  id     TEXT PRIMARY KEY,
  ref    TEXT NOT NULL,               -- "HOD-MP-3-CP1", "LM-VEH-1-CP2"
  title  TEXT NOT NULL,               -- "CC within 3 Days"
  target TEXT DEFAULT '',             -- "3 Days" or "95%"
  freq   TEXT DEFAULT 'Daily',
  source TEXT DEFAULT '',             -- Data source description
  mp_id  TEXT DEFAULT ''              -- FK → mps.id
);
```

#### `perf` — Performance Records
```sql
CREATE TABLE perf(
  id            TEXT PRIMARY KEY,
  fy            TEXT NOT NULL,        -- "2082-83"
  bs_month      TEXT NOT NULL,        -- "Shrawan", "Bhadra", ..., "Ashadh"
  quarter       TEXT DEFAULT 'Q1',    -- Q1|Q2|Q3|Q4
  emp_id        TEXT DEFAULT '',      -- FK → employees.id
  emp_code      TEXT DEFAULT '',      -- "EMP000105"
  mp_ref        TEXT DEFAULT '',      -- "HOD-MP-1"
  cp_ref        TEXT DEFAULT '',      -- "HOD-MP-1-CP2"
  metric        TEXT DEFAULT '',      -- KPI description
  total         INTEGER DEFAULT 0,    -- Total count/volume
  compliant     INTEGER DEFAULT 0,    -- Compliant count
  non_compliant INTEGER DEFAULT 0,    -- Non-compliant count
  pct_compliant REAL DEFAULT 0,       -- Compliance %
  pct_nc        REAL DEFAULT 0,       -- Non-compliance %
  target_val    REAL DEFAULT 0,       -- Numeric target
  actual_val    REAL DEFAULT 0,       -- Actual achieved
  unit          TEXT DEFAULT '%',     -- %, Days, Hours, Count, Nos, Trips
  status        TEXT DEFAULT 'C',     -- C | NC
  notes         TEXT DEFAULT '',      -- Free text
  loc           TEXT DEFAULT ''       -- Auto-populated from emp_locations
);
```

#### `perf_cache` — FY Summary Cache
```sql
CREATE TABLE perf_cache(
  fy           TEXT PRIMARY KEY,      -- "2082-83"
  label        TEXT NOT NULL,         -- Display label
  record_count INTEGER DEFAULT 0,
  created_at   TEXT,
  updated_at   TEXT,
  locked       INTEGER DEFAULT 0      -- 1 = locked (no edits)
);
```

#### `roles` — Role Templates
```sql
CREATE TABLE roles(
  id          TEXT PRIMARY KEY,
  code        TEXT NOT NULL,
  name        TEXT NOT NULL,
  description TEXT DEFAULT '',
  color       TEXT DEFAULT '#1d4ed8'
);
```

#### `locations`
```sql
CREATE TABLE locations(
  id      TEXT PRIMARY KEY,
  code    TEXT,                        -- "THP", "BIR", "BGD"
  name    TEXT,                        -- "Thapathali", "Birgunj", "Bagdole"
  address TEXT,
  type    TEXT,                        -- "Branch", "HQ", "Depot"
  dept    TEXT DEFAULT 'Ops',
  active  INTEGER DEFAULT 1
);
```

#### `sectors`
```sql
CREATE TABLE sectors(
  id    TEXT PRIMARY KEY,
  code  TEXT,
  name  TEXT,
  color TEXT DEFAULT '#475569'
);
```

#### `cascade_links` — Org Cascade Assignments
```sql
CREATE TABLE cascade_links(
  id                 TEXT PRIMARY KEY,
  superior_emp_id    TEXT NOT NULL,   -- Manager's employee ID
  superior_cp_id     TEXT NOT NULL,   -- Manager's CP being cascaded
  subordinate_emp_id TEXT NOT NULL,   -- Subordinate employee ID
  subordinate_mp_id  TEXT DEFAULT '', -- Mapped MP for subordinate
  auto_created       INTEGER DEFAULT 0,
  created_at         TEXT DEFAULT ''
);
```

#### Junction Tables
| Table | Purpose |
|---|---|
| `emp_roles(emp_id, role_id)` | Employee ↔ Role assignments |
| `emp_mps(emp_id, mp_id)` | Direct MP assignments to employees |
| `emp_cps(emp_id, cp_id)` | Direct CP assignments to employees |
| `mp_owners(mp_id, emp_id)` | MP ownership (who is responsible) |
| `cp_owners(cp_id, emp_id)` | CP ownership |
| `emp_sectors(emp_id, sector_id, is_primary)` | Employee ↔ Sector with primary flag |
| `emp_locations(emp_id, loc_id, is_primary)` | Employee ↔ Location with primary flag |
| `role_mps(role_id, mp_id)` | MPs bundled in a role template |
| `role_cps(role_id, cp_id)` | CPs bundled in a role template |

---

## 5. Authentication & Access Control

### Role Hierarchy

| Role | Description | Access |
|---|---|---|
| `master_admin` | System administrator | All departments, admin panel, user management, audit log |
| `dept_admin` | Department administrator | Full access within own department only |
| `moderator` | Limited write access | Read + limited write within own department |
| `user` | Read-only | View data within own department |

### Auth Flow

```
Browser Request
      │
      ▼
before_request → auth_guard()
      │
      ├─ /login, /logout, /change_password → PUBLIC (no auth required)
      ├─ /static/* → PUBLIC
      │
      └─ session['mpcp_user'] exists?
            ├─ NO  → /api/* → 401 JSON {"error":"Not authenticated"}
            │         other → redirect /login
            └─ YES → proceed to route handler
                      │
                      └─ require_role('master_admin', 'dept_admin') checks role
```

### Department Isolation (`get_db()`)

```python
def get_db(dept_override=None):
    user = session.get('mpcp_user')
    role = user.get('role', 'user')

    if role == 'master_admin':
        # master_admin can switch departments via URL param or active_dept
        dept = dept_override or request.args.get('dept') or user.get('active_dept')
        path = get_dept_db_path(dept) if dept else DB  # fallback to legacy
    else:
        # ALL other roles are locked to their assigned department
        path = get_dept_db_path(user['dept_code'])

    if not os.path.exists(path):
        _init_dept_db(path)   # auto-create DB with full schema if missing

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
```

### Password Security

Passwords are hashed using PBKDF2-SHA256 with 260,000 iterations and a random 16-byte salt:

```python
def hash_password(pw):
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 260000)
    return salt + ':' + h.hex()

def verify_password(pw, stored):
    salt, h = stored.split(':', 1)
    check = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 260000)
    return check.hex() == h
```

### Self-Service Password Change

Users can change their own password at `/change_password` (accessible from the login page) without admin intervention. The form requires current password + new password + confirm password. Minimum 6 characters enforced.

---

## 6. API Reference

### Authentication
| Method | Route | Description |
|---|---|---|
| POST | `/login` | Authenticate user, set session |
| GET | `/logout` | Clear session, redirect to login |
| GET/POST | `/change_password` | Self-service password change page |
| POST | `/api/change_password` | API endpoint for password change |

### Users & Admin
| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/admin` | master_admin, dept_admin | Admin panel HTML |
| POST | `/admin/users/create` | master_admin, dept_admin | Create new user |
| POST | `/admin/users/<id>/reset` | master_admin, dept_admin | Reset user password |
| POST | `/admin/users/<id>/toggle` | master_admin, dept_admin | Enable/disable user |
| POST | `/admin/users/<id>/edit` | master_admin, dept_admin | Edit user details |
| GET | `/api/audit_log` | master_admin | Fetch audit log (last 200 entries) |

### Departments
| Method | Route | Description |
|---|---|---|
| GET/POST | `/api/departments` | List all / Create new department |
| PUT/DELETE | `/api/departments/<id>` | Update / Soft-delete department |

### Employees
| Method | Route | Description |
|---|---|---|
| GET/POST | `/api/employees` | List all / Create employee |
| PUT/DELETE | `/api/employees/<id>` | Update / Delete employee |
| GET/POST | `/api/emp_links/<id>` | Get/set role+MP+CP assignments |
| POST | `/api/employees/import` | Bulk import from Excel/CSV |

### Managing Points
| Method | Route | Description |
|---|---|---|
| GET/POST | `/api/mps` | List all / Create MP |
| PUT/DELETE | `/api/mps/<id>` | Update / Delete MP |
| POST | `/api/mps/import_excel` | Bulk import MPs from Excel |
| GET | `/api/mps/template_excel` | Download MP import template |

### Checking Points
| Method | Route | Description |
|---|---|---|
| GET/POST | `/api/cps` | List all / Create CP |
| PUT/DELETE | `/api/cps/<id>` | Update / Delete CP |
| POST | `/api/cps/import_excel` | Bulk import CPs from Excel |
| GET | `/api/cps/template_excel` | Download CP import template |

### Roles
| Method | Route | Description |
|---|---|---|
| GET/POST | `/api/roles` | List / Create role templates |
| PUT/DELETE | `/api/roles/<id>` | Update / Delete role |

### Locations & Sectors
| Method | Route | Description |
|---|---|---|
| GET/POST | `/api/locations` | List / Create locations |
| PUT/DELETE | `/api/locations/<id>` | Update / Delete location |
| GET/POST | `/api/sectors` | List / Create sectors |
| PUT/DELETE | `/api/sectors/<id>` | Update / Delete sector |

### Performance
| Method | Route | Description |
|---|---|---|
| GET | `/api/perf` | Get performance records (filterable by FY, month, emp, mp, cp) |
| POST | `/api/perf` | Create/update performance records (batch) |
| POST | `/api/perf/quick` | Quick single-record entry |
| GET | `/api/perf/exceptions` | Get NC records and repeat failures |
| GET | `/api/export/perf` | Export perf as Excel |

### Analytics
| Method | Route | Description |
|---|---|---|
| GET | `/api/analytics/summary` | Overall compliance summary by FY |
| GET | `/api/analytics/by_location` | Compliance grouped by location |
| GET | `/api/analytics/by_sector` | Compliance grouped by sector/dept |
| GET | `/api/analytics/by_employee` | Per-employee compliance breakdown |

### Cache & FY Management
| Method | Route | Description |
|---|---|---|
| GET | `/api/cache` | List FY cache entries |
| POST | `/api/cache/<fy>/lock` | Lock an FY (prevent edits) |
| POST | `/api/cache/<fy>/clear` | Clear FY data |
| DELETE | `/api/cache/<fy>` | Delete FY completely |

### Org / Cascade
| Method | Route | Description |
|---|---|---|
| GET/POST | `/api/cascade_links` | List / Create cascade assignments |
| DELETE | `/api/cascade_links/<id>` | Remove cascade link |
| GET | `/api/bs_date` | Convert AD date to BS FY/month/quarter |

### Exports
| Method | Route | Description |
|---|---|---|
| GET | `/api/export/org_tree_html` | Org tree as printable HTML |
| GET | `/api/export/employee_mpcp_excel/<id>` | Individual employee MPCP report |
| GET | `/api/export/team_mpcp_excel` | Full team MPCP workbook |
| GET | `/api/export/sector_summary_excel` | Sector summary Excel |
| GET | `/api/export/employee_mpcp_html/<id>` | Individual report as HTML |

---

## 7. Frontend Architecture

### State Management

All application state is held in a single global object `S`:

```javascript
const S = {
  employees: [],      // All employees in active dept
  mps: [],            // All Managing Points
  cps: [],            // All Checking Points
  roles: [],          // Role templates
  perf: [],           // Performance records
  cache: [],          // FY cache entries
  locations: [],      // Branch/office locations
  sectors: [],        // Sector/sub-dept groupings
  bsToday: {},        // Today's BS date info
  dashLayouts: [],    // Dashboard widget configs
  currentTab: 'dashboard',
  teamView: 'cards',
  masterSub: 'mps',
  reportSub: 'overview',
  currentFY: '2081-82',
  authUser: null,     // Logged-in user object
  activeDept: null    // Active department for master_admin
}
```

### Data Loading

On login/tab switch, `loadAll()` fetches all data in parallel:

```javascript
async function loadAll() {
  const [e, m, c, r, p, ca] = await Promise.all([
    api.get('/api/employees'),
    api.get('/api/mps'),
    api.get('/api/cps'),
    api.get('/api/roles'),
    api.get('/api/perf'),
    api.get('/api/cache')
  ])
  setAll(e, m, c, r, p, ca)
  render()
}
```

### API Wrapper

```javascript
const api = {
  get:  url           => fetch(url).then(r => r.json()),
  post: (url, body)   => fetch(url, {method:'POST',   headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}).then(_json),
  put:  (url, body)   => fetch(url, {method:'PUT',    headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}).then(_json),
  del:  url           => fetch(url, {method:'DELETE'}).then(_json),
}
```

### Tab System

Six main tabs: Dashboard, Team, Master Setup, Data Manager, Reports, Org & Cascade. Each has a `<div id="tab-{name}" class="tab-panel">` container. Switching calls `switchTab(name)` which shows/hides panels and calls the appropriate render function.

### Modal System

```javascript
function openModal(title, bodyHTML, actions=[], wide=false) {
  // Sets modal-title, modal-body innerHTML, modal-foot buttons
  // wide=true adds .wide class for 960px width (e.g., Quick Entry)
  // Always includes a Cancel button
}
function closeModal() { /* hides overlay */ }
function handleBackdrop(e) { /* disabled — modal only closes via button */ }
```

### Nepali Calendar Utilities

```javascript
async function fyFromDate(isoDateStr)  // Returns {fy, bs_month, quarter}
function todayISO()                    // Returns today as "YYYY-MM-DD"
```

BS month sequence: Shrawan, Bhadra, Ashwin, Kartik, Mangsir, Poush, Magh, Falgun, Chaitra, Baisakh, Jestha, Ashadh

Quarter mapping: Q1=Shrawan–Ashwin, Q2=Kartik–Poush, Q3=Magh–Chaitra, Q4=Baisakh–Ashadh

---

## 8. Core Modules

### Module: Quick Entry

The Quick Performance Entry modal (`openQuickEntry()`) provides inline KPI entry:

**Fields:**
- Date (auto-populates FY, Month, Quarter)
- Employee dropdown
- MP dropdown (filters CPs when changed)
- CP dropdown (auto-fills Metric from CP title, auto-selects MP)
- Metric / KPI (editable)
- Total count + Compliant count
- Auto-calculated: % C, NC count, % NC, Status (C/NC at ≥95% threshold)
- Unit dropdown (%, Days, Hours, Count, Nos, Trips, Tons)
- Notes

**Save flow:** `qeSave()` → POST `/api/perf/quick` → backend validates, calculates, inserts, returns full record → `S.perf.push(data)` → table re-renders without page reload.

**Duplicate guard:** If a record already exists for that employee/CP/month/FY, backend returns 409 with a confirm-overwrite prompt.

### Module: Employee Management

Employees are stored per-department DB. Each employee has:
- Core fields: code, name, role, level, dept, manager, email, photo
- Assignments (junction tables): roles, MPs, CPs, sectors, locations

Import supports `.xlsx` and `.csv`. Required columns: `emp_code`, `name`. Optional: `role`, `level`, `department`, `manager_code`, `email`.

Manager resolution happens in a second pass — all employees are inserted first, then `manager_code` is resolved to `manager_id`.

### Module: MP/CP Setup

MPs and CPs can be created individually or bulk-imported from Excel. The MP import template has columns: ref, title, target, freq, kpi_c, kpi_nc, kpi_total. The CP import template has: ref, title, mp_ref, target, freq, source.

CPs link to MPs via `mp_id`. When selecting a CP in Quick Entry, the parent MP is auto-selected and the CP title auto-fills the Metric field.

### Module: Role Templates

Roles bundle MPs and CPs together. Assigning a role to an employee automatically assigns all the role's MPs and CPs to that employee via junction tables. This makes batch onboarding fast.

### Module: Cascade / Org Tree

Cascade links connect a manager's CP to a subordinate's MP, creating a traceable delegation chain. The org tree visualizes the full hierarchy with compliance coloring.

### Module: FY Cache

Each fiscal year is cached as a summary row in `perf_cache`. The cache tracks total record count, lock status, and timestamps. Locked FYs cannot receive new perf records. Cache can be cleared (deletes perf data) or locked/unlocked from the FY Cache panel.

---

## 9. Reports & Analytics

### Report Tabs

**Overview** — Global compliance summary for the active FY: total records, compliant %, NC count, trend chart, at-risk MPs, monthly breakdown table.

**By Location/Sector** — Compliance cards grouped by workstation location (from `emp_locations → locations`) and sector (from `employees.dept`). Features:
- Primary FY selector (auto-selects latest FY with data)
- Optional comparison FY with delta indicators (▲▼)
- "No data for this FY" message with guidance

**YoY Comparison** — Side-by-side comparison of two fiscal years.

**Employee Report** — Per-employee compliance breakdown with MP/CP drill-down.

**MP/CP Report** — Compliance by individual Managing Point or Checking Point.

### Analytics API Patterns

```
GET /api/analytics/by_location?fy=2082-83
→ { "Birgunj": { total:2, compliant:2, non_compliant:0, pct:100.0 } }

GET /api/analytics/by_sector?fy=2082-83
→ { "CVBU": { name:"CVBU", emp_count:5, total:100, compliant:92, nc:8, pct:92.0, color:"#475569" } }

GET /api/analytics/summary?fys=2081-82,2082-83
→ { "2082-83": { total:50, compliant:48, pct_c:96.0, by_mp:{...}, by_employee:{...} } }
```

### Location Data Flow

```
perf.loc is auto-populated at save time:
  emp_code → employees.id → emp_locations.emp_id → locations.id → locations.name

If perf.loc is empty, analytics queries do a live JOIN:
  SELECT COALESCE(NULLIF(p.loc,''),
    (SELECT l.name FROM employees e
     JOIN emp_locations el ON el.emp_id=e.id
     JOIN locations l ON l.id=el.loc_id
     WHERE e.emp_code=p.emp_code
     ORDER BY el.is_primary DESC LIMIT 1),
    'Unassigned') grp
  FROM perf p
```

### Compliance Color Logic

```javascript
pct >= 95 → green  (#16A34A / var(--green))
pct >= 80 → amber  (#D97706 / var(--amber))
pct < 80  → red    (#ED1C24 / var(--red))
no data   → gray   (#94A3B8)
```

---

## 10. Audit Log System

### Overview

Every data mutation and auth event calls `log_audit()` which inserts a row into `master.db → audit_log`. The function never throws — failures are silently caught so they never break the primary operation.

```python
def log_audit(action, target_type='', target_id='', detail=''):
    try:
        mdb = get_master_conn()
        u = session.get('mpcp_user') or {}
        mdb.execute(
            "INSERT INTO audit_log(ts,actor_id,actor_name,action,target_type,target_id,detail,ip) VALUES(?,?,?,?,?,?,?,?)",
            (utcnow(), u.get('id',''), u.get('full_name','system'),
             action, target_type, str(target_id), detail, request.remote_addr)
        )
        mdb.commit(); mdb.close()
    except Exception: pass
```

### Events (19 Total)

| Event Code | Trigger | Detail |
|---|---|---|
| `LOGIN` | Successful login | Username + role |
| `LOGOUT` | Session cleared | — |
| `PASSWORD_CHANGE` | Self-service change | User ID (last 4) |
| `PASSWORD_RESET` | Admin reset | Target user ID |
| `USER_CREATE` | New user created | Username, role, dept |
| `USER_ENABLE` | Account re-enabled | User ID |
| `USER_DISABLE` | Account disabled | User ID |
| `EMP_CREATE` | Employee inserted/updated | Employee ID |
| `EMP_UPDATE` | Employee edited | Employee ID |
| `EMP_DELETE` | Employee deleted | Employee ID |
| `MP_SAVE` | MP created | MP ID |
| `MP_UPDATE` | MP edited | MP ID |
| `MP_DELETE` | MP deleted | MP ID |
| `CP_SAVE` | CP created | CP ID |
| `CP_UPDATE` | CP edited | CP ID |
| `CP_DELETE` | CP deleted | CP ID |
| `PERF_IMPORT` | Bulk perf import | Record count |
| `DEPT_CREATE` | Department created | — |
| `LOC_SAVE` | Location saved | Location ID |

### Viewing the Audit Log

Navigate to `/admin` → click **📋 Audit Log** tab → click **⟳ Refresh**.

The log renders human-readable descriptions with color-coded action badges:
- Blue = auth events (LOGIN, LOGOUT)
- Green = create events
- Amber = edit events
- Red = delete/disable events

Filterable by typing in the search box. Shows last 200 entries by default.

---

## 11. Data Flow Diagrams

### Quick Entry Save Flow

```
User fills Quick Entry modal
  │
  ├─ Selects Employee
  ├─ Selects MP → CP list filters to that MP's CPs
  ├─ Selects CP → Metric auto-fills from CP title
  │              → Parent MP auto-selected
  ├─ Enters Total + Compliant
  │  → qeAutoCalc() fires:
  │     NC = Total - Compliant
  │     % C = Compliant/Total × 100
  │     % NC = NC/Total × 100
  │     Status = %C ≥ 95 ? 'C' : 'NC'
  │     window._qPayload = {total, compliant, pct_c}
  └─ Clicks Save Entry
       │
       ▼
  qeSave() builds body:
  { date, emp_code, cp_ref, mp_ref, total, compliant,
    metric, unit, notes, fy, bs_month, overwrite }
       │
       ▼
  POST /api/perf/quick
       │
       ├─ Validate: date, emp_code, cp_ref required
       ├─ Lookup employee by emp_code → get eid
       ├─ Lookup CP by ref → get cp record
       ├─ Auto-detect FY + BS month from AD date
       ├─ Check FY lock → 403 if locked
       ├─ Calculate nc, pct_c, pct_nc
       ├─ Duplicate check → 409 if exists (confirm overwrite)
       ├─ INSERT OR REPLACE INTO perf (19 fields + loc)
       ├─ _upd_cache(db, fy) → update perf_cache
       ├─ log_audit('PERF_IMPORT', ...)
       └─ Return full record JSON
            │
            ▼
  Frontend: S.perf.push(data) → updateHeader() → table re-renders
  Toast: "✓ Saved — Jestha 2082-83 | 96.0% compliant"
```

### Department Switching (master_admin)

```
master_admin selects dept from header dropdown
  │
  ▼
switchDept(deptCode)
  │
  ├─ PUT /api/me { active_dept: deptCode }
  │   → session['mpcp_user']['active_dept'] = deptCode
  │
  └─ loadAll()
      │
      └─ All subsequent API calls:
          get_db() → data/deptCode.db
          master_admin sees that department's data only
          (while master.db remains shared for users/audit)
```

### Employee Import Flow

```
User selects Excel/CSV file → clicks Upload
  │
  ▼
POST /api/employees/import (multipart/form-data)
  │
  ├─ Detect file type: .xlsx (openpyxl) or .csv
  ├─ Read headers: emp_code, name, role, level,
  │               department, manager_code, email
  │
  ├─ Pass 1: INSERT OR REPLACE INTO employees
  │   (without manager_id — managers may not exist yet)
  │
  ├─ Pass 2: Resolve manager_code → manager_id
  │   UPDATE employees SET manager_id=? WHERE id=?
  │
  ├─ log_audit('EMP_CREATE', 'employee', eid, ...)
  │
  └─ Return { imported: N, updated: M, errors: [...] }
      │
      ▼
  Frontend toast: "Imported 25 employees (3 updated)"
  loadAll() → renderTeam()
```

---

## 12. User Manual

### Getting Started

**Login:** Navigate to `http://[server]:5050`. Enter username and password. To change your password before logging in, click **🔒 Change Password** below the Sign In button.

**Default credentials:** username `admin`, password `admin123` — change immediately after first login.

### First-Time Setup (master_admin)

1. **Create departments** — Master → Departments → fill code + name → Create
2. **Create users** — `/admin` → Users tab → Create New User → assign dept + role
3. **Switch to a department** — use the dropdown in the top-right header
4. Follow the department setup steps below for each department

### Setting Up a Department

Work through these in order:

1. **Locations** — Master → Locations → add branches (Thapathali, Birgunj, etc.)
2. **Sectors** — Master → Sectors → add sector groups (CVBU, EXIDE, etc.)
3. **Employees** — Team tab → Import Excel (or add manually)
   - Required Excel columns: `emp_code`, `name`
   - Optional: `role`, `level`, `department`, `manager_code`, `email`
4. **Managing Points** — Master → MPs → Import from Excel or create manually
   - Template: `ref, title, target, freq`
5. **Checking Points** — Master → CPs → Import or create
   - Template: `ref, title, mp_ref, target, freq`
   - CPs must reference a valid MP ref
6. **Roles** — Master → Roles → create role templates bundling MPs+CPs
7. **Assign roles** — Org → Assignment → select employee → assign roles → MPs/CPs inherit automatically

### Recording Performance

**Quick Entry (single record):**
1. Data tab → click ⚡ Quick Entry
2. Select Employee, then MP, then CP
3. Metric auto-fills from CP title
4. Enter Total count and Compliant count
5. System calculates NC, % C, % NC, Status automatically
6. Add notes (optional) → click 💾 Save Entry

**Bulk Import:**
1. Data tab → Download Template → fill in data
2. Required columns: `fy, bs_month, emp_code, cp_ref, total, compliant`
3. Upload file → system validates and imports

### Reading Reports

| Report | Location | Shows |
|---|---|---|
| Dashboard | Home tab | Real-time KPI cards + compliance % |
| Overview | Reports → Overview | Summary, trend chart, at-risk MPs |
| By Location/Sector | Reports → Location | Compliance by branch/team with FY comparison |
| YoY | Reports → YoY | Year-over-year delta |
| Employee | Reports → Employee | Individual staff breakdown |
| Trend | Team → employee card → Trend | Monthly KPI chart per employee |

### Exporting Data

| Export | How |
|---|---|
| Individual employee Excel | Team tab → employee → Download Excel |
| Full team workbook | Reports → Export Team MPCP Book |
| Sector summary | Reports → Export Sector Summary |
| All perf records | Data tab → Export Excel |

### Admin Tasks (master_admin only)

| Task | Where |
|---|---|
| Create / disable users | `/admin` → Users tab |
| Reset user password | `/admin` → Users → Reset button |
| View audit trail | `/admin` → Audit Log tab → Refresh |
| Switch departments | Header dropdown (top-right) |
| Create departments | Master → Departments |
| Lock/clear FY data | Header → FY Cache button |

---

## 13. Deployment Guide

### Local Development

```bash
# Clone and run
git clone https://github.com/nnivog/MPCP.git mpcp
cd mpcp
pip install flask openpyxl
python app.py
# → http://127.0.0.1:5050
# Default login: admin / admin123
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MPCP_DATA_DIR` | `./data` | Directory for all SQLite databases |
| `SECRET_KEY` | Auto-generated | Flask session key — set in production |
| Port | `5050` | Hardcoded in `app.run()` |

### Production Deployment

```bash
# Install WSGI server
pip install gunicorn

# Run with 2 workers
gunicorn app:app -w 2 -b 0.0.0.0:5050

# Or with systemd service
[Unit]
Description=MPCP Management System
After=network.target

[Service]
WorkingDirectory=/opt/mpcp
ExecStart=/usr/bin/gunicorn app:app -w 2 -b 0.0.0.0:5050
Restart=always
Environment=MPCP_DATA_DIR=/opt/mpcp/data

[Install]
WantedBy=multi-user.target
```

### Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR=/opt/mpcp/backups
mkdir -p $BACKUP_DIR
cp -r /opt/mpcp/data $BACKUP_DIR/data_$DATE
# Keep last 30 days
find $BACKUP_DIR -name "data_*" -mtime +30 -exec rm -rf {} \;
```

### Security Checklist

- [ ] Change default `admin` / `admin123` credentials immediately
- [ ] Set a fixed `SECRET_KEY` environment variable (random key = sessions invalidated on restart)
- [ ] Restrict `/admin` to internal network via reverse proxy (nginx)
- [ ] Set up regular database backups
- [ ] Use HTTPS in production (nginx + Let's Encrypt)
- [ ] Review audit log monthly for suspicious activity

### Scaling Considerations

SQLite works well for up to ~50 concurrent users per department. For larger deployments:
- Migrate to PostgreSQL (requires updating connection strings and SQL syntax in a few places)
- Use a CDN for `index.html` static serving
- Add Redis for session storage
- Deploy behind nginx with load balancing

---

## Appendix A: Quick Reference

### BS Month → Quarter Mapping

| BS Months | Quarter | Approx. AD Period |
|---|---|---|
| Shrawan, Bhadra, Ashwin | Q1 | July–October |
| Kartik, Mangsir, Poush | Q2 | October–January |
| Magh, Falgun, Chaitra | Q3 | January–April |
| Baisakh, Jestha, Ashadh | Q4 | April–July |

### Nepali FY Calendar

| FY | Start | End |
|---|---|---|
| 2079-80 | July 17, 2022 | July 16, 2023 |
| 2080-81 | July 17, 2023 | July 15, 2024 |
| 2081-82 | July 16, 2024 | July 15, 2025 |
| 2082-83 | July 16, 2025 | July 15, 2026 |
| 2083-84 | July 16, 2026 | July 15, 2027 |

### Compliance Thresholds

| Color | Range | Meaning |
|---|---|---|
| 🟢 Green | ≥ 95% | On target — compliant |
| 🟡 Amber | 80–94% | Needs attention |
| 🔴 Red | < 80% | Critical — non-compliant |

### Employee Levels

| Level | Code | Typical Role |
|---|---|---|
| 1 | HOD | Head of Department / AGM / GM |
| 2 | Supervisor | Deputy Manager / Sr. Officer |
| 3 | Operations | Officer / Executive / Staff |

### Unit Types

`%` · `Days` · `Hours` · `Count` · `Nos` · `Trips` · `Tons`

Lower-is-better detection: if unit contains "day" or "hour" → compliance = actual ≤ target × 1.05

---

## Appendix B: Common Issues

| Issue | Cause | Fix |
|---|---|---|
| Page not loading | JS syntax error | Open DevTools Console (F12) → find red error |
| Quick Entry not saving | `_qPayload` null | Ensure Total field is filled before Compliant |
| Location report empty | Wrong FY selected | Use FY selector in report — pick a FY with data |
| Audit log empty | log_audit() calls missing | Verify `log_audit` is in app.py at mutation points |
| Excel download corrupt | Missing `_rels/.rels` in zip | Ensure `_xl_sheet()` includes `_rels/.rels` entry |
| FY not detected | Date outside FY_MAP | Add new FY entry to `FY_MAP` in app.py |
| Dept DB not found | New dept not initialized | `_init_dept_db()` is called automatically on first `get_db()` |

---

## 14. Master Prompt

The following single prompt will instruct an AI coding assistant to build the entire MPCP system from scratch:

---

```
Build a complete multi-department KPI compliance tracking web application called MPCP
(Managing Point & Checking Point) with the following specifications:

## Stack
- Backend: Flask (Python), single file app.py
- Database: SQLite — one master.db (shared) + one {dept_code}.db per department
- Frontend: Single file index.html — vanilla JS (ES6+, no framework, no build step)
- Charts: Chart.js 4.4 from CDN
- Excel: openpyxl for reading; custom _xl_sheet() function for writing .xlsx without pandas
- Auth: Flask sessions, PBKDF2-SHA256 passwords (260,000 iterations, random salt)

## Master DB (master.db)
Tables: users, departments, audit_log
- users: id(TEXT PK), username(UNIQUE), password_hash, full_name, role, dept_code, emp_code, active, created_at
- departments: id, code(UNIQUE), name, active, created_at
- audit_log: id(AUTOINCREMENT), ts, actor_id, actor_name, action, target_type, target_id, detail, ip
- Roles: master_admin, dept_admin, moderator, user

## Department DB ({dept_code}.db) — one per department
Tables: employees, mps, cps, roles, perf, perf_cache, locations, sectors, cascade_links
Junction tables: emp_roles, emp_mps, emp_cps, mp_owners, cp_owners, emp_sectors, emp_locations, role_mps, role_cps
- employees: id, emp_code(UNIQUE), name, role(job title), level(1-3), dept, manager_id, email, photo
- mps: id, ref, title, target, freq(Daily/Weekly/Monthly/Quarterly), kpi_c, kpi_nc, kpi_total
- cps: id, ref, title, target, freq, source, mp_id(FK→mps)
- perf: id, fy, bs_month, quarter, emp_id, emp_code, mp_ref, cp_ref, metric, total, compliant,
        non_compliant, pct_compliant, pct_nc, target_val, actual_val, unit, status(C/NC), notes, loc
- perf_cache: fy(PK), label, record_count, created_at, updated_at, locked
- locations: id, code, name, address, type, dept, active
- sectors: id, code, name, color

## Auth & Access Control
- before_request guard: /login, /logout, /change_password are public; all else requires session
- get_db() routes to correct dept DB based on user role:
  master_admin → dept_override or request.args['dept'] or user.active_dept
  all others → always user.dept_code (locked)
- require_role(*roles) helper returns 403 JSON if role not in list
- Self-service password change at /change_password (GET/POST page, no login required)
- Admin panel at /admin with Users tab and Audit Log tab

## Nepali Calendar
- Fiscal year: Shrawan→Ashadh (approx July 16 → July 15)
- FY format: "2082-83"
- BS months: Shrawan, Bhadra, Ashwin, Kartik, Mangsir, Poush, Magh, Falgun, Chaitra, Baisakh, Jestha, Ashadh
- Quarters: Q1=Shrawan-Ashwin, Q2=Kartik-Poush, Q3=Magh-Chaitra, Q4=Baisakh-Ashadh
- FY_MAP: list of (start_date, end_date, fy_string) tuples for date→FY conversion
- /api/bs_date?date=YYYY-MM-DD returns {fy, bs_month, quarter}

## API Routes (all return JSON)
Auth: POST /login, GET /logout, GET/POST /change_password, POST /api/change_password
Users: GET/POST /api/users, PUT/DELETE /api/users/<id>
Admin: GET /admin, POST /admin/users/create, POST /admin/users/<id>/reset,
       POST /admin/users/<id>/toggle, POST /admin/users/<id>/edit, GET /api/audit_log
Departments: GET/POST /api/departments, PUT/DELETE /api/departments/<id>
Employees: GET/POST /api/employees, PUT/DELETE /api/employees/<id>,
           GET/POST /api/emp_links/<id>, POST /api/employees/import
MPs: GET/POST /api/mps, PUT/DELETE /api/mps/<id>, POST /api/mps/import_excel
CPs: GET/POST /api/cps, PUT/DELETE /api/cps/<id>, POST /api/cps/import_excel
Roles: GET/POST /api/roles, PUT/DELETE /api/roles/<id>
Locations: GET/POST /api/locations, PUT/DELETE /api/locations/<id>
Sectors: GET/POST /api/sectors, PUT/DELETE /api/sectors/<id>
Perf: GET/POST /api/perf, POST /api/perf/quick, GET /api/perf/exceptions
Analytics: GET /api/analytics/summary, GET /api/analytics/by_location,
           GET /api/analytics/by_sector, GET /api/analytics/by_employee
Cache: GET /api/cache, POST /api/cache/<fy>/lock, POST /api/cache/<fy>/clear,
       DELETE /api/cache/<fy>
Cascade: GET/POST /api/cascade_links, DELETE /api/cascade_links/<id>
Exports: GET /api/export/team_mpcp_excel, GET /api/export/sector_summary_excel,
         GET /api/export/employee_mpcp_excel/<id>

## Quick Entry (/api/perf/quick POST)
- Validates: date, emp_code, cp_ref required
- Auto-detects FY and BS month from AD date using FY_MAP
- Checks FY lock (perf_cache.locked=1 → 403)
- Calculates: nc=total-compliant, pct_c, pct_nc
- Duplicate guard: 409 if same emp/cp/month/FY exists (overwrite=true bypasses)
- Auto-populates loc from emp_locations → locations join
- Returns full record including emp_code, mp_ref, cp_ref, metric

## Audit Logging
log_audit(action, target_type, target_id, detail) — inserts to master.db audit_log
Never throws. Called at: LOGIN, LOGOUT, PASSWORD_CHANGE, PASSWORD_RESET,
USER_CREATE, USER_ENABLE, USER_DISABLE, EMP_CREATE, EMP_UPDATE, EMP_DELETE,
MP_SAVE, MP_UPDATE, MP_DELETE, CP_SAVE, CP_UPDATE, CP_DELETE,
PERF_IMPORT, DEPT_CREATE, LOC_SAVE

## Frontend (index.html) Structure
State object S{employees, mps, cps, roles, perf, cache, locations, sectors,
  bsToday, currentTab, authUser, activeDept, currentFY}
loadAll() → parallel fetch all → setAll() → render()
api wrapper: get(url), post(url,body), put(url,body), del(url)
Tabs: dashboard, team, master, data, reports, org
openModal(title, body, actions, wide) — modal system, no outside-click close
Toast notifications: toast(msg, 'ok'|'err')
renderUserBadge() — shows user info, dept switcher for master_admin, logout button
Quick Entry: openQuickEntry() with qeAutoCalc(), qeFilterMPs(), qeFilterCPs(), qeLoadTarget(), qeSave()

## UI Design System
Colors: --red:#ED1C24, --green:#16A34A, --amber:#D97706, --text:#1A1A1A, --border:#DDDDDD
Fonts: Syne (headings), Inter (body) from Google Fonts
Compliance cards: green≥95%, amber 80-94%, red<80%
Responsive grid: grid-3, grid-4 CSS classes
Brand: "SIPRADI TRADING PVT. LTD." in red header, "MPCP MANAGEMENT SYSTEM" subtitle

## Admin Panel HTML (ADMIN_HTML string in app.py)
Tabs: Users (create + table with edit/reset/toggle) + Audit Log (load via /api/audit_log)
User creation form: full_name, username, password, role, dept_code, emp_code
Audit log: table with ts, actor, action (color-coded), target, detail, ip
JS: switchAdminTab(), filterTable(), filterAudit(), loadAudit()

## Sample Data (seed on empty DB)
At least 5 employees across 2 levels, 3 MPs, 6 CPs, 10 perf records across 2 FYs

## File naming
- app.py (all backend, ~3500 lines)
- index.html (all frontend, ~300KB)
- data/master.db (auto-created)
- data/{dept_code}.db (auto-created per dept)
- data/secret.key (auto-generated Flask secret)

Run with: python app.py → http://localhost:5050
Default login: admin / admin123
```

---

*MPCP Management System v3.0 — Sipradi Trading Pvt. Ltd.*
*© Govinda Upadhyay — Internal Use Only*
*Built with Flask + SQLite + Vanilla JS — No framework, no build step, runs anywhere Python runs*
