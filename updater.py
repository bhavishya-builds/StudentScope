"""
updater.py — OppTrack Auto-Update Engine
Runs daily at midnight. Scrapes/checks real sources and updates the DB.
Also auto-updates exam dot statuses based on today's date.
"""

import sqlite3, os, datetime, requests
from datetime import date

DB = os.path.join(os.path.dirname(__file__), 'instance', 'opptrack.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ─── 1. AUTO-STATUS: mark expired opportunities ───────────────────────────────
def auto_expire_opportunities():
    db = get_db()
    expired = db.execute(
        "UPDATE opportunities SET is_active=0 WHERE deadline < date('now') AND is_active=1"
    ).rowcount
    db.commit()
    db.close()
    if expired:
        print(f"[Updater] Auto-expired {expired} past-deadline opportunities")

# ─── 2. EXAM DOT STATUS: recalculate based on today ──────────────────────────
def days_from_now(date_str):
    """Parse a YYYY-MM-DD string and return days from today."""
    try:
        d = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        return (d - date.today()).days
    except:
        return 999

def smart_status(deadline_str):
    d = days_from_now(deadline_str)
    if d < 0:    return 'done'
    if d <= 5:   return 'next'
    if d <= 25:  return 'soon'
    return 'future'

# ─── 3. SCRAPE NEW OPPORTUNITIES from free public APIs ───────────────────────
SOURCES = [
    # Internshala RSS-style (public endpoint)
    {
        'name': 'Unstop Hackathons',
        'url': 'https://unstop.com/api/public/opportunity/search-new?opportunity=hackathon&per_page=5&oppstatus=open',
        'type': 'json',
        'parser': 'unstop',
        'category': 'Hackathon',
    },
    # DevFolio hackathons (public API)
    {
        'name': 'Devfolio Hackathons',
        'url': 'https://devfolio.co/api/hackathons/?offset=0&limit=5&filter=open',
        'type': 'json',
        'parser': 'devfolio',
        'category': 'Hackathon',
    },
]

def parse_unstop(data, category):
    """Parse Unstop API response into opportunity dicts."""
    opps = []
    try:
        items = data.get('data', {}).get('data', [])
        for item in items[:5]:
            title = item.get('title', '')
            org   = item.get('organisation', {}).get('name', 'Unknown')
            link  = f"https://unstop.com/{item.get('public_url','')}"
            dl    = item.get('end_date', '')[:10] if item.get('end_date') else ''
            reward = item.get('prizes_text', '') or 'Check website'
            if title and dl:
                opps.append({
                    'title': title[:120],
                    'org': org[:80],
                    'category': category,
                    'description': item.get('description', '')[:300],
                    'eligibility': 'Open to all students',
                    'reward': reward[:80],
                    'deadline': dl,
                    'apply_link': link,
                    'class_filter': 'All',
                    'tags': 'Unstop,Live,Auto-updated',
                })
    except Exception as e:
        print(f"[Updater] Unstop parse error: {e}")
    return opps

def parse_devfolio(data, category):
    """Parse Devfolio API response."""
    opps = []
    try:
        items = data.get('results', [])
        for item in items[:5]:
            title = item.get('name', '')
            org   = item.get('organization_name', '') or 'Devfolio'
            link  = f"https://devfolio.co/hackathons/{item.get('slug','')}"
            dl    = (item.get('ends_at') or '')[:10]
            if title and dl:
                opps.append({
                    'title': title[:120],
                    'org': org[:80],
                    'category': category,
                    'description': item.get('description', '')[:300],
                    'eligibility': 'Open to all developers',
                    'reward': 'Check website',
                    'deadline': dl,
                    'apply_link': link,
                    'class_filter': 'All',
                    'tags': 'Devfolio,Live,Hackathon',
                })
    except Exception as e:
        print(f"[Updater] Devfolio parse error: {e}")
    return opps

PARSERS = {'unstop': parse_unstop, 'devfolio': parse_devfolio}

def scrape_and_insert():
    """Fetch from public APIs and insert new opportunities."""
    db = get_db()
    added = 0
    for src in SOURCES:
        try:
            resp = requests.get(src['url'], timeout=8,
                headers={'User-Agent': 'OppTrack/1.0 (student opportunity aggregator)'})
            if resp.status_code != 200:
                print(f"[Updater] {src['name']}: HTTP {resp.status_code}")
                continue
            data = resp.json()
            parser = PARSERS.get(src['parser'])
            if not parser:
                continue
            opps = parser(data, src['category'])
            for o in opps:
                # Only insert if not already present (match by title+org)
                exists = db.execute(
                    'SELECT id FROM opportunities WHERE title=? AND org=?',
                    (o['title'], o['org'])
                ).fetchone()
                if not exists and o['deadline'] >= str(date.today()):
                    db.execute('''INSERT INTO opportunities
                        (title,org,category,description,eligibility,reward,
                         deadline,apply_link,class_filter,tags,is_active)
                        VALUES (?,?,?,?,?,?,?,?,?,?,1)''',
                        (o['title'], o['org'], o['category'], o['description'],
                         o['eligibility'], o['reward'], o['deadline'],
                         o['apply_link'], o['class_filter'], o['tags']))
                    added += 1
        except requests.Timeout:
            print(f"[Updater] {src['name']}: timeout")
        except Exception as e:
            print(f"[Updater] {src['name']}: {e}")
    if added:
        db.commit()
        print(f"[Updater] Added {added} new opportunities from live sources")
    db.close()
    return added

# ─── 4. SCHOLARSHIP REMINDERS from NSP (National Scholarship Portal) ─────────
NSP_SCHOLARSHIPS = [
    {'title': 'PM Scholarship Scheme (PMSS) 2025-26', 'org': 'Ministry of Education',
     'deadline': '2026-10-31', 'link': 'https://scholarships.gov.in', 'reward': '₹25,000/yr'},
    {'title': 'Central Sector Scholarship (CSSS)', 'org': 'Dept. of Higher Education',
     'deadline': '2026-10-31', 'link': 'https://scholarships.gov.in', 'reward': '₹12,000/yr'},
    {'title': 'Post Matric Scholarship (SC/ST/OBC)', 'org': 'Ministry of Social Justice',
     'deadline': '2026-11-30', 'link': 'https://scholarships.gov.in', 'reward': 'Variable'},
    {'title': 'National Means cum Merit Scholarship (NMMS)', 'org': 'Ministry of Education',
     'deadline': '2026-09-30', 'link': 'https://scholarships.gov.in', 'reward': '₹12,000/yr'},
    {'title': 'Inspire Scholarship (DST)', 'org': 'Dept. of Science & Technology',
     'deadline': '2026-10-31', 'link': 'https://online-inspire.gov.in', 'reward': '₹80,000/yr'},
]

def seed_nsp_scholarships():
    """Insert curated NSP scholarships if not already present."""
    db = get_db()
    added = 0
    for s in NSP_SCHOLARSHIPS:
        if s['deadline'] < str(date.today()):
            continue
        exists = db.execute('SELECT id FROM opportunities WHERE title=?', (s['title'],)).fetchone()
        if not exists:
            db.execute('''INSERT INTO opportunities
                (title,org,category,description,eligibility,reward,
                 deadline,apply_link,class_filter,tags,is_active)
                VALUES (?,?,?,?,?,?,?,?,?,?,1)''',
                (s['title'], s['org'], 'Scholarship',
                 'Government scholarship via National Scholarship Portal.',
                 'Indian students; check NSP portal for eligibility',
                 s['reward'], s['deadline'], s['link'], 'All',
                 'Govt,NSP,Scholarship'))
            added += 1
    if added:
        db.commit()
        print(f"[Updater] Seeded {added} NSP scholarships")
    db.close()

# ─── MAIN: run all updates ────────────────────────────────────────────────────
def run_all_updates():
    print(f"[Updater] Running daily update — {date.today()}")
    auto_expire_opportunities()
    seed_nsp_scholarships()
    scrape_and_insert()
    print(f"[Updater] Done ✓")

if __name__ == '__main__':
    run_all_updates()
