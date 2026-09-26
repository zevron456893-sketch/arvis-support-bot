import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from config import DB_PATH

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL UNIQUE,
            username TEXT,
            telegram_name TEXT,
            server TEXT,
            account_id TEXT,
            nickname TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL REFERENCES users(id),
            category TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            admin_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            closed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL REFERENCES tickets(id),
            sender_id INTEGER NOT NULL,
            sender_type TEXT NOT NULL,
            message_type TEXT NOT NULL,
            text TEXT,
            telegram_message_id INTEGER,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS admins (
            telegram_id INTEGER PRIMARY KEY,
            role TEXT NOT NULL DEFAULT 'operator',
            added_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ticket_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL REFERENCES tickets(id),
            action TEXT NOT NULL,
            admin_id INTEGER,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS admin_sessions (
            admin_id INTEGER PRIMARY KEY,
            ticket_id INTEGER REFERENCES tickets(id),
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id);
        CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
        CREATE INDEX IF NOT EXISTS idx_messages_ticket ON messages(ticket_id);
        """)
        for admin_id in __import__("config").ADMIN_IDS:
            c.execute(
                "INSERT OR IGNORE INTO admins(telegram_id, role, added_at) VALUES (?, 'operator', ?)",
                (admin_id, now_iso())
            )

def upsert_user(tg_user):
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE telegram_id=?", (tg_user.id,)).fetchone()
        ts = now_iso()
        username = tg_user.username or ""
        name = " ".join(x for x in [tg_user.first_name, tg_user.last_name] if x).strip()
        if row:
            c.execute(
                "UPDATE users SET username=?, telegram_name=?, updated_at=? WHERE telegram_id=?",
                (username, name, ts, tg_user.id)
            )
        else:
            c.execute(
                """INSERT INTO users(telegram_id, username, telegram_name, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (tg_user.id, username, name, ts, ts)
            )
        return c.execute("SELECT * FROM users WHERE telegram_id=?", (tg_user.id,)).fetchone()

def get_user(tg_id):
    with db() as c:
        return c.execute("SELECT * FROM users WHERE telegram_id=?", (tg_id,)).fetchone()

def update_profile(tg_id, server=None, account_id=None, nickname=None):
    fields, vals = [], []
    if server is not None:
        fields += ["server=?"]; vals += [server]
    if account_id is not None:
        fields += ["account_id=?"]; vals += [account_id]
    if nickname is not None:
        fields += ["nickname=?"]; vals += [nickname]
    fields += ["updated_at=?"]; vals += [now_iso()]
    vals += [tg_id]
    with db() as c:
        c.execute(f"UPDATE users SET {', '.join(fields)} WHERE telegram_id=?", vals)
        return c.execute("SELECT * FROM users WHERE telegram_id=?", (tg_id,)).fetchone()

def profile_complete(user):
    return bool(user and user["server"] and user["account_id"] and user["nickname"])

def _next_ticket_number(c):
    row = c.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM tickets").fetchone()
    return f"#ARVIS-{row['n']:04d}"

def create_ticket(tg_id, category):
    with db() as c:
        user = c.execute("SELECT * FROM users WHERE telegram_id=?", (tg_id,)).fetchone()
        if not user:
            raise ValueError("User profile does not exist")
        ticket_number = _next_ticket_number(c)
        ts = now_iso()
        cur = c.execute(
            """INSERT INTO tickets(ticket_number,user_id,category,status,created_at,updated_at)
               VALUES (?, ?, ?, 'new', ?, ?)""",
            (ticket_number, user["id"], category, ts, ts)
        )
        ticket_id = cur.lastrowid
        c.execute(
            "INSERT INTO ticket_history(ticket_id, action, admin_id, created_at) VALUES (?, 'created', NULL, ?)",
            (ticket_id, ts)
        )
        return c.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()

def get_ticket(ticket_id):
    with db() as c:
        return c.execute("""
            SELECT t.*, u.telegram_id, u.username, u.telegram_name, u.server,
                   u.account_id, u.nickname
            FROM tickets t JOIN users u ON u.id=t.user_id WHERE t.id=?
        """, (ticket_id,)).fetchone()

def get_ticket_by_number(number):
    with db() as c:
        return c.execute("""
            SELECT t.*, u.telegram_id, u.username, u.telegram_name, u.server,
                   u.account_id, u.nickname
            FROM tickets t JOIN users u ON u.id=t.user_id
            WHERE t.ticket_number=?
        """, (number,)).fetchone()

def list_user_tickets(tg_id, limit=50):
    with db() as c:
        return c.execute("""
            SELECT t.* FROM tickets t JOIN users u ON u.id=t.user_id
            WHERE u.telegram_id=? ORDER BY t.id DESC LIMIT ?
        """, (tg_id, limit)).fetchall()

def get_latest_active_ticket(tg_id):
    with db() as c:
        return c.execute("""
            SELECT t.*, u.telegram_id, u.username, u.telegram_name, u.server,
                   u.account_id, u.nickname
            FROM tickets t JOIN users u ON u.id=t.user_id
            WHERE u.telegram_id=? AND t.status!='closed'
            ORDER BY t.id DESC LIMIT 1
        """, (tg_id,)).fetchone()

def list_tickets(status=None, limit=50):
    with db() as c:
        if status:
            return c.execute("""
                SELECT t.*, u.telegram_id, u.nickname, u.account_id, u.server, u.username
                FROM tickets t JOIN users u ON u.id=t.user_id
                WHERE t.status=? ORDER BY t.id DESC LIMIT ?
            """, (status, limit)).fetchall()
        return c.execute("""
            SELECT t.*, u.telegram_id, u.nickname, u.account_id, u.server, u.username
            FROM tickets t JOIN users u ON u.id=t.user_id
            ORDER BY t.id DESC LIMIT ?
        """, (limit,)).fetchall()

def set_ticket_working(ticket_id, admin_id):
    with db() as c:
        ts = now_iso()
        cur = c.execute("""
            UPDATE tickets SET status='working', admin_id=?, updated_at=?
            WHERE id=? AND status='new'
        """, (admin_id, ts, ticket_id))
        if cur.rowcount == 0:
            return None
        c.execute(
            "INSERT INTO ticket_history(ticket_id, action, admin_id, created_at) VALUES (?, 'taken', ?, ?)",
            (ticket_id, admin_id, ts)
        )
        return c.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()

def close_ticket(ticket_id, admin_id):
    with db() as c:
        ts = now_iso()
        cur = c.execute("""
            UPDATE tickets SET status='closed', admin_id=COALESCE(admin_id, ?),
            updated_at=?, closed_at=? WHERE id=? AND status!='closed'
        """, (admin_id, ts, ts, ticket_id))
        if cur.rowcount == 0:
            return None
        c.execute(
            "INSERT INTO ticket_history(ticket_id, action, admin_id, created_at) VALUES (?, 'closed', ?, ?)",
            (ticket_id, admin_id, ts)
        )
        c.execute("DELETE FROM admin_sessions WHERE ticket_id=?", (ticket_id,))
        return c.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()

def add_message(ticket_id, sender_id, sender_type, message_type, text_value, telegram_message_id):
    with db() as c:
        ts = now_iso()
        cur = c.execute("""
            INSERT INTO messages(ticket_id,sender_id,sender_type,message_type,text,
                                 telegram_message_id,created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ticket_id, sender_id, sender_type, message_type, text_value,
              telegram_message_id, ts))
        c.execute("UPDATE tickets SET updated_at=? WHERE id=?", (ts, ticket_id))
        return cur.lastrowid

def get_messages(ticket_id, limit=200):
    with db() as c:
        return c.execute(
            "SELECT * FROM messages WHERE ticket_id=? ORDER BY id ASC LIMIT ?",
            (ticket_id, limit)
        ).fetchall()

def set_admin_session(admin_id, ticket_id):
    with db() as c:
        c.execute("""
            INSERT INTO admin_sessions(admin_id,ticket_id,updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(admin_id) DO UPDATE SET ticket_id=excluded.ticket_id,
            updated_at=excluded.updated_at
        """, (admin_id, ticket_id, now_iso()))

def get_admin_session(admin_id):
    with db() as c:
        return c.execute("SELECT * FROM admin_sessions WHERE admin_id=?", (admin_id,)).fetchone()

def clear_admin_session(admin_id):
    with db() as c:
        c.execute("DELETE FROM admin_sessions WHERE admin_id=?", (admin_id,))

def is_admin(tg_id):
    with db() as c:
        return c.execute("SELECT 1 FROM admins WHERE telegram_id=?", (tg_id,)).fetchone() is not None

def list_admins():
    with db() as c:
        return c.execute("SELECT * FROM admins ORDER BY telegram_id").fetchall()

def add_admin(tg_id, role="operator"):
    with db() as c:
        c.execute(
            "INSERT OR IGNORE INTO admins(telegram_id,role,added_at) VALUES (?, ?, ?)",
            (tg_id, role, now_iso())
        )

def remove_admin(tg_id):
    with db() as c:
        c.execute("DELETE FROM admins WHERE telegram_id=?", (tg_id,))

def search_tickets(query):
    q = query.strip()
    number = q if q.startswith("#") else f"#ARVIS-{q.zfill(4)}" if q.isdigit() else q
    with db() as c:
        return c.execute("""
            SELECT t.*, u.telegram_id, u.nickname, u.account_id, u.server, u.username
            FROM tickets t JOIN users u ON u.id=t.user_id
            WHERE t.ticket_number=? OR CAST(u.telegram_id AS TEXT)=?
               OR u.nickname LIKE ? OR u.account_id=? OR u.server LIKE ?
            ORDER BY t.id DESC LIMIT 50
        """, (number, q, f"%{q}%", q, f"%{q}%")).fetchall()

def stats():
    with db() as c:
        total = c.execute("SELECT COUNT(*) n FROM tickets").fetchone()["n"]
        statuses = {
            s: c.execute("SELECT COUNT(*) n FROM tickets WHERE status=?", (s,)).fetchone()["n"]
            for s in ("new","working","closed")
        }
        by_admin = c.execute("""
            SELECT COALESCE(CAST(admin_id AS TEXT),'Не взято') admin, COUNT(*) n
            FROM tickets GROUP BY admin_id ORDER BY n DESC
        """).fetchall()
        by_category = c.execute("""
            SELECT category, COUNT(*) n FROM tickets GROUP BY category ORDER BY n DESC
        """).fetchall()
        avg = c.execute("""
            SELECT AVG((julianday(closed_at)-julianday(created_at))*86400.0) seconds
            FROM tickets WHERE closed_at IS NOT NULL
        """).fetchone()["seconds"]
        return total, statuses, by_admin, by_category, avg
