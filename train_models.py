"""Train and compare the three forecasting models, then save them in models/.

    python train_models.py
"""
import json

import ml

bundle = ml.train(verbose=True)
print(json.dumps({"best": bundle["best"], "metrics": bundle["metrics"], "per_year": bundle["per_year"],
                  "baselines": bundle["baselines"], "lag_share": bundle["lag_share"],
                  "clustering": bundle["clustering"], "rl": bundle["rl"]["results"]},
                 indent=2, ensure_ascii=False))
