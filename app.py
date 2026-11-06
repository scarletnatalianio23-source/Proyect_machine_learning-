import json
import math
from pathlib import Path

import pandas as pd
from flask import Flask, render_template, request

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)

# Context figures shown on the home page as a timeline on a tree branch.
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
            "Develop an intelligent website that, using a regression model trained "
            "on real IDEAM data and complementary sources, estimates the hectares of "
            "forest lost in a municipality from manually entered data."
        ),
    },
    "specific": {
        "title": "Specific objectives",
        "color": "#2ec4b6",
        "items": [
            "Collect and clean the official deforestation dataset by municipality "
            "and year, together with its explanatory variables.",
            "Train and evaluate the model using metrics such as R² and mean "
            "absolute error.",
            "Build a web interface with a data-entry form and a visualization of "
            "the results.",
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
            "Train a multiple linear regression and compare it with a Random Forest.",
            "Evaluate with five-fold cross-validation (R² and mean absolute error).",
            "Deploy the best model in a Flask web form.",
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
# Prediction model (trained with train_model.py, stored as plain JSON)
# ---------------------------------------------------------------------------
MODEL = json.loads((BASE_DIR / "model.json").read_text(encoding="utf-8"))
_DATA = pd.read_csv(BASE_DIR / "data" / "forest_loss_municipalities.csv")

# Latest year of every municipality, used to pre-fill the form.
_LATEST = _DATA[_DATA["year"] == _DATA["year"].max()].sort_values(["municipality", "department"])
MUNICIPALITIES = [
    {
        "label": f"{r.municipality} ({r.department})",
        "area_km2": r.area_km2,
        "population": int(r.population),
        "cattle_heads": int(r.cattle_heads),
        "planted_area_ha": r.planted_area_ha,
        "nbi_pct": r.nbi_pct,
    }
    for r in _LATEST.itertuples()
]

FIELDS = [
    # name, label, unit, min, max, step, icon, help text
    ("area_km2", "Municipal area", "km²", 5, 70000, "any", "bi-bounding-box",
     "Total surface of the municipality."),
    ("population", "Population", "people", 100, 8000000, 1, "bi-people-fill",
     "Number of inhabitants."),
    ("cattle_heads", "Cattle", "heads", 0, 1000000, 1, "bi-egg-fried",
     "Cattle heads raised in the municipality."),
    ("planted_area_ha", "Planted area", "hectares", 0, 500000, "any", "bi-flower2",
     "Land used for crops."),
    ("nbi_pct", "Unmet basic needs (NBI)", "%", 0, 100, "any", "bi-house-exclamation-fill",
     "Share of the population with unmet basic needs. Higher means more poverty."),
]
LABELS = {f[0]: f[1] for f in FIELDS}

_MEANS = {
    "area_km2": float(pd.Series([math.log(v) for v in _DATA["area_km2"]]).mean()),
    "population": float(pd.Series([math.log(v) for v in _DATA["population"]]).mean()),
    "cattle_heads": float(pd.Series([math.log1p(v) for v in _DATA["cattle_heads"]]).mean()),
    "planted_area_ha": float(pd.Series([math.log1p(v) for v in _DATA["planted_area_ha"]]).mean()),
    "nbi_pct": float(_DATA["nbi_pct"].mean()),
}


def _transform(v):
    return [
        math.log(v["area_km2"]),
        math.log(v["population"]),
        math.log1p(v["cattle_heads"]),
        math.log1p(v["planted_area_ha"]),
        v["nbi_pct"],
    ]


def parse_form(form):
    """Return (values, errors). Every field is required and range-checked."""
    values, errors = {}, {}
    for name, label, unit, low, high, _step, _icon, _help in FIELDS:
        raw = (form.get(name) or "").strip().replace(",", "")
        try:
            number = float(raw)
        except ValueError:
            errors[name] = "Enter a number."
            continue
        if not (low <= number <= high):
            errors[name] = f"Must be between {low:,} and {high:,} {unit}."
            continue
        values[name] = number
    return values, errors


def predict(values):
    x = _transform(values)
    log_pred = MODEL["intercept"] + sum(c * xi for c, xi in zip(MODEL["coefficients"], x))
    sigma = MODEL["residual_sigma"]
    estimate = max(math.expm1(log_pred), 0.0)
    low = max(math.expm1(log_pred - 0.67 * sigma), 0.0)   # ~50% of cases fall inside
    high = math.expm1(log_pred + 0.67 * sigma)

    q = MODEL["loss_quantiles"]
    if estimate < q["0.25"]:
        level, color = "Low", "teal"
    elif estimate < q["0.75"]:
        level, color = "Moderate", "amber"
    elif estimate < q["0.95"]:
        level, color = "High", "coral"
    else:
        level, color = "Very high", "plum"

    # Share of dataset rows with less loss than this estimate.
    percentile = round(float((_DATA["forest_loss_ha"] < estimate).mean()) * 100)

    # What pushes the estimate up or down compared with an average municipality.
    drivers = []
    for name, coef, xi in zip(MODEL["features"], MODEL["coefficients"], x):
        effect = coef * (xi - _MEANS[name])
        drivers.append({"label": LABELS[name], "effect": effect})
    drivers.sort(key=lambda d: abs(d["effect"]), reverse=True)
    top = max(abs(d["effect"]) for d in drivers) or 1
    for d in drivers:
        d["direction"] = "up" if d["effect"] > 0 else "down"
        d["width"] = max(8, round(abs(d["effect"]) / top * 100))

    # Position on a log scale for the gauge (0 - 12,000 ha).
    gauge = min(100, round(math.log1p(estimate) / math.log1p(12000) * 100))
    return {
        "estimate": round(estimate), "low": round(low), "high": round(high),
        "level": level, "color": color, "percentile": percentile,
        "median": round(q["0.5"]), "drivers": drivers[:4], "gauge": gauge,
    }


@app.route("/")
def home():
    return render_template("index.html", stats=STATS, project=PROJECT)


@app.route("/predict", methods=["GET", "POST"])
def predict_page():
    values, errors, result = {}, {}, None
    if request.method == "POST":
        values, errors = parse_form(request.form)
        if not errors:
            result = predict(values)
        values = {k: request.form.get(k, "") for k, *_ in FIELDS}
    return render_template(
        "predict.html",
        fields=FIELDS, values=values, errors=errors, result=result,
        municipalities=MUNICIPALITIES, metrics=MODEL["metrics"],
        rows=MODEL["training_rows"], selected=request.form.get("municipality", ""),
    )


@app.route("/project")
def project_page():
    return render_template("project.html", stats=STATS, project=PROJECT)


if __name__ == "__main__":
    app.run(debug=True)
