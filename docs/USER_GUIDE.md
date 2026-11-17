# User guide

System: https://forest-awareness-4qpy.onrender.com/ (the free plan can take about a minute to wake up).

## For everyone (no account)

- **Home**: project documentation, key figures and links to the report, repository, guide and video.
- **Models**: how the three models were compared and which one was chosen, with a plain-language box under each result.

## Create an account and sign in

1. Open **Sign in** (top right) and choose the **Register** tab.
2. Pick your role: **Citizen** (open), or **Authority** / **Administrator** (they need the institutional access code that your organization gives you).
3. Enter your name, email and a password of at least 8 characters, and confirm it.
4. Return to the **Sign in** tab, choose the same role and sign in.

## Citizen

1. Open **Predict**.
2. Optionally choose a municipality to fill the form with its history and conditions, or type your own values: the hectares lost in the last three years and the current conditions.
3. Press **Forecast forest loss**.
4. Read the result: forecast in hectares with its range, alert level (Low, Moderate, High, Critical), probability of reaching the High level, change against last year, main drivers and advice.
5. Open **My history** in your user menu to see your previous forecasts or export them as CSV.

## Authority

Everything a citizen can do, plus:

- **Dashboard**: totals, forecasts by alert level, recent forecasts, K-Means risk profiles and the suggested allocation of 10 monitoring teams across 8 departments (Q-learning).
- **What-if scenario** on the Predict page: move the sliders (cattle, planted area, coca cultivation, unmet basic needs, armed groups) to test an intervention; the forecast is recalculated and the avoided hectares are shown.
- **History** with all users' forecasts.

## Administrator

Everything an authority can do, plus **Users** (create users, change roles, activate or disable accounts) and a **Retrain** button on the **Models** page that retrains the models with the current dataset.

## Good to know

- Forecasts beyond the first year are recursive, so their uncertainty grows.
- The data are simulated: use the results to understand how the system works, not as real predictions.
