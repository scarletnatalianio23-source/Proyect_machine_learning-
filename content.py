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
        {"weeks": "Weeks 1-2", "name": "Understanding", "text": "Problem statement, objectives, review of IDEAM sources and public datasets."},
        {"weeks": "Weeks 3-4", "name": "Data", "text": "Design and generation of the simulated municipal dataset, documentation of every variable."},
        {"weeks": "Weeks 5-6", "name": "Modeling", "text": "Training and time-based comparison of the three models; analysis and choice of the final model."},
        {"weeks": "Weeks 7-8", "name": "Application", "text": "Flask web app: registration, login and roles, forecast, alerts, scenario simulator and dashboard."},
        {"weeks": "Week 9", "name": "Testing and delivery", "text": "Tests by role, documentation, final presentation."},
    ],
    "method_note": (
        "The methodology follows the CRISP-DM cycle (understanding, data, modeling, evaluation, deployment). "
        "The web application is built with Flask and Bootstrap, and versioned with Git using one branch per work package."
    ),
    "references": [
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
