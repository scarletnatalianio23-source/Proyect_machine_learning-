import csv
import io
import re
import json
import math
import os
import secrets
import sqlite3
from functools import wraps

from markupsafe import Markup, escape
from flask import (Flask, Response, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

import db
import ml
from content import DOC, PROJECT, STATS

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.teardown_appcontext(db.close_db)


@app.template_filter("apa")
def apa(text):
    """Show *italics* and make URLs clickable in a reference."""
    safe = str(escape(text))
    safe = re.sub(r"\*(.+?)\*", r"<em>\1</em>", safe)
    safe = re.sub(r"(https?://[^\s<]+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', safe)
    return Markup(safe)
db.init_db()

# ---------------------------------------------------------------------------
# Data and models (loaded once; retrained from the admin panel)
# ---------------------------------------------------------------------------
STATE = {}


def load_state(retrain=False):
    bundle = ml.train() if retrain else ml.load_bundle()
    data = ml.load_data()
    year = int(data["year"].max())
    wide = data.pivot_table(index=["municipality", "department"], columns="year", values="forest_loss_ha")
    latest = data[data["year"] == year].sort_values(["municipality", "department"])
    items = []
    for r in latest.itertuples():
        hist = [int(v) for v in wide.loc[(r.municipality, r.department)].tolist()]
        items.append({
            "label": f"{r.municipality} ({r.department})",
            "area_km2": r.area_km2, "population": int(r.population), "cattle_heads": int(r.cattle_heads),
            "planted_area_ha": r.planted_area_ha, "nbi_pct": r.nbi_pct, "coca_ha": r.coca_ha,
            "armed_groups": int(r.armed_groups),
            "loss_a": hist[-3], "loss_b": hist[-2], "loss_c": hist[-1], "history": hist,
        })
    STATE.update(bundle=bundle, data=data, municipalities=items, year=year,
                 by_label={m["label"]: m for m in items})


load_state()

CONDITION_FIELDS = [
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
HISTORY_FIELDS = ["loss_a", "loss_b", "loss_c"]
SCENARIO_FIELDS = [
    # name, label, min, max, step, suffix
    ("cattle_pct", "Cattle", -60, 60, 5, "%"),
    ("planted_pct", "Planted area", -60, 60, 5, "%"),
    ("coca_pct", "Coca cultivation", -100, 50, 10, "%"),
    ("nbi_delta", "Unmet basic needs", -20, 10, 1, " pts"),
    ("armed_delta", "Armed groups", -2, 1, 1, ""),
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
            flash("Please sign in to use the model.", "info")
            return redirect(url_for("access", next=request.full_path.rstrip("?")))
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
    return target if target and target.startswith("/") and not target.startswith("//") else url_for("predict_page")


@app.errorhandler(403)
def forbidden(_e):
    return render_template("error.html", code=403, title="Access denied",
                           message="Your role does not have access to this page."), 403


@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400, title="Request not valid",
                           message=getattr(e, "description", "Bad request.")), 400


@app.route("/access", methods=["GET", "POST"])
def access():
    """View 3: choose a role, then sign in or create an account."""
    if g.user:
        return redirect(url_for("predict_page"))
    tab = request.args.get("tab", "login")
    if request.method == "POST":
        action = request.form.get("action", "login")
        role = request.form.get("role", "citizen")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if role not in db.ROLES:
            abort(400, "Unknown role.")
        if action == "login":
            tab = "login"
            row = db.get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if not (row and row["active"] and check_password_hash(row["password_hash"], password)):
                flash("Wrong email or password, or the account is disabled.", "danger")
            elif row["role"] != role:
                flash(f"That account is registered as {db.ROLE_LABELS[row['role']]}, not {db.ROLE_LABELS[role]}. "
                      "Choose your role again.", "danger")
            else:
                session.clear()
                session["user_id"] = row["id"]
                flash(f"Welcome, {row['name']}.", "success")
                return redirect(safe_next(request.args.get("next")))
        else:
            tab = "register"
            name = request.form.get("name", "").strip()
            errors = []
            if len(name) < 2:
                errors.append("Enter your name.")
            if "@" not in email or "." not in email.split("@")[-1]:
                errors.append("Enter a valid email.")
            if len(password) < 8:
                errors.append("The password needs at least 8 characters.")
            if password != request.form.get("password2", ""):
                errors.append("The passwords do not match.")
            if role != "citizen" and not secrets.compare_digest(
                    request.form.get("code", "").strip(), db.ROLE_CODES[role]):
                errors.append(f"The institutional access code for {db.ROLE_LABELS[role]} is not valid.")
            if not errors:
                try:
                    conn = db.get_db()
                    conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                                 (name, email, generate_password_hash(password), role))
                    conn.commit()
                    flash("Account created. Sign in with your role and credentials.", "success")
                    return redirect(url_for("access", tab="login"))
                except sqlite3.IntegrityError:
                    errors.append("That email is already registered.")
            for message in errors:
                flash(message, "danger")
    return render_template("access.html", tab=tab, demo=db.DEMO_USERS, roles=db.ROLES,
                           chosen_role=request.form.get("role", "citizen"), codes=db.ROLE_CODES)


@app.route("/login")
def login():
    return redirect(url_for("access", tab="login", **({"next": request.args["next"]} if "next" in request.args else {})))


@app.route("/register")
def register():
    return redirect(url_for("access", tab="register"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You signed out.", "info")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# View 1: the project  |  View 2: model comparison (both public)
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html", stats=STATS, project=PROJECT, doc=DOC)


@app.route("/project")
def project_page():
    return redirect(url_for("home") + "#documentation")


@app.route("/models")
def models_page():
    bundle = STATE["bundle"]
    names = [ml.FEATURE_LABELS[f] for f in ml.FEATURE_NAMES]
    m = bundle["metrics"]
    best = bundle["best"]
    base = bundle["baselines"]
    gain_last = round((base["Same as last year"]["mae"] - m[best]["mae"]) / base["Same as last year"]["mae"] * 100, 1)
    return render_template(
        "compare.html", b=bundle, model_names=ml.MODEL_NAMES, feature_names=names, gain_last=gain_last,
        year_wins=sum(1 for y in bundle["test_years"]
                      if min(ml.MODEL_NAMES, key=lambda k: bundle["per_year"][k][y]) == best),
        chart={"scatter": bundle["scatter"], "importance": bundle["importance"], "features": names,
               "models": ml.MODEL_NAMES, "metrics": m, "per_year": bundle["per_year"],
               "years": bundle["test_years"]},
    )


# ---------------------------------------------------------------------------
# View 3: the early-warning model (needs login)
# ---------------------------------------------------------------------------
def parse_form(form):
    values, errors = {}, {}
    for name, _label, unit, low, high, _step, _icon, _help in CONDITION_FIELDS:
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
    for name in HISTORY_FIELDS:
        raw = (form.get(name) or "").strip().replace(",", "")
        try:
            number = float(raw)
        except ValueError:
            errors[name] = "Enter a number."
            continue
        if not math.isfinite(number) or not (0 <= number <= 60000):
            errors[name] = "Must be between 0 and 60,000 ha."
            continue
        values[name] = number
    return values, errors


def parse_scenario(form):
    scen = {}
    for name, _label, low, high, _step, _suffix in SCENARIO_FIELDS:
        try:
            value = float(form.get(name, 0) or 0)
        except ValueError:
            value = 0
        scen[name] = min(max(value, low), high) if math.isfinite(value) else 0
    return scen if any(scen.values()) else None


ADVICE = {
    "citizen": {
        "Low": ["Forest loss is expected to stay low. Keep reporting anything unusual you see.",
                "Share this forecast with your community council or local environmental group."],
        "Moderate": ["Pressure on the forest is moderate. Follow local land-use decisions and community meetings.",
                     "Report suspicious clearing to your local government and regional environmental authority."],
        "High": ["High forest loss is likely. Ask your municipality what monitoring and prevention actions are planned.",
                 "Report illegal clearing to your regional environmental authority and join community watch activities."],
        "Critical": ["Very high forest loss is likely. This municipality needs urgent attention.",
                     "Contact your regional environmental authority and local government, and support community reporting."],
    },
    "authority": {
        "Low": ["Keep routine satellite monitoring; no extra resources are needed for now.",
                "Use the simulator to check how changes in cattle or coca would shift the forecast."],
        "Moderate": ["Add this municipality to the watch list and review early alerts monthly.",
                     "Coordinate with the local government on land-use control."],
        "High": ["Schedule field verification and strengthen monitoring in the coming months.",
                 "Check the dashboard to see how many teams the agent suggests sending to this department."],
        "Critical": ["Prioritize this municipality for monitoring teams and inter-institutional action now.",
                     "Use the scenario simulator to compare interventions on cattle, coca and poverty before deciding."],
    },
}


def build_chart(selected, history, fc, fc_s, last_year):
    full = selected["history"] if selected and [selected["loss_a"], selected["loss_b"], selected["loss_c"]] == history else history
    years = list(range(last_year - len(full) + 1, last_year + 1))
    return {
        "years": years + [f["year"] for f in fc],
        "history": full + [None] * len(fc),
        "forecast": [None] * (len(full) - 1) + [full[-1]] + [f["estimate"] for f in fc],
        "low": [None] * (len(full) - 1) + [full[-1]] + [f["low"] for f in fc],
        "high": [None] * (len(full) - 1) + [full[-1]] + [f["high"] for f in fc],
        "scenario": ([None] * (len(full) - 1) + [full[-1]] + [f["estimate"] for f in fc_s]) if fc_s else None,
    }


@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict_page():
    bundle = STATE["bundle"]
    best = bundle["best"]
    last_year = STATE["year"]
    role = g.user["role"]
    can_simulate = role in ("authority", "admin")
    values, errors, result = {}, {}, None
    scen_values = {n: 0 for n, *_ in SCENARIO_FIELDS}

    if request.method == "POST":
        values, errors = parse_form(request.form)
        if can_simulate:
            scen = parse_scenario(request.form)
            scen_values = {n: request.form.get(n, 0) for n, *_ in SCENARIO_FIELDS}
        else:
            scen = None
        if not errors:
            cond = {k: values[k] for k in ml.CONDITIONS}
            history = [values[k] for k in HISTORY_FIELDS]
            fc = ml.forecast(bundle, history, cond, best, last_year)
            level, color = ml.alert_level(bundle, fc[0]["estimate"])
            prob = ml.prob_high(bundle, fc[0])
            last = history[-1]
            change = round((fc[0]["estimate"] - last) / max(last, 1) * 100)
            selected = STATE["by_label"].get(request.form.get("municipality", ""))
            fc_s = ml.forecast(bundle, history, cond, best, last_year, scen=scen) if scen else None
            avoided = (sum(f["estimate"] for f in fc) - sum(f["estimate"] for f in fc_s)) if fc_s else None
            result = {
                "name": ml.MODEL_NAMES[best], "forecast": fc, "level": level, "color": color,
                "prob": prob, "change": change, "last": round(last), "scenario": fc_s, "avoided": avoided,
                "advice": ADVICE["authority" if can_simulate else "citizen"][level],
                "drivers": ml.drivers(bundle, history, cond, best, last_year),
                "chart": build_chart(selected, [int(v) for v in history], fc, fc_s, last_year),
                "median": round(bundle["quantiles"]["0.5"]),
            }
            conn = db.get_db()
            conn.execute(
                """INSERT INTO forecasts (user_id, municipality, model, loss_last_year, forecast_year1,
                   forecast_year3, level, prob_high, avoided_ha) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (g.user["id"], request.form.get("municipality") or None, ml.MODEL_NAMES[best], round(last),
                 fc[0]["estimate"], fc[2]["estimate"], level, prob, round(avoided) if avoided is not None else None),
            )
            conn.commit()
        values = {k: request.form.get(k, "") for k in [f[0] for f in CONDITION_FIELDS] + HISTORY_FIELDS}
    return render_template(
        "predict.html", fields=CONDITION_FIELDS, history_fields=HISTORY_FIELDS, scenario_fields=SCENARIO_FIELDS,
        scen_values=scen_values, values=values, errors=errors, result=result, can_simulate=can_simulate,
        municipalities=STATE["municipalities"], selected=request.form.get("municipality", ""),
        best_name=ml.MODEL_NAMES[best], last_year=last_year, mae=bundle["metrics"][best]["mae"],
    )


# ---------------------------------------------------------------------------
# History and CSV
# ---------------------------------------------------------------------------
CSV_COLUMNS = ["created_at", "municipality", "model", "loss_last_year", "forecast_year1", "forecast_year3",
               "level", "prob_high", "avoided_ha"]


def fetch_forecasts(scope_all, limit=None):
    sql = """SELECT f.*, u.name AS user_name FROM forecasts f JOIN users u ON u.id = f.user_id"""
    args = []
    if not scope_all:
        sql += " WHERE f.user_id = ?"
        args.append(g.user["id"])
    sql += " ORDER BY f.id DESC"
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
    return render_template("history.html", rows=fetch_forecasts(scope_all, 200), scope_all=scope_all,
                           year=STATE["year"])


@app.route("/history.csv")
@login_required
def history_csv():
    scope_all = wants_all()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow((["user"] if scope_all else []) + CSV_COLUMNS)
    for r in fetch_forecasts(scope_all):
        writer.writerow(([r["user_name"]] if scope_all else []) + [r[c] for c in CSV_COLUMNS])
    name = "forecasts_all.csv" if scope_all else "my_forecasts.csv"
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
        "forecasts": conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0],
    }
    data = STATE["data"]
    totals["loss_latest"] = int(data[data["year"] == bundle["latest_year"]]["forest_loss_ha"].sum())
    totals["forecast_next"] = bundle["forecast_total"]
    by_level = conn.execute("SELECT level, COUNT(*) AS n FROM forecasts GROUP BY level").fetchall()
    rl = bundle["rl"]
    return render_template(
        "dashboard.html", b=bundle, model_names=ml.MODEL_NAMES, totals=totals, by_level=by_level, rl=rl,
        recent=fetch_forecasts(True, 8), trend=bundle["trend"],
        rl_rows=sorted(zip(rl["departments"], rl["risk_ha"], rl["allocation"]), key=lambda r: -r[2]),
    )


# ---------------------------------------------------------------------------
# Administrator
# ---------------------------------------------------------------------------
@app.route("/admin/users")
@roles_required("admin")
def admin_users():
    users = db.get_db().execute(
        """SELECT u.*, (SELECT COUNT(*) FROM forecasts f WHERE f.user_id = u.id) AS n_forecasts
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
