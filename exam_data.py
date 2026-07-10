"""
exam_data.py — Single source of truth for all exam & counselling dates.
Edit dates here. The scheduler picks them up daily automatically.
"""

from datetime import datetime, date

TODAY = date.today()

def days_from_now(d):
    if isinstance(d, str):
        try: d = datetime.strptime(d, '%Y-%m-%d').date()
        except: return 999
    return (d - TODAY).days

def status(deadline_str):
    """Return 'done','next','soon','future' based on date."""
    d = days_from_now(deadline_str)
    if d < 0:   return 'done'
    if d <= 7:  return 'next'
    if d <= 30: return 'soon'
    return 'future'

EXAMS = [
    {
        'name': 'JEE Main',
        'full': 'B.Tech/B.E Admissions',
        'icon': '🔬',
        'col':  'rgba(0,212,255,.12)',
        'tl': [
            {'ev': 'Session 1 Registration', 'dt': 'Nov 1–Dec 4, 2025',     's': 'done'},
            {'ev': 'Session 1 Exam',         'dt': 'Jan 22–Feb 2, 2026',    's': 'done'},
            {'ev': 'Session 1 Result',        'dt': 'Feb 12, 2026 ✅',       's': 'done'},
            {'ev': 'Session 2 Exam',         'dt': 'Apr 2–9, 2026',         's': 'done'},
            {'ev': 'Session 2 Result & Final Rank', 'dt': 'Apr 2026 — Awaited', 's': status('2026-04-30')},
        ]
    },
    {
        'name': 'JEE Advanced',
        'full': 'IIT Admissions — Top 2.5L qualifiers',
        'icon': '⚛️',
        'col':  'rgba(191,95,255,.12)',
        'tl': [
            {'ev': 'Registration Opens',  'dt': 'Apr 23, 2026', 's': status('2026-04-23')},
            {'ev': 'Last Date to Register','dt': 'May 2, 2026',  's': status('2026-05-02')},
            {'ev': 'Admit Card',          'dt': 'May 12, 2026', 's': status('2026-05-12')},
            {'ev': 'Exam Date',           'dt': 'May 18, 2026', 's': status('2026-05-18')},
            {'ev': 'Result',             'dt': 'Jun 2, 2026',   's': status('2026-06-02')},
        ]
    },
    {
        'name': 'NEET UG',
        'full': 'MBBS/BDS/BAMS Admissions',
        'icon': '🏥',
        'col':  'rgba(0,255,136,.10)',
        'tl': [
            {'ev': 'Registration',  'dt': 'Feb 7–Mar 7, 2026',  's': 'done'},
            {'ev': 'Admit Card',    'dt': 'Apr 28, 2026',        's': status('2026-04-28')},
            {'ev': 'Exam Date',     'dt': 'May 4, 2026',         's': status('2026-05-04')},
            {'ev': 'Result',        'dt': 'Jun 2026',            's': status('2026-06-15')},
        ]
    },
    {
        'name': 'CUET UG',
        'full': '250+ Central Universities',
        'icon': '🏛️',
        'col':  'rgba(255,184,0,.10)',
        'tl': [
            {'ev': 'Registration',   'dt': 'Feb–Mar 2026',        's': 'done'},
            {'ev': 'Admit Card',     'dt': 'May 2026',             's': status('2026-05-10')},
            {'ev': 'Exam Window',    'dt': 'May 15–31, 2026',      's': status('2026-05-15')},
            {'ev': 'Result',         'dt': 'Jun 2026',             's': status('2026-06-20')},
        ]
    },
    {
        'name': 'CLAT',
        'full': 'NLU Law Admissions',
        'icon': '⚖️',
        'col':  'rgba(255,110,180,.10)',
        'tl': [
            {'ev': 'Registration',   'dt': 'Jan 1–Mar 31, 2026',  's': 'done'},
            {'ev': 'Exam Date',      'dt': 'May 10, 2026',         's': status('2026-05-10')},
            {'ev': 'Result',         'dt': 'May 2026',             's': status('2026-05-25')},
        ]
    },
    {
        'name': 'BITSAT',
        'full': 'BITS Pilani Engineering',
        'icon': '🛸',
        'col':  'rgba(0,212,255,.10)',
        'tl': [
            {'ev': 'Registration',   'dt': 'Jan 9–Mar 31, 2026',  's': 'done'},
            {'ev': 'Slot Booking',   'dt': 'Apr 2026',             's': status('2026-04-20')},
            {'ev': 'Exam Window',    'dt': 'May 19–Jun 8, 2026',   's': status('2026-05-19')},
            {'ev': 'Result',         'dt': 'Jun 2026',             's': status('2026-06-20')},
        ]
    },
    {
        'name': 'MHT CET',
        'full': 'Maharashtra Engineering & Pharma',
        'icon': '🔧',
        'col':  'rgba(255,77,109,.10)',
        'tl': [
            {'ev': 'Registration',   'dt': 'Jan–Mar 2026',         's': 'done'},
            {'ev': 'Admit Card',     'dt': 'Apr 2026',             's': status('2026-04-25')},
            {'ev': 'Exam Window',    'dt': 'May 2026',             's': status('2026-05-15')},
            {'ev': 'Result',         'dt': 'Jun 2026',             's': status('2026-06-15')},
        ]
    },
    {
        'name': 'CAT',
        'full': 'MBA/IIM Admissions',
        'icon': '📊',
        'col':  'rgba(191,95,255,.10)',
        'tl': [
            {'ev': 'Registration Opens', 'dt': 'Aug 2026',    's': status('2026-08-01')},
            {'ev': 'Last Date',          'dt': 'Sep 2026',    's': status('2026-09-15')},
            {'ev': 'Exam Date',          'dt': 'Nov 30, 2026','s': status('2026-11-30')},
            {'ev': 'Result',             'dt': 'Jan 2027',    's': status('2027-01-15')},
        ]
    },
    {
        'name': 'GATE',
        'full': 'M.Tech/PSU Jobs',
        'icon': '⚙️',
        'col':  'rgba(0,255,136,.10)',
        'tl': [
            {'ev': 'Registration Opens', 'dt': 'Aug 28, 2026',      's': status('2026-08-28')},
            {'ev': 'Last Date',          'dt': 'Oct 3, 2026',        's': status('2026-10-03')},
            {'ev': 'Exam Window',        'dt': 'Feb 1–16, 2027',     's': status('2027-02-01')},
            {'ev': 'Result',             'dt': 'Mar 2027',           's': status('2027-03-15')},
        ]
    },
]

COUNSELLING_LIST = [
    {'id':'josaa',          'name':'JoSAA',            'full':'Joint Seat Allocation — IITs, NITs, IIITs, GFTIs','icon':'🏫','status':'open',
     'rounds':[{'l':'Round 1','d':'Jun 17–19, 2026','s':'act'},{'l':'Round 2','d':'Jun 22–24, 2026','s':''},{'l':'Round 3','d':'Jun 27–29, 2026','s':''},{'l':'Round 4','d':'Jul 2–4, 2026','s':''},{'l':'Round 5','d':'Jul 6–8, 2026','s':''},{'l':'Round 6','d':'Jul 10–12, 2026','s':''}]},
    {'id':'mcc-neet',       'name':'MCC NEET UG',      'full':'Medical Counselling — MBBS/BDS 15% AIQ','icon':'🏥','status':'soon',
     'rounds':[{'l':'Round 1','d':'Jul 14–21, 2026','s':''},{'l':'Round 2','d':'Aug 1–8, 2026','s':''},{'l':'Mop-Up','d':'Aug 20–27, 2026','s':''},{'l':'Stray Vacancy','d':'Sep 5–10, 2026','s':''}]},
    {'id':'jac-delhi',      'name':'JAC Delhi',         'full':'Delhi Engineering Colleges Counselling','icon':'🔬','status':'soon',
     'rounds':[{'l':'Round 1 Choice Fill','d':'Jun 25–Jul 1, 2026','s':''},{'l':'Round 1 Allotment','d':'Jul 4, 2026','s':''},{'l':'Round 2','d':'Jul 8–15, 2026','s':''},{'l':'Round 3','d':'Jul 19–25, 2026','s':''}]},
    {'id':'du-csas',        'name':'DU CSAS',           'full':'Delhi University — UG Admissions','icon':'🏛️','status':'open',
     'rounds':[{'l':'Registration','d':'May 20–Jun 30, 2026','s':'act'},{'l':'Merit List 1','d':'Jul 10, 2026','s':''},{'l':'Merit List 2','d':'Jul 20, 2026','s':''},{'l':'Merit List 3','d':'Jul 30, 2026','s':''}]},
    {'id':'clat',           'name':'CLAT Counselling',  'full':'NLU Admissions — 24 National Law Universities','icon':'⚖️','status':'soon',
     'rounds':[{'l':'Round 1','d':'Jun 10–15, 2026','s':''},{'l':'Round 2','d':'Jun 20–25, 2026','s':''},{'l':'Mop-Up','d':'Jun 30–Jul 4, 2026','s':''}]},
    {'id':'josaa-nit',      'name':'JoSAA NIT/IIIT',   'full':'NITs, IIITs & GFTIs via JoSAA Portal','icon':'⚙️','status':'open',
     'rounds':[{'l':'Round 1','d':'Jun 17–19, 2026','s':'act'},{'l':'Round 2','d':'Jun 22–24, 2026','s':''},{'l':'Round 3','d':'Jun 27–29, 2026','s':''},{'l':'Round 4','d':'Jul 2–4, 2026','s':''},{'l':'Round 5','d':'Jul 6–8, 2026','s':''}]},
    {'id':'maharashtra-cap','name':'Maharashtra CAP',   'full':'MHT CET Engineering CAP Rounds','icon':'🔧','status':'soon',
     'rounds':[{'l':'CAP Round 1','d':'Jul 5–10, 2026','s':''},{'l':'CAP Round 2','d':'Jul 18–23, 2026','s':''},{'l':'CAP Round 3','d':'Aug 1–5, 2026','s':''}]},
    {'id':'mcc-pg',         'name':'MCC PG (NEET PG)',  'full':'PG Medical Admissions — MD/MS/Diploma','icon':'👨‍⚕️','status':'soon',
     'rounds':[{'l':'Round 1','d':'Aug 2026','s':''},{'l':'Round 2','d':'Sep 2026','s':''},{'l':'Mop-Up','d':'Oct 2026','s':''}]},
]
