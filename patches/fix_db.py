import sqlite3, os

db_path = 'scm.db'
if not os.path.exists(db_path):
    print("No scm.db found - will be created fresh on app start")
else:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS locations(
      id TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
      address TEXT DEFAULT '', type TEXT DEFAULT 'Branch',
      dept TEXT DEFAULT 'Ops', active INTEGER DEFAULT 1)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS location_employees(
      loc_id TEXT, emp_id TEXT, PRIMARY KEY(loc_id, emp_id))""")
    cols = [r[1] for r in cur.execute("PRAGMA table_info(locations)").fetchall()]
    if 'dept' not in cols:
        cur.execute("ALTER TABLE locations ADD COLUMN dept TEXT DEFAULT 'Ops'")
        print("Added dept column")
    con.commit()
    con.close()
    print("DB migration done")
    con2 = sqlite3.connect(db_path)
    print("Columns:", [r[1] for r in con2.execute("PRAGMA table_info(locations)").fetchall()])
    con2.close()
