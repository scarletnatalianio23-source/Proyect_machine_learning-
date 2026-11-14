"""Machine Learning layer of Forest Awareness: an early-warning system.

Task: forecast the hectares of forest a municipality will lose NEXT year, using
its loss in the last three years and its current conditions (area, population,
cattle, planted area, poverty, coca, armed groups).

* Three supervised regression models are compared with a time-based validation
  (train on the past, test on later years): multiple linear regression,
  Random Forest and Gradient Boosting. Two naive baselines give a reference.
* The best model becomes the final model of the web app. It forecasts one to
  three years ahead and powers the what-if scenario simulator.
* K-Means groups municipalities into risk profiles (unsupervised).
* A Q-learning agent suggests where to send limited monitoring teams
  (reinforcement learning).

Everything is trained on the SIMULATED dataset in data/. Retrain with
`python train_models.py` or from the admin panel.
"""
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, silhouette_score
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "data" / "forest_loss_municipalities.csv"
BUNDLE_FILE = BASE / "models" / "bundle.joblib"

CONDITIONS = ["area_km2", "population", "cattle_heads", "planted_area_ha", "nbi_pct", "coca_ha", "armed_groups"]
CONDITION_LABELS = {
    "area_km2": "Municipal area", "population": "Population", "cattle_heads": "Cattle",
    "planted_area_ha": "Planted area", "nbi_pct": "Unmet basic needs (NBI)",
    "coca_ha": "Coca cultivation", "armed_groups": "Armed groups",
}
LAG_LABELS = {"loss_t": "Loss last year", "loss_t1": "Loss 2 years ago", "loss_t2": "Loss 3 years ago"}
FEATURE_NAMES = list(LAG_LABELS) + CONDITIONS
FEATURE_LABELS = {**LAG_LABELS, **CONDITION_LABELS}
MODEL_NAMES = {
    "linear": "Multiple linear regression",
    "forest": "Random Forest",
    "boosting": "Gradient Boosting",
}
SEED = 2026
HORIZON = 3
TEST_YEARS = (2021, 2022, 2023)  # target years used as the "future" in the validation


def load_data():
    return pd.read_csv(DATA_FILE)


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------
def transform_conditions(frame):
    return np.column_stack([
        np.log(frame["area_km2"]), np.log(frame["population"]),
        np.log1p(frame["cattle_heads"]), np.log1p(frame["planted_area_ha"]),
        frame["nbi_pct"], np.log1p(frame["coca_ha"]), frame["armed_groups"],
    ])


def features(lag0, lag1, lag2, cond_frame):
    lags = np.column_stack([np.log1p(lag0), np.log1p(lag1), np.log1p(lag2)])
    return np.hstack([lags, transform_conditions(cond_frame)])


def build_panel(df):
    """One row per municipality and origin year: loss in the 3 latest years + conditions."""
    d = df.sort_values(["municipality", "department", "year"]).copy()
    g = d.groupby(["municipality", "department"])["forest_loss_ha"]
    d["lag0"] = d["forest_loss_ha"]
    d["lag1"] = g.shift(1)
    d["lag2"] = g.shift(2)
    d["target"] = g.shift(-1)
    d = d.dropna(subset=["lag1", "lag2"]).copy()
    d["target_year"] = d["year"] + 1
    return d


def make_models():
    return {
        "linear": LinearRegression(),
        "forest": RandomForestRegressor(n_estimators=250, min_samples_leaf=3, n_jobs=-1, random_state=SEED),
        "boosting": GradientBoostingRegressor(n_estimators=250, learning_rate=0.05, max_depth=3,
                                              subsample=0.8, random_state=SEED),
    }


def _metrics(actual, pred_log):
    pred = np.clip(np.expm1(pred_log), 0, None)
    return {
        "mae": round(float(mean_absolute_error(actual, pred)), 1),
        "rmse": round(float(math.sqrt(np.mean((actual - pred) ** 2))), 1),
        "r2_log": round(float(r2_score(np.log1p(actual), pred_log)), 3),
    }


def _baseline_metrics(actual, pred):
    pred = np.asarray(pred, dtype=float)
    return {
        "mae": round(float(mean_absolute_error(actual, pred)), 1),
        "rmse": round(float(math.sqrt(np.mean((actual - pred) ** 2))), 1),
        "r2_log": round(float(r2_score(np.log1p(actual), np.log1p(pred))), 3),
    }


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train(verbose=False):
    df = load_data()
    panel = build_panel(df)
    labeled = panel.dropna(subset=["target"]).copy()
    X = features(labeled["lag0"], labeled["lag1"], labeled["lag2"], labeled)
    actual = labeled["target"].to_numpy(dtype=float)
    y = np.log1p(actual)
    ty = labeled["target_year"].to_numpy()

    # ---- Time-based validation: train on the past, forecast a later year ----
    oof = {k: np.full(len(labeled), np.nan) for k in MODEL_NAMES}
    for year in TEST_YEARS:
        tr, te = ty < year, ty == year
        for key, model in make_models().items():
            model.fit(X[tr], y[tr])
            oof[key][te] = model.predict(X[te])
        if verbose:
            print("validated on", year)
    test = ~np.isnan(oof["linear"])
    a = actual[test]
    metrics = {k: _metrics(a, oof[k][test]) for k in MODEL_NAMES}
    per_year = {
        k: {int(yr): round(float(mean_absolute_error(
            actual[ty == yr], np.clip(np.expm1(oof[k][ty == yr]), 0, None))), 1) for yr in TEST_YEARS}
        for k in MODEL_NAMES
    }
    lag0 = labeled["lag0"].to_numpy(dtype=float)[test]
    mean3 = labeled[["lag0", "lag1", "lag2"]].mean(axis=1).to_numpy()[test]
    baselines = {
        "Same as last year": _baseline_metrics(a, lag0),
        "Average of the last 3 years": _baseline_metrics(a, mean3),
        "Always the median": _baseline_metrics(a, np.full(len(a), np.median(actual))),
    }
    best = min(MODEL_NAMES, key=lambda k: metrics[k]["mae"])
    sigma = {k: float(np.std(y[test] - oof[k][test])) for k in MODEL_NAMES}

    # ---- Final models on all the history -------------------------------------
    models = {key: model.fit(X, y) for key, model in make_models().items()}
    std = X.std(axis=0)
    lin = np.abs(models["linear"].coef_) * std
    importance = {
        "linear": (lin / lin.sum()).tolist(),
        "forest": models["forest"].feature_importances_.tolist(),
        "boosting": models["boosting"].feature_importances_.tolist(),
    }
    rng = np.random.default_rng(SEED)
    pick = rng.choice(int(test.sum()), size=min(420, int(test.sum())), replace=False)
    scatter = {
        k: [[int(a[i]), int(max(round(math.expm1(oof[k][test][i])), 0))] for i in pick] for k in MODEL_NAMES
    }

    # ---- Unsupervised: risk profiles with K-Means (current conditions) ------
    latest_year = int(df["year"].max())
    latest = panel[panel["year"] == latest_year].copy()
    Xc = np.hstack([np.log1p(latest[["lag0"]].to_numpy()), transform_conditions(latest)])
    scaler = StandardScaler().fit(Xc)
    Xs = scaler.transform(Xc)
    kmeans = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit(Xs)
    labels = kmeans.labels_
    mean_loss = {c: float(latest["lag0"].to_numpy()[labels == c].mean()) for c in range(4)}
    order = sorted(mean_loss, key=mean_loss.get)
    pnames = ["Low pressure", "Moderate pressure", "High pressure", "Critical pressure"]
    names = {c: pnames[r] for r, c in enumerate(order)}
    profiles = []
    for c in order:
        part = latest[labels == c]
        profiles.append({
            "name": names[c], "municipalities": int(len(part)),
            "mean_loss": round(float(part["lag0"].mean())),
            "area_km2": round(float(part["area_km2"].median())),
            "cattle_heads": round(float(part["cattle_heads"].median())),
            "nbi_pct": round(float(part["nbi_pct"].mean()), 1),
            "coca_share": round(float((part["coca_ha"] > 0).mean()) * 100),
        })
    clustering = {"silhouette": round(float(silhouette_score(Xs, labels)), 3), "k": 4, "profiles": profiles}
    latest["profile"] = [names[int(c)] for c in labels]

    # ---- Next-year forecast for every municipality (used by dashboard, map, RL) ----
    Xl = features(latest["lag0"], latest["lag1"], latest["lag2"], latest)
    latest["forecast_ha"] = np.clip(np.expm1(models[best].predict(Xl)), 0, None).round().astype(int)
    dept_risk = latest.groupby("department")["forecast_ha"].sum().sort_values(ascending=False)
    rl = reinforcement_learning(dept_risk.to_dict())

    by_dept_year = df.groupby(["department", "year"])["forest_loss_ha"].mean().round().unstack().fillna(0)
    dept_forecast = latest.groupby("department")["forecast_ha"].mean().round()
    dept_year = {}
    for d in by_dept_year.index:
        dept_year[d] = [int(v) for v in by_dept_year.loc[d]] + [int(dept_forecast.get(d, 0))]
    yearly_region = df.groupby(["year", "region"])["forest_loss_ha"].sum().unstack().fillna(0)

    bundle = {
        "models": models, "metrics": metrics, "per_year": per_year, "baselines": baselines,
        "best": best, "sigma": sigma, "importance": importance, "scatter": scatter,
        "clustering": clustering, "rl": rl, "latest_year": latest_year,
        "rows": int(len(labeled)), "municipalities": int(df[["municipality", "department"]].drop_duplicates().shape[0]),
        "years": [int(v) for v in sorted(df["year"].unique())],
        "test_years": list(TEST_YEARS),
        "quantiles": {str(q): float(df["forest_loss_ha"].quantile(q)) for q in (0.25, 0.5, 0.75, 0.95)},
        "feature_medians": {f: float(v) for f, v in zip(CONDITIONS, np.median(transform_conditions(df), axis=0))},
        "lag_share": {k: round(float(sum(importance[k][:3])) * 100) for k in MODEL_NAMES},
        "trend": {"years": [int(i) for i in yearly_region.index],
                  "regions": {r: [int(v) for v in yearly_region[r]] for r in yearly_region.columns}},
        "dept_year": dept_year, "forecast_total": int(latest["forecast_ha"].sum()),
        "ranking": latest.sort_values("forecast_ha", ascending=False).head(12)[
            ["municipality", "department", "region", "profile", "forecast_ha", "lag0"]].to_dict("records"),
    }
    BUNDLE_FILE.parent.mkdir(exist_ok=True)
    joblib.dump(bundle, BUNDLE_FILE)
    (BUNDLE_FILE.parent / "report.json").write_text(json.dumps({
        "best": best, "metrics": metrics, "per_year": per_year, "baselines": baselines,
        "clustering": clustering, "rl": rl, "validation_rows": int(test.sum()),
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return bundle


# ---------------------------------------------------------------------------
# Reinforcement learning: where should limited monitoring teams go?
# ---------------------------------------------------------------------------
def reinforcement_learning(dept_risk, teams=10, n_depts=8, episodes=40000, seed=SEED):
    """Q-learning on a small allocation game.

    State  = how many teams each department already has.
    Action = send the next team to one department.
    Reward = hectares protected; each extra team in the same department is 60% as
             effective as the previous one (diminishing returns).
    """
    depts = list(dept_risk)[:n_depts]
    risk = np.array([dept_risk[d] for d in depts], dtype=float)
    base = risk * 0.30
    scale = base.max()

    def gain(d, n):
        return base[d] * (0.6 ** n)

    rnd = random.Random(seed)
    Q = defaultdict(lambda: np.zeros(len(depts)))
    for ep in range(episodes):
        eps = max(0.05, 1.0 - ep / (episodes * 0.7))
        state = tuple([0] * len(depts))
        for step in range(teams):
            a = rnd.randrange(len(depts)) if rnd.random() < eps else int(np.argmax(Q[state]))
            r = gain(a, state[a]) / scale
            nxt = list(state); nxt[a] += 1; nxt = tuple(nxt)
            future = 0.0 if step == teams - 1 else float(np.max(Q[nxt]))
            Q[state][a] += 0.2 * (r + future - Q[state][a])
            state = nxt

    def run(policy):
        counts, total = [0] * len(depts), 0.0
        for _ in range(teams):
            a = policy(tuple(counts))
            total += gain(a, counts[a])
            counts[a] += 1
        return total, counts

    q_total, q_counts = run(lambda s: int(np.argmax(Q[s])))
    opt_total, _ = run(lambda s: int(np.argmax([gain(i, s[i]) for i in range(len(depts))])))
    top_total, _ = run(lambda s: 0)
    rand_total = float(np.mean([run(lambda s: rnd.randrange(len(depts)))[0] for _ in range(2000)]))
    prop = np.floor(risk / risk.sum() * teams).astype(int)
    prop[0] += teams - prop.sum()
    prop_total = sum(gain(i, n) for i in range(len(depts)) for n in range(int(prop[i])))
    return {
        "teams": teams, "departments": depts, "risk_ha": [round(float(v)) for v in risk],
        "allocation": [int(c) for c in q_counts],
        "results": {
            "Q-learning agent": round(q_total), "Optimal (benchmark)": round(opt_total),
            "Proportional to risk": round(prop_total),
            "All teams in the riskiest department": round(top_total),
            "Random assignment (average)": round(rand_total),
        },
    }


# ---------------------------------------------------------------------------
# Loading, forecasting, scenarios
# ---------------------------------------------------------------------------
def load_bundle():
    try:
        b = joblib.load(BUNDLE_FILE)
        if "per_year" not in b:  # bundle from an older version of the project
            raise ValueError("old bundle")
        return b
    except Exception:  # missing file, other scikit-learn version, or old format
        return train()


def apply_scenario(cond, scen):
    """Change the conditions as a what-if: percentages for cattle/planted/coca, points for NBI and groups."""
    if not scen:
        return dict(cond)
    out = dict(cond)
    out["cattle_heads"] = max(cond["cattle_heads"] * (1 + scen.get("cattle_pct", 0) / 100), 0)
    out["planted_area_ha"] = max(cond["planted_area_ha"] * (1 + scen.get("planted_pct", 0) / 100), 0)
    out["coca_ha"] = max(cond["coca_ha"] * (1 + scen.get("coca_pct", 0) / 100), 0)
    out["nbi_pct"] = min(max(cond["nbi_pct"] + scen.get("nbi_delta", 0), 0), 100)
    out["armed_groups"] = min(max(round(cond["armed_groups"] + scen.get("armed_delta", 0)), 0), 5)
    return out


def forecast(bundle, history, cond, model_key, last_year, scen=None, horizon=HORIZON):
    """history = [loss 2 years ago, loss last year, loss this year]. Returns one dict per future year.

    Years beyond the first are forecast recursively (the previous forecast becomes a lag), so
    uncertainty is widened with the horizon.
    """
    cond = apply_scenario(cond, scen)
    cframe = pd.DataFrame([cond])
    lags = [float(v) for v in history]
    sigma0 = bundle["sigma"][model_key]
    out = []
    for h in range(1, horizon + 1):
        x = features(np.array([lags[-1]]), np.array([lags[-2]]), np.array([lags[-3]]), cframe)
        log_pred = float(bundle["models"][model_key].predict(x)[0])
        sigma = sigma0 * (1 + 0.35 * (h - 1))
        est = max(math.expm1(log_pred), 0.0)
        out.append({
            "year": last_year + h, "estimate": round(est),
            "low": max(round(math.expm1(log_pred - 0.67 * sigma)), 0),
            "high": round(math.expm1(log_pred + 0.67 * sigma)),
            "log": log_pred, "sigma": sigma,
        })
        lags.append(est)
    return out


def alert_level(bundle, estimate):
    q = bundle["quantiles"]
    if estimate < q["0.25"]:
        return "Low", "teal"
    if estimate < q["0.75"]:
        return "Moderate", "amber"
    if estimate < q["0.95"]:
        return "High", "coral"
    return "Critical", "plum"


def prob_high(bundle, first_year_forecast):
    """Chance that next year's loss reaches the High alert threshold (normal errors on the log scale)."""
    threshold = math.log1p(bundle["quantiles"]["0.75"])
    z = (threshold - first_year_forecast["log"]) / first_year_forecast["sigma"]
    return round((1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))) * 100)


def drivers(bundle, history, cond, model_key, last_year, top=4):
    """Model-agnostic: set one input at a time to a typical value and see how the next-year forecast moves."""
    base = forecast(bundle, history, cond, model_key, last_year, horizon=1)[0]["log"]
    rows = []
    typical_loss = bundle["quantiles"]["0.5"]
    for i, name in enumerate(LAG_LABELS):  # last year, 2 years ago, 3 years ago
        alt = list(history)
        alt[2 - i] = typical_loss
        rows.append((LAG_LABELS[name], base - forecast(bundle, alt, cond, model_key, last_year, horizon=1)[0]["log"]))
    medians = bundle["feature_medians"]
    raw_median = {
        "area_km2": math.exp(medians["area_km2"]), "population": math.exp(medians["population"]),
        "cattle_heads": math.expm1(medians["cattle_heads"]), "planted_area_ha": math.expm1(medians["planted_area_ha"]),
        "nbi_pct": medians["nbi_pct"], "coca_ha": math.expm1(medians["coca_ha"]), "armed_groups": medians["armed_groups"],
    }
    for name in CONDITIONS:
        alt = dict(cond); alt[name] = raw_median[name]
        rows.append((CONDITION_LABELS[name], base - forecast(bundle, history, alt, model_key, last_year, horizon=1)[0]["log"]))
    rows = [r for r in rows if abs(r[1]) > 1e-6]
    rows.sort(key=lambda r: abs(r[1]), reverse=True)
    rows = rows[:top]
    peak = max((abs(r[1]) for r in rows), default=1) or 1
    return [{"label": l, "direction": "up" if e > 0 else "down", "width": max(8, round(abs(e) / peak * 100))}
            for l, e in rows]
