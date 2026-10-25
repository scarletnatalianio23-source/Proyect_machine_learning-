# BosqueIA

An intelligent website to analyze and estimate deforestation in Colombia with Machine Learning.

> Current status: home page. The Machine Learning model and the prediction form will be added in the next phase.

## Problem

Colombia loses natural forest every year, and the official IDEAM data are mostly published as reports and bulletins. BosqueIA aims to turn that data into a simple web tool that estimates the deforestation of a municipality from manually entered variables.

## Home page

The home page features an interactive, animated tree. Each branch opens a piece of the project: the problem, the general objective and the specific objectives. The text of each branch lives in `app.py` (the `PROJECT` dictionary).

## Technologies

- Python 3 and Flask
- Bootstrap 5 and Bootstrap Icons
- Vanilla JavaScript and an inline SVG for the tree
- Git and GitHub

## Run it locally

```bash
# 1. Create and activate the virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

## Structure

```
bosqueia/
├── app.py
├── requirements.txt
├── templates/
│   ├── base.html
│   └── index.html
└── static/
    └── css/
        └── style.css
```

## Authors

Iris Peñaloza, Julian Canchon and Scarlet Niño (Knowledge Managers).

## Data source

Instituto de Hidrología, Meteorología y Estudios Ambientales (IDEAM), Sistema de Monitoreo de Bosques y Carbono (SMByC).