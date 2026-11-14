"""Train the forest-loss regression model and save it as JSON.

Run:  python train_model.py
Needs: pandas, numpy, scikit-learn (only for training, not for the web app).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold, cross_val_predict

BASE = Path(__file__).resolve().parent
df = pd.read_csv(BASE / "data" / "forest_loss_municipalities.csv")

FEATURES = ["area_km2", "population", "cattle_heads", "planted_area_ha", "nbi_pct"]


def transform(frame):
    return np.column_stack([
        np.log(frame["area_km2"]),
        np.log(frame["population"]),
        np.log1p(frame["cattle_heads"]),
        np.log1p(frame["planted_area_ha"]),
        frame["nbi_pct"],
    ])


X = transform(df)
y = np.log1p(df["forest_loss_ha"])
groups = df["municipality"]          # all years of a municipality stay together
cv = GroupKFold(n_splits=5)

report = {}
for name, model in [
    ("Multiple linear regression", LinearRegression()),
    ("Random Forest", RandomForestRegressor(n_estimators=200, min_samples_leaf=5, random_state=2026)),
]:
    pred = cross_val_predict(model, X, y, cv=cv, groups=groups)
    report[name] = {
        "r2_log": round(r2_score(y, pred), 3),
        "mae_ha": round(mean_absolute_error(df["forest_loss_ha"], np.expm1(pred)), 1),
    }
baseline = mean_absolute_error(df["forest_loss_ha"], np.full(len(df), df["forest_loss_ha"].median()))
report["Always predicting the median"] = {"r2_log": None, "mae_ha": round(baseline, 1)}

final = LinearRegression().fit(X, y)
resid = y - final.predict(X)
sigma = float(resid.std())

model = {
    "features": FEATURES,
    "intercept": float(final.intercept_),
    "coefficients": [float(c) for c in final.coef_],
    "residual_sigma": sigma,
    "loss_quantiles": {str(q): float(df["forest_loss_ha"].quantile(q)) for q in (0.25, 0.5, 0.75, 0.9, 0.95)},
    "training_rows": int(len(df)),
    "metrics": report,
}
(BASE / "model.json").write_text(json.dumps(model, indent=2), encoding="utf-8")

print(json.dumps(report, indent=2))
print("coefficients:", dict(zip(FEATURES, np.round(final.coef_, 3))), "sigma", round(sigma, 3))
