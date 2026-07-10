from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_mail import Mail, Message
import sqlite3, os, json, requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = 'opptrack-secret-2025'

# ── Mail config (update with your SMTP) ──────────────────────────
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'
app.config['MAIL_DEFAULT_SENDER'] = 'OppTrack <your_email@gmail.com>'
mail = Mail(app)

DB = os.path.join(os.path.dirname(__file__), 'instance', 'opptrack.db')

# ─────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            class_year TEXT,
            stream TEXT,
            interests TEXT,
            alert_email INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            org TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            eligibility TEXT,
            reward TEXT,
            deadline TEXT,
            apply_link TEXT,
            class_filter TEXT,
            tags TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS saved (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            opp_id INTEGER,
            saved_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, opp_id)
        );

        CREATE TABLE IF NOT EXISTS alert_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            opp_id INTEGER,
            sent_at TEXT DEFAULT (datetime('now'))
        );
    ''')
    db.commit()
    _seed_sample_data(db)
    db.close()

def _seed_sample_data(db):
    count = db.execute('SELECT COUNT(*) FROM opportunities').fetchone()[0]
    if count > 0:
        return
    opps = [
        ('National Merit Scholarship 2025', 'Ministry of Education, India', 'Scholarship',
         'Top national scholarship for meritorious students based on Class 10 marks.',
         'Class 12 students with >80% in Class 10', '₹1,20,000/yr',
         (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
         'https://scholarships.gov.in', 'Class 12', 'Merit-based,Central Govt,Open now'),

        ('Google STEP Internship 2025', 'Google India, Bengaluru', 'Internship',
         'Software Engineering internship for 2nd and 3rd year CS students.',
         '2nd or 3rd year B.Tech/BE (CS/IT)', '₹80,000/month',
         (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
         'https://careers.google.com', '2nd Year,3rd Year', 'Tech,Paid,CS/IT'),

        ('Smart India Hackathon 2025', 'MoE, Govt of India', 'Hackathon',
         '36-hour national hackathon solving real government problem statements.',
         'All college students, team of 6', '₹1,00,000 prize',
         (datetime.now() + timedelta(days=18)).strftime('%Y-%m-%d'),
         'https://sih.gov.in', 'All', 'Team,National,36-hr'),

        ('NTSE Science Olympiad', 'NCERT, New Delhi', 'Competition',
         'National level talent search exam for Class 10 students.',
         'Class 10 students only', '₹50,000 + Certificate',
         (datetime.now() + timedelta(days=22)).strftime('%Y-%m-%d'),
         'https://ncert.nic.in', 'Class 10', 'Science,Individual'),

        ('Tata Trust UG Scholarship', 'Tata Trusts Foundation', 'Scholarship',
         'Need-based scholarship for first-year undergraduate students.',
         '1st Year UG, family income < ₹6 lakh/yr', '₹2,50,000/yr',
         (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
         'https://tatatrusts.org', '1st Year', 'Need-based,Private'),

        ('Microsoft Engage Mentorship', 'Microsoft India', 'Internship',
         'Paid mentorship program with a live project and Microsoft mentor.',
         'Pre-final year students', '₹50,000 stipend',
         (datetime.now() + timedelta(days=12)).strftime('%Y-%m-%d'),
         'https://microsoft.com/en-in/engage', '3rd Year', 'Tech,Mentorship,Paid'),

        ('IIT Bombay TechFest', 'IIT Bombay', 'Competition',
         'Asia\'s largest science & technology festival with 50+ competitions.',
         'All students', 'Prizes worth ₹1 Crore+',
         (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
         'https://techfest.org', 'All', 'Tech,Science,National'),

        ('Aicte Pragati Scholarship', 'AICTE', 'Scholarship',
         'Scholarship for girl students in AICTE-approved technical institutions.',
         'Girl students in B.Tech/BE/B.Arch, family income < ₹8 lakh', '₹50,000/yr',
         (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'),
         'https://aicte-india.org', '1st Year,2nd Year', 'Girl students,Technical,Govt'),
    ]
    db.executemany('''INSERT INTO opportunities
        (title, org, category, description, eligibility, reward, deadline, apply_link, class_filter, tags)
        VALUES (?,?,?,?,?,?,?,?,?,?)''', opps)
    db.commit()

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def days_left(deadline_str):
    try:
        d = datetime.strptime(deadline_str, '%Y-%m-%d')
        diff = (d - datetime.now()).days
        return diff
    except:
        return 999

def deadline_label(days):
    if days < 0:
        return 'Expired', 'expired'
    elif days <= 5:
        return f'{days} days left', 'hot'
    elif days <= 15:
        return f'{days} days left', 'warm'
    else:
        return f'{days} days left', 'cool'

# ─────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    cat    = request.args.get('cat', 'All')
    cls    = request.args.get('cls', 'All')
    search = request.args.get('q', '').strip()

    query  = 'SELECT * FROM opportunities WHERE is_active=1'
    params = []

    if cat != 'All':
        query += ' AND category=?'; params.append(cat)
    if cls != 'All':
        query += ' AND (class_filter LIKE ? OR class_filter="All")'; params.append(f'%{cls}%')
    if search:
        query += ' AND (title LIKE ? OR org LIKE ? OR tags LIKE ?)'; params += [f'%{search}%']*3

    query += ' ORDER BY deadline ASC'
    opps = db.execute(query, params).fetchall()

    counts = {r['category']: r['cnt'] for r in
              db.execute('SELECT category, COUNT(*) cnt FROM opportunities WHERE is_active=1 GROUP BY category').fetchall()}

    expiring = db.execute(
        "SELECT COUNT(*) cnt FROM opportunities WHERE is_active=1 AND deadline BETWEEN date('now') AND date('now','+7 days')"
    ).fetchone()['cnt']

    saved_ids = set()
    if 'user_id' in session:
        rows = db.execute('SELECT opp_id FROM saved WHERE user_id=?', (session['user_id'],)).fetchall()
        saved_ids = {r['opp_id'] for r in rows}

    # Attach computed fields
    enriched = []
    for o in opps:
        d = days_left(o['deadline'])
        label, urgency = deadline_label(d)
        enriched.append({**dict(o), 'days_left': d, 'deadline_label': label,
                         'urgency': urgency, 'is_saved': o['id'] in saved_ids,
                         'tags_list': o['tags'].split(',') if o['tags'] else []})

    db.close()
    return render_template('index.html',
        opps=enriched, counts=counts, expiring=expiring,
        active_cat=cat, active_cls=cls, search=search,
        categories=['All','Scholarship','Internship','Hackathon','Competition','Admission'],
        class_options=['All','Class 10','Class 11','Class 12','1st Year','2nd Year','3rd Year','Final Year'])

@app.route('/opp/<int:opp_id>')
def opp_detail(opp_id):
    db = get_db()
    opp = db.execute('SELECT * FROM opportunities WHERE id=?', (opp_id,)).fetchone()
    if not opp:
        db.close(); return redirect(url_for('index'))
    d = days_left(opp['deadline'])
    label, urgency = deadline_label(d)
    is_saved = False
    if 'user_id' in session:
        row = db.execute('SELECT 1 FROM saved WHERE user_id=? AND opp_id=?',
                         (session['user_id'], opp_id)).fetchone()
        is_saved = row is not None
    db.close()
    return render_template('detail.html', opp=dict(opp),
        deadline_label=label, urgency=urgency, is_saved=is_saved,
        tags_list=opp['tags'].split(',') if opp['tags'] else [])

@app.route('/save/<int:opp_id>', methods=['POST'])
def toggle_save(opp_id):
    if 'user_id' not in session:
        return jsonify({'status': 'login_required'})
    db = get_db()
    existing = db.execute('SELECT id FROM saved WHERE user_id=? AND opp_id=?',
                          (session['user_id'], opp_id)).fetchone()
    if existing:
        db.execute('DELETE FROM saved WHERE user_id=? AND opp_id=?', (session['user_id'], opp_id))
        saved = False
    else:
        db.execute('INSERT OR IGNORE INTO saved (user_id, opp_id) VALUES (?,?)',
                   (session['user_id'], opp_id))
        saved = True
    db.commit(); db.close()
    return jsonify({'status': 'ok', 'saved': saved})

@app.route('/saved')
def saved_opps():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    opps = db.execute('''SELECT o.* FROM opportunities o
                         JOIN saved s ON s.opp_id=o.id
                         WHERE s.user_id=? ORDER BY o.deadline ASC''',
                      (session['user_id'],)).fetchall()
    enriched = []
    for o in opps:
        d = days_left(o['deadline'])
        label, urgency = deadline_label(d)
        enriched.append({**dict(o), 'days_left': d, 'deadline_label': label,
                         'urgency': urgency, 'tags_list': o['tags'].split(',') if o['tags'] else []})
    db.close()
    return render_template('saved.html', opps=enriched)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name  = request.form['name'].strip()
        email = request.form['email'].strip()
        pwd   = request.form['password']
        cls   = request.form.get('class_year', '')
        stream= request.form.get('stream', '')
        interests = ','.join(request.form.getlist('interests'))
        db = get_db()
        try:
            db.execute('INSERT INTO users (name,email,password,class_year,stream,interests) VALUES (?,?,?,?,?,?)',
                       (name, email, pwd, cls, stream, interests))
            db.commit()
            flash('Account created! Please login.', 'success')
            db.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'danger')
            db.close()
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        pwd   = request.form['password']
        db    = get_db()
        user  = db.execute('SELECT * FROM users WHERE email=? AND password=?', (email, pwd)).fetchone()
        db.close()
        if user:
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/alerts', methods=['GET','POST'])
def alerts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        alert = 1 if request.form.get('alert_email') else 0
        db.execute('UPDATE users SET alert_email=? WHERE id=?', (alert, session['user_id']))
        db.commit()
        flash('Alert preferences saved.', 'success')
    user = db.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    db.close()
    return render_template('alerts.html', user=dict(user))

# ─────────────────────────────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────────────────────────────
@app.route('/admin')
def admin():
    db = get_db()
    opps = db.execute('SELECT * FROM opportunities ORDER BY created_at DESC').fetchall()
    db.close()
    return render_template('admin.html', opps=opps)

@app.route('/admin/add', methods=['GET','POST'])
def admin_add():
    if request.method == 'POST':
        f = request.form
        db = get_db()
        db.execute('''INSERT INTO opportunities
            (title,org,category,description,eligibility,reward,deadline,apply_link,class_filter,tags)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (f['title'], f['org'], f['category'], f['description'],
             f['eligibility'], f['reward'], f['deadline'], f['apply_link'],
             f['class_filter'], f['tags']))
        db.commit(); db.close()
        flash('Opportunity added!', 'success')
        return redirect(url_for('admin'))
    return render_template('admin_add.html')

@app.route('/admin/delete/<int:opp_id>', methods=['POST'])
def admin_delete(opp_id):
    db = get_db()
    db.execute('UPDATE opportunities SET is_active=0 WHERE id=?', (opp_id,))
    db.commit(); db.close()
    flash('Opportunity removed.', 'success')
    return redirect(url_for('admin'))

# ─────────────────────────────────────────────────────────────────
# EMAIL ALERTS (APScheduler runs daily at 8 AM)
# ─────────────────────────────────────────────────────────────────
def send_deadline_alerts():
    with app.app_context():
        db = get_db()
        users = db.execute('SELECT * FROM users WHERE alert_email=1').fetchall()
        for user in users:
            opps = db.execute(
                """SELECT o.* FROM opportunities o
                   LEFT JOIN alert_log al ON al.opp_id=o.id AND al.user_id=?
                   WHERE o.is_active=1
                   AND o.deadline BETWEEN date('now') AND date('now','+3 days')
                   AND al.id IS NULL""",
                (user['id'],)).fetchall()
            if not opps:
                continue
            try:
                msg = Message(f'OppTrack — {len(opps)} deadline(s) in 3 days!',
                              recipients=[user['email']])
                msg.html = _build_alert_email(user['name'], opps)
                mail.send(msg)
                for o in opps:
                    db.execute('INSERT INTO alert_log (user_id,opp_id) VALUES (?,?)',
                               (user['id'], o['id']))
            except Exception as e:
                print(f'Mail error for {user["email"]}: {e}')
        db.commit(); db.close()

def _build_alert_email(name, opps):
    rows = ''.join(f'<tr><td>{o["title"]}</td><td>{o["org"]}</td><td><b>{o["deadline"]}</b></td>'
                   f'<td><a href="{o["apply_link"]}">Apply</a></td></tr>' for o in opps)
    return f'''<h2>Hi {name},</h2>
<p>These opportunities are closing in 3 days:</p>
<table border="1" cellpadding="6" style="border-collapse:collapse">
<tr><th>Opportunity</th><th>Organisation</th><th>Deadline</th><th>Link</th></tr>
{rows}
</table>
<p>— OppTrack Team</p>'''

# ── DAILY AUTO-UPDATE SCHEDULER ──────────────────────────────
from updater import run_all_updates

def daily_update():
    with app.app_context():
        run_all_updates()

scheduler = BackgroundScheduler()
scheduler.add_job(send_deadline_alerts, 'cron', hour=8,  minute=0)   # email alerts 8am
scheduler.add_job(daily_update,         'cron', hour=0,  minute=30)  # full update 12:30am
scheduler.start()

# ─────────────────────────────────────────────────────────────────
COUNSELLINGS = {
    'josaa': {
        'id': 'josaa',
        'name': 'JoSAA',
        'full': 'Joint Seat Allocation Authority',
        'icon': '🏫',
        'color': 'rgba(0,212,255,.12)',
        'conducting': 'Ministry of Education, Govt. of India',
        'seats': '~50,000+ seats across IITs, NITs, IIITs, GFTIs',
        'eligibility': 'JEE Main / JEE Advanced qualified candidates',
        'website': 'https://josaa.nic.in',
        'reg_status': 'open',
        'reg_note': 'Registration open along with Round 1 choice filling',
        'reg_deadline': 'Jun 19, 2026',
        'extended': False,
        'results_out': False,
        'result_note': 'Round 1 seat allotment on Jun 20, 2026',
        'helpline': '1800-11-2199',
        'summary': 'JoSAA conducts the joint seat allocation for IITs (via JEE Advanced rank), NITs, IIITs and Government Funded Technical Institutes (via JEE Main rank). It runs 6 rounds of seat allocation. Missing even one round means losing your seat permanently — so track every round deadline.',
        'important_warning': 'If you are allotted a seat and do NOT report/pay within the deadline, your seat is CANCELLED and you cannot participate in further rounds.',
        'rounds': [
            {'num': 1, 'reg': 'Jun 17–19, 2026', 'allot': 'Jun 20, 2026', 'accept': 'Jun 20–22, 2026', 'status': 'active'},
            {'num': 2, 'reg': 'Jun 22–24, 2026', 'allot': 'Jun 25, 2026', 'accept': 'Jun 25–27, 2026', 'status': 'next'},
            {'num': 3, 'reg': 'Jun 27–29, 2026', 'allot': 'Jun 30, 2026', 'accept': 'Jun 30 – Jul 2, 2026', 'status': 'future'},
            {'num': 4, 'reg': 'Jul 2–4, 2026',   'allot': 'Jul 5, 2026',  'accept': 'Jul 5–7, 2026', 'status': 'future'},
            {'num': 5, 'reg': 'Jul 6–8, 2026',   'allot': 'Jul 9, 2026',  'accept': 'Jul 9–11, 2026', 'status': 'future'},
            {'num': 6, 'reg': 'Jul 10–12, 2026', 'allot': 'Jul 13, 2026', 'accept': 'Jul 13–15, 2026','status': 'future'},
        ],
        'docs': ['JEE Admit Card','Class 10 Certificate','Class 12 Marksheet','Category Certificate (if applicable)','ID Proof (Aadhaar)','Passport Photo','OCI/PIO Card (if applicable)'],
        'tips': [
            'Fill choices in DECREASING order of preference — your top choice first.',
            'Lock your choices before the deadline. Unlocked choices are NOT considered.',
            'After allotment, pay the seat acceptance fee within 24 hours or lose the seat.',
            'You can upgrade your seat in later rounds even after accepting in Round 1.',
            'Keep scanned copies of ALL documents ready before Round 1 starts.',
        ],
    },
    'mcc-neet': {
        'id': 'mcc-neet',
        'name': 'MCC NEET UG',
        'full': 'Medical Counselling Committee — MBBS/BDS Admissions',
        'icon': '🏥',
        'color': 'rgba(0,255,136,.10)',
        'conducting': 'Medical Counselling Committee (MCC), MoHFW',
        'seats': '~1.08 Lakh MBBS + BDS seats — 15% All India Quota',
        'eligibility': 'NEET UG qualified; 15% AIQ (all states except J&K)',
        'website': 'https://mcc.nic.in',
        'reg_status': 'soon',
        'reg_note': 'Registration opens approximately 2 weeks after NEET result',
        'reg_deadline': 'Jul 21, 2026 (estimated)',
        'extended': True,
        'result_note': 'Allotment results declared after each round',
        'results_out': False,
        'helpline': '1800-11-1454',
        'summary': 'MCC conducts counselling for the 15% All India Quota (AIQ) seats in Government medical colleges across India, plus 100% seats in Deemed/Central Universities. NEET UG rank determines your eligibility. There are typically 2 main rounds + 1 Mop-Up + Stray Vacancy round.',
        'important_warning': 'State quota seats (85%) are handled by individual state counselling bodies — check your state separately. MCC only covers AIQ + Deemed/Central University seats.',
        'rounds': [
            {'num': 1, 'reg': 'Jul 14–17, 2026', 'allot': 'Jul 21, 2026', 'accept': 'Jul 21–28, 2026', 'status': 'future'},
            {'num': 2, 'reg': 'Aug 1–4, 2026',   'allot': 'Aug 8, 2026',  'accept': 'Aug 8–15, 2026', 'status': 'future'},
            {'num': 'Mop-Up', 'reg': 'Aug 20–22, 2026', 'allot': 'Aug 27, 2026', 'accept': 'Aug 27 – Sep 3, 2026', 'status': 'future'},
            {'num': 'Stray Vacancy', 'reg': 'Sep 5–7, 2026', 'allot': 'Sep 10, 2026', 'accept': 'Sep 10–12, 2026', 'status': 'future'},
        ],
        'docs': ['NEET Admit Card','NEET Result/Scorecard','Class 10 Certificate','Class 12 Marksheet','Category Certificate (SC/ST/OBC/EWS)','ID Proof','Passport Photo','OBC NCL Certificate (if applicable)','PwD Certificate (if applicable)'],
        'tips': [
            'Register on MCC portal as soon as it opens — seats fill up fast.',
            'Fill ALL valid choices. Do not leave fields blank hoping for better — always fill a backup.',
            'Mop-Up round is your LAST chance if you miss Round 1 & 2.',
            'Stray Vacancy round is only for specific unfilled seats — very limited.',
            'Check your state counselling separately for 85% state quota seats.',
        ],
    },
    'jac-delhi': {
        'id': 'jac-delhi',
        'name': 'JAC Delhi',
        'full': 'Joint Admission Counselling — Delhi Engineering Colleges',
        'icon': '🔬',
        'color': 'rgba(191,95,255,.12)',
        'conducting': 'Guru Gobind Singh Indraprastha University (GGSIPU)',
        'seats': '~10,000+ seats across 28 engineering colleges in Delhi',
        'eligibility': 'JEE Main qualified; Delhi domicile preferred for state quota',
        'website': 'https://jacdelhi.admissions.nic.in',
        'reg_status': 'soon',
        'reg_note': 'Registration expected to open after JEE Main results',
        'reg_deadline': 'Jul 1, 2026 (estimated)',
        'extended': False,
        'results_out': False,
        'result_note': 'Round 1 allotment expected Jul 4, 2026',
        'helpline': '011-25302170',
        'summary': 'JAC Delhi conducts joint counselling for B.Tech/B.Arch admissions across DTU, NSIT, IGDTUW, IIIT Delhi and affiliated colleges. Seats are divided between Delhi domicile and outside Delhi candidates. JEE Main score is the primary criteria.',
        'important_warning': 'Delhi domicile candidates get a separate merit list with more seats. Ensure your domicile certificate is ready before registration.',
        'rounds': [
            {'num': 1, 'reg': 'Jun 25 – Jul 1, 2026', 'allot': 'Jul 4, 2026', 'accept': 'Jul 4–8, 2026', 'status': 'next'},
            {'num': 2, 'reg': 'Jul 8–12, 2026', 'allot': 'Jul 15, 2026', 'accept': 'Jul 15–18, 2026', 'status': 'future'},
            {'num': 3, 'reg': 'Jul 19–22, 2026', 'allot': 'Jul 25, 2026', 'accept': 'Jul 25–28, 2026', 'status': 'future'},
        ],
        'docs': ['JEE Main Admit Card','JEE Main Scorecard','Class 10 Certificate','Class 12 Marksheet','Delhi Domicile Certificate','Category Certificate','ID Proof (Aadhaar)','Passport Photo'],
        'tips': [
            'Fill choices for ALL colleges you are willing to attend — don\'t be picky early.',
            'Delhi domicile certificate must be issued by SDM/Tehsildar — get it early.',
            'IIIT Delhi has a separate admission process — check their website too.',
            'Round 3 is usually for leftover/surrendered seats — very limited options.',
            'Document verification is in-person — be ready to visit the allotted college.',
        ],
    },
    'du-csas': {
        'id': 'du-csas',
        'name': 'DU CSAS',
        'full': 'Delhi University — Common Seat Allocation System',
        'icon': '🏛️',
        'color': 'rgba(255,184,0,.10)',
        'conducting': 'University of Delhi',
        'seats': '70,000+ UG seats across 90 colleges',
        'eligibility': 'CUET UG score; Class 12 from any recognised board',
        'website': 'https://ugadmission.uod.ac.in',
        'reg_status': 'open',
        'reg_note': 'Registration currently open — apply now',
        'reg_deadline': 'Jun 30, 2026',
        'extended': False,
        'results_out': False,
        'result_note': 'Merit List 1 expected Jul 10, 2026',
        'helpline': '011-27667011',
        'summary': 'Delhi University uses CUET UG scores for all UG admissions through the CSAS portal. You can apply to multiple programmes and colleges. DU releases 3 merit lists — if you miss accepting in ML1, you can still get a seat in ML2 or ML3, but choices reduce each time.',
        'important_warning': 'Acceptance deadline after each merit list is typically just 2-3 days. Missing it means you move to the next list with fewer options.',
        'rounds': [
            {'num': 'Merit List 1', 'reg': 'Registration by Jun 30', 'allot': 'Jul 10, 2026', 'accept': 'Jul 10–13, 2026', 'status': 'next'},
            {'num': 'Merit List 2', 'reg': 'Auto-considered', 'allot': 'Jul 20, 2026', 'accept': 'Jul 20–23, 2026', 'status': 'future'},
            {'num': 'Merit List 3', 'reg': 'Auto-considered', 'allot': 'Jul 30, 2026', 'accept': 'Jul 30 – Aug 2, 2026', 'status': 'future'},
            {'num': 'Spot Round', 'reg': 'Walk-in only', 'allot': 'Aug 10, 2026', 'accept': 'Aug 10, 2026', 'status': 'future'},
        ],
        'docs': ['CUET Scorecard','Class 10 Certificate','Class 12 Marksheet','Category Certificate (if applicable)','EWS Certificate','PwBD Certificate (if applicable)','ID Proof','Passport Photo'],
        'tips': [
            'Apply to as many programmes and colleges as possible — no extra fee.',
            'CUET score is the ONLY criteria — Class 12 % does not matter for DU.',
            'Accept your best allotted seat quickly — the acceptance window is only 2-3 days.',
            'You can upgrade in later merit lists even after accepting in ML1.',
            'Sports/ECA quota has a separate process — apply separately if eligible.',
        ],
    },
    'clat': {
        'id': 'clat',
        'name': 'CLAT Counselling',
        'full': 'NLU Admissions — CLAT Consortium of NLUs',
        'icon': '⚖️',
        'color': 'rgba(255,110,180,.10)',
        'conducting': 'Consortium of National Law Universities',
        'seats': '~3,500+ BA LLB / LLM seats across 24 NLUs',
        'eligibility': 'CLAT qualified; 45% in Class 12 (40% for SC/ST)',
        'website': 'https://consortiumofnlus.ac.in',
        'reg_status': 'soon',
        'reg_note': 'Counselling registration opens after CLAT result',
        'reg_deadline': 'Jun 15, 2026 (estimated)',
        'extended': False,
        'results_out': False,
        'result_note': 'Round 1 allotment expected Jun 10, 2026',
        'helpline': 'consortium@nluodisha.ac.in',
        'summary': 'CLAT Consortium conducts centralized counselling for all 24 National Law Universities (NLUs). NLSIU Bangalore, NALSAR Hyderabad, WBNUJS Kolkata are among the top NLUs. Seat allotment is based purely on CLAT rank and your choice preferences.',
        'important_warning': 'NLU Delhi (NLU D) has its own entrance exam AILET — it does NOT participate in CLAT counselling.',
        'rounds': [
            {'num': 1, 'reg': 'Jun 5–10, 2026', 'allot': 'Jun 10, 2026', 'accept': 'Jun 10–15, 2026', 'status': 'next'},
            {'num': 2, 'reg': 'Jun 18–22, 2026', 'allot': 'Jun 25, 2026', 'accept': 'Jun 25 – Jul 1, 2026', 'status': 'future'},
            {'num': 'Mop-Up', 'reg': 'Jul 5–8, 2026', 'allot': 'Jul 10, 2026', 'accept': 'Jul 10–14, 2026', 'status': 'future'},
        ],
        'docs': ['CLAT Scorecard','CLAT Admit Card','Class 10 Certificate','Class 12 Marksheet','Category Certificate','Domicile Certificate','ID Proof','Passport Photo'],
        'tips': [
            'Fill all 24 NLUs as choices — rank them carefully by preference.',
            'NLU Delhi is NOT part of CLAT — apply separately via AILET.',
            'Domicile quota exists in some NLUs — check individual NLU rules.',
            'You must pay counselling registration fee online before filling choices.',
            'Keep original documents ready for verification at the allotted NLU.',
        ],
    },
    'maharashtra-cap': {
        'id': 'maharashtra-cap',
        'name': 'Maharashtra CAP',
        'full': 'MHT CET Engineering — Centralised Admission Process',
        'icon': '🔧',
        'color': 'rgba(255,77,109,.10)',
        'conducting': 'State CET Cell, Maharashtra',
        'seats': '~1.5 Lakh+ Engineering seats across Maharashtra',
        'eligibility': 'MHT CET / JEE Main qualified; Maharashtra domicile or J&K migrant',
        'website': 'https://cetcell.mahacet.org',
        'reg_status': 'soon',
        'reg_note': 'CAP registration expected after MHT CET results',
        'reg_deadline': 'Jul 10, 2026 (estimated)',
        'extended': True,
        'results_out': False,
        'result_note': 'CAP Round 1 allotment expected Jul 15, 2026',
        'helpline': '1800-223-131',
        'summary': 'Maharashtra State CET Cell conducts CAP (Centralised Admission Process) for B.Tech/B.E admissions across government, aided and unaided engineering colleges in Maharashtra. Both MHT CET and JEE Main scores are accepted. There are 3 CAP rounds.',
        'important_warning': 'Maharashtra domicile is mandatory for most reserved category seats. Candidates without domicile can only apply for open category seats.',
        'rounds': [
            {'num': 1, 'reg': 'Jul 5–10, 2026', 'allot': 'Jul 15, 2026', 'accept': 'Jul 15–20, 2026', 'status': 'future'},
            {'num': 2, 'reg': 'Jul 22–25, 2026', 'allot': 'Jul 28, 2026', 'accept': 'Jul 28 – Aug 2, 2026', 'status': 'future'},
            {'num': 3, 'reg': 'Aug 5–8, 2026', 'allot': 'Aug 10, 2026', 'accept': 'Aug 10–14, 2026', 'status': 'future'},
        ],
        'docs': ['MHT CET / JEE Main Scorecard','Class 10 Certificate','Class 12 Marksheet','Maharashtra Domicile Certificate','Category Certificate','Non-Creamy Layer Certificate','Income Certificate','ID Proof','Passport Photo'],
        'tips': [
            'Verify your category certificate is valid and updated before applying.',
            'Use the MHT CET percentile OR JEE Main percentile — whichever is higher.',
            'Fill choices for both Mumbai and outstation colleges for more options.',
            'Institute preference matters more than branch for top colleges.',
            'Autonomy status of college affects curriculum — research before choosing.',
        ],
    },
    'josaa-nit': {
        'id': 'josaa-nit',
        'name': 'JoSAA NIT/IIIT',
        'full': 'NITs, IIITs & GFTIs via JoSAA',
        'icon': '⚙️',
        'color': 'rgba(0,255,136,.10)',
        'conducting': 'Joint Seat Allocation Authority (JoSAA)',
        'seats': '~35,000+ seats across 31 NITs, 26 IIITs, 33 GFTIs',
        'eligibility': 'JEE Main qualified (Paper 1); 75% in Class 12 or top 20 percentile',
        'website': 'https://josaa.nic.in',
        'reg_status': 'open',
        'reg_note': 'Same portal as JoSAA IIT — register together',
        'reg_deadline': 'Jun 19, 2026',
        'extended': False,
        'results_out': False,
        'result_note': 'Round 1 allotment Jun 20, 2026',
        'helpline': '1800-11-2199',
        'summary': 'NITs, IIITs and GFTIs are allocated through the same JoSAA portal as IITs. JEE Main rank (CRL) determines NIT/IIIT/GFTI eligibility. Home State quota (50% seats) gives preference to candidates from the state where the NIT is located.',
        'important_warning': 'You need 75% in Class 12 (or top 20 percentile of your board) to be eligible for NITs/IIITs. Without this, your seat allotment will be cancelled at document verification.',
        'rounds': [
            {'num': 1, 'reg': 'Jun 17–19, 2026', 'allot': 'Jun 20, 2026', 'accept': 'Jun 20–22, 2026', 'status': 'active'},
            {'num': 2, 'reg': 'Jun 22–24, 2026', 'allot': 'Jun 25, 2026', 'accept': 'Jun 25–27, 2026', 'status': 'next'},
            {'num': 3, 'reg': 'Jun 27–29, 2026', 'allot': 'Jun 30, 2026', 'accept': 'Jun 30 – Jul 2, 2026', 'status': 'future'},
            {'num': 4, 'reg': 'Jul 2–4, 2026', 'allot': 'Jul 5, 2026', 'accept': 'Jul 5–7, 2026', 'status': 'future'},
            {'num': 5, 'reg': 'Jul 6–8, 2026', 'allot': 'Jul 9, 2026', 'accept': 'Jul 9–11, 2026', 'status': 'future'},
        ],
        'docs': ['JEE Main Scorecard','Class 10 Certificate','Class 12 Marksheet (with 75%+ or top 20 percentile proof)','Category Certificate','PwD Certificate (if applicable)','Home State Domicile (for state quota)','ID Proof','Passport Photo'],
        'tips': [
            'Home State quota (HS) gives you an advantage in the NIT of your home state.',
            'Verify your Class 12 % crosses 75% — this is strictly checked.',
            'NIT Trichy, NIT Warangal, NIT Surathkal are top-ranked — fill these early.',
            'Branch matters more than college for placement in many cases — research.',
            'You can fill both IIT and NIT/IIIT choices in the same JoSAA form.',
        ],
    },
    'mcc-pg': {
        'id': 'mcc-pg',
        'name': 'MCC PG (NEET PG)',
        'full': 'PG Medical Admissions — MD/MS/Diploma',
        'icon': '👨‍⚕️',
        'color': 'rgba(0,212,255,.10)',
        'conducting': 'Medical Counselling Committee (MCC), MoHFW',
        'seats': '~6,000+ PG medical seats (AIQ 50%)',
        'eligibility': 'NEET PG qualified; MBBS with 1 year internship completed',
        'website': 'https://mcc.nic.in',
        'reg_status': 'soon',
        'reg_note': 'Registration opens after NEET PG result 2026',
        'reg_deadline': 'Aug 2026 (estimated)',
        'extended': False,
        'results_out': False,
        'result_note': 'Expected allotment Aug–Sep 2026',
        'helpline': '1800-11-1454',
        'summary': 'MCC PG conducts counselling for 50% All India Quota seats in MD/MS/PG Diploma programmes across government medical colleges. NEET PG rank is the sole criteria. The remaining 50% state quota seats are managed by individual state counselling bodies.',
        'important_warning': 'Internship completion certificate is mandatory. Without it, your allotment is cancelled even if you have a rank.',
        'rounds': [
            {'num': 1, 'reg': 'Aug 1–5, 2026', 'allot': 'Aug 12, 2026', 'accept': 'Aug 12–18, 2026', 'status': 'future'},
            {'num': 2, 'reg': 'Sep 1–5, 2026', 'allot': 'Sep 12, 2026', 'accept': 'Sep 12–18, 2026', 'status': 'future'},
            {'num': 'Mop-Up', 'reg': 'Oct 1–4, 2026', 'allot': 'Oct 10, 2026', 'accept': 'Oct 10–14, 2026', 'status': 'future'},
        ],
        'docs': ['NEET PG Scorecard','MBBS Certificate','Internship Completion Certificate','Attempt Certificate','Registration Certificate (MCI/NMC)','Category Certificate','ID Proof','Passport Photo'],
        'tips': [
            'Internship certificate must be obtained BEFORE registration opens.',
            'Fill ALL specialty choices across all colleges — not just top ones.',
            'State quota 50% seats are separate — register with your state too.',
            'MD vs MS vs Diploma — rank required varies greatly; research cut-offs.',
            'Bond/service obligation exists in some states for govt college seats.',
        ],
    },
}

@app.route('/counselling')
def counselling_list():
    return render_template('counselling_list.html', counsellings=COUNSELLINGS.values())

@app.route('/counselling/<cid>')
def counselling_detail(cid):
    c = COUNSELLINGS.get(cid)
    if not c:
        return redirect(url_for('index'))
    return render_template('counselling_detail.html', c=c)

if __name__ == '__main__':
    os.makedirs('instance', exist_ok=True)
    init_db()
    app.run(debug=True, port=5050)

# ─────────────────────────────────────────────────────────────────
# COUNSELLING DETAIL DATA & ROUTES
# ─────────────────────────────────────────────────────────────────
