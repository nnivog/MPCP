# MPCP Management System — Complete Technical Manual & Architectural Guide
### Managing Point & Checking Point Control System v3.0
**Sipradi Trading Pvt. Ltd. — Logistics Department**
*Prepared by: Govinda Upadhyay | Stack: Flask + SQLite + Vanilla JS*

---

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Database Design](#3-database-design)
4. [Authentication & Access Control](#4-authentication--access-control)
5. [API Reference](#5-api-reference)
6. [Frontend Structure](#6-frontend-structure)
7. [Core Modules](#7-core-modules)
8. [Reports & Analytics](#8-reports--analytics)
9. [Audit Log System](#9-audit-log-system)
10. [Data Flow Diagrams](#10-data-flow-diagrams)
11. [User Manual](#11-user-manual)
12. [Deployment Guide](#12-deployment-guide)

---

## 1. System Overview

MPCP is an internal KPI compliance tracking system for Sipradi's Logistics department. It tracks whether employees are meeting their assigned Managing Points (MPs) and Checking Points (CPs) each month in the Nepali Bikram Sambat calendar.

### What It Tracks
- **Managing Points (MPs)** — Top-level KPI categories assigned to a department or role (e.g., "Vehicle Border Tracking", "Goods SLA Delivery")
- **Checking Points (CPs)** — Specific measurable sub-indicators under each MP (e.g., "CC within 3 Days", "Registration within 15 Days")
- **Performance Records** — Monthly actual vs. target entries per employee per CP, recorded in BS calendar months
- **Compliance Status** — Each record is either Compliant (C) or Non-Compliant (NC) based on actual vs. target

### Key Metrics
- Compliance % per employee, per MP, per CP, per location, per sector
- YoY comparison across fiscal years (FY format: 2081-82, 2082-83)
- Exception tracking (overdue or non-compliant records)
- KPI trend charts per employee across months

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Browser (Client)                   │
│  Single HTML file (index.html) — 208 JS functions   │
│  Chart.js for visualizations                        │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / JSON API
┌──────────────────────▼──────────────────────────────┐
│              Flask App (app.py)                      │
│  81 API routes — Python 3.x                         │
│  Session-based auth — before_request guard          │
│  openpyxl for Excel I/O                             │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
┌──────────▼──────────┐  ┌───────▼─────────────────┐
│   master.db          │  │  {dept_code}.db           │
│  (shared/global)     │  │  (per department)         │
│  - users             │  │  - employees              │
│  - departments       │  │  - mps                    │
│  - audit_log         │  │  - cps                    │
└─────────────────────┘  │  - roles                  │
                          │  - perf                   │
                          │  - cascade links          │
                          │  - locations              │
                          │  - sectors                │
                          └───────────────────────────┘
```

### File Structure
```
mpcp/
├── app.py              # All backend logic (~3,400 lines, 81 routes)
├── index.html          # Entire frontend (~208 JS functions, single file)
├── data/
│   ├── master.db       # Users, departments, audit log
│   ├── logistics.db    # Logistics dept data
│   └── salesmarketing.db
└── .github/workflows/  # CI/CD (optional HF deploy)
```

### Technology Choices
| Layer | Technology | Reason |
|---|---|---|
| Backend | Flask (Python) | Lightweight, fast to develop |
| Database | SQLite | Zero-config, file-based, portable |
| Frontend | Vanilla JS | No build step, fast load |
| Charts | Chart.js | Rich, free, CDN-loaded |
| Excel I/O | openpyxl | Full xlsx read/write |
| Calendar | Custom BS logic | Nepali BS calendar support |
| Auth | Flask sessions | Simple, stateless |

---

## 3. Database Design

### master.db — Global / Shared

#### `users` table
| Column | Type | Description |
|---|---|---|
| id | TEXT PK | UUID |
| username | TEXT UNIQUE | Login username |
| password_hash | TEXT | PBKDF2 hash |
| full_name | TEXT | Display name |
| role | TEXT | master_admin / dept_admin / moderator / user |
| dept_code | TEXT | Linked department (null = master) |
| emp_code | TEXT | Linked employee code |
| active | INTEGER | 1=active, 0=disabled |
| created_at | TEXT | ISO timestamp |

#### `departments` table
| Column | Type | Description |
|---|---|---|
| id | TEXT PK | UUID |
| code | TEXT | Short code (e.g., "logistics") |
| name | TEXT | Display name |
| active | INTEGER | Active status |
| created_at | TEXT | ISO timestamp |

#### `audit_log` table
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| ts | TEXT | UTC timestamp |
| actor_id | TEXT | User ID who performed action |
| actor_name | TEXT | Display name |
| action | TEXT | Event code (LOGIN, EMP_UPDATE, etc.) |
| target_type | TEXT | What was affected (employee, mp, cp, user) |
| target_id | TEXT | ID of affected record |
| detail | TEXT | Human-readable change description |
| ip | TEXT | Client IP address |

---

### {dept}.db — Per Department

#### `employees` table
| Column | Type | Description |
|---|---|---|
| id | TEXT PK | UUID |
| emp_code | TEXT | Employee code (EMP000XXX) |
| name | TEXT | Full name |
| role | TEXT | Job title/designation |
| level | INTEGER | 1=HOD, 2=Supervisor, 3=Operations |
| dept | TEXT | Sub-department/sector |
| manager_id | TEXT | FK → employees.id |
| email | TEXT | Email address |

#### `mps` table — Managing Points
| Column | Type | Description |
|---|---|---|
| id | TEXT PK | UUID |
| ref | TEXT | Reference code (HOD-MP-1) |
| title | TEXT | MP name |
| target | TEXT | Target description |
| freq | TEXT | Daily/Weekly/Monthly/Quarterly |
| kpi_c | REAL | KPI weight for compliant |
| kpi_nc | REAL | KPI weight for non-compliant |
| kpi_total | REAL | Total KPI weight |
| created_at | TEXT | Timestamp |

#### `cps` table — Checking Points
| Column | Type | Description |
|---|---|---|
| id | TEXT PK | UUID |
| ref | TEXT | Reference code (LM-VEH-1) |
| title | TEXT | CP name |
| mp_id | TEXT | FK → mps.id |
| target_val | REAL | Numeric target |
| unit | TEXT | %, Days, Count, etc. |
| freq | TEXT | Frequency |
| better | TEXT | Higher/Lower (direction) |
| created_at | TEXT | Timestamp |

#### `perf` table — Performance Records
| Column | Type | Description |
|---|---|---|
| id | TEXT PK | UUID |
| fy | TEXT | Fiscal year (2081-82) |
| bs_month | TEXT | BS month name (Shrawan…Ashadh) |
| quarter | TEXT | Q1/Q2/Q3/Q4 |
| emp_id | TEXT | FK → employees.id |
| emp_code | TEXT | Employee code |
| mp_ref | TEXT | MP reference |
| cp_ref | TEXT | CP reference |
| metric | TEXT | Metric description |
| total | REAL | Total count/volume |
| compliant | REAL | Compliant count |
| non_compliant | REAL | Non-compliant count |
| pct_compliant | REAL | Compliance % |
| pct_nc | REAL | Non-compliance % |
| target_val | REAL | Target value |
| actual_val | REAL | Actual achieved |
| unit | TEXT | Unit of measure |
| status | TEXT | C (Compliant) / NC (Non-Compliant) |
| notes | TEXT | Free text notes |
| loc | TEXT | Location (auto-populated from emp_locations) |

#### Junction Tables
| Table | Links |
|---|---|
| emp_roles | employees ↔ roles |
| emp_mps | employees ↔ mps |
| emp_cps | employees ↔ cps |
| mp_owners | mps ↔ employees (ownership) |
| cp_owners | cps ↔ employees (ownership) |
| emp_sectors | employees ↔ sectors |
| emp_locations | employees ↔ locations |
| role_mps | roles ↔ mps |
| role_cps | roles ↔ cps |

---

## 4. Authentication & Access Control

### Roles
| Role | Access Level |
|---|---|
| **master_admin** | Full access to all departments, admin panel, user management |
| **dept_admin** | Full access within own department only |
| **moderator** | Read + limited write within own department |
| **user** | Read-only within own department |

### Auth Flow
```
Browser Request
      │
      ▼
before_request auth_guard()
      │
      ├─ /login, /logout, /change_password → PASS (public)
      ├─ /static/* → PASS
      │
      └─ session['mpcp_user'] exists?
            ├─ NO  → redirect /login (or 401 for API calls)
            └─ YES → continue to route handler
```

### Department Isolation (`get_db()`)
```python
def get_db(dept_override=None):
    user = session.get('mpcp_user')
    if role == 'master_admin':
        dept = dept_override or request.args.get('dept') or user.get('active_dept')
        path = get_dept_db_path(dept) if dept else DB  # master DB fallback
    else:
        path = get_dept_db_path(user['dept_code'])  # ALWAYS own dept
    return sqlite3.connect(path)
```

**master_admin** can switch departments via the dept switcher dropdown in the header. All other roles are locked to their assigned department and cannot bypass this.

### Session Structure
```json
{
  "id": "uuid",
  "username": "govinda",
  "full_name": "Govinda Upadhyay",
  "role": "master_admin",
  "dept_code": null,
  "dept_name": "All Departments",
  "emp_code": "EMP000513",
  "active_dept": "logistics"
}
```

---

## 5. API Reference

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/login` | Login page and form handler |
| GET | `/logout` | Clear session and redirect |
| GET/POST | `/change_password` | Self-service password change (public) |
| POST | `/api/change_password` | API password change (authenticated) |
| GET | `/api/auth/me` | Get current user info |
| POST | `/api/auth/switch_dept` | master_admin switches active department |

### Employees
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/employees` | List all / Create employee |
| PUT/DELETE | `/api/employees/<eid>` | Update / Delete employee |
| GET/POST | `/api/emp_links/<eid>` | Get/Set role+MP+CP assignments |
| GET | `/api/employees/template` | Download Excel import template |
| POST | `/api/employees/import` | Bulk import from Excel/CSV |
| POST | `/api/employees/bulk_delete` | Delete multiple employees |

### Managing Points (MPs)
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/mps` | List all / Create MP |
| PUT/DELETE | `/api/mps/<mid>` | Update / Delete MP |
| POST | `/api/mps/import_excel` | Import MPs from Excel |
| GET | `/api/mps/template_excel` | Download MP import template |
| POST | `/api/mps/bulk_delete` | Delete multiple MPs |

### Checking Points (CPs)
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/cps` | List all / Create CP |
| PUT/DELETE | `/api/cps/<cid>` | Update / Delete CP |
| POST | `/api/cps/import_excel` | Import CPs from Excel |
| GET | `/api/cps/template_excel` | Download CP import template |
| POST | `/api/cps/bulk_delete` | Delete multiple CPs |

### Performance Records
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/perf` | List / Add performance record |
| POST | `/api/perf/quick` | Quick single-entry save |
| GET | `/api/perf/exceptions` | List non-compliant / overdue records |
| GET | `/api/perf/template` | Download full performance Excel template |
| GET | `/api/perf/simple_template` | Download simple entry template |
| POST | `/api/perf/import` | Import performance data from Excel |
| POST | `/api/perf/import_simple` | Import from simple template |
| GET | `/api/perf/export` | Export all perf records to Excel |
| PUT/DELETE | `/api/perf/<pid>` | Update / Delete single record |
| POST | `/api/perf/bulk_delete` | Delete multiple records |
| POST | `/api/perf/bulk_delete_fy` | Delete all records for a FY |

### FY Cache Management
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/cache` | List FY profiles / Create new FY |
| POST | `/api/cache/<fy>/clear` | Clear all performance data for FY |
| POST | `/api/cache/<fy>/lock` | Lock/unlock a FY |
| DELETE | `/api/cache/<fy>` | Delete entire FY profile and data |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/analytics/summary` | Overall compliance summary |
| GET | `/api/analytics/summary_yoy` | Year-over-Year comparison data |
| GET | `/api/analytics/widget` | Dashboard widget data |
| GET | `/api/analytics/by_location` | Compliance grouped by location |
| GET | `/api/analytics/by_sector` | Compliance grouped by sector/dept |
| GET | `/api/analytics/employee_trend/<emp_code>` | Monthly trend per employee |

### Exports
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/export/org_tree_html` | Export org chart as HTML |
| GET | `/api/export/employee_mpcp_excel/<eid>` | Individual employee MPCP report |
| GET | `/api/export/team_mpcp_excel` | Full team MPCP workbook |
| GET | `/api/export/sector_summary_excel` | Sector compliance summary |
| GET | `/api/export/employee_mpcp_html/<eid>` | Individual MPCP as printable HTML |

### Organization & Cascade
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/org/tree` | Full org hierarchy with compliance rollup |
| POST | `/api/org/move` | Move employee in org chart |
| POST | `/api/org/assign_mp` | Assign MP to org node |
| POST | `/api/org/assign_cp` | Assign CP to org node |
| GET/POST | `/api/cascade` | List / Create cascade links |
| DELETE | `/api/cascade/<lid>` | Remove cascade link |
| GET | `/api/cascade/tree` | Full cascade tree structure |
| POST | `/api/org/cascade_assign` | Assign cascade relationships |

### Master Data
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/roles` | Manage role templates |
| PUT/DELETE | `/api/roles/<rid>` | Update/Delete role |
| GET/POST | `/api/sectors` | Manage sectors |
| PUT/DELETE | `/api/sectors/<sid>` | Update/Delete sector |
| GET/POST | `/api/locations` | Manage locations |
| PUT/DELETE | `/api/locations/<lid>` | Update/Delete location |
| GET/POST | `/api/departments` | Manage departments (master_admin only) |
| PUT/DELETE | `/api/departments/<did>` | Update/Delete department |
| GET/POST | `/api/users` | Manage users |
| PUT/DELETE | `/api/users/<uid>` | Update/Delete user |

### Admin Panel (master_admin only)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin` | Admin panel — Users tab |
| POST | `/admin/users/create` | Create new user |
| POST | `/admin/users/<uid>/reset` | Reset user password |
| POST | `/admin/users/<uid>/toggle` | Enable/disable user |
| GET | `/api/audit_log` | Fetch audit log (last 200 records) |

### Utilities
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/fy_from_date` | Convert ISO date to BS FY |
| GET | `/api/bs_today` | Get today's BS date |
| GET | `/api/calendar` | BS calendar data |
| GET | `/api/master/summary` | Global summary stats |
| GET/POST | `/api/dashboard_layouts` | Save/load dashboard widget layouts |

---

## 6. Frontend Structure

### Tab Navigation
```
Main Tabs:
├── 📊 Dashboard    — KPI summary cards, widgets, charts
├── 👥 Team         — Employee cards (Level 1/2/3), org chart
├── 🏗 Master       — MPs, CPs, Roles, Locations, Sectors, Departments
├── 📋 Data         — Performance records table, quick entry
├── 📈 Reports      — Overview, Location/Sector, YoY, Employee, MPCP
├── 🌐 Org          — Org tree, cascade builder, assignment panel
└── 📍 Locations    — Location master and assignment
```

### State Object (S)
All application state lives in a single global object:
```javascript
S = {
  employees: [],      // All employees for active dept
  mps: [],           // All Managing Points
  cps: [],           // All Checking Points
  perf: [],          // All performance records
  cache: [],         // FY profiles
  roles: [],         // Role templates
  locations: [],     // Locations
  sectors: [],       // Sectors
  authUser: {},      // Current logged-in user
  activeDept: null,  // Active department code
  currentFY: '2081-82',  // Active fiscal year
  currentTab: 'dashboard',
  masterSub: 'mps',      // Active master sub-tab
  reportSub: 'overview', // Active report sub-tab
}
```

### Data Loading (`loadAll()`)
On every page load or after any mutation:
```javascript
async function loadAll() {
  const [employees, mps, cps, roles, perf, cache, 
         locations, cascade, bsToday, layouts, sectors] 
    = await Promise.all([
      safeGet('/api/employees', []),
      safeGet('/api/mps', []),
      safeGet('/api/cps', []),
      safeGet('/api/roles', []),
      safeGet('/api/perf', []),
      safeGet('/api/cache', []),
      safeGet('/api/locations', []),
      safeGet('/api/cascade', []),
      safeGet('/api/bs_today', {}),
      safeGet('/api/dashboard_layouts', []),
      safeGet('/api/sectors', []),
  ])
  // Assign to S.* and re-render current tab
}
```

All 11 API calls run in parallel on every `loadAll()`. This ensures the UI is always in sync with the database.

### Rendering Pipeline
```
User Action
    │
    ▼
API Call (fetch/POST)
    │
    ▼
loadAll() — refreshes all state
    │
    ▼
render() — routes to current tab renderer
    │
    ├── renderDashboard()
    ├── renderTeam()
    ├── renderMaster() → renderMPs() / renderCPs() / renderRoles() ...
    ├── renderData() → renderPerfData()
    ├── renderReport() → renderOverviewReport() / renderLocationReport() ...
    └── renderOrgTab() → renderOrgTree() / renderCascadeBuilder() ...
```

---

## 7. Core Modules

### 7.1 Nepali BS Calendar
The system uses Bikram Sambat calendar for all date references.

- **FY Format**: `2081-82` (Shrawan 2081 to Ashadh 2082)
- **Months**: Shrawan, Bhadra, Ashwin, Kartik, Mangsir, Poush, Magh, Falgun, Chaitra, Baisakh, Jestha, Ashadh
- **Quarters**: Q1 (Shrawan-Ashwin), Q2 (Kartik-Poush), Q3 (Magh-Chaitra), Q4 (Baisakh-Ashadh)
- **API**: `/api/fy_from_date?date=2025-07-17` → returns `{fy: "2082-83", bs_month: "Shrawan"}`

### 7.2 Compliance Calculation
```
status = 'C' if:
  - unit = '%' and actual >= target
  - unit = 'Days' and better = 'Lower' and actual <= target
  - unit = 'Days' and better = 'Higher' and actual >= target
  - unit = 'Count' and actual >= target

pct_compliant = (compliant / total) × 100
```

### 7.3 Role Templates
Roles are reusable bundles of MPs and CPs. Assigning a role to an employee automatically assigns all linked MPs and CPs.

```
Role Template (e.g., "Logistics Officer")
    ├── MP: Vehicle Border Tracking
    │     ├── CP: CC within 3 Days
    │     └── CP: Documentation Accuracy
    └── MP: Goods SLA Delivery
          └── CP: Delivery within SLA
```

### 7.4 Cascade System
The cascade system defines superior-subordinate relationships for performance delegation. When a HOD's CP is linked in cascade to a subordinate's CP, the subordinate's performance feeds into the HOD's compliance score.

### 7.5 Dashboard Builder
Users can create custom dashboard layouts by dragging and dropping widget types:
- Overall Compliance %
- Top Non-Compliant MPs
- Location Heatmap
- Sector Breakdown
- Monthly Trend
- Exception Count

Layouts are saved per user in `dashboard_layouts` table.

---

## 8. Reports & Analytics

### Overview Report
- Total records, compliant count, NC count, overall compliance %
- Risk MPs (lowest compliance)
- Monthly trend bar chart
- Top performers and bottom performers

### Location & Sector Report
- Per-location compliance cards with color-coded bars (green ≥95%, amber ≥80%, red <80%)
- Per-sector breakdown
- FY selector dropdown
- Compare two FYs side-by-side with delta indicators (▲▼)

### Year-over-Year (YoY) Report
- Side-by-side compliance % for each FY
- Trend direction per MP/CP
- Data sourced from `/api/analytics/summary_yoy`

### Employee MPCP Report
- Per-employee compliance table showing each CP, target, actual, status
- Downloadable as Excel (`/api/export/employee_mpcp_excel/<eid>`)
- Printable as HTML (`/api/export/employee_mpcp_html/<eid>`)

### KPI Trend Chart (Per Employee)
- Line chart showing monthly compliance % per FY
- FY selector to filter or view all FYs overlaid
- Summary stats: Avg, Best Month, Worst Month, Total Data Points
- Accessible from Team tab → employee card → 📈 Trend button

### Export Bar (Reports Tab)
Available exports in the reports toolbar:
- **Compliance Excel** — Full compliance data table
- **Team MPCP Book** — Workbook with one sheet per employee
- **Sector Summary** — Sector-wise compliance summary

---

## 9. Audit Log System

### Events Captured (19 total)
| Event Code | Trigger | Detail Captured |
|---|---|---|
| LOGIN | Successful login | Username, role |
| LOGOUT | Session end | — |
| PASSWORD_CHANGE | Self-service change | User ID |
| PASSWORD_RESET | Admin reset | Target user |
| USER_CREATE | New user created | Username, role, dept |
| USER_ENABLE | Account re-enabled | User ID |
| USER_DISABLE | Account disabled | User ID |
| EMP_CREATE | Employee added/imported | Employee ID |
| EMP_UPDATE | Employee record edited | **Field diffs** (e.g., Role: X → Y) |
| EMP_DELETE | Employee deleted | Name + Emp Code |
| MP_SAVE | MP created | MP ID |
| MP_UPDATE | MP edited | **Field diffs** (Ref, Title, Target, Freq) |
| MP_DELETE | MP deleted | Ref + Title |
| CP_SAVE | CP created | CP ID |
| CP_UPDATE | CP edited | CP ID |
| CP_DELETE | CP deleted | CP ID |
| PERF_IMPORT | Bulk perf import | Record count |
| DEPT_CREATE | Department created | — |
| LOC_SAVE | Location saved | Location ID |

### Viewing the Audit Log
Go to `/admin` → click **📋 Audit Log** tab → click **⟳ Refresh**

The log displays human-readable descriptions:
```
🔑  Master Admin signed in as Master Admin          127.0.0.1   2026-05-11 05:59
✏️  govinda edited an employee profile              127.0.0.1   2026-05-11 05:54
    Role: Officer → Manager; Dept: CVBU → EXIDE
🗑️  govinda deleted: Laxmi Shrestha (EMP000105)    127.0.0.1   2026-05-11 05:54
```

---

## 10. Data Flow Diagrams

### Performance Entry Flow
```
User opens Quick Entry modal
         │
         ▼
Selects Employee → FY auto-detected from BS date
         │
         ▼
System loads employee's CPs from emp_cps junction
         │
         ▼
User enters actual values for each CP
         │
         ▼
POST /api/perf/quick
         │
         ▼
Backend calculates status (C/NC) per record
         │
         ▼
INSERT OR IGNORE INTO perf (with loc auto-populated)
         │
         ▼
log_audit('PERF_IMPORT', ...)
         │
         ▼
loadAll() → re-render Dashboard + Data tab
```

### Compliance Calculation Flow
```
GET /api/analytics/summary?fys=2081-82,2082-83
         │
         ▼
Query perf table grouped by fy, emp_code, cp_ref
         │
         ▼
For each record: status='C' → compliant++
         │
         ▼
pct = (compliant / total) × 100
         │
         ▼
Return JSON: {total, compliant, nc, pct_c, by_mp, by_cp, by_emp}
         │
         ▼
Frontend renderOverviewReport() renders cards + chart
```

### Employee Import Flow
```
User clicks ⬆ Import Excel in Team tab
         │
         ▼
File picker opens (accepts .xlsx, .csv)
         │
         ▼
POST /api/employees/import (multipart/form-data)
         │
         ▼
Backend reads headers: emp_code, name, role, level,
         department, manager_code, email
         │
         ▼
For each row: INSERT OR REPLACE INTO employees
         │
         ▼
Second pass: resolve manager_code → manager_id
         │
         ▼
log_audit('EMP_CREATE', ...)
         │
         ▼
Return {imported: N, errors: [...]}
         │
         ▼
Frontend toast: "Imported 25 employees"
loadAll() → renderTeam()
```

---

## 11. User Manual

### Getting Started

#### Logging In
1. Navigate to `http://[server]:5050`
2. Enter your username and password
3. If you need to change your password before logging in, click **🔒 Change Password** below the login form

#### First-Time Setup (master_admin)
1. Go to **Master → Departments** → create your departments
2. Go to **Admin Panel** (`/admin`) → create users and assign departments
3. Switch to a department using the dept switcher in the top-right

#### Setting Up a Department
1. **Master → Locations** → add branch/office locations
2. **Master → Sectors** → add sector/sub-department groupings
3. **Team tab** → add employees (or use ⬆ Import Excel)
4. **Master → MPs** → create Managing Points (or import from Excel template)
5. **Master → CPs** → create Checking Points linked to MPs
6. **Master → Roles** → create role templates bundling MPs+CPs
7. **Org tab → Assignment** → assign roles to employees

### Recording Performance
1. Go to **Data tab**
2. Click **+ Quick Entry** to add a single record
   - Select Employee, FY is auto-detected
   - Enter actual vs target for each CP
   - System auto-calculates Compliant/NC status
3. For bulk entry: download the **Excel Template** → fill in data → **Upload**

### Reading Reports
- **Dashboard** — Real-time KPI cards and compliance %
- **Reports → Overview** — Summary with risk MPs and monthly trend
- **Reports → Location/Sector** — Compliance by branch or team
- **Reports → YoY** — Year-over-year comparison
- **Reports → Employee** — Individual staff compliance
- **Team tab → 📈 Trend** — Monthly KPI trend chart per employee

### Exporting Data
| What | How |
|---|---|
| Individual employee report | Team tab → employee card → Profile → Download Excel |
| Full team workbook | Reports tab → Export → Team MPCP Book |
| Sector summary | Reports tab → Export → Sector Summary |
| All performance records | Data tab → Export |

### Admin Tasks (master_admin only)
| Task | Where |
|---|---|
| Create/disable users | `/admin` → Users tab |
| Reset user password | `/admin` → Users → Reset button |
| View audit log | `/admin` → Audit Log tab → Refresh |
| Switch departments | Header dropdown (top-right) |
| Create departments | Master → Departments |

---

## 12. Deployment Guide

### Local Development
```bash
cd ~/mpcp
python app.py
# Runs on http://127.0.0.1:5050
```

### Environment Variables
| Variable | Default | Description |
|---|---|---|
| `MPCP_DATA_DIR` | `./data` | Directory for all SQLite databases |
| `MPCP_SECRET_KEY` | Random | Flask session secret key (set in production) |
| `PORT` | 5050 | Server port |

### Production Considerations
1. Set a fixed `SECRET_KEY` in app.py or environment (sessions will break on restart otherwise)
2. Use a WSGI server: `gunicorn app:app -w 2 -b 0.0.0.0:5050`
3. Back up the `/data` directory regularly — all data lives in SQLite files
4. For multi-user concurrent access, consider migrating to PostgreSQL

### Backup Procedure
```bash
# Backup all databases
cp -r ~/mpcp/data ~/mpcp/data_backup_$(date +%Y%m%d)

# Or zip
zip -r mpcp_backup_$(date +%Y%m%d).zip ~/mpcp/data
```

### Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`
- ⚠️ Change immediately after first login via `/change_password`

---

## Appendix: Quick Reference

### BS Month → Quarter Mapping
| Months | Quarter |
|---|---|
| Shrawan, Bhadra, Ashwin | Q1 |
| Kartik, Mangsir, Poush | Q2 |
| Magh, Falgun, Chaitra | Q3 |
| Baisakh, Jestha, Ashadh | Q4 |

### Compliance Color Codes
| Color | Threshold | Meaning |
|---|---|---|
| 🟢 Green | ≥ 95% | On target |
| 🟡 Amber | 80–94% | Needs attention |
| 🔴 Red | < 80% | Critical |

### Role Hierarchy
| Level | Role | Typical Title |
|---|---|---|
| 1 | HOD | Head of Department / AGM |
| 2 | Supervisor | Deputy Manager / Senior Officer |
| 3 | Operations | Officer / Executive |

---

*MPCP Management System v3.0 — Sipradi Trading Pvt. Ltd.*
*© Govinda Upadhyay — Internal Use Only*
