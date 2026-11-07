"""Machine Learning layer of Forest Awareness.

* Three supervised regression models are compared with the same validation:
  multiple linear regression, Random Forest and Gradient Boosting.
* K-Means groups municipalities into risk profiles (unsupervised).
* A small Q-learning agent suggests how to spread limited monitoring teams
  (reinforcement learning).

Everything is trained on the SIMULATED dataset in data/. Run `python train_models.py`
to retrain, or use the button in the admin panel.
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
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "data" / "forest_loss_municipalities.csv"
BUNDLE_FILE = BASE / "models" / "bundle.joblib"

FEATURES = ["area_km2", "population", "cattle_heads", "planted_area_ha", "nbi_pct", "coca_ha", "armed_groups"]
FEATURE_LABELS = {
    "area_km2": "Municipal area", "population": "Population", "cattle_heads": "Cattle",
    "planted_area_ha": "Planted area", "nbi_pct": "Unmet basic needs (NBI)",
    "coca_ha": "Coca cultivation", "armed_groups": "Armed groups",
}
MODEL_NAMES = {
    "linear": "Multiple linear regression",
    "forest": "Random Forest",
    "boosting": "Gradient Boosting",
}
SEED = 2026


def load_data():
    return pd.read_csv(DATA_FILE)


def transform(frame):
    """Log-transform the skewed variables so the models see well-behaved inputs."""
    return np.column_stack([
        np.log(frame["area_km2"]),
        np.log(frame["population"]),
        np.log1p(frame["cattle_heads"]),
        np.log1p(frame["planted_area_ha"]),
        frame["nbi_pct"],
        np.log1p(frame["coca_ha"]),
        frame["armed_groups"],
    ])


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
        "r2": round(float(r2_score(actual, pred)), 3),
        "r2_log": round(float(r2_score(np.log1p(actual), pred_log)), 3),
    }


def _profile_names(order):
    names = ["Low pressure", "Moderate pressure", "High pressure", "Critical pressure"]
    return {cluster: names[rank] for rank, cluster in enumerate(order)}


def train(verbose=False):
    df = load_data()
    X = transform(df)
    actual = df["forest_loss_ha"].to_numpy(dtype=float)
    y = np.log1p(actual)
    groups = (df["municipality"] + "|" + df["department"]).to_numpy()
    folds = list(GroupKFold(n_splits=5).split(X, y, groups))

    # ---- Cross-validation: same folds for every model ----------------------
    oof = {key: np.zeros(len(df)) for key in MODEL_NAMES}
    oof["boosting_kmeans"] = np.zeros(len(df))
    for train_idx, test_idx in folds:
        for key, model in make_models().items():
            model.fit(X[train_idx], y[train_idx])
            oof[key][test_idx] = model.predict(X[test_idx])
        # Experiment: add the unsupervised risk profile as an extra input.
        scaler = StandardScaler().fit(X[train_idx])
        km = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit(scaler.transform(X[train_idx]))
        def with_profile(rows):
            labels = km.predict(scaler.transform(rows))
            return np.column_stack([rows, np.eye(4)[labels]])
        gb = make_models()["boosting"].fit(with_profile(X[train_idx]), y[train_idx])
        oof["boosting_kmeans"][test_idx] = gb.predict(with_profile(X[test_idx]))
        if verbose:
            print("fold done")

    metrics = {key: _metrics(actual, oof[key]) for key in oof}
    sigma = {key: float(np.std(y - oof[key])) for key in MODEL_NAMES}
    baseline_pred = np.full(len(df), np.median(actual))
    baseline = {
        "mae": round(float(mean_absolute_error(actual, baseline_pred)), 1),
        "rmse": round(float(math.sqrt(np.mean((actual - baseline_pred) ** 2))), 1),
    }
    best = min(MODEL_NAMES, key=lambda k: metrics[k]["mae"])

    # ---- Final models on all data -----------------------------------------
    models = {key: model.fit(X, y) for key, model in make_models().items()}
    std = X.std(axis=0)
    lin = np.abs(models["linear"].coef_) * std
    importance = {
        "linear": (lin / lin.sum()).tolist(),
        "forest": models["forest"].feature_importances_.tolist(),
        "boosting": models["boosting"].feature_importances_.tolist(),
    }

    rng = np.random.default_rng(SEED)
    pick = rng.choice(len(df), size=min(450, len(df)), replace=False)
    scatter = {
        key: [[int(actual[i]), int(max(round(math.expm1(oof[key][i])), 0))] for i in pick]
        for key in MODEL_NAMES
    }

    # ---- Unsupervised: risk profiles with K-Means --------------------------
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    kmeans = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit(Xs)
    labels = kmeans.labels_
    mean_loss = {c: float(actual[labels == c].mean()) for c in range(4)}
    order = sorted(mean_loss, key=mean_loss.get)
    names = _profile_names(order)
    profiles = []
    for c in order:
        part = df[labels == c]
        profiles.append({
            "name": names[c], "cluster": int(c), "rows": int(len(part)),
            "municipalities": int(part[["municipality", "department"]].drop_duplicates().shape[0]),
            "mean_loss": round(mean_loss[c]),
            "area_km2": round(float(part["area_km2"].median())),
            "cattle_heads": round(float(part["cattle_heads"].median())),
            "nbi_pct": round(float(part["nbi_pct"].mean()), 1),
            "coca_share": round(float((part["coca_ha"] > 0).mean()) * 100),
        })
    clustering = {
        "silhouette": round(float(silhouette_score(Xs, labels)), 3),
        "k": 4, "profiles": profiles,
        "gain_mae": round(metrics["boosting"]["mae"] - metrics["boosting_kmeans"]["mae"], 1),
    }
    cluster_of = dict(zip(df.index, [names[int(c)] for c in labels]))

    # ---- Dataset summaries used by the pages -------------------------------
    latest_year = int(df["year"].max())
    latest = df[df["year"] == latest_year].copy()
    latest_pred = np.clip(np.expm1(models[best].predict(transform(latest))), 0, None)
    latest["predicted_ha"] = latest_pred.round().astype(int)
    latest["profile"] = [cluster_of[i] for i in latest.index]

    dept = latest.groupby("department")["predicted_ha"].sum().sort_values(ascending=False)
    rl = reinforcement_learning(dept.to_dict())

    yearly_region = (df.groupby(["year", "region"])["forest_loss_ha"].sum().unstack().fillna(0))
    by_dept_year = df.groupby(["department", "year"])["forest_loss_ha"].mean().round().unstack().fillna(0)

    bundle = {
        "models": models, "kmeans": kmeans, "scaler": scaler, "profile_names": names,
        "metrics": metrics, "baseline": baseline, "best": best, "sigma": sigma,
        "importance": importance, "scatter": scatter, "clustering": clustering,
        "rl": rl, "rows": int(len(df)), "municipalities": int(df[["municipality", "department"]].drop_duplicates().shape[0]),
        "years": [int(y_) for y_ in sorted(df["year"].unique())],
        "quantiles": {str(q): float(df["forest_loss_ha"].quantile(q)) for q in (0.25, 0.5, 0.75, 0.95)},
        "feature_means": {f: float(v) for f, v in zip(FEATURES, X.mean(axis=0))},
        "feature_medians": {f: float(v) for f, v in zip(FEATURES, np.median(X, axis=0))},
        "trend": {
            "years": [int(i) for i in yearly_region.index],
            "regions": {r: [int(v) for v in yearly_region[r]] for r in yearly_region.columns},
        },
        "dept_year": {d: [int(v) for v in row] for d, row in by_dept_year.iterrows()},
        "top_municipalities": latest.sort_values("predicted_ha", ascending=False).head(12)[
            ["municipality", "department", "region", "profile", "predicted_ha", "forest_loss_ha"]
        ].to_dict("records"),
        "latest_year": latest_year,
    }
    BUNDLE_FILE.parent.mkdir(exist_ok=True)
    joblib.dump(bundle, BUNDLE_FILE)
    (BUNDLE_FILE.parent / "report.json").write_text(json.dumps({
        "metrics": metrics, "baseline": baseline, "best": best, "clustering": clustering,
        "rl": rl, "rows": bundle["rows"],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return bundle


# ---------------------------------------------------------------------------
# Reinforcement learning: where should limited monitoring teams go?
# ---------------------------------------------------------------------------
def reinforcement_learning(dept_risk, teams=10, n_depts=8, episodes=40000, seed=SEED):
    """Q-learning on a small allocation game.

    State  = how many teams each department already has.
    Action = send the next team to one department.
    Reward = hectares protected. Every extra team in the same department protects
             less (diminishing returns: each one is 60% as effective as the last).
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
            if rnd.random() < eps:
                a = rnd.randrange(len(depts))
            else:
                a = int(np.argmax(Q[state]))
            r = gain(a, state[a]) / scale
            nxt = list(state); nxt[a] += 1; nxt = tuple(nxt)
            future = 0.0 if step == teams - 1 else float(np.max(Q[nxt]))
            Q[state][a] += 0.2 * (r + future - Q[state][a])
            state = nxt

    def run(policy):
        counts = [0] * len(depts)
        total = 0.0
        for _ in range(teams):
            a = policy(tuple(counts))
            total += gain(a, counts[a])
            counts[a] += 1
        return total, counts

    q_total, q_counts = run(lambda s: int(np.argmax(Q[s])))
    opt_total, _ = run(lambda s: int(np.argmax([gain(i, s[i]) for i in range(len(depts))])))
    top_total, _ = run(lambda s: 0)
    rand_totals = []
    for _ in range(2000):
        rand_totals.append(run(lambda s: rnd.randrange(len(depts)))[0])
    prop_counts = np.floor(risk / risk.sum() * teams).astype(int)
    prop_counts[0] += teams - prop_counts.sum()
    prop_total = sum(gain(i, n) for i in range(len(depts)) for n in range(int(prop_counts[i])))

    return {
        "teams": teams,
        "departments": depts,
        "risk_ha": [round(float(v)) for v in risk],
        "allocation": [int(c) for c in q_counts],
        "results": {
            "Q-learning agent": round(q_total),
            "Optimal (benchmark)": round(opt_total),
            "Proportional to risk": round(prop_total),
            "All teams in the riskiest department": round(top_total),
            "Random assignment (average)": round(float(np.mean(rand_totals))),
        },
    }


# ---------------------------------------------------------------------------
# Loading and predicting
# ---------------------------------------------------------------------------
def load_bundle():
    try:
        return joblib.load(BUNDLE_FILE)
    except Exception:  # missing file or different scikit-learn version
        return train()


def predict(bundle, values, model_key):
    """Return the estimate (ha) and a likely range for one model."""
    row = pd.DataFrame([values])
    x = transform(row)
    log_pred = float(bundle["models"][model_key].predict(x)[0])
    sigma = bundle["sigma"][model_key]
    return {
        "key": model_key,
        "name": MODEL_NAMES[model_key],
        "estimate": max(round(math.expm1(log_pred)), 0),
        "low": max(round(math.expm1(log_pred - 0.67 * sigma)), 0),
        "high": round(math.expm1(log_pred + 0.67 * sigma)),
        "log": log_pred,
    }


def drivers(bundle, values, model_key, top=4):
    """Model-agnostic: change one input at a time to a typical value and see how the estimate moves."""
    model = bundle["models"][model_key]
    x = transform(pd.DataFrame([values]))
    base = float(model.predict(x)[0])
    out = []
    for i, name in enumerate(FEATURES):
        alt = x.copy()
        alt[0, i] = bundle["feature_medians"][name]
        out.append({"label": FEATURE_LABELS[name], "effect": base - float(model.predict(alt)[0])})
    out = [d for d in out if abs(d["effect"]) > 1e-6]
    out.sort(key=lambda d: abs(d["effect"]), reverse=True)
    out = out[:top]
    peak = max((abs(d["effect"]) for d in out), default=1) or 1
    for d in out:
        d["direction"] = "up" if d["effect"] > 0 else "down"
        d["width"] = max(8, round(abs(d["effect"]) / peak * 100))
    return out


def level_for(bundle, estimate):
    q = bundle["quantiles"]
    if estimate < q["0.25"]:
        return "Low", "teal"
    if estimate < q["0.75"]:
        return "Moderate", "amber"
    if estimate < q["0.95"]:
        return "High", "coral"
    return "Very high", "plum"
