"""Train and compare the three models, then save them in models/.

    python train_models.py
"""
import json

import ml

bundle = ml.train(verbose=True)
print(json.dumps({"best": bundle["best"], "metrics": bundle["metrics"],
                  "baseline": bundle["baseline"], "clustering": bundle["clustering"],
                  "rl": bundle["rl"]["results"]}, indent=2, ensure_ascii=False))
