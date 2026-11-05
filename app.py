from flask import Flask, render_template

app = Flask(__name__)

# Context figures shown on the home page.
# Source: IDEAM - Sistema de Monitoreo de Bosques y Carbono (SMByC).
STATS = [
    {
        "icon": "bi-tree-fill",
        "color": "coral",
        "value": "119,483",
        "description": "hectares of forest lost in Colombia during 2025",
    },
    {
        "icon": "bi-graph-up-arrow",
        "color": "amber",
        "value": "+5.2%",
        "description": "increase compared to 2024, when 113,608 hectares were lost",
    },
    {
        "icon": "bi-globe-americas",
        "color": "teal",
        "value": "52%",
        "description": "of Colombia's territory is covered by natural forest",
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
        "color": "#7b5ea7",
        "text": (
            "Deforestation in Colombia is monitored officially by IDEAM through the "
            "Forest and Carbon Monitoring System (SMByC). On the technical side, the "
            "project uses regression, a supervised learning technique that predicts a "
            "numeric value, here the hectares of forest lost, and measures its quality "
            "with metrics such as R² and mean absolute error. The model is served "
            "through a Python and Flask website."
        ),
    },
    "methodology": {
        "title": "Methodology and schedule",
        "color": "#4cc9f0",
        "text": (
            "The work follows four stages: collect, prepare, model and deliver. It is "
            "planned for about three weeks: week 1 for data collection and cleaning, "
            "week 2 for model training and evaluation, and week 3 for the web "
            "interface and final delivery."
        ),
    },
    "references": {
        "title": "References",
        "color": "#52b788",
        "text": (
            "Official deforestation figures and bulletins come from IDEAM, through "
            "the Forest and Carbon Monitoring System (SMByC)."
        ),
    },
}

# ---------------------------------------------------------------
# Content of the "Project structure" page (/project)
# ---------------------------------------------------------------

PROJECT_TITLE = "Forest Awareness: Estimating Deforestation in Colombia with Machine Learning"

JUSTIFICATION = [
    "Deforestation is not only an environmental issue: it affects water regulation, "
    "biodiversity and the livelihoods of the communities that live around forests. "
    "In Colombia the data to follow it exist, but they are published mostly as reports "
    "and bulletins that are hard to explore for someone without technical training.",
    "A tool that turns those official figures into an estimate for a specific "
    "municipality makes the information easier to understand and use. Students, "
    "communities and local authorities could explore how forest loss may vary with the "
    "conditions they enter, instead of reading static documents.",
    "The project also has an educational purpose: it shows how a Machine Learning "
    "regression model is built end to end, from open data to a working website.",
]

FRAMEWORK = [
    {
        "icon": "bi-tree-fill",
        "color": "coral",
        "title": "Contextual",
        "text": "Deforestation in Colombia is monitored officially by IDEAM through the "
                "Forest and Carbon Monitoring System (SMByC). Departments such as Meta, "
                "Caquetá, Guaviare and Putumayo concentrate most of the loss.",
    },
    {
        "icon": "bi-graph-up",
        "color": "amber",
        "title": "Theoretical",
        "text": "Regression is a supervised learning technique that predicts a numeric "
                "value, here the hectares of forest lost, from input variables. Its "
                "quality is measured with metrics such as R² and mean absolute error.",
    },
    {
        "icon": "bi-code-slash",
        "color": "teal",
        "title": "Technical",
        "text": "The trained model is served through a Python and Flask website, with a "
                "Bootstrap interface where the user enters the data and sees the "
                "estimate.",
    },
]

METHODOLOGY = [
    {
        "color": "coral",
        "title": "Collect",
        "text": "Obtain the official IDEAM deforestation data by municipality and year, "
                "plus the explanatory variables.",
    },
    {
        "color": "amber",
        "title": "Prepare",
        "text": "Clean the data, handle missing values and split it into training and "
                "test sets.",
    },
    {
        "color": "teal",
        "title": "Model",
        "text": "Train a regression model and evaluate it with R² and mean absolute "
                "error.",
    },
    {
        "color": "sky",
        "title": "Deliver",
        "text": "Build the website with a data-entry form and a visualization of the "
                "estimate.",
    },
]

# Three-week schedule, one week per specific objective.
SCHEDULE = [
    {
        "week": "Week 1",
        "color": "coral",
        "title": "Data collection and cleaning",
        "objective": "Specific objective 1",
        "tasks": [
            "Locate and download the official deforestation data by municipality and year.",
            "Identify and gather the explanatory variables.",
            "Clean, standardize and document the dataset.",
        ],
    },
    {
        "week": "Week 2",
        "color": "amber",
        "title": "Model training and evaluation",
        "objective": "Specific objective 2",
        "tasks": [
            "Choose and train the regression model.",
            "Evaluate it with R² and mean absolute error on the test set.",
            "Adjust the model and save the final version.",
        ],
    },
    {
        "week": "Week 3",
        "color": "teal",
        "title": "Web interface and delivery",
        "objective": "Specific objective 3",
        "tasks": [
            "Build the data-entry form and the results visualization.",
            "Connect the model to the website and test it with sample municipalities.",
            "Polish the design, review the whole project and deliver.",
        ],
    },
]

REFERENCES = [
    "IDEAM. Sistema de Monitoreo de Bosques y Carbono (SMByC). Official deforestation "
    "figures and bulletins for Colombia. smbyc.ideam.gov.co",
]


@app.route("/")
def home():
    return render_template("index.html", stats=STATS, project=PROJECT)


@app.route("/project")
def project_page():
    return render_template(
        "project.html",
        project=PROJECT,
        project_title=PROJECT_TITLE,
        justification=JUSTIFICATION,
        framework=FRAMEWORK,
        methodology=METHODOLOGY,
        schedule=SCHEDULE,
        references=REFERENCES,
    )


if __name__ == "__main__":
    app.run(debug=True)