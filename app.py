"""
Sipradi SC-MPCP Control System  v2.0
Flask + SQLite | python app.py | http://localhost:5050
"""
from flask import Flask, jsonify, request, send_file
import sqlite3, csv, io, os, json, datetime, random, string

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

app = Flask(__name__)
DB  = os.path.join(os.path.dirname(__file__), "scm.db")

# -- BIKRAM SAMWAT CALENDAR (precise dates) -----------------------------------
# -- BIKRAM SAMWAT CALENDAR (precise dates) -----------------------------------
BS_MONTHS = ['Baisakh','Jestha','Ashadh','Shrawan','Bhadra','Ashwin',
             'Kartik','Mangsir','Poush','Magh','Falgun','Chaitra']
BS_MONTH_DAYS = {
    2078:[31,31,32,32,31,30,30,29,30,29,30,30],
    2079:[31,32,31,32,31,30,30,30,29,29,30,30],
    2080:[31,32,31,32,31,30,30,30,29,30,29,31],
    2081:[31,31,32,32,31,30,30,30,29,30,30,30],
    2082:[31,32,31,32,31,30,30,30,29,30,29,31],
}
BS_DEFAULT_DAYS=[31,32,31,32,31,30,30,30,29,30,29,31]
BS_FY_Q={'Shrawan':'Q1','Bhadra':'Q1','Ashwin':'Q1',
         'Kartik':'Q2','Mangsir':'Q2','Poush':'Q2',
         'Magh':'Q3','Falgun':'Q3','Chaitra':'Q3',
         'Baisakh':'Q4','Jestha':'Q4','Ashadh':'Q4'}
AD_TO_BS={
    'Jul':'Shrawan','Aug':'Bhadra','Sep':'Ashwin','Oct':'Kartik','Nov':'Mangsir','Dec':'Poush',
    'Jan':'Magh','Feb':'Falgun','Mar':'Chaitra','Apr':'Baisakh','May':'Jestha','Jun':'Ashadh',
    'July':'Shrawan','August':'Bhadra','September':'Ashwin','October':'Kartik',
    'November':'Mangsir','December':'Poush','January':'Magh','February':'Falgun',
    'March':'Chaitra','April':'Baisakh','June':'Ashadh'}

def bs_days_in_month(year,month_idx):
    return (BS_MONTH_DAYS.get(year,BS_DEFAULT_DAYS))[month_idx]

def bs_month_idx(mn):
    try: return BS_MONTHS.index(mn)
    except: return 0

def norm_month(m):
    m=str(m or '').strip()
    if m in BS_MONTHS: return m
    if m in AD_TO_BS: return AD_TO_BS[m]
    for bs in BS_MONTHS:
        if m.lower()==bs.lower(): return bs
    for ad,bs in AD_TO_BS.items():
        if m.lower()==ad.lower(): return bs
    try:
        idx=int(m)-1
        if 0<=idx<12: return BS_MONTHS[idx]
    except: pass
    return m or 'Shrawan'

def bs_date_str(year,month_name,day):
    idx=bs_month_idx(month_name)
    return f'{year}-{idx+1:02d}-{int(day):02d}'

def today_bs():
    import datetime
    ad=datetime.date.today()
    bs_year=ad.year+56
    ad_to_bs_m=[
        (1,1,'Poush'),(2,1,'Magh'),(3,1,'Falgun'),
        (4,1,'Chaitra'),(4,14,'Baisakh'),(5,15,'Jestha'),
        (6,16,'Ashadh'),(7,1,'Shrawan'),(8,1,'Bhadra'),
        (9,1,'Ashwin'),(10,1,'Kartik'),(11,1,'Mangsir'),(12,1,'Poush')
    ]
    bs_month='Shrawan'
    for (m,d,bsm) in reversed(ad_to_bs_m):
        if (ad.month,ad.day)>=(m,d): bs_month=bsm; break
    return bs_date_str(bs_year,bs_month,ad.day)

def current_bs_fy():
    import datetime
    ad=datetime.date.today()
    bs_year=ad.year+56
    if ad.month<4 or (ad.month==4 and ad.day<14): bs_year-=1
    return f'{bs_year}-{str(bs_year+1)[-2:]}'

def bs_q(month): return BS_FY_Q.get(month,'Q1')

def uid(): return ''.join(random.choices(string.ascii_lowercase+string.digits,k=8))
def get_db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); return c
def R(rows): return [dict(r) for r in rows]

def calc_status(actual, target, unit):
    try: a,t = float(actual), float(target)
    except: return "C"
    lb = any(u in str(unit).lower() for u in ["day","hour","hr"])
    return "C" if (a<=t*1.05 if lb else a>=t*0.95) else "NC"

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees(
  id TEXT PRIMARY KEY, emp_code TEXT UNIQUE,
  name TEXT NOT NULL, role TEXT DEFAULT '', level INTEGER DEFAULT 3,
  dept TEXT DEFAULT 'Ops', manager_id TEXT, email TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS mps(
  id TEXT PRIMARY KEY, ref TEXT NOT NULL, title TEXT NOT NULL,
  target TEXT DEFAULT '', freq TEXT DEFAULT 'Monthly',
  kpi_c INTEGER DEFAULT 0, kpi_nc INTEGER DEFAULT 0, kpi_total INTEGER DEFAULT 0,
  parent_cp_id TEXT DEFAULT '', emp_level INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS mp_owners(mp_id TEXT, emp_id TEXT, PRIMARY KEY(mp_id,emp_id));
CREATE TABLE IF NOT EXISTS cps(
  id TEXT PRIMARY KEY, ref TEXT NOT NULL, title TEXT NOT NULL,
  target TEXT DEFAULT '', freq TEXT DEFAULT 'Daily',
  source TEXT DEFAULT '', mp_id TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS cp_owners(cp_id TEXT, emp_id TEXT, PRIMARY KEY(cp_id,emp_id));
CREATE TABLE IF NOT EXISTS roles(
  id TEXT PRIMARY KEY, code TEXT NOT NULL, name TEXT NOT NULL,
  description TEXT DEFAULT '', color TEXT DEFAULT '#1d4ed8',
  emp_level INTEGER DEFAULT 1, parent_role_id TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS role_mps(role_id TEXT, mp_id TEXT, PRIMARY KEY(role_id,mp_id));
CREATE TABLE IF NOT EXISTS role_cps(role_id TEXT, cp_id TEXT, PRIMARY KEY(role_id,cp_id));
CREATE TABLE IF NOT EXISTS emp_roles(emp_id TEXT, role_id TEXT, PRIMARY KEY(emp_id,role_id));
CREATE TABLE IF NOT EXISTS cascade_links(
  id TEXT PRIMARY KEY,
  parent_emp_id TEXT NOT NULL, parent_cp_id TEXT NOT NULL,
  child_emp_id  TEXT NOT NULL, child_mp_id   TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS emp_mps(emp_id TEXT, mp_id TEXT, PRIMARY KEY(emp_id,mp_id));
CREATE TABLE IF NOT EXISTS emp_cps(emp_id TEXT, cp_id TEXT, PRIMARY KEY(emp_id,cp_id));
CREATE TABLE IF NOT EXISTS perf(
  id TEXT PRIMARY KEY, fy TEXT NOT NULL, bs_month TEXT NOT NULL,
  quarter TEXT DEFAULT 'Q1', emp_id TEXT DEFAULT '', emp_code TEXT DEFAULT '',
  mp_ref TEXT DEFAULT '', cp_ref TEXT DEFAULT '', metric TEXT DEFAULT '',
  total INTEGER DEFAULT 0, compliant INTEGER DEFAULT 0,
  non_compliant INTEGER DEFAULT 0,
  pct_compliant REAL DEFAULT 0, pct_nc REAL DEFAULT 0,
  target_val REAL DEFAULT 0, actual_val REAL DEFAULT 0,
  unit TEXT DEFAULT '%', status TEXT DEFAULT 'C', notes TEXT DEFAULT '',
  location TEXT DEFAULT '', bs_date TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS locations(
  id TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL, type TEXT DEFAULT 'Office',
  address TEXT DEFAULT '');

CREATE TABLE IF NOT EXISTS emp_locations(
  emp_id TEXT, loc_id TEXT, PRIMARY KEY(emp_id, loc_id));

CREATE TABLE IF NOT EXISTS cp_locations(
  cp_id TEXT, loc_id TEXT, PRIMARY KEY(cp_id, loc_id));

CREATE TABLE IF NOT EXISTS mp_locations(
  mp_id TEXT, loc_id TEXT, PRIMARY KEY(mp_id, loc_id));

CREATE TABLE IF NOT EXISTS perf_cache(
  fy TEXT PRIMARY KEY, label TEXT NOT NULL,
  record_count INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT, locked INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS dashboard_layouts(
  id TEXT PRIMARY KEY, name TEXT NOT NULL,
  user TEXT DEFAULT 'default',
  layout_json TEXT DEFAULT '[]',
  created_at TEXT, updated_at TEXT);

"""

def init_db():
    with get_db() as db:
        db.executescript(SCHEMA)
        if not db.execute("SELECT 1 FROM employees LIMIT 1").fetchone():
            _seed(db)

def _upd_cache(db, fy):
    cnt = db.execute("SELECT COUNT(*) FROM perf WHERE fy=?",(fy,)).fetchone()[0]
    now = datetime.datetime.now().isoformat()
    db.execute("INSERT OR IGNORE INTO perf_cache VALUES(?,?,?,?,?,?)",(fy,f"FY {fy}",cnt,now,now,0))
    db.execute("UPDATE perf_cache SET record_count=?,updated_at=? WHERE fy=?",(cnt,now,fy))

def _seed(db):
    emps=[
      ("e1","EMP-001","Govinda Upadhyay","Head of Department",1,"HOD",None,"govinda@sipradi.com"),
      ("e2","EMP-002","Sandeep Gupta Kanu","Vehicle Import & Logistics",2,"Vehicle","e1","sandeep@sipradi.com"),
      ("e3","EMP-003","Sagar Koirala","Custom Clearance Support",2,"Vehicle","e1","sagar@sipradi.com"),
      ("e4","EMP-004","Rajeshwori Maharjan","Registration & WOW Manager",2,"Registration","e1","rajeshwori@sipradi.com"),
      ("e5","EMP-005","Laxmi","Vehicle Registration Exec.",3,"Registration","e4","laxmi@sipradi.com"),
      ("e6","EMP-006","Ishwor Shrestha","Registration Process",3,"Registration","e4","ishwor@sipradi.com"),
      ("e7","EMP-007","Hari Prasad Pandey","Customs Agent Coord.",3,"Vehicle","e2","hari@sipradi.com"),
      ("e8","EMP-008","Aashish Patel","Physical Stock Verification",3,"Stock","e1","aashish@sipradi.com"),
      ("e9","EMP-009","Bipin KC","Vehicle Delivery",3,"Vehicle","e2","bipin@sipradi.com"),
      ("e10","EMP-010","Mahesh Adhikari","Vehicle Movement",3,"Vehicle","e2","mahesh@sipradi.com"),
      ("e11","EMP-011","Rose Basnet","Goods Receipt & GRN",2,"Warehouse","e1","rose@sipradi.com"),
      ("e12","EMP-012","Sanjay Rauniyar","Warehouse Receipt",3,"Warehouse","e11","sanjay@sipradi.com"),
      ("e13","EMP-013","Rabindra","Goods Clearance",3,"Warehouse","e11","rabindra@sipradi.com"),
      ("e14","EMP-014","Ranjit Chhetri","Goods Dispatch",3,"Warehouse","e11","ranjit@sipradi.com"),
      ("e15","EMP-015","Purshottam Kr. Patel","Border Clearance",3,"Warehouse","e11","purshottam@sipradi.com"),
      ("e16","EMP-016","Babim / Manoj","Operations Support",3,"Ops","e1","babim@sipradi.com"),
    ]
    db.executemany("INSERT OR IGNORE INTO employees VALUES(?,?,?,?,?,?,?,?)",emps)
    mps=[
      ("mp1","HODL-1","Fully compliant and timely vehicle import","1 Day","Monthly",3183,116,3299),
      ("mp2","HODL-2","100% NIAC Claim resolution within 120 Days","120 Days","Fortnightly",0,0,0),
      ("mp3","HODL-3","Error and Penalty free registration process","15 Days","Fortnightly",1420,219,1639),
      ("mp4","HODL-4","100% ownership requests timebound","3 Days","Weekly",1531,108,1639),
      ("mp5","HODL-5","Vehicle readiness and driver arrangements within 24hrs","24 Hours","Fortnightly",3396,70,3466),
      ("mp6","HODL-6","Vehicle delivery hygiene and cost control","24 Hours","Quarterly",5580,300,5880),
      ("mp7","HODL-7","100% WOW update within 15 days CV / 10 days PV","10-15 Days","Monthly",0,0,0),
      ("mp8","HODL-8","Monthly physical verification of new vehicles","Monthly","Monthly",174,0,174),
      ("mp9","HODL-9","Goods availability within 5 days of border arrival","5 Days","Fortnightly",127,9,136),
      ("mp10","HODL-10","Performance visibility and cost optimization 20% reduction","20% Reduction","Monthly",1194,445,1639),
      ("mp11","HODL-11","Employee motivation and process capability","Per Calendar","Quarterly",0,0,0),
      ("mp12","HODL-12","Strengthen monitoring and review mechanism","Fortnightly","Fortnightly",0,0,0),
    ]
    # mps seed: pad with empty parent_cp_id and default emp_level=1
    mps_padded = [m+('',1) if len(m)==8 else m for m in mps]
    db.executemany("INSERT OR IGNORE INTO mps VALUES(?,?,?,?,?,?,?,?,?,?)",mps_padded)
    mpo=[("mp1","e2"),("mp1","e3"),("mp2","e2"),("mp2","e3"),("mp3","e2"),("mp3","e4"),
         ("mp4","e4"),("mp4","e2"),("mp5","e2"),("mp5","e3"),("mp5","e10"),("mp6","e2"),
         ("mp6","e3"),("mp6","e10"),("mp7","e4"),("mp8","e4"),("mp8","e8"),("mp9","e2"),
         ("mp9","e11"),("mp9","e14"),("mp10","e4"),("mp10","e2"),("mp10","e11"),("mp12","e4")]
    db.executemany("INSERT OR IGNORE INTO mp_owners VALUES(?,?)",mpo)
    cps=[
      ("cp1","LM-VEH-1","Tracking of New Vehicles till arrival at border","100%","Monthly","Manual","mp1"),
      ("cp2","LM-VEH-2-B","On time custom clearance within 3 days of CC memo","3 Days","Daily","System","mp1"),
      ("cp3","LM-VEH-2-S","Custom clearance monitoring","3 Days","Daily","System","mp1"),
      ("cp4","LM-VEH-3-B","100% vehicles with valid GST before expiry","90 Days","Weekly","System","mp1"),
      ("cp5","LM-VEH-3-S","GST validity monitoring","90 Days","Weekly","System","mp1"),
      ("cp6","LM-VEH-4-B","100% POE submission within 90 days of CC","90 Days","Weekly","Manual","mp1"),
      ("cp7","LM-VEH-4-S","POE submission monitoring","90 Days","Weekly","","mp1"),
      ("cp8","LM-VEH-5-B","Registration of Vehicles within 15 Days of PP","15 Days","Weekly","System","mp3"),
      ("cp9","LM-VEH-5-A","Registration tracking","15 Days","Weekly","","mp3"),
      ("cp10","LM-VEH-6-B","Ownership Transfer within 3 Days","3 Days","Daily","System","mp4"),
      ("cp11","LM-VEH-6-A","Ownership transfer support","3 Days","Daily","","mp4"),
      ("cp12","LM-VEH-7-B","Final Delivery of Vehicles within 24 Hours","24 Hours","Daily","System","mp5"),
      ("cp13","LM-VEH-7-S","Final Delivery coordination","24 Hours","Daily","","mp5"),
      ("cp14","LM-VEH-7-A","Final Delivery support","24 Hours","Daily","","mp5"),
      ("cp15","LM-VEH-8-B","Vehicle Dispatch to Locations within 24 hrs","24 Hours","Daily","","mp6"),
      ("cp16","LM-VEH-8-S","Dispatch coordination","24 Hours","Daily","System","mp6"),
      ("cp17","LM-VEH-8-A","Dispatch support","24 Hours","Daily","","mp6"),
      ("cp18","LM-VEH-11","WOW update within 10/15 Days of Delivery PV/CV","10/15 Days","Weekly","System","mp7"),
      ("cp19","LM-VEH-12","Monthly Physical Verification of new vehicles","Monthly","Monthly","Manual","mp8"),
      ("cp20","LM-WH-1","Custom Clearance of Goods within 2 working days","2 Days","Daily","Manual","mp9"),
      ("cp21","LM-WH-2","GRN and Verification of Goods within 2 Days of CC","2 Days","Daily","System","mp9"),
      ("cp22","LM-WH-3-B","Goods delivered as per SLA","SLA","Daily","System","mp9"),
      ("cp23","LM-WH-3-A","Goods delivery SLA monitoring","SLA","Daily","System","mp9"),
      ("cp24","LM-WH-4-B","Handling discrepancies 100% closure","100%","Daily","","mp10"),
      ("cp25","LM-WH-4-A","Discrepancy closure","100%","Daily","","mp10"),
      ("cp26","LM-VEH-13","Sahamati Just in Time for tax reduction","20% Reduction","Daily","","mp10"),
      ("cp27","LM-VH-14","Conduct Periodic Review Meeting","Fortnightly","Fortnightly","","mp12"),
    ]
    db.executemany("INSERT OR IGNORE INTO cps VALUES(?,?,?,?,?,?,?)",cps)
    cpo=[("cp1","e2"),("cp2","e2"),("cp3","e3"),("cp4","e2"),("cp5","e3"),("cp6","e2"),("cp7","e3"),
         ("cp8","e2"),("cp9","e4"),("cp10","e4"),("cp11","e2"),("cp12","e2"),("cp13","e3"),("cp14","e10"),
         ("cp15","e2"),("cp16","e3"),("cp17","e10"),("cp18","e4"),("cp19","e4"),("cp20","e2"),
         ("cp21","e2"),("cp22","e2"),("cp23","e11"),("cp24","e2"),("cp25","e11"),("cp26","e4"),("cp27","e4")]
    db.executemany("INSERT OR IGNORE INTO cp_owners VALUES(?,?)",cpo)
    roles=[("r1","ROLE-VIM","Vehicle Import Manager","Full vehicle import, GST, NIAC, CC and POE management","#1d4ed8"),
           ("r2","ROLE-VDM","Vehicle Delivery Manager","Manages final delivery, dispatch and driver coordination","#0891b2"),
           ("r3","ROLE-REG","Registration Manager","Vehicle registration, ownership transfer and WOW updates","#6d28d9"),
           ("r4","ROLE-WH","Warehouse & Goods Manager","Goods clearance, GRN, dispatch and discrepancy closure","#047857"),
           ("r5","ROLE-STCK","Stock Verification Officer","Physical vehicle stock verification and reporting","#b45309")]
    roles_padded = [r+(1,'') if len(r)==5 else r for r in roles]
    db.executemany("INSERT OR IGNORE INTO roles VALUES(?,?,?,?,?,?,?)",roles_padded)
    role_mps=[("r1","mp1"),("r1","mp2"),("r2","mp5"),("r2","mp6"),("r3","mp3"),("r3","mp4"),
              ("r3","mp7"),("r4","mp9"),("r4","mp10"),("r5","mp8")]
    db.executemany("INSERT OR IGNORE INTO role_mps VALUES(?,?)",role_mps)
    role_cps=[("r1","cp1"),("r1","cp2"),("r1","cp3"),("r1","cp4"),("r1","cp5"),("r1","cp6"),("r1","cp7"),
              ("r2","cp12"),("r2","cp13"),("r2","cp14"),("r2","cp15"),("r2","cp16"),("r2","cp17"),
              ("r3","cp8"),("r3","cp9"),("r3","cp10"),("r3","cp11"),("r3","cp18"),
              ("r4","cp20"),("r4","cp21"),("r4","cp22"),("r4","cp23"),("r4","cp24"),("r4","cp25"),
              ("r5","cp19")]
    db.executemany("INSERT OR IGNORE INTO role_cps VALUES(?,?)",role_cps)
    emp_roles=[("e2","r1"),("e2","r2"),("e3","r1"),("e4","r3"),("e11","r4"),("e8","r5")]
    db.executemany("INSERT OR IGNORE INTO emp_roles VALUES(?,?)",emp_roles)

    def P(pid,fy,bsm,eid,ec,mpr,cpr,metric,tot,comp,tgt,act,unit,notes=""):
        nc=tot-comp; pct_c=round(comp/tot*100,2) if tot else 0; pct_nc=round(nc/tot*100,2) if tot else 0
        st=calc_status(act,tgt,unit)
        return (pid,fy,bsm,bs_q(bsm),eid,ec,mpr,cpr,metric,tot,comp,nc,pct_c,pct_nc,tgt,act,unit,st,notes,'')
    perf=[
      P("p01","2080-81","Shrawan","e2","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",250,240,100,96,"%","All tracked"),
      P("p02","2080-81","Shrawan","e2","EMP-002","HODL-1","LM-VEH-2-B","CC within 3 Days",280,265,3,2.8,"Days","On track"),
      P("p03","2080-81","Shrawan","e3","EMP-003","HODL-1","LM-VEH-2-S","CC Monitoring",180,170,3,3.2,"Days","1 delay"),
      P("p04","2080-81","Shrawan","e4","EMP-004","HODL-3","LM-VEH-5-A","Registration 15 Days",320,305,15,14,"Days","Within SLA"),
      P("p05","2080-81","Shrawan","e4","EMP-004","HODL-4","LM-VEH-6-B","Ownership Transfer",180,172,3,2.5,"Days","Good"),
      P("p06","2080-81","Shrawan","e11","EMP-011","HODL-9","LM-WH-3-A","Goods SLA Delivery",95,95,2,2,"Days","On SLA"),
      P("p07","2080-81","Bhadra","e2","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",310,304,100,98,"%",""),
      P("p08","2080-81","Bhadra","e2","EMP-002","HODL-1","LM-VEH-2-B","CC within 3 Days",310,295,3,2.5,"Days",""),
      P("p09","2080-81","Bhadra","e4","EMP-004","HODL-3","LM-VEH-5-A","Registration 15 Days",295,279,15,16,"Days","Slight delay"),
      P("p10","2080-81","Bhadra","e11","EMP-011","HODL-9","LM-WH-3-A","Goods SLA Delivery",88,72,2,2.8,"Days","Delayed"),
      P("p11","2080-81","Ashwin","e2","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",420,420,100,100,"%","100%"),
      P("p12","2080-81","Ashwin","e2","EMP-002","HODL-1","LM-VEH-2-B","CC within 3 Days",420,409,3,2.3,"Days","Best month"),
      P("p13","2080-81","Kartik","e2","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",380,357,100,94,"%","4 missed"),
      P("p14","2080-81","Kartik","e2","EMP-002","HODL-1","LM-VEH-2-B","CC within 3 Days",380,342,3,3.5,"Days","Over SLA"),
      P("p15","2080-81","Kartik","e4","EMP-004","HODL-3","LM-VEH-5-A","Registration 15 Days",340,329,15,13,"Days","Good"),
      P("p16","2080-81","Mangsir","e2","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",350,340,100,97,"%",""),
      P("p17","2080-81","Mangsir","e4","EMP-004","HODL-4","LM-VEH-6-B","Ownership Transfer",200,195,3,3,"Days","On target"),
      P("p18","2080-81","Poush","e2","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",280,258,100,92,"%","Year end"),
      P("p19","2080-81","Poush","e11","EMP-011","HODL-9","LM-WH-3-A","Goods SLA Delivery",72,58,2,3,"Days","Holiday"),
      P("p20","2081-82","Shrawan","e2","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",410,398,100,97,"%",""),
      P("p21","2081-82","Shrawan","e2","EMP-002","HODL-1","LM-VEH-2-B","CC within 3 Days",410,390,3,2.6,"Days",""),
      P("p22","2081-82","Shrawan","e3","EMP-003","HODL-1","LM-VEH-2-S","CC Monitoring",260,248,3,2.9,"Days",""),
      P("p23","2081-82","Shrawan","e4","EMP-004","HODL-3","LM-VEH-5-A","Registration 15 Days",380,370,15,13,"Days","Improved"),
      P("p24","2081-82","Shrawan","e4","EMP-004","HODL-4","LM-VEH-6-B","Ownership Transfer",210,207,3,2.2,"Days","Best ever"),
      P("p25","2081-82","Shrawan","e11","EMP-011","HODL-9","LM-WH-3-A","Goods SLA Delivery",105,103,2,1.8,"Days","Better"),
      P("p26","2081-82","Bhadra","e2","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",450,446,100,99,"%",""),
      P("p27","2081-82","Bhadra","e2","EMP-002","HODL-1","LM-VEH-2-B","CC within 3 Days",450,436,3,2.4,"Days",""),
      P("p28","2081-82","Bhadra","e4","EMP-004","HODL-3","LM-VEH-5-A","Registration 15 Days",400,395,15,12,"Days",""),
      P("p29","2081-82","Ashwin","e2","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",480,470,100,98,"%",""),
      P("p30","2081-82","Ashwin","e2","EMP-002","HODL-1","LM-VEH-2-B","CC within 3 Days",480,458,3,2.7,"Days",""),
      P("p31","2081-82","Ashwin","e4","EMP-004","HODL-4","LM-VEH-6-B","Ownership Transfer",220,218,3,2,"Days",""),
      P("p32","2081-82","Kartik","e2","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",390,374,100,96,"%",""),
      P("p33","2081-82","Kartik","e11","EMP-011","HODL-9","LM-WH-3-A","Goods SLA Delivery",98,94,2,2.1,"Days","Slight over"),
    ]
    db.executemany("INSERT OR IGNORE INTO perf VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",perf)
    locs=[
        ("loc1","HQ","Head Office - Sipradi","Office","Kathmandu"),
        ("loc2","BORDER","Border Clearance Station","Border","Birgunj"),
        ("loc3","WH-KTM","Kathmandu Warehouse","Warehouse","Kathmandu"),
        ("loc4","REG-KTM","Registration Office","Office","Kathmandu"),
        ("loc5","WH-BRG","Birgunj Warehouse","Warehouse","Birgunj"),
    ]
    db.executemany("INSERT OR IGNORE INTO locations VALUES(?,?,?,?,?)",locs)
    emp_locs=[
        ("e1","loc1"),("e2","loc1"),("e2","loc2"),("e3","loc2"),("e4","loc4"),
        ("e5","loc4"),("e6","loc4"),("e7","loc2"),("e8","loc1"),("e9","loc1"),
        ("e10","loc1"),("e11","loc3"),("e12","loc3"),("e13","loc3"),("e14","loc3"),
        ("e15","loc2"),("e16","loc1"),
    ]
    db.executemany("INSERT OR IGNORE INTO emp_locations VALUES(?,?)",emp_locs)
    for fy in ["2080-81","2081-82"]: _upd_cache(db,fy)

# ── EMPLOYEES ──────────────────────────────────────────────────────────────
def enrich_emp(e,db):
    r=dict(e)
    r['role_ids']=[x['role_id'] for x in db.execute("SELECT role_id FROM emp_roles WHERE emp_id=?",(r['id'],))]
    r['mp_ids']  =[x['mp_id']   for x in db.execute("SELECT mp_id   FROM emp_mps   WHERE emp_id=?",(r['id'],))]
    r['cp_ids']  =[x['cp_id']   for x in db.execute("SELECT cp_id   FROM emp_cps   WHERE emp_id=?",(r['id'],))]
    return r

@app.route('/api/employees',methods=['GET','POST'])
def employees_api():
    db=get_db()
    if request.method=='GET':
        return jsonify([enrich_emp(e,db) for e in db.execute("SELECT * FROM employees ORDER BY level,name")])
    d=request.json; eid=d.get('id') or uid()
    code=d.get('emp_code','').strip()
    if not code:
        last=db.execute("SELECT emp_code FROM employees WHERE emp_code LIKE 'EMP-%' ORDER BY emp_code DESC LIMIT 1").fetchone()
        try: num=int(last['emp_code'].split('-')[1])+1 if last else 1
        except: num=1
        code=f"EMP-{num:03d}"
    db.execute("INSERT OR REPLACE INTO employees VALUES(?,?,?,?,?,?,?,?)",
        (eid,code,d['name'],d.get('role',''),d.get('level',3),d.get('dept','Ops'),d.get('manager_id') or None,d.get('email','')))
    db.commit(); return jsonify({'id':eid,'emp_code':code})

@app.route('/api/employees/<eid>',methods=['PUT','DELETE'])
def employee_api(eid):
    db=get_db()
    if request.method=='DELETE':
        for t,c in [('employees','id'),('mp_owners','emp_id'),('cp_owners','emp_id'),
                    ('emp_roles','emp_id'),('emp_mps','emp_id'),('emp_cps','emp_id')]:
            db.execute(f"DELETE FROM {t} WHERE {c}=?",(eid,))
        db.commit(); return jsonify({'ok':True})
    d=request.json
    db.execute("UPDATE employees SET emp_code=?,name=?,role=?,level=?,dept=?,manager_id=?,email=? WHERE id=?",
        (d.get('emp_code'),d['name'],d.get('role',''),d.get('level',3),d.get('dept','Ops'),d.get('manager_id') or None,d.get('email',''),eid))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/emp_links/<eid>',methods=['GET','POST'])
def emp_links(eid):
    db=get_db()
    if request.method=='GET':
        return jsonify({'role_ids':[r['role_id'] for r in db.execute("SELECT role_id FROM emp_roles WHERE emp_id=?",(eid,))],
                        'mp_ids':  [r['mp_id']   for r in db.execute("SELECT mp_id   FROM emp_mps   WHERE emp_id=?",(eid,))],
                        'cp_ids':  [r['cp_id']   for r in db.execute("SELECT cp_id   FROM emp_cps   WHERE emp_id=?",(eid,))]})
    d=request.json
    for t in ['emp_roles','emp_mps','emp_cps']: db.execute(f"DELETE FROM {t} WHERE emp_id=?",(eid,))
    for rid in d.get('role_ids',[]):
        db.execute("INSERT OR IGNORE INTO emp_roles VALUES(?,?)",(eid,rid))
        for mid in [r['mp_id'] for r in db.execute("SELECT mp_id FROM role_mps WHERE role_id=?",(rid,))]:
            db.execute("INSERT OR IGNORE INTO emp_mps   VALUES(?,?)",(eid,mid))
            db.execute("INSERT OR IGNORE INTO mp_owners VALUES(?,?)",(mid,eid))
        for cid in [r['cp_id'] for r in db.execute("SELECT cp_id FROM role_cps WHERE role_id=?",(rid,))]:
            db.execute("INSERT OR IGNORE INTO emp_cps   VALUES(?,?)",(eid,cid))
            db.execute("INSERT OR IGNORE INTO cp_owners VALUES(?,?)",(cid,eid))
    for mid in d.get('mp_ids',[]): db.execute("INSERT OR IGNORE INTO emp_mps   VALUES(?,?)",(eid,mid)); db.execute("INSERT OR IGNORE INTO mp_owners VALUES(?,?)",(mid,eid))
    for cid in d.get('cp_ids',[]): db.execute("INSERT OR IGNORE INTO emp_cps   VALUES(?,?)",(eid,cid)); db.execute("INSERT OR IGNORE INTO cp_owners VALUES(?,?)",(cid,eid))
    db.commit(); return jsonify({'ok':True})

# ── MPs ────────────────────────────────────────────────────────────────────
def enrich_mp(m,db):
    r=dict(m); r['owner_ids']=[x['emp_id'] for x in db.execute("SELECT emp_id FROM mp_owners WHERE mp_id=?",(r['id'],))]
    r['pct']=round(r['kpi_c']/r['kpi_total']*100,1) if r['kpi_total'] else None
    r['parent_cp_id']=r.get('parent_cp_id','')
    r['emp_level']=r.get('emp_level',1)
    r['cascade_children']=[dict(x) for x in db.execute("SELECT cl.*,e.name as child_name,e.emp_code as child_code FROM cascade_links cl LEFT JOIN employees e ON cl.child_emp_id=e.id WHERE cl.parent_cp_id IN (SELECT id FROM cps WHERE mp_id=?)", (r['id'],))]
    return r

@app.route('/api/mps',methods=['GET','POST'])
def mps_api():
    db=get_db()
    if request.method=='GET': return jsonify([enrich_mp(m,db) for m in db.execute("SELECT * FROM mps ORDER BY ref")])
    d=request.json; mid=d.get('id') or uid()
    db.execute("INSERT OR REPLACE INTO mps VALUES(?,?,?,?,?,?,?,?,?,?)",
        (mid,d['ref'],d['title'],d.get('target',''),d.get('freq','Monthly'),d.get('kpi_c',0),d.get('kpi_nc',0),d.get('kpi_total',0),d.get('parent_cp_id',''),d.get('emp_level',1)))
    db.execute("DELETE FROM mp_owners WHERE mp_id=?",(mid,))
    for eid in d.get('owner_ids',[]): db.execute("INSERT OR IGNORE INTO mp_owners VALUES(?,?)",(mid,eid))
    db.commit(); return jsonify({'id':mid})

@app.route('/api/mps/<mid>',methods=['PUT','DELETE'])
def mp_api(mid):
    db=get_db()
    if request.method=='DELETE':
        db.execute("DELETE FROM mps WHERE id=?",(mid,)); db.execute("DELETE FROM mp_owners WHERE mp_id=?",(mid,))
        db.execute("UPDATE cps SET mp_id='' WHERE mp_id=?",(mid,)); db.commit(); return jsonify({'ok':True})
    d=request.json
    db.execute("UPDATE mps SET ref=?,title=?,target=?,freq=?,kpi_c=?,kpi_nc=?,kpi_total=?,parent_cp_id=?,emp_level=? WHERE id=?",
        (d['ref'],d['title'],d.get('target',''),d.get('freq','Monthly'),d.get('kpi_c',0),d.get('kpi_nc',0),d.get('kpi_total',0),d.get('parent_cp_id',''),d.get('emp_level',1),mid))
    db.execute("DELETE FROM mp_owners WHERE mp_id=?",(mid,))
    for eid in d.get('owner_ids',[]): db.execute("INSERT OR IGNORE INTO mp_owners VALUES(?,?)",(mid,eid))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/mps/import_excel',methods=['POST'])
def import_mps_excel():
    if not HAS_OPENPYXL: return jsonify({'error':'pip install openpyxl'}),400
    f=request.files.get('file')
    if not f: return jsonify({'error':'No file'}),400
    db=get_db(); wb=openpyxl.load_workbook(f,data_only=True); ws=wb.active
    hdrs=[str(c.value or '').strip().lower() for c in next(ws.iter_rows(min_row=1,max_row=1))]
    def col(n,al=[]): return next((hdrs.index(a) for a in [n]+al if a in hdrs),None)
    ci=col('ref',['mp ref','mp_ref','reference']); ct=col('title',['managing point','mp title'])
    cta=col('target',['sla']); cf=col('frequency',['freq']); ctot=col('kpi_total',['total'])
    cc=col('kpi_c',['compliant','c']); cnc=col('kpi_nc',['non_compliant','nc'])
    co=col('owner_codes',['owners','employee codes'])
    code_map={r['emp_code']:r['id'] for r in db.execute("SELECT id,emp_code FROM employees WHERE emp_code IS NOT NULL")}
    imp=0; errs=[]
    for i,row in enumerate(ws.iter_rows(min_row=2,values_only=True),2):
        try:
            ref=str(row[ci] or '').strip() if ci is not None else ''
            if not ref: continue
            title=str(row[ct] or '') if ct is not None else ''
            tgt=str(row[cta] or '') if cta is not None else ''
            freq=str(row[cf] or 'Monthly') if cf is not None else 'Monthly'
            tot=int(row[ctot] or 0) if ctot is not None else 0
            cv=int(row[cc] or 0) if cc is not None else 0
            nv=int(row[cnc] or 0) if cnc is not None else 0
            ex=db.execute("SELECT id FROM mps WHERE ref=?",(ref,)).fetchone()
            mid=ex['id'] if ex else uid()
            db.execute("INSERT OR REPLACE INTO mps VALUES(?,?,?,?,?,?,?,?)",(mid,ref,title,tgt,freq,cv,nv,tot))
            if co is not None and row[co]:
                codes=[x.strip() for x in str(row[co]).split(',') if x.strip()]
                db.execute("DELETE FROM mp_owners WHERE mp_id=?",(mid,))
                for code in codes:
                    eid=code_map.get(code)
                    if eid: db.execute("INSERT OR IGNORE INTO mp_owners VALUES(?,?)",(mid,eid))
            imp+=1
        except Exception as e: errs.append(f"Row {i}: {e}")
    db.commit(); return jsonify({'imported':imp,'errors':errs})

@app.route('/api/mps/template_excel')
def mp_excel_template():
    wb=openpyxl.Workbook(); ws=wb.active; ws.title="Managing Points"
    ws.append(["Ref","Title","Target","Frequency","KPI_Total","KPI_C","KPI_NC","Owner_Codes"])
    ws.append(["HODL-1","Fully compliant and timely vehicle import","1 Day","Monthly",3299,3183,116,"EMP-002,EMP-003"])
    ws.append(["HODL-2","100% NIAC Claim resolution","120 Days","Fortnightly",0,0,0,"EMP-002"])
    out=io.BytesIO(); wb.save(out); out.seek(0)
    return send_file(out,mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,download_name='MP_Template.xlsx')

# ── CPs ────────────────────────────────────────────────────────────────────
def enrich_cp(c,db):
    r=dict(c); r['owner_ids']=[x['emp_id'] for x in db.execute("SELECT emp_id FROM cp_owners WHERE cp_id=?",(r['id'],))]; return r

@app.route('/api/cps',methods=['GET','POST'])
def cps_api():
    db=get_db()
    if request.method=='GET': return jsonify([enrich_cp(c,db) for c in db.execute("SELECT * FROM cps ORDER BY ref")])
    d=request.json; cid=d.get('id') or uid()
    db.execute("INSERT OR REPLACE INTO cps VALUES(?,?,?,?,?,?,?)",
        (cid,d['ref'],d['title'],d.get('target',''),d.get('freq','Daily'),d.get('source',''),d.get('mp_id','')))
    db.execute("DELETE FROM cp_owners WHERE cp_id=?",(cid,))
    for eid in d.get('owner_ids',[]): db.execute("INSERT OR IGNORE INTO cp_owners VALUES(?,?)",(cid,eid))
    db.commit(); return jsonify({'id':cid})

@app.route('/api/cps/<cid>',methods=['PUT','DELETE'])
def cp_api(cid):
    db=get_db()
    if request.method=='DELETE':
        db.execute("DELETE FROM cps WHERE id=?",(cid,)); db.execute("DELETE FROM cp_owners WHERE cp_id=?",(cid,)); db.commit(); return jsonify({'ok':True})
    d=request.json
    db.execute("UPDATE cps SET ref=?,title=?,target=?,freq=?,source=?,mp_id=? WHERE id=?",
        (d['ref'],d['title'],d.get('target',''),d.get('freq','Daily'),d.get('source',''),d.get('mp_id',''),cid))
    db.execute("DELETE FROM cp_owners WHERE cp_id=?",(cid,))
    for eid in d.get('owner_ids',[]): db.execute("INSERT OR IGNORE INTO cp_owners VALUES(?,?)",(cid,eid))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/cps/import_excel',methods=['POST'])
def import_cps_excel():
    if not HAS_OPENPYXL: return jsonify({'error':'pip install openpyxl'}),400
    f=request.files.get('file')
    if not f: return jsonify({'error':'No file'}),400
    db=get_db(); wb=openpyxl.load_workbook(f,data_only=True); ws=wb.active
    hdrs=[str(c.value or '').strip().lower() for c in next(ws.iter_rows(min_row=1,max_row=1))]
    def col(n,al=[]): return next((hdrs.index(a) for a in [n]+al if a in hdrs),None)
    ci=col('ref',['cp ref','cp_ref']); ct=col('title',['checking point','cp title'])
    cta=col('target',['sla']); cf=col('frequency',['freq']); cs=col('source',['report source'])
    cmpr=col('mp_ref',['mp ref','managing point ref']); co=col('owner_codes',['owners','employee codes'])
    code_map={r['emp_code']:r['id'] for r in db.execute("SELECT id,emp_code FROM employees WHERE emp_code IS NOT NULL")}
    mp_map={r['ref']:r['id'] for r in db.execute("SELECT id,ref FROM mps")}
    imp=0; errs=[]
    for i,row in enumerate(ws.iter_rows(min_row=2,values_only=True),2):
        try:
            ref=str(row[ci] or '').strip() if ci is not None else ''
            if not ref: continue
            title=str(row[ct] or '') if ct is not None else ''
            tgt=str(row[cta] or '') if cta is not None else ''
            freq=str(row[cf] or 'Daily') if cf is not None else 'Daily'
            src=str(row[cs] or '') if cs is not None else ''
            mpref=str(row[cmpr] or '') if cmpr is not None else ''
            mp_id=mp_map.get(mpref,'')
            ex=db.execute("SELECT id FROM cps WHERE ref=?",(ref,)).fetchone()
            cid=ex['id'] if ex else uid()
            db.execute("INSERT OR REPLACE INTO cps VALUES(?,?,?,?,?,?,?)",(cid,ref,title,tgt,freq,src,mp_id))
            if co is not None and row[co]:
                codes=[x.strip() for x in str(row[co]).split(',') if x.strip()]
                db.execute("DELETE FROM cp_owners WHERE cp_id=?",(cid,))
                for code in codes:
                    eid=code_map.get(code)
                    if eid: db.execute("INSERT OR IGNORE INTO cp_owners VALUES(?,?)",(cid,eid))
            imp+=1
        except Exception as e: errs.append(f"Row {i}: {e}")
    db.commit(); return jsonify({'imported':imp,'errors':errs})

@app.route('/api/cps/template_excel')
def cp_excel_template():
    wb=openpyxl.Workbook(); ws=wb.active; ws.title="Checking Points"
    ws.append(["Ref","Title","Target","Frequency","Source","MP_Ref","Owner_Codes"])
    ws.append(["LM-VEH-1","Tracking of New Vehicles till arrival at border","100%","Monthly","Manual","HODL-1","EMP-002"])
    ws.append(["LM-VEH-2-B","On time custom clearance within 3 days of CC memo","3 Days","Daily","System","HODL-1","EMP-002"])
    out=io.BytesIO(); wb.save(out); out.seek(0)
    return send_file(out,mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,download_name='CP_Template.xlsx')

# ── Roles ──────────────────────────────────────────────────────────────────
@app.route('/api/roles',methods=['GET','POST'])
def roles_api():
    db=get_db()
    if request.method=='GET':
        res=[]
        for r in db.execute("SELECT * FROM roles ORDER BY code"):
            role=dict(r)
            role['mp_ids']=[x['mp_id'] for x in db.execute("SELECT mp_id FROM role_mps WHERE role_id=?",(r['id'],))]
            role['cp_ids']=[x['cp_id'] for x in db.execute("SELECT cp_id FROM role_cps WHERE role_id=?",(r['id'],))]
            res.append(role)
        return jsonify(res)
    d=request.json; rid=d.get('id') or uid()
    db.execute("INSERT OR REPLACE INTO roles VALUES(?,?,?,?,?,?,?)",(rid,d['code'],d['name'],d.get('description',''),d.get('color','#1d4ed8'),d.get('emp_level',1),d.get('parent_role_id','')))
    db.execute("DELETE FROM role_mps WHERE role_id=?",(rid,)); db.execute("DELETE FROM role_cps WHERE role_id=?",(rid,))
    for mid in d.get('mp_ids',[]): db.execute("INSERT OR IGNORE INTO role_mps VALUES(?,?)",(rid,mid))
    for cid in d.get('cp_ids',[]): db.execute("INSERT OR IGNORE INTO role_cps VALUES(?,?)",(rid,cid))
    db.commit(); return jsonify({'id':rid})

@app.route('/api/roles/<rid>',methods=['PUT','DELETE'])
def role_api(rid):
    db=get_db()
    if request.method=='DELETE':
        for t,c in [('roles','id'),('role_mps','role_id'),('role_cps','role_id'),('emp_roles','role_id')]:
            db.execute(f"DELETE FROM {t} WHERE {c}=?",(rid,))
        db.commit(); return jsonify({'ok':True})
    d=request.json
    db.execute("UPDATE roles SET code=?,name=?,description=?,color=?,emp_level=?,parent_role_id=? WHERE id=?",(d['code'],d['name'],d.get('description',''),d.get('color','#1d4ed8'),d.get('emp_level',1),d.get('parent_role_id',''),rid))
    db.execute("DELETE FROM role_mps WHERE role_id=?",(rid,)); db.execute("DELETE FROM role_cps WHERE role_id=?",(rid,))
    for mid in d.get('mp_ids',[]): db.execute("INSERT OR IGNORE INTO role_mps VALUES(?,?)",(rid,mid))
    for cid in d.get('cp_ids',[]): db.execute("INSERT OR IGNORE INTO role_cps VALUES(?,?)",(rid,cid))
    db.commit(); return jsonify({'ok':True})

# ── CACHE ──────────────────────────────────────────────────────────────────
@app.route('/api/cache',methods=['GET','POST'])
def cache_api():
    db=get_db()
    if request.method=='GET':
        rows=db.execute("SELECT * FROM perf_cache ORDER BY fy DESC").fetchall()
        res=[]
        for r in rows:
            item=dict(r); item['record_count']=db.execute("SELECT COUNT(*) FROM perf WHERE fy=?",(r['fy'],)).fetchone()[0]; res.append(item)
        return jsonify(res)
    d=request.json; fy=d.get('fy','').strip()
    if not fy: return jsonify({'error':'FY required'}),400
    now=datetime.datetime.now().isoformat()
    db.execute("INSERT OR IGNORE INTO perf_cache VALUES(?,?,?,?,?,?)",(fy,d.get('label',f"FY {fy}"),0,now,now,0))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/cache/<fy>/clear',methods=['POST'])
def clear_cache(fy):
    db=get_db()
    row=db.execute("SELECT locked FROM perf_cache WHERE fy=?",(fy,)).fetchone()
    if not row: return jsonify({'error':'FY not found'}),404
    if row['locked']: return jsonify({'error':'FY is locked'}),400
    db.execute("DELETE FROM perf WHERE fy=?",(fy,)); _upd_cache(db,fy); db.commit(); return jsonify({'cleared':True,'fy':fy})

@app.route('/api/cache/<fy>/lock',methods=['POST'])
def toggle_lock(fy):
    db=get_db()
    row=db.execute("SELECT locked FROM perf_cache WHERE fy=?",(fy,)).fetchone()
    if not row: return jsonify({'error':'Not found'}),404
    nl=0 if row['locked'] else 1
    db.execute("UPDATE perf_cache SET locked=? WHERE fy=?",(nl,fy)); db.commit(); return jsonify({'locked':bool(nl)})

@app.route('/api/cache/<fy>',methods=['DELETE'])
def delete_cache(fy):
    db=get_db()
    row=db.execute("SELECT locked FROM perf_cache WHERE fy=?",(fy,)).fetchone()
    if row and row['locked']: return jsonify({'error':'Locked'}),400
    db.execute("DELETE FROM perf WHERE fy=?",(fy,)); db.execute("DELETE FROM perf_cache WHERE fy=?",(fy,)); db.commit(); return jsonify({'deleted':True})

# ── PERF ──────────────────────────────────────────────────────────────────
@app.route('/api/perf',methods=['GET','POST'])
def perf_api():
    db=get_db()
    if request.method=='GET':
        q="SELECT * FROM perf WHERE 1=1"; args=[]
        for p,c in [('fy','fy'),('emp_code','emp_code'),('emp_id','emp_id'),('mp_ref','mp_ref'),('bs_month','bs_month'),('quarter','quarter')]:
            if request.args.get(p): q+=f" AND {c}=?"; args.append(request.args[p])
        return jsonify(R(db.execute(q+' ORDER BY fy DESC,bs_month',args).fetchall()))
    d=request.json; pid=d.get('id') or uid()
    eid=d.get('emp_id',''); ec=d.get('emp_code','')
    if not eid and ec:
        row=db.execute("SELECT id FROM employees WHERE emp_code=?",(ec,)).fetchone()
        if row: eid=row['id']
    bsm=norm_month(d.get('bs_month','Shrawan')); fy=d.get('fy','2081-82')
    tot=int(d.get('total',0)); comp=int(d.get('compliant',0))
    nc=int(d.get('non_compliant',tot-comp))
    pct_c=round(comp/tot*100,2) if tot else 0; pct_nc=round(nc/tot*100,2) if tot else 0
    st=d.get('status') or calc_status(d.get('actual_val',0),d.get('target_val',0),d.get('unit','%'))
    db.execute("INSERT OR REPLACE INTO perf VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (pid,fy,bsm,bs_q(bsm),eid,ec,d.get('mp_ref',''),d.get('cp_ref',''),d.get('metric',''),
         tot,comp,nc,pct_c,pct_nc,d.get('target_val',0),d.get('actual_val',0),d.get('unit','%'),st,d.get('notes','')))
    _upd_cache(db,fy); db.commit(); return jsonify({'id':pid})

@app.route('/api/perf/<pid>',methods=['PUT','DELETE'])
def perf_record(pid):
    db=get_db()
    if request.method=='DELETE':
        row=db.execute("SELECT fy FROM perf WHERE id=?",(pid,)).fetchone()
        db.execute("DELETE FROM perf WHERE id=?",(pid,))
        if row: _upd_cache(db,row['fy'])
        db.commit(); return jsonify({'ok':True})
    d=request.json; bsm=norm_month(d.get('bs_month','Shrawan'))
    tot=int(d.get('total',0)); comp=int(d.get('compliant',0))
    nc=int(d.get('non_compliant',tot-comp))
    pct_c=round(comp/tot*100,2) if tot else 0; pct_nc=round(nc/tot*100,2) if tot else 0
    db.execute("""UPDATE perf SET fy=?,bs_month=?,quarter=?,emp_id=?,emp_code=?,mp_ref=?,cp_ref=?,
        metric=?,total=?,compliant=?,non_compliant=?,pct_compliant=?,pct_nc=?,
        target_val=?,actual_val=?,unit=?,status=?,notes=? WHERE id=?""",
        (d.get('fy'),bsm,bs_q(bsm),d.get('emp_id',''),d.get('emp_code',''),d.get('mp_ref',''),d.get('cp_ref',''),
         d.get('metric',''),tot,comp,nc,pct_c,pct_nc,d.get('target_val',0),d.get('actual_val',0),d.get('unit','%'),
         d.get('status','C'),d.get('notes',''),pid))
    db.commit(); return jsonify({'ok':True})

PHDR=['FY','BS_Month','Emp_Code','MP_Ref','CP_Ref','Metric',
      'Total','Compliant','Non_Compliant','Pct_Compliant','Pct_NC',
      'Target_Val','Actual_Val','Unit','Status','Notes']

@app.route('/api/perf/template')
def perf_template():
    out=io.StringIO(); w=csv.writer(out); w.writerow(PHDR)
    for s in [
        ["2081-82","Shrawan","EMP-002","HODL-1","LM-VEH-1","Vehicle Border Tracking",410,398,12,97.07,2.93,100,97,"%","C","All tracked"],
        ["2081-82","Shrawan","EMP-002","HODL-1","LM-VEH-2-B","CC within 3 Days",410,390,20,95.12,4.88,3,2.6,"Days","C","On track"],
        ["2081-82","Bhadra","EMP-004","HODL-3","LM-VEH-5-A","Registration 15 Days",380,370,10,97.37,2.63,15,13,"Days","C","Improved"],
        ["2081-82","Kartik","EMP-011","HODL-9","LM-WH-3-A","Goods SLA Delivery",98,94,4,95.92,4.08,2,2.1,"Days","NC","Slight over"],
    ]: w.writerow(s)
    out.seek(0)
    return send_file(io.BytesIO(out.getvalue().encode()),mimetype='text/csv',
                     as_attachment=True,download_name='MPCP_Perf_Template.csv')

@app.route('/api/perf/export')
def export_perf():
    db=get_db(); fy=request.args.get('fy')
    q="SELECT p.*,e.name as emp_name FROM perf p LEFT JOIN employees e ON p.emp_id=e.id"
    args=[]
    if fy: q+=" WHERE p.fy=?"; args.append(fy)
    rows=db.execute(q+' ORDER BY p.fy DESC,p.bs_month',args).fetchall()
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(['FY','BS_Month','Quarter','Emp_Code','Emp_Name','MP_Ref','CP_Ref','Metric',
                'Total','Compliant','Non_Compliant','Pct_Compliant','Pct_NC',
                'Target_Val','Actual_Val','Unit','Status','Notes'])
    for r in rows:
        w.writerow([r['fy'],r['bs_month'],r['quarter'],r['emp_code'],r['emp_name'] or '',
                    r['mp_ref'],r['cp_ref'],r['metric'],r['total'],r['compliant'],r['non_compliant'],
                    r['pct_compliant'],r['pct_nc'],r['target_val'],r['actual_val'],r['unit'],r['status'],r['notes']])
    out.seek(0)
    return send_file(io.BytesIO(out.getvalue().encode()),mimetype='text/csv',
                     as_attachment=True,download_name=f'MPCP_Perf_{fy or "All"}.csv')

@app.route('/api/perf/import',methods=['POST'])
def import_perf():
    f=request.files.get('file')
    if not f: return jsonify({'error':'No file'}),400
    text=f.read().decode('utf-8-sig'); reader=csv.DictReader(io.StringIO(text))
    db=get_db()
    code_map={r['emp_code']:r['id'] for r in db.execute("SELECT id,emp_code FROM employees WHERE emp_code IS NOT NULL")}
    count=0; errs=[]; fys_seen=set()
    for i,row in enumerate(reader,2):
        try:
            fy=str(row.get('FY','') or row.get('fy','')).strip()
            if not fy: continue
            fys_seen.add(fy)
            bsm=norm_month(row.get('BS_Month','') or row.get('bs_month','') or row.get('Month',''))
            ec=str(row.get('Emp_Code','') or row.get('emp_code','')).strip()
            eid=code_map.get(ec,'')
            tot=int(float(row.get('Total','0') or 0)); comp=int(float(row.get('Compliant','0') or 0))
            nc=tot-comp
            pct_c=float(row.get('Pct_Compliant','0') or (round(comp/tot*100,2) if tot else 0))
            pct_nc=float(row.get('Pct_NC','0') or (round(nc/tot*100,2) if tot else 0))
            tgt=float(row.get('Target_Val','0') or 0); act=float(row.get('Actual_Val','0') or 0)
            unit=str(row.get('Unit','%') or '%')
            st=str(row.get('Status','') or calc_status(act,tgt,unit))
            if st not in ('C','NC'): st=calc_status(act,tgt,unit)
            db.execute("INSERT OR IGNORE INTO perf VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (uid(),fy,bsm,bs_q(bsm),eid,ec,str(row.get('MP_Ref','') or ''),str(row.get('CP_Ref','') or ''),
                 str(row.get('Metric','') or ''),tot,comp,nc,pct_c,pct_nc,tgt,act,unit,st,str(row.get('Notes','') or '')))
            count+=1
        except Exception as e: errs.append(f"Row {i}: {e}")
    for fy in fys_seen: _upd_cache(db,fy)
    db.commit(); return jsonify({'imported':count,'errors':errs[:10]})

# ── ANALYTICS ──────────────────────────────────────────────────────────────
@app.route('/api/analytics/summary')
def analytics_summary():
    db=get_db(); fys=request.args.get('fys','')
    q="SELECT * FROM perf"; args=[]
    if fys:
        flist=[x.strip() for x in fys.split(',') if x.strip()]
        if flist: q+=f" WHERE fy IN ({','.join('?'*len(flist))})"; args=flist
    rows=db.execute(q,args).fetchall(); result={}
    for r in rows:
        fy=r['fy']
        if fy not in result:
            result[fy]={'total':0,'compliant':0,'nc':0,'by_mp':{},'by_month':{},'by_emp':{}}
        rv=result[fy]
        t=r['total'] or 1; c=r['compliant'] or (1 if r['status']=='C' else 0)
        n=r['non_compliant'] or (1 if r['status']=='NC' else 0)
        rv['total']+=t; rv['compliant']+=c; rv['nc']+=n
        mp=r['mp_ref']
        if mp:
            rv['by_mp'].setdefault(mp,{'total':0,'compliant':0,'nc':0,'by_cp':{}})
            rv['by_mp'][mp]['total']+=t; rv['by_mp'][mp]['compliant']+=c; rv['by_mp'][mp]['nc']+=n
            cp=r['cp_ref']
            if cp:
                rv['by_mp'][mp]['by_cp'].setdefault(cp,{'total':0,'compliant':0,'nc':0})
                rv['by_mp'][mp]['by_cp'][cp]['total']+=t
                rv['by_mp'][mp]['by_cp'][cp]['compliant']+=c
                rv['by_mp'][mp]['by_cp'][cp]['nc']+=n
        mo=r['bs_month']
        if mo:
            rv['by_month'].setdefault(mo,{'total':0,'compliant':0,'nc':0})
            rv['by_month'][mo]['total']+=t; rv['by_month'][mo]['compliant']+=c; rv['by_month'][mo]['nc']+=n
        ec=r['emp_code'] or r['emp_id']
        if ec:
            rv['by_emp'].setdefault(ec,{'total':0,'compliant':0,'nc':0,'by_mp':{}})
            rv['by_emp'][ec]['total']+=t; rv['by_emp'][ec]['compliant']+=c; rv['by_emp'][ec]['nc']+=n
            if mp:
                rv['by_emp'][ec]['by_mp'].setdefault(mp,{'total':0,'compliant':0,'nc':0})
                rv['by_emp'][ec]['by_mp'][mp]['total']+=t; rv['by_emp'][ec]['by_mp'][mp]['compliant']+=c; rv['by_emp'][ec]['by_mp'][mp]['nc']+=n
    def pct(d):
        t=d.get('total',0)
        d['pct_c']=round(d.get('compliant',0)/t*100,2) if t else 0
        d['pct_nc']=round(d.get('nc',0)/t*100,2) if t else 0
    for rv in result.values():
        pct(rv)
        for mp_d in rv['by_mp'].values():
            pct(mp_d)
            for cp_d in mp_d.get('by_cp',{}).values(): pct(cp_d)
        for mo_d in rv['by_month'].values(): pct(mo_d)
        for emp_d in rv['by_emp'].values():
            pct(emp_d)
            for mp2 in emp_d.get('by_mp',{}).values(): pct(mp2)
    return jsonify(result)

@app.route('/api/calendar')
def calendar_api():
    return jsonify({'bs_months':BS_MONTHS,'quarter_map':BS_Q})


# -- LOCATIONS -----------------------------------------------------------------
@app.route('/api/locations', methods=['GET','POST'])
def locations_api():
    db = get_db()
    if request.method == 'GET':
        res = []
        for loc in db.execute("SELECT * FROM locations ORDER BY code"):
            l = dict(loc)
            l['emp_ids'] = [r['emp_id'] for r in db.execute(
                "SELECT emp_id FROM emp_locations WHERE loc_id=?", (l['id'],))]
            res.append(l)
        return jsonify(res)
    d = request.json; lid = d.get('id') or uid()
    db.execute("INSERT OR REPLACE INTO locations VALUES(?,?,?,?,?)",
               (lid, d['code'], d['name'], d.get('type','Office'), d.get('address','')))
    db.execute("DELETE FROM emp_locations WHERE loc_id=?", (lid,))
    for eid in d.get('emp_ids', []):
        db.execute("INSERT OR IGNORE INTO emp_locations VALUES(?,?)", (eid, lid))
    db.commit(); return jsonify({'id': lid})

@app.route('/api/locations/<lid>', methods=['PUT','DELETE'])
def location_api(lid):
    db = get_db()
    if request.method == 'DELETE':
        for t,c in [('locations','id'),('emp_locations','loc_id'),
                    ('cp_locations','loc_id'),('mp_locations','loc_id')]:
            db.execute(f"DELETE FROM {t} WHERE {c}=?", (lid,))
        db.commit(); return jsonify({'ok': True})
    d = request.json
    db.execute("UPDATE locations SET code=?,name=?,type=?,address=? WHERE id=?",
               (d['code'], d['name'], d.get('type','Office'), d.get('address',''), lid))
    db.execute("DELETE FROM emp_locations WHERE loc_id=?", (lid,))
    for eid in d.get('emp_ids', []):
        db.execute("INSERT OR IGNORE INTO emp_locations VALUES(?,?)", (eid, lid))
    db.commit(); return jsonify({'ok': True})

@app.route('/api/analytics/by_location')
def analytics_by_location():
    db = get_db(); fy = request.args.get('fy','')
    locs = db.execute("SELECT * FROM locations ORDER BY code").fetchall()
    result = {}
    for loc in locs:
        emp_ids = [r['emp_id'] for r in db.execute(
            "SELECT emp_id FROM emp_locations WHERE loc_id=?", (loc['id'],))]
        if emp_ids:
            emp_codes = [r['emp_code'] for r in db.execute(
                "SELECT emp_code FROM employees WHERE id IN ({})".format(
                    ','.join('?'*len(emp_ids))), emp_ids)]
        else:
            emp_codes = []
        q2 = "SELECT * FROM perf WHERE 1=1"; args = []
        if fy: q2 += " AND fy=?"; args.append(fy)
        if emp_codes:
            q2 += " AND emp_code IN ({})".format(','.join('?'*len(emp_codes)))
            args += emp_codes
        rows = db.execute(q2, args).fetchall()
        tot  = sum(r['total'] or 1 for r in rows)
        comp = sum(r['compliant'] or (1 if r['status']=='C' else 0) for r in rows)
        nc   = tot - comp
        result[loc['code']] = {
            'id': loc['id'], 'name': loc['name'], 'type': loc['type'],
            'address': loc['address'], 'emp_count': len(emp_ids), 'emp_ids': emp_ids,
            'total': tot, 'compliant': comp, 'nc': nc,
            'pct_c':  round(comp/tot*100, 2) if tot else 0,
            'pct_nc': round(nc/tot*100,   2) if tot else 0,
        }
    return jsonify(result)


# ── CASCADE ────────────────────────────────────────────────────────────────────
@app.route('/api/cascade', methods=['GET','POST'])
def cascade_api():
    db = get_db()
    if request.method == 'GET':
        rows = db.execute("""
            SELECT cl.*,
                   pe.name as parent_name, pe.emp_code as parent_code,
                   ce.name as child_name,  ce.emp_code as child_code,
                   cp.ref as cp_ref, cp.title as cp_title,
                   mp.ref as mp_ref, mp.title as mp_title
            FROM cascade_links cl
            LEFT JOIN employees pe ON cl.parent_emp_id = pe.id
            LEFT JOIN employees ce ON cl.child_emp_id  = ce.id
            LEFT JOIN cps cp ON cl.parent_cp_id = cp.id
            LEFT JOIN mps mp ON cl.child_mp_id  = mp.id
            ORDER BY pe.level, pe.name
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    d = request.json
    lid = d.get('id') or uid()
    db.execute("INSERT OR REPLACE INTO cascade_links VALUES(?,?,?,?,?)",
               (lid, d['parent_emp_id'], d['parent_cp_id'],
                d['child_emp_id'],  d['child_mp_id']))
    # Also update the child MP's parent_cp_id field
    db.execute("UPDATE mps SET parent_cp_id=? WHERE id=?",
               (d['parent_cp_id'], d['child_mp_id']))
    db.commit()
    return jsonify({'id': lid})

@app.route('/api/cascade/<lid>', methods=['DELETE'])
def cascade_delete(lid):
    db = get_db()
    # Clear parent_cp_id on the child MP
    row = db.execute("SELECT child_mp_id FROM cascade_links WHERE id=?", (lid,)).fetchone()
    if row:
        db.execute("UPDATE mps SET parent_cp_id='' WHERE id=?", (row['child_mp_id'],))
    db.execute("DELETE FROM cascade_links WHERE id=?", (lid,))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/cascade/tree')
def cascade_tree():
    """Returns the full cascade tree from any employee downward"""
    db = get_db()
    emp_id = request.args.get('emp_id','')
    def build_node(eid, depth=0):
        if depth > 6: return []   # safety limit
        emp = db.execute("SELECT * FROM employees WHERE id=?", (eid,)).fetchone()
        if not emp: return []
        emp = dict(emp)
        # Get this employee's role
        roles = [dict(r) for r in db.execute(
            "SELECT r.* FROM roles r JOIN emp_roles er ON r.id=er.role_id WHERE er.emp_id=?", (eid,))]
        # Get MPs owned by this employee
        mps = [dict(m) for m in db.execute(
            "SELECT m.* FROM mps m JOIN mp_owners mo ON m.id=mo.mp_id WHERE mo.emp_id=?", (eid,))]
        for mp in mps:
            # Get CPs under this MP
            mp['cps'] = [dict(c) for c in db.execute(
                "SELECT c.* FROM cps c WHERE c.mp_id=?", (mp['id'],))]
            for cp in mp['cps']:
                cp['owners'] = [dict(e) for e in db.execute(
                    "SELECT e.* FROM employees e JOIN cp_owners co ON e.id=co.emp_id WHERE co.cp_id=?",
                    (cp['id'],))]
                # Find cascade children — sub-employees whose MP derives from this CP
                links = db.execute(
                    "SELECT * FROM cascade_links WHERE parent_cp_id=?", (cp['id'],)).fetchall()
                cp['cascade_children'] = []
                for lnk in links:
                    child_nodes = build_node(lnk['child_emp_id'], depth+1)
                    cp['cascade_children'].extend(child_nodes)
        emp['roles'] = roles
        emp['mps']   = mps
        return [emp]

    if emp_id:
        tree = build_node(emp_id)
    else:
        # Start from top-level employees (no manager)
        roots = db.execute(
            "SELECT id FROM employees WHERE manager_id IS NULL OR manager_id=''").fetchall()
        tree = []
        for r in roots:
            tree.extend(build_node(r['id']))
    return jsonify(tree)


# -- BS DATE & ORG TREE API ----------------------------------------------------








# -- BS DATE & ORG TREE API ----------------------------------------------------








# -- BS DATE & ORG TREE API ----------------------------------------------------
@app.route('/api/bs_today')
def bs_today():
    return jsonify({'date':today_bs(),'fy':current_bs_fy(),
        'months':BS_MONTHS,'quarter_map':BS_FY_Q,
        'month_days':{str(k):v for k,v in BS_MONTH_DAYS.items()}})

@app.route('/api/bs_calendar/<int:year>')
def bs_calendar(year):
    return jsonify({'year':year,'months':[
        {'name':m,'index':i+1,'days':bs_days_in_month(year,i),'quarter':BS_FY_Q.get(m,'Q1')}
        for i,m in enumerate(BS_MONTHS)]})

@app.route('/api/org/tree')
def org_tree():
    db=get_db()
    fy=request.args.get('fy',''); loc=request.args.get('loc',''); sect=request.args.get('sect','')
    def get_perf(eid,ec):
        q2="SELECT * FROM perf WHERE (emp_id=? OR emp_code=?)"; args=[eid,ec]
        if fy: q2+=" AND fy=?"; args.append(fy)
        if loc: q2+=" AND location=?"; args.append(loc)
        rows=db.execute(q2,args).fetchall()
        tot=sum(r['total'] or 1 for r in rows)
        comp=sum(r['compliant'] or (1 if r['status']=='C' else 0) for r in rows)
        return {'tot':tot,'comp':comp,'nc':tot-comp,
                'pct':round(comp/tot*100,2) if tot else None,'records':len(rows)}
    def build(eid,depth=0,visited=None):
        if visited is None: visited=set()
        if eid in visited or depth>10: return None
        visited.add(eid)
        emp=db.execute("SELECT * FROM employees WHERE id=?",(eid,)).fetchone()
        if not emp: return None
        emp=dict(emp)
        if sect and emp.get('dept','')!=sect: return None
        own=get_perf(eid,emp.get('emp_code',''))
        roles=[dict(r) for r in db.execute(
            "SELECT r.* FROM roles r JOIN emp_roles er ON r.id=er.role_id WHERE er.emp_id=?",(eid,))]
        mps=[]
        for mp in db.execute(
            "SELECT m.* FROM mps m JOIN mp_owners mo ON m.id=mo.mp_id WHERE mo.emp_id=?",(eid,)).fetchall():
            mp=dict(mp); mp['cps']=[dict(c) for c in db.execute("SELECT * FROM cps WHERE mp_id=?",(mp['id'],))]
            mps.append(mp)
        locs=[dict(l) for l in db.execute(
            "SELECT lo.* FROM locations lo JOIN emp_locations el ON lo.id=el.loc_id WHERE el.emp_id=?",(eid,))]
        subs=db.execute("SELECT id FROM employees WHERE manager_id=?",(eid,)).fetchall()
        children=[]; sub_tot=0; sub_comp=0
        for s in subs:
            node=build(s['id'],depth+1,visited)
            if node:
                children.append(node)
                sub_tot+=node['rollup']['tot']; sub_comp+=node['rollup']['comp']
        rt=own['tot']+sub_tot; rc=own['comp']+sub_comp
        return {'id':emp['id'],'name':emp['name'],'emp_code':emp.get('emp_code',''),
                'role':emp.get('role',''),'dept':emp.get('dept','Ops'),'level':emp.get('level',3),
                'roles':roles,'mps':mps,'locations':locs,'own':own,
                'rollup':{'tot':rt,'comp':rc,'nc':rt-rc,'pct':round(rc/rt*100,2) if rt else None},
                'children':children,'depth':depth}
    roots=db.execute("SELECT id FROM employees WHERE manager_id IS NULL OR manager_id=''").fetchall()
    tree=[build(r['id']) for r in roots]; tree=[t for t in tree if t]
    return jsonify(tree)

@app.route('/api/org/move',methods=['POST'])
def org_move():
    db=get_db(); d=request.json
    eid=d.get('emp_id'); new_mgr=d.get('new_manager_id') or None
    if not eid: return jsonify({'error':'emp_id required'}),400
    def is_sub(root,target):
        subs=db.execute("SELECT id FROM employees WHERE manager_id=?",(root,)).fetchall()
        for s in subs:
            if s['id']==target: return True
            if is_sub(s['id'],target): return True
        return False
    if new_mgr and is_sub(eid,new_mgr): return jsonify({'error':'Cannot assign subordinate as manager'}),400
    db.execute("UPDATE employees SET manager_id=? WHERE id=?",(new_mgr,eid))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/org/assign_mp',methods=['POST'])
def org_assign_mp():
    db=get_db(); d=request.json
    eid=d.get('emp_id'); mid=d.get('mp_id'); loc_id=d.get('loc_id','')
    if not eid or not mid: return jsonify({'error':'emp_id and mp_id required'}),400
    db.execute("INSERT OR IGNORE INTO mp_owners VALUES(?,?)",(mid,eid))
    db.execute("INSERT OR IGNORE INTO emp_mps VALUES(?,?)",(eid,mid))
    if loc_id: db.execute("INSERT OR IGNORE INTO mp_locations VALUES(?,?)",(mid,loc_id))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/org/assign_cp',methods=['POST'])
def org_assign_cp():
    db=get_db(); d=request.json
    eid=d.get('emp_id'); cid=d.get('cp_id'); loc_id=d.get('loc_id','')
    if not eid or not cid: return jsonify({'error':'emp_id and cp_id required'}),400
    db.execute("INSERT OR IGNORE INTO cp_owners VALUES(?,?)",(cid,eid))
    db.execute("INSERT OR IGNORE INTO emp_cps VALUES(?,?)",(eid,cid))
    if loc_id: db.execute("INSERT OR IGNORE INTO cp_locations VALUES(?,?)",(cid,loc_id))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/org/cascade_assign',methods=['POST'])
def org_cascade_assign():
    db=get_db(); d=request.json
    parent_cp_id=d.get('parent_cp_id'); child_emp_id=d.get('child_emp_id')
    child_mp_id=d.get('child_mp_id')
    if not parent_cp_id or not child_emp_id: return jsonify({'error':'parent_cp_id and child_emp_id required'}),400
    cp=db.execute("SELECT * FROM cps WHERE id=?",(parent_cp_id,)).fetchone()
    if not cp: return jsonify({'error':'CP not found'}),404
    if not child_mp_id:
        mid=uid()
        db.execute("INSERT OR IGNORE INTO mps VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (mid,cp['ref'],cp['title'],cp['target'],'Monthly',0,0,0,parent_cp_id,2))
        child_mp_id=mid
    else:
        db.execute("UPDATE mps SET parent_cp_id=? WHERE id=?",(parent_cp_id,child_mp_id))
    link_id=uid()
    db.execute("INSERT OR REPLACE INTO cascade_links VALUES(?,?,?,?,?)",
               (link_id,d.get('parent_emp_id',''),parent_cp_id,child_emp_id,child_mp_id))
    db.execute("INSERT OR IGNORE INTO mp_owners VALUES(?,?)",(child_mp_id,child_emp_id))
    db.commit(); return jsonify({'ok':True,'mp_id':child_mp_id,'link_id':link_id})


# ── DASHBOARD LAYOUTS ──────────────────────────────────────────────────────────
@app.route('/api/dashboard_layouts', methods=['GET','POST'])
def dashboard_layouts_api():
    db = get_db()
    if request.method == 'GET':
        user = request.args.get('user','default')
        rows = db.execute("SELECT * FROM dashboard_layouts WHERE user=? ORDER BY name",(user,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try: d['layout'] = json.loads(d['layout_json'])
            except: d['layout'] = []
            result.append(d)
        return jsonify(result)
    d = request.json
    lid = d.get('id') or uid()
    now = datetime.datetime.now().isoformat()
    layout_json = json.dumps(d.get('layout',[]))
    user = d.get('user','default')
    existing = db.execute("SELECT id FROM dashboard_layouts WHERE id=?",(lid,)).fetchone()
    if existing:
        db.execute("UPDATE dashboard_layouts SET name=?,layout_json=?,updated_at=? WHERE id=?",
                   (d['name'], layout_json, now, lid))
    else:
        db.execute("INSERT INTO dashboard_layouts VALUES(?,?,?,?,?,?)",
                   (lid, d['name'], user, layout_json, now, now))
    db.commit()
    return jsonify({'id': lid})

@app.route('/api/dashboard_layouts/<lid>', methods=['PUT','DELETE'])
def dashboard_layout_api(lid):
    db = get_db()
    if request.method == 'DELETE':
        db.execute("DELETE FROM dashboard_layouts WHERE id=?",(lid,))
        db.commit(); return jsonify({'ok':True})
    d = request.json
    now = datetime.datetime.now().isoformat()
    db.execute("UPDATE dashboard_layouts SET name=?,layout_json=?,updated_at=? WHERE id=?",
               (d['name'], json.dumps(d.get('layout',[])), now, lid))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/analytics/widget', methods=['GET'])
def analytics_widget():
    """Flexible analytics endpoint for dashboard widgets"""
    db = get_db()
    metric  = request.args.get('metric','overall')  # overall|by_mp|by_cp|by_emp|by_location|by_month|by_sector
    fy      = request.args.get('fy','')
    loc     = request.args.get('loc','')
    emp_id  = request.args.get('emp_id','')
    sector  = request.args.get('sector','')
    mp_ref  = request.args.get('mp_ref','')

    q2 = "SELECT p.*, e.dept FROM perf p LEFT JOIN employees e ON p.emp_id=e.id WHERE 1=1"
    args = []
    if fy:     q2 += " AND p.fy=?";       args.append(fy)
    if emp_id: q2 += " AND p.emp_id=?";   args.append(emp_id)
    if mp_ref: q2 += " AND p.mp_ref=?";   args.append(mp_ref)
    if loc:
        emp_codes = [r['emp_code'] for r in db.execute(
            "SELECT e.emp_code FROM employees e JOIN emp_locations el ON e.id=el.emp_id "
            "JOIN locations l ON el.loc_id=l.id WHERE l.code=?", (loc,))]
        if emp_codes:
            q2 += " AND p.emp_code IN ({})".format(','.join('?'*len(emp_codes)))
            args += emp_codes
        else:
            return jsonify({'labels':[],'values':[],'compliant':[],'nc':[],'total':[],'pct':[]})
    if sector:
        emp_codes2 = [r['emp_code'] for r in db.execute(
            "SELECT emp_code FROM employees WHERE dept=?", (sector,))]
        if emp_codes2:
            q2 += " AND p.emp_code IN ({})".format(','.join('?'*len(emp_codes2)))
            args += emp_codes2

    rows = db.execute(q2, args).fetchall()

    def agg(rows):
        tot  = sum(r['total'] or 1 for r in rows)
        comp = sum(r['compliant'] or (1 if r['status']=='C' else 0) for r in rows)
        nc   = tot - comp
        return {'tot':tot,'comp':comp,'nc':nc,'pct':round(comp/tot*100,2) if tot else 0}

    if metric == 'overall':
        a = agg(rows)
        return jsonify({'labels':['Compliant','Non-Compliant'],
                        'values':[a['comp'],a['nc']],
                        'summary': a})

    elif metric == 'by_month':
        buckets = {}
        for r in rows:
            m = r['bs_month'] or 'Unknown'
            buckets.setdefault(m,[]).append(r)
        BS_ORDER = ['Shrawan','Bhadra','Ashwin','Kartik','Mangsir','Poush','Magh','Falgun','Chaitra','Baisakh','Jestha','Ashadh']
        keys = sorted(buckets.keys(), key=lambda x: BS_ORDER.index(x) if x in BS_ORDER else 99)
        result = {'labels':[],'values':[],'compliant':[],'nc':[],'total':[]}
        for k in keys:
            a = agg(buckets[k])
            result['labels'].append(k); result['values'].append(a['pct'])
            result['compliant'].append(a['comp']); result['nc'].append(a['nc']); result['total'].append(a['tot'])
        return jsonify(result)

    elif metric == 'by_mp':
        buckets = {}
        for r in rows:
            m = r['mp_ref'] or 'Unknown'
            buckets.setdefault(m,[]).append(r)
        result = {'labels':[],'values':[],'compliant':[],'nc':[],'total':[]}
        for k in sorted(buckets.keys()):
            a = agg(buckets[k])
            result['labels'].append(k); result['values'].append(a['pct'])
            result['compliant'].append(a['comp']); result['nc'].append(a['nc']); result['total'].append(a['tot'])
        return jsonify(result)

    elif metric == 'by_emp':
        buckets = {}
        for r in rows:
            ec = r['emp_code'] or r['emp_id'] or 'Unknown'
            buckets.setdefault(ec,[]).append(r)
        emps = {e['emp_code']:e['name'] for e in db.execute("SELECT emp_code,name FROM employees")}
        result = {'labels':[],'values':[],'compliant':[],'nc':[],'total':[]}
        for k in sorted(buckets.keys()):
            a = agg(buckets[k])
            result['labels'].append(emps.get(k,k)); result['values'].append(a['pct'])
            result['compliant'].append(a['comp']); result['nc'].append(a['nc']); result['total'].append(a['tot'])
        return jsonify(result)

    elif metric == 'by_location':
        locs = db.execute("SELECT * FROM locations").fetchall()
        result = {'labels':[],'values':[],'compliant':[],'nc':[],'total':[]}
        for loc_row in locs:
            eids = [r['emp_id'] for r in db.execute("SELECT emp_id FROM emp_locations WHERE loc_id=?",(loc_row['id'],))]
            ecodes = [r['emp_code'] for r in db.execute(
                "SELECT emp_code FROM employees WHERE id IN ({})".format(','.join('?'*len(eids))),eids)] if eids else []
            loc_rows = [r for r in rows if r['emp_code'] in ecodes] if ecodes else []
            if not loc_rows: continue
            a = agg(loc_rows)
            result['labels'].append(loc_row['name']); result['values'].append(a['pct'])
            result['compliant'].append(a['comp']); result['nc'].append(a['nc']); result['total'].append(a['tot'])
        return jsonify(result)

    elif metric == 'by_sector':
        buckets = {}
        for r in rows:
            dept = r['dept'] or 'Unknown'
            buckets.setdefault(dept,[]).append(r)
        result = {'labels':[],'values':[],'compliant':[],'nc':[],'total':[]}
        for k in sorted(buckets.keys()):
            a = agg(buckets[k])
            result['labels'].append(k); result['values'].append(a['pct'])
            result['compliant'].append(a['comp']); result['nc'].append(a['nc']); result['total'].append(a['tot'])
        return jsonify(result)

    return jsonify({'labels':[],'values':[],'compliant':[],'nc':[],'total':[]})

@app.route('/')
def index():
    with open(os.path.join(os.path.dirname(__file__),'index.html'),'r', encoding='utf-8') as f: return f.read()

if __name__=='__main__':
    init_db()
    print("\n"+"="*55)
    print("  Sipradi SC-MPCP System v2.0")
    print("  http://localhost:5050")
    print("="*55+"\n")
    app.run(debug=True,port=5050,host='0.0.0.0')

# ── SAMPLE FILE DOWNLOADS ──────────────────────────────────────────────────
@app.route('/api/samples/<fname>')
def sample_file(fname):
    safe = {'employees':'Sample_Employees.xlsx',
            'mps':'Sample_ManagingPoints.xlsx',
            'cps':'Sample_CheckingPoints.xlsx',
            'perf':'Sample_Performance.csv'}
    if fname not in safe: return 'Not found', 404
    path = os.path.join(os.path.dirname(__file__), safe[fname])
    if not os.path.exists(path): return 'File not found — run app.py to regenerate', 404
    return send_file(path, as_attachment=True, download_name=safe[fname])

@app.route('/api/employees/import', methods=['POST'])
def import_employees():
    """Excel/CSV employee bulk import"""
    f = request.files.get('file')
    if not f: return jsonify({'error':'No file'}), 400
    db = get_db()
    ext = f.filename.lower().split('.')[-1]
    code_re = {}  # manager_code -> id (resolved after insert)
    imported = 0; errors = []
    rows = []
    if ext in ('xlsx','xls'):
        if not HAS_OPENPYXL: return jsonify({'error':'pip install openpyxl'}), 400
        wb = openpyxl.load_workbook(f, data_only=True); ws = wb.active
        hdrs = [str(c.value or '').strip().lower() for c in next(ws.iter_rows(min_row=1,max_row=1))]
        def col(n,al=[]): return next((hdrs.index(a) for a in [n]+al if a in hdrs), None)
        ci=col('emp_code',['code','employee code']); cn=col('name',['full name'])
        cr=col('role',['designation','job title']); cl=col('level')
        cd=col('department',['dept']); cm=col('manager_code',['manager code','reports to'])
        ce=col('email',['email address'])
        for i,row in enumerate(ws.iter_rows(min_row=3,values_only=True),3):
            try:
                name=str(row[cn] or '').strip() if cn is not None else ''
                if not name or name.startswith('←'): continue  # skip instruction rows
                rows.append({'emp_code':str(row[ci] or '').strip() if ci is not None else '',
                    'name':name,'role':str(row[cr] or '') if cr is not None else '',
                    'level':int(row[cl] or 3) if cl is not None else 3,
                    'dept':str(row[cd] or 'Ops') if cd is not None else 'Ops',
                    'manager_code':str(row[cm] or '').strip() if cm is not None else '',
                    'email':str(row[ce] or '') if ce is not None else ''})
            except Exception as e: errors.append(f"Row {i}: {e}")
    else:
        text = f.read().decode('utf-8-sig'); reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            name = (row.get('Name','') or row.get('name','')).strip()
            if not name: continue
            rows.append({'emp_code':(row.get('Emp_Code','') or row.get('emp_code','')).strip(),
                'name':name,'role':row.get('Role',''),'level':int(row.get('Level',3) or 3),
                'dept':row.get('Department','Ops') or 'Ops',
                'manager_code':(row.get('Manager_Code','') or row.get('manager_code','')).strip(),
                'email':row.get('Email','') or ''})
    # First pass: insert all without manager links
    id_map = {}  # emp_code -> id
    for r in rows:
        code = r['emp_code']
        if not code:
            last = db.execute("SELECT emp_code FROM employees WHERE emp_code LIKE 'EMP-%' ORDER BY emp_code DESC LIMIT 1").fetchone()
            try: num = int(last['emp_code'].split('-')[1])+1 if last else 1
            except: num = 1
            code = f"EMP-{num:03d}"
        eid = uid()
        db.execute("INSERT OR REPLACE INTO employees VALUES(?,?,?,?,?,?,?,?)",
            (eid,code,r['name'],r['role'],r['level'],r['dept'],None,r['email']))
        id_map[code] = eid; imported += 1
    # Second pass: link managers
    for r in rows:
        mc = r['manager_code']
        if mc and mc in id_map:
            code = r['emp_code'] or list(id_map.keys())[-1]
            eid = id_map.get(code)
            mid = id_map.get(mc)
            if eid and mid: db.execute("UPDATE employees SET manager_id=? WHERE id=?",(mid,eid))
    db.commit()
    return jsonify({'imported':imported,'errors':errors[:10]})
