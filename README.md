# Forest Awareness

An intelligent early-warning web system for deforestation in Colombian municipalities, built with Machine Learning.
It forecasts the hectares of forest a municipality could lose, classifies the forecast into four alert levels, groups
municipalities with similar behavior and suggests where to send a limited number of monitoring teams.

Final project of the Machine Learning course, Universidad de Cundinamarca. Team **Knowledge Managers**: Iris Lorena Peñaloza, Julián Santiago Canchon and Scarlet Niño.

| Resource | Link |
| --- | --- |
| Published system | https://forest-awareness-4qpy.onrender.com/ |
| Repository | https://github.com/scarletnatalianio23-source/Proyect_machine_learning- |
| Technical report (PDF) | [`docs/Forest_Awareness_Technical_Report.pdf`](docs/Forest_Awareness_Technical_Report.pdf) |
| CRISP-ML(Q) evidence | [`docs/CRISP-ML_EVIDENCE.md`](docs/CRISP-ML_EVIDENCE.md) |
| User documentation | [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) |
| Presentation video | linked on the homepage of the published system |

The homepage contains the mandatory PGC documentation: project title, problem statement and justification, general and
specific objectives, referential framework, methodology and development schedule, and APA references.

> **Data notice.** The dataset is simulated (seed 2026) and follows the structure of an open municipal dataset on
> deforestation in Colombia. Municipality names are real; population, cattle, planted area, unmet basic needs, coca
> cultivation, armed groups and forest loss are generated. Results demonstrate the method and the system, not real forecasts.
> See [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).

## What the system does

- **Home**: documentation of the project, key figures and links to every resource.
- **Models**: comparison of linear regression, Random Forest and Gradient Boosting with a time-based validation, written in plain language; K-Means profiles and the Q-learning team allocation.
- **Predict** (signed-in users): forecast of the next three years for a municipality, range, alert level (Low, Moderate, High, Critical), probability of reaching the High threshold, main drivers and advice. Authorities and administrators also get a what-if scenario simulator.
- **Dashboard** (authority and administrator): totals, forecasts by alert level, recent forecasts, K-Means risk profiles and the Q-learning allocation of 10 monitoring teams across 8 departments.
- **History**: every forecast is stored and can be exported as CSV.
- **Users** (administrator): create users, change roles and activate or disable accounts. The administrator also sees a **Retrain** button on the **Models** page.

Roles: **citizen**, **authority** and **administrator**. Authority and administrator accounts require an institutional access code.

## Results (time-based validation on 2021, 2022 and 2023)

| Model | MAE (ha) | RMSE (ha) | R² (log) |
| --- | --- | --- | --- |
| **Random Forest (selected)** | **319.1** | **880.3** | 0.636 |
| Linear regression | 344.8 | 1,017.9 | 0.643 |
| Gradient Boosting | 345.9 | 998.4 | 0.635 |

Naive baselines: same as last year 327.1 ha, average of the last three years 346.0 ha, always the median 555.9 ha.
K-Means (k = 4) has a silhouette of 0.152. The Q-learning agent reaches 99.9% of the optimal benchmark in the allocation game.
Full detail in `models/report.json` and in the technical report.

## Technologies

Python 3.11+, Flask 3, scikit-learn, pandas, NumPy, joblib, SQLite, Bootstrap 5, Chart.js, Gunicorn.

## Project structure

```
app.py               Flask routes, sessions, roles, CSRF, forecast and dashboard logic
db.py                SQLite schema and helpers (users, forecasts)
ml.py                Training, validation, forecasting, alert levels, K-Means, Q-learning
train_models.py      Trains and evaluates the models and saves models/
content.py           Texts of the homepage documentation, references and resources
data/                Dataset (CSV), generator and data dictionary
models/              bundle.joblib (trained models) and report.json (metrics)
templates/, static/  Jinja2 pages, CSS and JavaScript
tests/               Functional tests of the workflow
docs/                Technical report, CRISP-ML(Q) evidence and user guide
requirements.txt     Dependencies
```

## Run it locally

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The trained models are included, so no training is needed to start.

## Database setup

SQLite is created automatically on first run at `instance/forest.db` (ignored by Git), with the tables `users` and
`forecasts`. To use another location set `FOREST_DB=/path/to/forest.db`.

## Configuration (environment variables)

No passwords or secrets are stored in the repository. Set these variables locally (a `.env` file is ignored by Git) and in the hosting service:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Signs the session cookie. Use a long random value in production. |
| `AUTHORITY_CODE` | Institutional code required to register as authority. If empty, that role cannot be registered. |
| `ADMIN_CODE` | Institutional code required to register as administrator. If empty, that role cannot be registered. |
| `TEST_ADMIN_PASSWORD`, `TEST_AUTHORITY_PASSWORD`, `TEST_CITIZEN_PASSWORD` | Optional. On a brand-new database they create the test accounts `admin@forest.test`, `entity@forest.test` and `citizen@forest.test` for the instructor. |
| `FOREST_DB` | Optional path of the SQLite file. |

Example (macOS / Linux): `export SECRET_KEY=... AUTHORITY_CODE=... ADMIN_CODE=...` and then `python app.py`.

## Train or retrain the models

```bash
python train_models.py                 # trains, validates and saves models/bundle.joblib and models/report.json
python data/generate_dataset.py        # optional: regenerates the simulated dataset (seed 2026)
```

An administrator can also retrain from the **Models** page of the system. Commit the new `models/` files and redeploy.

## Tests

```bash
python tests/test_workflow.py
```

It runs 29 checks on a temporary database: public pages, registration, access codes, role permissions (403), CSRF,
forecast validation, forecast saving, CSV export, authority scenario, dashboard and administrator retraining.

## Deploy on Render

1. Create a **Web Service** from this repository and choose the branch to deploy.
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app`
4. Add the environment variables above (`SECRET_KEY`, `AUTHORITY_CODE`, `ADMIN_CODE` and, if needed, the `TEST_*_PASSWORD` variables).
5. Deploy. Every push to the chosen branch can trigger a new deployment; if the site looks old, check the branch that the service tracks and run **Manual Deploy**.

Note: on the free plan the SQLite file lives on the service disk and can be erased on redeploy. Use a persistent disk or a managed database for permanent data.

## Authors

Iris Lorena Peñaloza, Julián Santiago Canchon and Scarlet Niño (Knowledge Managers).

## References

The full list, in APA 7th edition, is on the homepage of the system and in the technical report. Main sources: Breiman (2001), Friedman (2001), Pedregosa et al. (2011), MacQueen (1967), Rousseeuw (1987), Watkins & Dayan (1992), Sutton & Barto (2018), Wirth & Hipp (2000), Studer et al. (2021), Hansen et al. (2013), Mendoza Montoya (2025) and IDEAM.
