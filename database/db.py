"""database/db.py — All database operations. SQLite by default, PostgreSQL if DATABASE_URL is set."""
import os, json, hashlib, secrets, sqlite3
from pathlib import Path
from typing import Optional, List, Dict

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_conn():
    if DATABASE_URL.startswith("postgresql"):
        try:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = False
            return conn
        except Exception as e:
            print(f"PG failed ({e}), using SQLite")
    Path("database").mkdir(exist_ok=True)
    conn = sqlite3.connect("database/jobs.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ph(conn):
    try:
        import psycopg2
        return "%s" if isinstance(conn, psycopg2.extensions.connection) else "?"
    except ImportError:
        return "?"


def _rows(cur) -> List[Dict]:
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def init_db():
    conn = get_conn()
    conn.cursor().executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        last_login TEXT
    );
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        run_at TEXT DEFAULT (datetime('now')),
        track_filter TEXT,
        jobs_found INTEGER DEFAULT 0,
        jobs_matched INTEGER DEFAULT 0,
        status TEXT DEFAULT 'completed'
    );
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        run_id INTEGER,
        external_id TEXT,
        title TEXT, company TEXT, location TEXT,
        description TEXT, url TEXT, source TEXT, salary TEXT,
        role_type TEXT, match_score REAL DEFAULT 0,
        match_category TEXT, common_skills TEXT, missing_skills TEXT,
        action_plan TEXT, application_pitch TEXT,
        networking_message TEXT, alignment_reasons TEXT,
        cover_letter TEXT, cover_letter_file TEXT, subject_line TEXT,
        cold_email TEXT, linkedin_note TEXT, resume_file TEXT,
        status TEXT DEFAULT 'Pending', tags TEXT,
        date_posted TEXT, notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(user_id, external_id)
    );
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        email_id TEXT, company TEXT, subject TEXT,
        category TEXT, received_at TEXT,
        body_preview TEXT, action_needed INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS resume_uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT, content TEXT, parsed_json TEXT,
        uploaded_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_jobs_user  ON jobs(user_id);
    CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(match_score DESC);
    """) if hasattr(conn.cursor(), 'executescript') else _init_pg(conn)
    conn.commit(); conn.close()


def _init_pg(conn):
    stmts = [
        """CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL,
           email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, salt TEXT NOT NULL,
           created_at TEXT DEFAULT NOW()::TEXT, last_login TEXT)""",
        """CREATE TABLE IF NOT EXISTS runs (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
           run_at TEXT DEFAULT NOW()::TEXT, track_filter TEXT, jobs_found INTEGER DEFAULT 0,
           jobs_matched INTEGER DEFAULT 0, status TEXT DEFAULT 'completed')""",
        """CREATE TABLE IF NOT EXISTS jobs (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
           run_id INTEGER, external_id TEXT, title TEXT, company TEXT, location TEXT,
           description TEXT, url TEXT, source TEXT, salary TEXT, role_type TEXT,
           match_score REAL DEFAULT 0, match_category TEXT, common_skills TEXT,
           missing_skills TEXT, action_plan TEXT, application_pitch TEXT,
           networking_message TEXT, alignment_reasons TEXT, cover_letter TEXT,
           cover_letter_file TEXT, subject_line TEXT, cold_email TEXT, linkedin_note TEXT,
           resume_file TEXT, status TEXT DEFAULT 'Pending', tags TEXT,
           date_posted TEXT, notes TEXT, created_at TEXT DEFAULT NOW()::TEXT)""",
        """CREATE TABLE IF NOT EXISTS responses (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
           email_id TEXT, company TEXT, subject TEXT, category TEXT,
           received_at TEXT, body_preview TEXT, action_needed BOOLEAN DEFAULT FALSE)""",
        """CREATE TABLE IF NOT EXISTS resume_uploads (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
           filename TEXT, content TEXT, parsed_json TEXT, uploaded_at TEXT DEFAULT NOW()::TEXT)""",
    ]
    cur = conn.cursor()
    for s in stmts:
        try: cur.execute(s)
        except Exception: pass


# ── Auth ──────────────────────────────────────────────────────────────────────

def _hash(pw, salt): return hashlib.sha256(f"{salt}{pw}".encode()).hexdigest()

def create_user(username: str, email: str, password: str) -> Optional[int]:
    salt = secrets.token_hex(16)
    conn = get_conn(); p = _ph(conn)
    try:
        cur = conn.cursor()
        cur.execute(f"INSERT INTO users (username,email,password_hash,salt) VALUES ({p},{p},{p},{p})",
                    (username.strip(), email.lower().strip(), _hash(password, salt), salt))
        conn.commit()
        uid = cur.lastrowid
        conn.close()
        return uid
    except Exception:
        conn.rollback(); conn.close(); return None

def verify_user(username: str, password: str) -> Optional[Dict]:
    conn = get_conn(); p = _ph(conn); cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE username={p} OR email={p}", (username, username.lower()))
    rows = _rows(cur); conn.close()
    if not rows: return None
    d = rows[0]
    if _hash(password, d["salt"]) == d["password_hash"]:
        return d
    return None

def get_user(user_id: int) -> Optional[Dict]:
    conn = get_conn(); p = _ph(conn); cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE id={p}", (user_id,))
    rows = _rows(cur); conn.close()
    return rows[0] if rows else None


# ── Runs ──────────────────────────────────────────────────────────────────────

def create_run(user_id: int, track_filter: str = None) -> int:
    conn = get_conn(); p = _ph(conn); cur = conn.cursor()
    cur.execute(f"INSERT INTO runs (user_id,track_filter) VALUES ({p},{p})", (user_id, track_filter))
    conn.commit()
    run_id = cur.lastrowid or _last_id(conn, "runs", user_id)
    conn.close(); return run_id

def finish_run(run_id: int, found: int, matched: int, status: str = "completed"):
    conn = get_conn(); p = _ph(conn)
    conn.cursor().execute(f"UPDATE runs SET jobs_found={p},jobs_matched={p},status={p} WHERE id={p}",
                          (found, matched, status, run_id))
    conn.commit(); conn.close()

def get_runs(user_id: int, limit: int = 20) -> List[Dict]:
    conn = get_conn(); p = _ph(conn); cur = conn.cursor()
    cur.execute(f"SELECT * FROM runs WHERE user_id={p} ORDER BY run_at DESC LIMIT {limit}", (user_id,))
    rows = _rows(cur); conn.close(); return rows

def _last_id(conn, table, user_id):
    p = _ph(conn); cur = conn.cursor()
    cur.execute(f"SELECT id FROM {table} WHERE user_id={p} ORDER BY id DESC LIMIT 1", (user_id,))
    r = cur.fetchone(); return (r[0] if r else 1)


# ── Jobs ──────────────────────────────────────────────────────────────────────

def _js(val):
    if isinstance(val, list): return json.dumps(val)
    return val or ""

def upsert_jobs(user_id: int, run_id: int, jobs: List[Dict]) -> int:
    conn = get_conn(); p = _ph(conn); cur = conn.cursor(); new = 0
    for job in jobs:
        cur.execute(f"SELECT id FROM jobs WHERE user_id={p} AND external_id={p}",
                    (user_id, job.get("id", "")))
        if cur.fetchone():
            cur.execute(f"""UPDATE jobs SET match_score={p},match_category={p},common_skills={p},
                missing_skills={p},action_plan={p},cover_letter={p},cover_letter_file={p},
                subject_line={p},cold_email={p},linkedin_note={p},run_id={p}
                WHERE user_id={p} AND external_id={p}""",
                (job.get("match_score",0), job.get("match_category",""),
                 _js(job.get("common_skills",[])), _js(job.get("missing_skills",[])),
                 job.get("action_plan",""), job.get("cover_letter",""),
                 job.get("cover_letter_file",""), job.get("subject_line",""),
                 job.get("cold_email",""), job.get("linkedin_note",""),
                 run_id, user_id, job.get("id","")))
        else:
            try:
                cur.execute(f"""INSERT INTO jobs (user_id,run_id,external_id,title,company,location,
                    description,url,source,salary,role_type,match_score,match_category,
                    common_skills,missing_skills,action_plan,application_pitch,
                    networking_message,alignment_reasons,cover_letter,cover_letter_file,
                    subject_line,cold_email,linkedin_note,resume_file,tags,date_posted)
                    VALUES ({",".join([p]*27)})""",
                    (user_id, run_id, job.get("id",""), job.get("title",""),
                     job.get("company",""), job.get("location",""),
                     job.get("description","")[:3000], job.get("url",""),
                     job.get("source",""), job.get("salary",""), job.get("role_type",""),
                     job.get("match_score",0), job.get("match_category",""),
                     _js(job.get("common_skills",[])), _js(job.get("missing_skills",[])),
                     job.get("action_plan",""), job.get("application_pitch",""),
                     job.get("networking_message",""), _js(job.get("alignment_reasons",[])),
                     job.get("cover_letter",""), job.get("cover_letter_file",""),
                     job.get("subject_line",""), job.get("cold_email",""),
                     job.get("linkedin_note",""), job.get("resume_file",""),
                     _js(job.get("tags",[])), job.get("date_posted","")))
                new += 1
            except Exception: pass
    conn.commit(); conn.close(); return new

def get_jobs(user_id: int, filters: Dict = None) -> List[Dict]:
    filters = filters or {}
    conn = get_conn(); p = _ph(conn)
    q = f"SELECT * FROM jobs WHERE user_id={p}"; params = [user_id]
    if filters.get("role_type"): q += f" AND role_type={p}"; params.append(filters["role_type"])
    if filters.get("status"):    q += f" AND status={p}";    params.append(filters["status"])
    if filters.get("min_score"): q += f" AND match_score>={p}"; params.append(filters["min_score"])
    if filters.get("search"):
        s = f"%{filters['search']}%"
        q += f" AND (title LIKE {p} OR company LIKE {p})"; params += [s, s]
    q += " ORDER BY match_score DESC"
    if filters.get("limit"): q += f" LIMIT {int(filters['limit'])}"
    cur = conn.cursor(); cur.execute(q, params)
    rows = _rows(cur); conn.close()
    for d in rows:
        for k in ("common_skills","missing_skills","alignment_reasons","tags"):
            try: d[k] = json.loads(d.get(k) or "[]")
            except: d[k] = []
    return rows

def update_job_status(job_id: int, user_id: int, status: str, notes: str = ""):
    conn = get_conn(); p = _ph(conn)
    conn.cursor().execute(f"UPDATE jobs SET status={p},notes={p} WHERE id={p} AND user_id={p}",
                          (status, notes, job_id, user_id))
    conn.commit(); conn.close()


# ── Resume ────────────────────────────────────────────────────────────────────

def save_resume(user_id: int, filename: str, content: str, parsed_json: str = ""):
    conn = get_conn(); p = _ph(conn)
    conn.cursor().execute(
        f"INSERT INTO resume_uploads (user_id,filename,content,parsed_json) VALUES ({p},{p},{p},{p})",
        (user_id, filename, content, parsed_json))
    conn.commit(); conn.close()

def get_latest_resume(user_id: int) -> Optional[Dict]:
    conn = get_conn(); p = _ph(conn); cur = conn.cursor()
    cur.execute(f"SELECT * FROM resume_uploads WHERE user_id={p} ORDER BY uploaded_at DESC LIMIT 1",
                (user_id,))
    rows = _rows(cur); conn.close()
    return rows[0] if rows else None


# ── Email responses ───────────────────────────────────────────────────────────

def save_email_responses(user_id: int, emails: List[Dict]):
    conn = get_conn(); p = _ph(conn); cur = conn.cursor()
    for e in emails:
        cur.execute(f"SELECT id FROM responses WHERE user_id={p} AND email_id={p}",
                    (user_id, e.get("id","")))
        if not cur.fetchone():
            try:
                cur.execute(f"""INSERT INTO responses
                    (user_id,email_id,company,subject,category,received_at,body_preview,action_needed)
                    VALUES ({p},{p},{p},{p},{p},{p},{p},{p})""",
                    (user_id, e.get("id",""), e.get("company",""), e.get("subject",""),
                     e.get("category","UNKNOWN"), e.get("date",""),
                     e.get("body_preview",""), int(e.get("action_needed", False))))
            except Exception: pass
    conn.commit(); conn.close()

def get_responses(user_id: int) -> List[Dict]:
    conn = get_conn(); p = _ph(conn); cur = conn.cursor()
    cur.execute(f"SELECT * FROM responses WHERE user_id={p} ORDER BY received_at DESC", (user_id,))
    rows = _rows(cur); conn.close(); return rows


# ── Analytics ────────────────────────────────────────────────────────────────

def get_analytics(user_id: int) -> Dict:
    conn = get_conn(); p = _ph(conn); cur = conn.cursor()
    def q(sql): cur.execute(sql, (user_id,)); return cur.fetchall()
    total    = q(f"SELECT COUNT(*) FROM jobs WHERE user_id={p}")[0][0]
    by_track = q(f"SELECT role_type,COUNT(*) FROM jobs WHERE user_id={p} GROUP BY role_type")
    by_stat  = q(f"SELECT status,COUNT(*) FROM jobs WHERE user_id={p} GROUP BY status")
    by_cat   = q(f"SELECT match_category,COUNT(*),AVG(match_score) FROM jobs WHERE user_id={p} GROUP BY match_category")
    top5     = q(f"SELECT title,company,role_type,match_score FROM jobs WHERE user_id={p} ORDER BY match_score DESC LIMIT 5")
    runs_ct  = q(f"SELECT COUNT(*) FROM runs WHERE user_id={p}")[0][0]
    st       = q(f"""SELECT DATE(r.run_at),AVG(j.match_score),COUNT(j.id) FROM runs r
                    JOIN jobs j ON j.run_id=r.id WHERE r.user_id={p}
                    GROUP BY DATE(r.run_at) ORDER BY DATE(r.run_at) DESC LIMIT 30""")
    conn.close()
    return {
        "total_jobs": total, "total_runs": runs_ct,
        "by_track":   {r[0]:r[1] for r in by_track if r[0]},
        "by_status":  {r[0]:r[1] for r in by_stat  if r[0]},
        "by_category":{r[0]:{"count":r[1],"avg":round(r[2] or 0,1)} for r in by_cat if r[0]},
        "top5":       [{"title":r[0],"company":r[1],"role_type":r[2],"match_score":r[3]} for r in top5],
        "score_over_time":[{"date":r[0],"avg_score":round(r[1] or 0,1),"job_count":r[2]} for r in st],
        "email_responses": {},
    }
