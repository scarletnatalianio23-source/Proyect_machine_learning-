"""Texts of the project documentation (home page) and of the interactive tree.

Structure follows the course template: title, problem statement and justification,
objectives, referential framework, methodology and schedule, references.
"""

# Context figures shown on the home page. Source: IDEAM - SMByC.
STATS = [
    {"icon": "bi-tree-fill", "color": "teal", "label": "Where we stand",
     "value": "52%", "target": 52, "prefix": "", "suffix": "%", "decimals": 0,
     "headline": "More than half of the country is forest",
     "description": "of Colombia's territory is covered by natural forest.",
     "extra": "Every hectare we protect counts", "extra_icon": "bi-shield-check"},
    {"icon": "bi-fire", "color": "coral", "label": "Lost in 2025",
     "value": "119,483", "target": 119483, "prefix": "", "suffix": "", "decimals": 0,
     "headline": "Hectares of forest gone in one year",
     "description": "hectares of forest were lost in Colombia during 2025.",
     "extra": "About 167,000 football fields", "extra_icon": "bi-trophy"},
    {"icon": "bi-graph-up-arrow", "color": "amber", "label": "The trend",
     "value": "+5.2%", "target": 5.2, "prefix": "+", "suffix": "%", "decimals": 1,
     "headline": "The loss is still going up",
     "description": "more than in 2024, when 113,608 hectares were lost.",
     "extra": "That is why early warning matters", "extra_icon": "bi-bell"},
]

DOC = {
    "title": "Forest Awareness: an early-warning system for deforestation in Colombian municipalities using Machine Learning",
    "problem": [
        "Colombia is about 52% covered by natural forest, yet it keeps losing it. According to IDEAM, 119,483 hectares "
        "were deforested in 2025, 5.2% more than in 2024. The loss is concentrated in departments such as Meta, Caquetá, "
        "Guaviare and Putumayo, and it is linked to extensive cattle ranching, agribusiness, illicit crops, illegal mining "
        "and infrastructure.",
        "Official figures are published as reports and bulletins after the loss has happened. Local authorities and "
        "communities do not have a simple tool that tells them which municipalities are likely to lose more forest "
        "next year, how urgent the situation is, or what could change it.",
    ],
    "justification": [
        "Anticipating deforestation allows prevention instead of reaction. A forecast by municipality helps authorities "
        "decide where to place scarce monitoring teams, and helps communities understand the risk in their territory.",
        "Machine Learning can combine the recent history of each municipality with its social and productive conditions "
        "to produce an estimate, an alert level and a range of uncertainty. A what-if simulator shows how changes in "
        "those conditions could affect the forecast, which supports planning and public policy discussions.",
        "The project uses a simulated dataset, inspired by public municipal data, so the method can be built and "
        "demonstrated while keeping every figure clearly labeled as illustrative.",
    ],
    "general": (
        "Develop an intelligent web platform that forecasts the hectares of forest a Colombian municipality could lose "
        "in the coming years, classifies the level of alert and lets citizens, authorities and administrators use "
        "the result according to their role."
    ),
    "specific": [
        "Build and document a municipal dataset (2015-2023) with deforestation and its explanatory variables.",
        "Compare three Machine Learning models (multiple linear regression, Random Forest and Gradient Boosting) with a "
        "time-based validation and choose the most suitable one using MAE, RMSE and R².",
        "Implement the chosen model as a forecast with alert levels, uncertainty range and a what-if scenario simulator.",
        "Develop a secure web application with registration, login and three roles (citizen, authority and administrator).",
        "Provide decision support for authorities with risk profiles (K-Means) and a suggestion of where to send "
        "monitoring teams (reinforcement learning).",
    ],
    "framework": [
        {"title": "Deforestation and its drivers",
         "text": "Deforestation is the permanent conversion of natural forest to other land uses. In Colombia it is monitored "
                 "by IDEAM through the Forest and Carbon Monitoring System (SMByC). Its main drivers include extensive cattle "
                 "ranching, agricultural expansion, illicit crops, illegal mining, infrastructure and the presence of "
                 "armed groups."},
        {"title": "Early-warning systems",
         "text": "An early-warning system detects the conditions that precede a harmful event and communicates the risk "
                 "in time to act. Here the event is a high level of forest loss in a municipality."},
        {"title": "Supervised regression and forecasting",
         "text": "Regression models learn a relationship between input variables and a numeric target. For forecasting, "
                 "the inputs include the recent past of the target, and the model is validated by predicting later years "
                 "than the ones it was trained on (Hyndman & Athanasopoulos, 2021)."},
        {"title": "Models compared",
         "text": "Multiple linear regression is the simplest and most interpretable. Random Forest (Breiman, 2001) averages "
                 "many decision trees. Gradient Boosting (Friedman, 2001) builds trees one after another, each correcting "
                 "the errors of the previous ones."},
        {"title": "Unsupervised and reinforcement learning",
         "text": "K-Means groups similar municipalities without using the target. Q-learning (Sutton & Barto, 2018) learns "
                 "a decision policy through trial and reward; here, how to assign limited monitoring teams."},
    ],
    "phases": [
        {"weeks": "All members", "name": "1. Business and data understanding",
         "text": "Define the problem and the success criterion (lowest error on unseen years), review the IDEAM sources and the open municipal dataset, set the objectives and the three user roles. Deliverable: problem statement, objectives and the first draft of the data dictionary."},
        {"weeks": "Julián", "name": "2. Data preparation",
         "text": "Generate the simulated municipal dataset (seed 2026), document every variable, check ranges, log-transform the losses and build the panel with the losses of the three previous years. Deliverable: dataset CSV, DATA_DICTIONARY.md and generate_dataset.py."},
        {"weeks": "Julián, Scarlet", "name": "3. Modeling",
         "text": "Train linear regression, Random Forest and Gradient Boosting; fit K-Means (k = 4) on municipality profiles; implement Q-learning for 10 teams and 8 departments. Deliverable: train_models.py and models/bundle.joblib."},
        {"weeks": "Scarlet", "name": "4. Evaluation",
         "text": "Time-based validation on 2021, 2022 and 2023 with MAE, RMSE and R², comparison against three naive baselines, model selection and the plain-language Models page. Deliverable: models/report.json and the Models page."},
        {"weeks": "Iris", "name": "5. Deployment",
         "text": "Flask application with registration, login, three roles, CSRF protection, SQLite, forecast page with alerts and scenario simulator, authority dashboard, and publication on Render. Deliverable: published system and repository with README."},
        {"weeks": "Iris, Scarlet", "name": "6. Monitoring and maintenance",
         "text": "Forecast history with CSV export, administrator retraining, role-based functional tests and a maintenance procedure that compares new errors with the 319.1 ha reference. Deliverable: History page, retrain function and docs/CRISP-ML_EVIDENCE.md."},
    ],
    "method_note": (
        "The methodology follows the six phases of CRISP-ML(Q): business and data understanding, data preparation, modeling, "
        "evaluation, deployment, and monitoring and maintenance. The web application is built with Flask and Bootstrap and "
        "versioned with Git using one branch per work package. The three members worked on every phase; the label shows who led each one."
    ),
    "references": [
        'Hansen, M. C., Potapov, P. V., Moore, R., Hancher, M., Turubanova, S. A., Tyukavina, A., Thau, D., Stehman, S. V., Goetz, S. J., Loveland, T. R., Kommareddy, A., Egorov, A., Chini, L., Justice, C. O., & Townshend, J. R. G. (2013). High-resolution global maps of 21st-century forest cover change. *Science, 342*(6160), 850-853. https://doi.org/10.1126/science.1244693',
        'MacQueen, J. (1967). Some methods for classification and analysis of multivariate observations. In L. M. Le Cam & J. Neyman (Eds.), *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability* (Vol. 1, pp. 281-297). University of California Press.',
        'Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics, 20*, 53-65. https://doi.org/10.1016/0377-0427(87)90125-7',
        'Studer, S., Bui, T. B., Drescher, C., Hanuschkin, A., Winkler, L., Peters, S., & Müller, K.-R. (2021). Towards CRISP-ML(Q): A machine learning process model with quality assurance methodology. *Machine Learning and Knowledge Extraction, 3*(2), 392-413. https://doi.org/10.3390/make3020020',
        'Watkins, C. J. C. H., & Dayan, P. (1992). Q-learning. *Machine Learning, 8*(3-4), 279-292. https://doi.org/10.1007/BF00992698',
        'Wirth, R., & Hipp, J. (2000). CRISP-DM: Towards a standard process model for data mining. In *Proceedings of the 4th International Conference on the Practical Applications of Knowledge Discovery and Data Mining* (pp. 29-39). Practical Application Company.',
        'Redacción Cambio. (2024, July 8). *Gobierno presenta la cifra más baja en deforestación de los últimos 23 años*. Cambio. https://cambiocolombia.com/medio-ambiente/deforestacion-2023-disminucion-record-minambiente',
        'Beltrán, J. (2025, July 30). *Aumentó la deforestación en Colombia: en el último año se perdieron más de 113.000 hectáreas*. Cambio. https://cambiocolombia.com/medio-ambiente/articulo/2025/7/aumento-la-deforestacion-en-colombia-en-el-ultimo-ano-se-perdieron-mas-de-113000',
        "Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5-32. https://doi.org/10.1023/A:1010933404324",
        "Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. *The Annals of Statistics, 29*(5), 1189-1232. https://doi.org/10.1214/aos/1013203451",
        "Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and practice* (3rd ed.). OTexts. https://otexts.com/fpp3/",
        "Instituto de Hidrología, Meteorología y Estudios Ambientales. (n.d.). *Sistema de Monitoreo de Bosques y Carbono (SMByC)*. http://smbyc.ideam.gov.co/",
        "Mendoza Montoya, E. (2025). *Municipal-level data on deforestation, prosecutions, and socioeconomic indicators in Colombia (2021-2023)* (Version 1) [Data set]. Mendeley Data. https://doi.org/10.17632/mn5s748pyt.1",
        "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825-2830.",
        "Sutton, R. S., & Barto, A. G. (2018). *Reinforcement learning: An introduction* (2nd ed.). MIT Press.",
    ],
}

# Short versions for the interactive tree on the home page.
PROJECT = {
    "problem": {"title": "Problem", "color": "#f3722c", "text": " ".join(DOC["problem"])},
    "general": {"title": "General objective", "color": "#f9c74f", "text": DOC["general"]},
    "specific": {"title": "Specific objectives", "color": "#2ec4b6", "items": [
        DOC["specific"][0],
        DOC["specific"][1],
        "Deliver a secure web platform with roles that forecasts forest loss, classifies the alert level, simulates "
        "scenarios and supports authorities with risk profiles and resource allocation.",
    ]},
    "framework": {"title": "Referential framework", "color": "#9b5de5",
                  "items": [f["title"] + ": " + f["text"].split(". ")[0].rstrip(".") + "." for f in DOC["framework"]]},
    "methodology": {"title": "Methodology", "color": "#4cc9f0",
                    "items": [p["weeks"] + " - " + p["name"] + ": " + p["text"] for p in DOC["phases"]]},
    "references": {"title": "References", "color": "#f15bb5",
                   "items": [r.replace("*", "") for r in DOC["references"]]},
}


DOC["references"].append(
    "Hansen, M. C., Krylov, A., Tyukavina, A., Potapov, P. V., Turubanova, S., Zutta, B., Ifo, S., Margono, B., Stolle, F., & Moore, R. (2016). Humid tropical forest disturbance alerts using Landsat data. *Environmental Research Letters, 11*(3), Article 034008. https://doi.org/10.1088/1748-9326/11/3/034008")
DOC["references"].append(
    "Instituto de Hidrología, Meteorología y Estudios Ambientales. (n.d.). *¿Cómo el IDEAM mide y genera la cifra anual oficial de cambio de la superficie del bosque en Colombia?* [Guide]. "
    "https://www.ideam.gov.co/sites/default/files/transparencia/informaciondelaentidad/noticias/guia6bpv_v5.pdf")
DOC["references"].sort(key=lambda r: r.lower())

# Resources shown on the home page (technical report, evidence, repository, system, guide, video).
REPO_URL = "https://github.com/scarletnatalianio23-source/Proyect_machine_learning-"
APP_URL = "https://forest-awareness-4qpy.onrender.com/"
VIDEO_URL = "https://mailunicundiedu.sharepoint.com/:v:/r/sites/MachineLearningVideoFinal/_layouts/15/stream.aspx?id=%2Fsites%2FMachineLearningVideoFinal%2FShared%20Documents%2FGeneral%2FRecordings%2FFinal%20project%20video-20261116_225610-Grabaci%C3%B3n%20de%20la%20reuni%C3%B3n.mp4&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D&share=cQqeBj3D84g1TJjge7r1xWl3EgUBGa--WEDb2dY4cNgdTNPRHA"
RESOURCES = [
    {"icon": "bi-file-earmark-pdf", "title": "Technical report (PDF)", "text": "Final report with every PGC section, the six CRISP-ML(Q) phases, testing, deployment and each member's contributions.", "url": REPO_URL + "/blob/r0611/docs/Forest_Awareness_Technical_Report.pdf"},
    {"icon": "bi-diagram-3", "title": "CRISP-ML(Q) evidence", "text": "What each phase produced and where to find it in the repository.", "url": REPO_URL + "/blob/r0611/docs/CRISP-ML_EVIDENCE.md"},
    {"icon": "bi-github", "title": "Repository", "text": "Source code, training and evaluation scripts, dataset, dependencies and README.", "url": REPO_URL},
    {"icon": "bi-box-arrow-up-right", "title": "Published system", "text": "The deployed application. Operational modules require an account.", "url": APP_URL},
    {"icon": "bi-book", "title": "User documentation", "text": "Step-by-step guide for citizens, authorities and administrators.", "url": REPO_URL + "/blob/r0611/docs/USER_GUIDE.md"},
    {"icon": "bi-camera-video", "title": "Presentation video", "text": "20-minute defense in English by the three team members.", "url": VIDEO_URL},
]
