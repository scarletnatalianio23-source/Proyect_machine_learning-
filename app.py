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
}


@app.route("/")
def home():
    return render_template("index.html", stats=STATS, project=PROJECT)


if __name__ == "__main__":
    app.run(debug=True)