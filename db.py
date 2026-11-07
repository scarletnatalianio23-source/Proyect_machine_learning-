"""SQLite helpers: users (with roles) and the history of queries."""
import os
import sqlite3
from pathlib import Path

from flask import g
from werkzeug.security import generate_password_hash

BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("FOREST_DB", BASE / "instance" / "forest.db"))

ROLES = ("citizen", "authority", "admin")
ROLE_LABELS = {"citizen": "Citizen", "authority": "Authority", "admin": "Administrator"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'citizen',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    municipality TEXT,
    model TEXT NOT NULL,
    area_km2 REAL, population REAL, cattle_heads REAL, planted_area_ha REAL,
    nbi_pct REAL, coca_ha REAL, armed_groups REAL,
    estimate INTEGER NOT NULL,
    level TEXT NOT NULL
);
"""

DEMO_USERS = [
    ("Admin Demo", "admin@forest.test", "Admin123!", "admin"),
    ("Authority Demo", "entity@forest.test", "Entity123!", "authority"),
    ("Citizen Demo", "citizen@forest.test", "Citizen123!", "citizen"),
]


def get_db():
    if "db" not in g:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the tables and, on a brand-new database, three demo accounts."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        for name, email, password, role in DEMO_USERS:
            db.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (name, email, generate_password_hash(password), role),
            )
    db.commit()
    db.close()
