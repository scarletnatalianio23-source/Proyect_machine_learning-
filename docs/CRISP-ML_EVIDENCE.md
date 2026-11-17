# CRISP-ML(Q) evidence

What each phase produced and where to verify it in this repository.

| Phase | What was done | Evidence |
| --- | --- | --- |
| 1. Business and data understanding | Problem (late detection, few monitoring teams), success criterion (lowest error on unseen years), objectives and three user roles. Review of IDEAM sources and an open municipal dataset. | Homepage sections 2 and 3; `content.py`; technical report sections 2 and 3 |
| 2. Data preparation | Simulated dataset with a fixed seed: 188 municipalities, 2015 to 2023, 1,692 records. Panel with the losses of the three previous years (log-transformed) and seven current conditions. | `data/forest_loss_municipalities.csv`, `data/generate_dataset.py`, `data/DATA_DICTIONARY.md`, `ml.py` (`build_panel`, `features`) |
| 3. Modeling | Linear regression, Random Forest (250 trees), Gradient Boosting (250 trees); K-Means with k = 4; Q-learning for 10 teams and 8 departments. | `ml.py` (`make_models`, `train`, `reinforcement_learning`), `train_models.py`, `models/bundle.joblib` |
| 4. Evaluation | Time-based validation: train on earlier years, test on 2021, 2022 and 2023 (564 validation rows). MAE, RMSE and R² on the log scale, three naive baselines, per-year errors, K-Means silhouette. Random Forest selected (MAE 319.1 ha). | `models/report.json`, **Models** page, technical report section 8 |
| 5. Deployment | Flask application with registration, login, three roles, CSRF, SQLite, forecast, dashboard and history. Published on Render with Gunicorn. | `app.py`, `db.py`, `requirements.txt`, https://forest-awareness-4qpy.onrender.com/ |
| 6. Monitoring and maintenance | Every forecast stored in `forecasts` and exportable as CSV; administrator retraining; reference error of 319.1 ha to compare against after new data; functional tests; Render logs. | **History** and **Models** (Retrain) pages, `app.py` (`/history.csv`, `/admin/retrain`), `tests/test_workflow.py` |

## Maintenance procedure

1. Append the new yearly data to the dataset.
2. Retrain (`python train_models.py` or the administrator button) and read the new validation errors in `models/report.json`.
3. Compare the new MAE with the reference of 319.1 ha. If it grows clearly, review the data and the models before trusting new forecasts.
4. Commit the new `models/` files and redeploy; run `python tests/test_workflow.py`.

## Quality decisions

- Time-based split instead of a random one, to avoid leaking future information.
- Comparison with naive baselines to show the real value of the models (the gain over "same as last year" is 2.4%).
- Weak results are reported openly (K-Means silhouette 0.152; simulated data).
- No secrets in the repository; access codes and test passwords are environment variables.
