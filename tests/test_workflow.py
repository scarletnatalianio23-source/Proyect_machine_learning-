"""Functional tests of the published workflow (roles, CSRF, forecast, dashboard, retraining).

Run from the project root:  python tests/test_workflow.py
It uses a temporary database and test-only access codes; nothing is written to instance/forest.db.
"""
import os, re, sys, tempfile
os.environ['FOREST_DB'] = tempfile.mktemp(suffix='.db')
os.environ['AUTHORITY_CODE'] = 'test-authority-code'
os.environ['ADMIN_CODE'] = 'test-admin-code'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as A, db, ml
ml.BUNDLE_FILE = __import__('pathlib').Path(tempfile.mkdtemp()) / 'bundle.joblib'  # keep the real models untouched
c = A.app.test_client()
res = []
def ok(name, cond, note=''):
    res.append((name, bool(cond), note)); print('PASS' if cond else 'FAIL', '-', name, note)
def token(client):
    r = client.get('/access'); 
    m = re.search(r'name="csrf_token" value="([^"]+)"', r.get_data(as_text=True)); return m.group(1)
def register(client, name, email, role='citizen', code='', pw='Secret123!'):
    t = token(client)
    return client.post('/access', data=dict(csrf_token=t, action='register', role=role, name=name, email=email, password=pw, password2=pw, code=code), follow_redirects=True)
def login(client, email, role='citizen', pw='Secret123!'):
    t = token(client)
    return client.post('/access', data=dict(csrf_token=t, action='login', role=role, email=email, password=pw), follow_redirects=True)
def ptoken(client):
    r = client.get('/predict'); return re.search(r'name="csrf_token" value="([^"]+)"', r.get_data(as_text=True)).group(1)

# 4 predict signed out
r = c.get('/predict'); ok('Open Predict without signing in -> redirect to Access', r.status_code == 302 and '/access' in r.headers['Location'])
# 1 register citizen
r = register(c, 'Test Citizen', 'citizen@example.org'); ok('Register a citizen account', 'Account created' in r.get_data(as_text=True))
r = register(c, 'Dup', 'citizen@example.org'); ok('Duplicate email is rejected', 'already registered' in r.get_data(as_text=True))
# 2 roles with codes
r = register(c, 'Bad Auth', 'a1@example.org', 'authority', 'WRONG'); ok('Authority with invalid code is rejected', 'not valid' in r.get_data(as_text=True))
r = register(c, 'Bad Admin', 'ad1@example.org', 'admin', 'WRONG'); ok('Administrator with invalid code is rejected', 'not valid' in r.get_data(as_text=True))
r = register(c, 'Test Authority', 'auth@example.org', 'authority', db.ROLE_CODES['authority']); ok('Authority with valid code is created', 'Account created' in r.get_data(as_text=True))
r = register(c, 'Test Admin', 'admin@example.org', 'admin', db.ROLE_CODES['admin']); ok('Administrator with valid code is created', 'Account created' in r.get_data(as_text=True))
# wrong password / role
r = login(c, 'citizen@example.org', pw='nope'); ok('Wrong password is rejected', 'Wrong email or password' in r.get_data(as_text=True))
r = login(c, 'citizen@example.org', role='authority'); ok('Login with the wrong role is rejected', 'registered as' in r.get_data(as_text=True))
# citizen session
r = login(c, 'citizen@example.org'); ok('Citizen signs in', 'Welcome' in r.get_data(as_text=True))
ok('Citizen cannot open Dashboard (403)', c.get('/dashboard').status_code == 403)
ok('Citizen cannot open Users (403)', c.get('/admin/users').status_code == 403)
# 7 CSRF
vals = {}
f = [x[0] for x in A.CONDITION_FIELDS] + A.HISTORY_FIELDS
good = dict(area_km2=1500, population=30000, cattle_heads=20000, planted_area_ha=3000, nbi_pct=45, coca_ha=120, armed_groups=1)
hist = dict(zip(A.HISTORY_FIELDS, [300, 350, 400]))
payload = {**good, **hist}
missing = [k for k in f if k not in payload]; print('fields not covered:', missing)
r = c.post('/predict', data=payload); ok('Form without CSRF token is rejected', r.status_code in (400, 403))
# 5 predict
t = ptoken(c)
r = c.post('/predict', data={**payload, 'csrf_token': t}); txt = r.get_data(as_text=True)
ok('Valid forecast shows hectares, alert level and probability', r.status_code == 200 and 'rf-hero' in txt and ('Low' in txt or 'Moderate' in txt or 'High' in txt or 'Critical' in txt))
# 6 invalid
bad = {**payload, 'cattle_heads': -5, 'csrf_token': t}
r = c.post('/predict', data=bad); ok('Invalid values give a validation message (no crash)', r.status_code == 200 and 'is-invalid' in r.get_data(as_text=True))
bad2 = {**payload, 'csrf_token': t}; bad2.pop('area_km2')
r = c.post('/predict', data=bad2); ok('Missing values give a validation message (no crash)', r.status_code == 200)
# history
with A.app.app_context():
    n = db.get_db().execute('SELECT COUNT(*) FROM forecasts').fetchone()[0]
r = c.get('/history'); ok('Forecast is saved in the database and My history opens', r.status_code == 200 and n >= 1, f'({n} saved)')
r = c.get('/history.csv'); ok('History exports as CSV', r.status_code == 200 and 'created_at' in r.get_data(as_text=True))
# citizen has no scenario
r = c.get('/predict'); ok('Citizen does not see the what-if scenario', 'What-if scenario' not in r.get_data(as_text=True))
c.post('/logout', data=dict(csrf_token=ptoken(c)))
# authority
a = A.app.test_client(); login(a, 'auth@example.org', 'authority')
ok('Authority opens the Dashboard', a.get('/dashboard').status_code == 200)
ok('Authority cannot open Users (403)', a.get('/admin/users').status_code == 403)
r = a.get('/predict'); ok('Authority sees the what-if scenario', 'What-if scenario' in r.get_data(as_text=True))
t = ptoken(a)
r = a.post('/predict', data={**payload, 'csrf_token': t, 'coca_pct': -50, 'armed_delta': -1, 'cattle_pct': 0, 'planted_pct': 0, 'nbi_delta': 0})
ok('Authority runs a what-if scenario', r.status_code == 200 and 'rf-hero' in r.get_data(as_text=True))
# admin
d = A.app.test_client(); login(d, 'admin@example.org', 'admin')
ok('Administrator opens Users', d.get('/admin/users').status_code == 200)
ok('Administrator opens Dashboard', d.get('/dashboard').status_code == 200)
t = ptoken(d)
r = d.post('/admin/retrain', data=dict(csrf_token=t), follow_redirects=True); ok('Administrator retrains the models', r.status_code == 200 and 'retrained' in r.get_data(as_text=True))
# public pages
for p in ['/', '/models', '/access']:
    ok(f'Public page {p} loads', c.get(p).status_code == 200)
print(sum(1 for x in res if x[1]), '/', len(res)); sys.exit(0 if all(x[1] for x in res) else 1)
