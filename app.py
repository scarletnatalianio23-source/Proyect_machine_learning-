import csv
import io
import json
import math
import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

import pandas as pd
from flask import (Flask, Response, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

import db
import ml

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.teardown_appcontext(db.close_db)
db.init_db()

# Context figures shown on the home page.
# Source: IDEAM - Sistema de Monitoreo de Bosques y Carbono (SMByC).
STATS = [
    {
        "icon": "bi-globe-americas",
        "color": "teal",
        "label": "Where we stand",
        "value": "52%",
        "description": "of Colombia's territory is covered by natural forest",
    },
    {
        "icon": "bi-tree-fill",
        "color": "coral",
        "label": "2025",
        "value": "119,483",
        "description": "hectares of forest lost in Colombia during 2025",
    },
    {
        "icon": "bi-graph-up-arrow",
        "color": "amber",
        "label": "The trend",
        "value": "+5.2%",
        "description": "increase compared to 2024, when 113,608 hectares were lost",
    },
]

# Content of the interactive tree on the home page.
# Each branch of the tree opens one of these entries.
PROJECT = {
    "problem": {
        "title": "Problem",
        "color": "#f3722c",
        "text": (
            "Colombia is about 52% covered by natural forest, yet it keeps losing it: "
            "according to IDEAM, 119,483 hectares were deforested in 2025, 5.2% more "
            "than in 2024. The loss is concentrated in departments such as Meta, "
            "Caquetá, Guaviare and Putumayo, and it is linked to extensive cattle "
            "ranching, agribusiness, illicit crops, illegal mining and infrastructure. "
            "Official data exist, but they are mostly published as reports and "
            "bulletins, and there is no simple tool that lets a student, a community "
            "or a local authority estimate how forest loss could change in a "
            "municipality given its conditions."
        ),
    },
    "general": {
        "title": "General objective",
        "color": "#f9c74f",
        "text": (
            "Develop an intelligent website that, using regression models trained "
            "on municipal data inspired by IDEAM sources, estimates the hectares of "
            "forest lost in a municipality from manually entered data."
        ),
    },
    "specific": {
        "title": "Specific objectives",
        "color": "#2ec4b6",
        "items": [
            "Collect and clean the deforestation dataset by municipality "
            "and year, together with its explanatory variables.",
            "Train and compare three models using metrics such as R², MAE and RMSE.",
            "Build a web interface with user roles, a data-entry form and a "
            "visualization of the results.",
        ],
    },
    "framework": {
        "title": "Referential framework",
        "color": "#9b5de5",
        "items": [
            "Deforestation: permanent loss of natural forest cover, tracked in Colombia by IDEAM's SMByC.",
            "Drivers: extensive cattle ranching, agriculture, illicit crops, illegal mining and infrastructure.",
            "Regression: a supervised Machine Learning technique that estimates a continuous value (hectares) from input variables.",
            "Data: a synthetic municipal dataset inspired by Mendoza Montoya (2025).",
        ],
    },
    "methodology": {
        "title": "Methodology",
        "color": "#4cc9f0",
        "items": [
            "Prepare the dataset and check ranges, outliers and missing values.",
            "Train a multiple linear regression, a Random Forest and a Gradient Boosting model.",
            "Evaluate with five-fold cross-validation (MAE, RMSE and R²).",
            "Deploy the models in a Flask web app with login and roles.",
        ],
    },
    "references": {
        "title": "References",
        "color": "#f15bb5",
        "items": [
            "IDEAM. Sistema de Monitoreo de Bosques y Carbono (SMByC).",
            "Mendoza Montoya, E. (2025). Municipal-level data on deforestation, prosecutions, and socioeconomic indicators in Colombia (2021-2023) (Version 1) [Data set]. Mendeley Data. https://doi.org/10.17632/mn5s748pyt.1",
        ],
    },
}

# ---------------------------------------------------------------------------
# Data and models (loaded once; retrained from the admin panel)
# ---------------------------------------------------------------------------
STATE = {}


def load_state(retrain=False):
    bundle = ml.train() if retrain else ml.load_bundle()
    data = ml.load_data()
    latest = data[data["year"] == data["year"].max()].sort_values(["municipality", "department"])
    STATE["bundle"] = bundle
    STATE["data"] = data
    STATE["municipalities"] = [
        {
            "label": f"{r.municipality} ({r.department})",
            "area_km2": r.area_km2, "population": int(r.population),
            "cattle_heads": int(r.cattle_heads), "planted_area_ha": r.planted_area_ha,
            "nbi_pct": r.nbi_pct, "coca_ha": r.coca_ha, "armed_groups": int(r.armed_groups),
        }
        for r in latest.itertuples()
    ]
    STATE["latest_by_dept"] = (
        data[data["year"] == data["year"].max()].groupby("department")["forest_loss_ha"].mean().round().to_dict()
    )


load_state()

FIELDS = [
    # name, label, unit, min, max, step, icon, help text
    ("area_km2", "Municipal area", "km²", 5, 70000, "any", "bi-bounding-box", "Total surface of the municipality."),
    ("population", "Population", "people", 100, 8000000, 1, "bi-people-fill", "Number of inhabitants."),
    ("cattle_heads", "Cattle", "heads", 0, 1000000, 1, "bi-egg-fried", "Cattle heads raised in the municipality."),
    ("planted_area_ha", "Planted area", "hectares", 0, 500000, "any", "bi-flower2", "Land used for crops."),
    ("nbi_pct", "Unmet basic needs (NBI)", "%", 0, 100, "any", "bi-house-exclamation-fill",
     "Share of the population with unmet basic needs. Higher means more poverty."),
    ("coca_ha", "Coca cultivation", "hectares", 0, 50000, "any", "bi-exclamation-diamond-fill",
     "Hectares of illicit coca crops. Use 0 if there are none."),
    ("armed_groups", "Armed groups present", "groups", 0, 5, 1, "bi-shield-exclamation",
     "Number of armed groups with presence in the municipality (0 to 5)."),
]

# ---------------------------------------------------------------------------
# Authentication, roles and CSRF
# ---------------------------------------------------------------------------
@app.before_request
def load_user():
    g.user = None
    user_id = session.get("user_id")
    if user_id is not None:
        row = db.get_db().execute("SELECT * FROM users WHERE id = ? AND active = 1", (user_id,)).fetchone()
        if row is None:
            session.clear()
        else:
            g.user = row


@app.before_request
def check_csrf():
    if request.method == "POST":
        token = session.get("csrf")
        if not token or not secrets.compare_digest(token, request.form.get("csrf_token", "")):
            abort(400, "Invalid or missing security token. Reload the page and try again.")


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]


@app.context_processor
def inject_globals():
    return {"csrf_token": csrf_token, "current_user": g.get("user"), "ROLE_LABELS": db.ROLE_LABELS}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def safe_next(target):
    return target if target and target.startswith("/") and not target.startswith("//") else url_for("home")


@app.errorhandler(403)
def forbidden(_e):
    return render_template("error.html", code=403, title="Access denied",
                           message="Your role does not have access to this page."), 403


@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400, title="Request not valid",
                           message=getattr(e, "description", "Bad request.")), 400


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("home"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        row = db.get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row and row["active"] and check_password_hash(row["password_hash"], request.form.get("password", "")):
            session.clear()
            session["user_id"] = row["id"]
            flash(f"Welcome back, {row['name']}.", "success")
            return redirect(safe_next(request.args.get("next")))
        flash("Wrong email or password, or the account is disabled.", "danger")
    return render_template("login.html", demo=db.DEMO_USERS)


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        errors = []
        if len(name) < 2:
            errors.append("Enter your name.")
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append("Enter a valid email.")
        if len(password) < 8:
            errors.append("The password needs at least 8 characters.")
        if password != request.form.get("password2", ""):
            errors.append("The passwords do not match.")
        if not errors:
            try:
                conn = db.get_db()
                conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'citizen')",
                             (name, email, generate_password_hash(password)))
                conn.commit()
                flash("Account created. You can sign in now.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                errors.append("That email is already registered.")
        for message in errors:
            flash(message, "danger")
    return render_template("register.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You signed out.", "info")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html", stats=STATS, project=PROJECT)


@app.route("/project")
def project_page():
    return render_template("project.html", stats=STATS, project=PROJECT)


# ---------------------------------------------------------------------------
# Predict
# ---------------------------------------------------------------------------
def parse_form(form):
    values, errors = {}, {}
    for name, _label, unit, low, high, _step, _icon, _help in FIELDS:
        raw = (form.get(name) or "").strip().replace(",", "")
        try:
            number = float(raw)
        except ValueError:
            errors[name] = "Enter a number."
            continue
        if not math.isfinite(number) or not (low <= number <= high):
            errors[name] = f"Must be between {low:,} and {high:,} {unit}."
            continue
        if name == "armed_groups" and number != int(number):
            errors[name] = "Use a whole number."
            continue
        values[name] = number
    return values, errors


@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict_page():
    bundle = STATE["bundle"]
    best = bundle["best"]
    values, errors, result = {}, {}, None
    choice = request.form.get("model", "best")
    if choice not in ("best", "all", *ml.MODEL_NAMES):
        choice = "best"

    if request.method == "POST":
        values, errors = parse_form(request.form)
        if not errors:
            main_key = best if choice in ("best", "all") else choice
            main = ml.predict(bundle, values, main_key)
            level, color = ml.level_for(bundle, main["estimate"])
            all_models = [ml.predict(bundle, values, k) for k in ml.MODEL_NAMES] if choice == "all" else []
            data = STATE["data"]
            gauge = min(100, round(math.log1p(main["estimate"]) / math.log1p(12000) * 100))
            result = {
                **main, "level": level, "color": color, "gauge": gauge,
                "percentile": round(float((data["forest_loss_ha"] < main["estimate"]).mean()) * 100),
                "median": round(bundle["quantiles"]["0.5"]),
                "drivers": ml.drivers(bundle, values, main_key),
                "all": all_models, "is_best": main_key == best,
            }
            conn = db.get_db()
            conn.execute(
                """INSERT INTO queries (user_id, municipality, model, area_km2, population, cattle_heads,
                   planted_area_ha, nbi_pct, coca_ha, armed_groups, estimate, level)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (g.user["id"], request.form.get("municipality") or None, main["name"],
                 *[values[f] for f in ml.FEATURES], main["estimate"], level),
            )
            conn.commit()
        values = {k: request.form.get(k, "") for k, *_ in FIELDS}
    return render_template(
        "predict.html", fields=FIELDS, values=values, errors=errors, result=result,
        municipalities=STATE["municipalities"], best=best, model_names=ml.MODEL_NAMES,
        choice=choice, rows=bundle["rows"], selected=request.form.get("municipality", ""),
    )


# ---------------------------------------------------------------------------
# Model comparison, risk map
# ---------------------------------------------------------------------------
@app.route("/models")
@login_required
def models_page():
    bundle = STATE["bundle"]
    names = [ml.FEATURE_LABELS[f] for f in ml.FEATURES]
    return render_template(
        "compare.html", b=bundle, model_names=ml.MODEL_NAMES, feature_names=names,
        chart={"scatter": bundle["scatter"], "importance": bundle["importance"], "features": names,
               "models": ml.MODEL_NAMES, "metrics": bundle["metrics"]},
    )


TILE_MAP = {
    "Atlántico": (3, 0), "Magdalena": (4, 0), "La Guajira": (5, 0),
    "Córdoba": (1, 1), "Sucre": (2, 1), "Bolívar": (3, 1), "Cesar": (4, 1), "Norte de Santander": (5, 1),
    "Chocó": (0, 2), "Antioquia": (2, 2), "Santander": (4, 2), "Boyacá": (5, 2), "Arauca": (6, 2),
    "Valle del Cauca": (0, 3), "Risaralda": (1, 3), "Caldas": (2, 3), "Tolima": (3, 3),
    "Cundinamarca": (4, 3), "Casanare": (5, 3), "Vichada": (6, 3),
    "Cauca": (0, 4), "Quindío": (1, 4), "Huila": (3, 4), "Meta": (4, 4), "Guaviare": (5, 4), "Guainía": (6, 4),
    "Nariño": (0, 5), "Putumayo": (2, 5), "Caquetá": (3, 5), "Vaupés": (5, 5),
    "Amazonas": (4, 6),
}


@app.route("/map")
@login_required
def risk_map():
    bundle = STATE["bundle"]
    tiles = [
        {"department": d, "col": c, "row": r, "values": bundle["dept_year"].get(d, [])}
        for d, (c, r) in TILE_MAP.items()
    ]
    return render_template("risk_map.html", tiles=tiles, years=bundle["years"], trend=bundle["trend"])


# ---------------------------------------------------------------------------
# History and CSV
# ---------------------------------------------------------------------------
QUERY_COLUMNS = ["created_at", "municipality", "model", "area_km2", "population", "cattle_heads",
                 "planted_area_ha", "nbi_pct", "coca_ha", "armed_groups", "estimate", "level"]


def fetch_queries(scope_all, limit=None):
    sql = """SELECT q.*, u.name AS user_name, u.role AS user_role FROM queries q
             JOIN users u ON u.id = q.user_id"""
    args = []
    if not scope_all:
        sql += " WHERE q.user_id = ?"
        args.append(g.user["id"])
    sql += " ORDER BY q.id DESC"
    if limit:
        sql += " LIMIT ?"
        args.append(limit)
    return db.get_db().execute(sql, args).fetchall()


def wants_all():
    return request.args.get("scope") == "all" and g.user["role"] in ("authority", "admin")


@app.route("/history")
@login_required
def history():
    scope_all = wants_all()
    return render_template("history.html", rows=fetch_queries(scope_all, 200), scope_all=scope_all)


@app.route("/history.csv")
@login_required
def history_csv():
    scope_all = wants_all()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow((["user"] if scope_all else []) + QUERY_COLUMNS)
    for r in fetch_queries(scope_all):
        writer.writerow(([r["user_name"]] if scope_all else []) + [r[c] for c in QUERY_COLUMNS])
    name = "queries_all.csv" if scope_all else "my_queries.csv"
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={name}"})


# ---------------------------------------------------------------------------
# Authority dashboard
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@roles_required("authority", "admin")
def dashboard():
    bundle = STATE["bundle"]
    conn = db.get_db()
    totals = {
        "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "queries": conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0],
    }
    data = STATE["data"]
    latest = data[data["year"] == bundle["latest_year"]]
    totals["loss_latest"] = int(latest["forest_loss_ha"].sum())
    by_level = conn.execute("SELECT level, COUNT(*) AS n FROM queries GROUP BY level").fetchall()
    rl = bundle["rl"]
    return render_template(
        "dashboard.html", b=bundle, model_names=ml.MODEL_NAMES, totals=totals, by_level=by_level, rl=rl,
        recent=fetch_queries(True, 8), trend=bundle["trend"],
        rl_rows=sorted(zip(rl["departments"], rl["risk_ha"], rl["allocation"]), key=lambda r: -r[2]),
    )


# ---------------------------------------------------------------------------
# Administrator
# ---------------------------------------------------------------------------
@app.route("/admin/users")
@roles_required("admin")
def admin_users():
    users = db.get_db().execute(
        """SELECT u.*, (SELECT COUNT(*) FROM queries q WHERE q.user_id = u.id) AS n_queries
           FROM users u ORDER BY u.id""").fetchall()
    return render_template("admin_users.html", users=users, roles=db.ROLES)


@app.route("/admin/users/new", methods=["POST"])
@roles_required("admin")
def admin_user_new():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role", "citizen")
    if role not in db.ROLES or len(name) < 2 or "@" not in email or len(password) < 8:
        flash("Check the data: name, valid email, role and a password of at least 8 characters.", "danger")
    else:
        try:
            conn = db.get_db()
            conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                         (name, email, generate_password_hash(password), role))
            conn.commit()
            flash(f"User {email} created as {db.ROLE_LABELS[role]}.", "success")
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "danger")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/update", methods=["POST"])
@roles_required("admin")
def admin_user_update(user_id):
    role = request.form.get("role")
    active = 1 if request.form.get("active") == "1" else 0
    if role not in db.ROLES:
        abort(400, "Unknown role.")
    if user_id == g.user["id"] and (role != "admin" or not active):
        flash("You cannot remove your own administrator access.", "danger")
        return redirect(url_for("admin_users"))
    conn = db.get_db()
    conn.execute("UPDATE users SET role = ?, active = ? WHERE id = ?", (role, active, user_id))
    conn.commit()
    flash("User updated.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/retrain", methods=["POST"])
@roles_required("admin")
def admin_retrain():
    load_state(retrain=True)
    flash("Models retrained with the current dataset.", "success")
    return redirect(url_for("models_page"))


if __name__ == "__main__":
    app.run(debug=True)
