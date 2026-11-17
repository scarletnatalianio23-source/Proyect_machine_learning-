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
# Institutional codes needed to register as authority or administrator. They come only from
# environment variables (never from the repository); without them those roles cannot be registered.
ROLE_CODES = {
    "authority": os.environ.get("AUTHORITY_CODE", ""),
    "admin": os.environ.get("ADMIN_CODE", ""),
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

# Optional test accounts for the instructor. An account is created on a brand-new database only if its
# password is set in the environment (TEST_ADMIN_PASSWORD, TEST_AUTHORITY_PASSWORD, TEST_CITIZEN_PASSWORD).
_TEST_ACCOUNTS = [
    ("Admin Test", "admin@forest.test", "TEST_ADMIN_PASSWORD", "admin"),
    ("Authority Test", "entity@forest.test", "TEST_AUTHORITY_PASSWORD", "authority"),
    ("Citizen Test", "citizen@forest.test", "TEST_CITIZEN_PASSWORD", "citizen"),
]
DEMO_USERS = [(n, e, os.environ[v], r) for n, e, v, r in _TEST_ACCOUNTS if os.environ.get(v)]


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
    """Create the tables and, on a brand-new database, the optional test accounts."""
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
