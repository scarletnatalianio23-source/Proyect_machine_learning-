"""SQLite helpers: users (with roles) and the history of forecasts."""
import os
import sqlite3
from pathlib import Path

from flask import g
from werkzeug.security import generate_password_hash

BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("FOREST_DB", BASE / "instance" / "forest.db"))

ROLES = ("citizen", "authority", "admin")
ROLE_LABELS = {"citizen": "Citizen", "authority": "Authority", "admin": "Administrator"}
# Institutional codes needed to register as authority or administrator (change them with env vars).
ROLE_CODES = {
    "authority": os.environ.get("AUTHORITY_CODE", "AUTH-2026"),
    "admin": os.environ.get("ADMIN_CODE", "ADMIN-2026"),
}

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
CREATE TABLE IF NOT EXISTS forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    municipality TEXT,
    model TEXT NOT NULL,
    loss_last_year INTEGER NOT NULL,
    forecast_year1 INTEGER NOT NULL,
    forecast_year3 INTEGER NOT NULL,
    level TEXT NOT NULL,
    prob_high INTEGER NOT NULL,
    avoided_ha INTEGER
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
