import sqlite3
import datetime
from pathlib import Path
import config

def get_db():
    conn = sqlite3.connect(config.DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    try:
        with conn:
            # Tabel Memori Abadi (Tanpa Batas Karakter)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                importance INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
            """)

            # Tabel Log Evolusi Harian (+10% Daily Growth)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS evolution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                skill_name TEXT NOT NULL,
                growth_rate TEXT DEFAULT '+10%',
                description TEXT NOT NULL,
                created_at TEXT
            )
            """)

            # Tabel Riwayat Sesi & Percakapan
            conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_calls TEXT,
                created_at TEXT
            )
            """)

            # Tabel Antrean Tugas Otonom
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                details TEXT,
                status TEXT DEFAULT 'PENDING',
                result TEXT,
                created_at TEXT,
                completed_at TEXT
            )
            """)
    finally:
        conn.close()

# Memory Operations
def save_memory(category, key, content, importance=1):
    conn = get_db()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with conn:
            conn.execute("""
            INSERT INTO memories (category, key, content, importance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                content = excluded.content,
                category = excluded.category,
                importance = excluded.importance,
                updated_at = excluded.updated_at
            """, (category, key, content, importance, now, now))
    finally:
        conn.close()

def get_all_memories(category=None):
    conn = get_db()
    try:
        cur = conn.cursor()
        if category:
            cur.execute("SELECT category, key, content, importance, updated_at FROM memories WHERE category = ? ORDER BY importance DESC, updated_at DESC", (category,))
        else:
            cur.execute("SELECT category, key, content, importance, updated_at FROM memories ORDER BY category, importance DESC, updated_at DESC")
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def search_memories(query):
    conn = get_db()
    try:
        cur = conn.cursor()
        pattern = f"%{query}%"
        cur.execute("SELECT category, key, content, importance FROM memories WHERE key LIKE ? OR content LIKE ? ORDER BY importance DESC", (pattern, pattern))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

# Evolution Logging
def log_evolution(skill_name, description, growth_rate="+10%"):
    conn = get_db()
    now_date = datetime.date.today().isoformat()
    now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with conn:
            conn.execute("""
            INSERT INTO evolution_log (date, skill_name, growth_rate, description, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (now_date, skill_name, growth_rate, description, now_time))
    finally:
        conn.close()

def get_evolution_history(limit=10):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT date, skill_name, growth_rate, description, created_at FROM evolution_log ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

# Chat & Message Sync Operations
def save_message(session_id, role, content, tool_calls=None):
    conn = get_db()
    now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with conn:
            conn.execute("""
            INSERT INTO messages (session_id, role, content, tool_calls, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (session_id, role, content, tool_calls, now_time))
    finally:
        conn.close()

def get_session_messages(session_id="unified", limit=24):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT role, content, created_at FROM (
            SELECT id, role, content, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        ) ORDER BY id ASC
        """, (session_id, limit))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def clear_session_messages(session_id="unified"):
    conn = get_db()
    try:
        with conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    finally:
        conn.close()
