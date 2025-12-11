import streamlit as st
import time
from openai import OpenAI
import os
import re
from datetime import datetime, timedelta
from fpdf import FPDF
import requests
import traceback
import logging
import sqlite3
import hashlib
import json
import random

# -------------------------------------------------------------------
# JEEx PRO - Enhanced (Personal tracking, Mock tests, DPQs, Gamification)
# Single-file Streamlit app with lightweight SQLite storage.
# NOTE: This is a pragmatic, on-app implementation meant for local
# prototyping. For production use, migrate storage to a proper DB
# (Postgres/Mongo) and host APIs for a mobile app.
# -------------------------------------------------------------------

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JEEx Pro", page_icon="⚛️", layout="centered", initial_sidebar_state="expanded")

# *** EMAIL SETTINGS ***
ADMIN_EMAIL = "jeexaipro@gmail.com"

# --- 2. GLOBAL CONSTANTS ---
LOGO_URL = "https://raw.githubusercontent.com/SwastikJEEx/jeex-launch/1d6ef8ca3ac05432ed370338d4c04d6a03541f23/logo.png.png"
DB_PATH = "jeex_pro.db"

# --- 3. LOGGER ---
logger = logging.getLogger("jeex")
logger.setLevel(logging.INFO)

# --- 4. DATABASE HELPERS ---
def get_db_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    cur = conn.cursor()
    # users: id, name, email, password_hash, created
    cur.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password_hash TEXT, created TIMESTAMP)''')
    # attempts: id, user_id, question_id, topic, difficulty, correct (0/1), time_taken, timestamp
    cur.execute('''CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, question_id TEXT, topic TEXT, difficulty INTEGER, correct INTEGER, time_taken REAL, timestamp TIMESTAMP)''')
    # questions pool: id, prompt, answer, topic, difficulty
    cur.execute('''CREATE TABLE IF NOT EXISTS questions (id TEXT PRIMARY KEY, prompt TEXT, answer TEXT, topic TEXT, difficulty INTEGER)''')
    # tests: id, user_id, questions_json, score, timestamp
    cur.execute('''CREATE TABLE IF NOT EXISTS tests (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, questions_json TEXT, score REAL, timestamp TIMESTAMP)''')
    # leaderboard caching
    cur.execute('''CREATE TABLE IF NOT EXISTS leaderboard (user_id INTEGER PRIMARY KEY, points INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- 5. UTILITY HELPERS ---

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(name, email, password):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO users (name,email,password_hash,created) VALUES (?,?,?,?)', (name,email,hash_password(password), datetime.now()))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"create_user failed: {e}")
        return False
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT id,name,email,password_hash FROM users WHERE email=?', (email,))
    row = cur.fetchone()
    conn.close()
    if not row: return None
    if row['password_hash'] == hash_password(password):
        return {'id': row['id'], 'name': row['name'], 'email': row['email']}
    return None

# Simple question bank seeding (in real app, seed from textbooks / pyqs)
def seed_questions_if_empty():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as c FROM questions')
    if cur.fetchone()['c'] == 0:
        sample = [
            ("q1", "Integrate x^2 dx", "$\
\frac{x^3}{3} + C$", "calculus", 1),
            ("q2", "Find velocity when s=4t^2", "Differentiate and evaluate", "kinematics", 2),
            ("q3", "Balancing: H2 + O2 -> ?", "2 H2 + O2 -> 2 H2O", "chemistry", 1),
            ("q4", "Irodov-level electrostatics problem (short)", "Use Gauss law etc.", "electrostatics", 4),
        ]
        cur.executemany('INSERT INTO questions (id,prompt,answer,topic,difficulty) VALUES (?,?,?,?,?)', sample)
        conn.commit()
    conn.close()

seed_questions_if_empty()

# --- 6. PERFORMANCE & GAMIFICATION HELPERS ---

def record_attempt(user_id, question_id, topic, difficulty, correct, time_taken):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO attempts (user_id,question_id,topic,difficulty,correct,time_taken,timestamp) VALUES (?,?,?,?,?,?,?)',
                (user_id, question_id, topic, difficulty, int(correct), float(time_taken), datetime.now()))
    conn.commit()
    # award points
    points = int((difficulty or 1) * (1 + (1 if correct else 0))) * (10 if correct else 1)
    cur.execute('INSERT OR IGNORE INTO leaderboard (user_id, points) VALUES (?,0)', (user_id,))
    cur.execute('UPDATE leaderboard SET points = points + ? WHERE user_id=?', (points, user_id))
    conn.commit()
    conn.close()

def get_user_accuracy(user_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT SUM(correct) as correct, COUNT(*) as total FROM attempts WHERE user_id=?', (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row or row['total'] == 0: return None
    return float(row['correct'])/row['total']

def get_weak_topics(user_id, top_n=5):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('''SELECT topic, SUM(correct) as correct, COUNT(*) as total, (CAST(SUM(correct) as FLOAT)/COUNT(*)) as accuracy
                   FROM attempts WHERE user_id=? GROUP BY topic ORDER BY accuracy ASC LIMIT ?''', (user_id, top_n))
    rows = cur.fetchall()
    conn.close()
    return [{'topic': r['topic'], 'accuracy': r['accuracy'], 'total': r['total']} for r in rows]

def get_leaderboard(top_n=10):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('''SELECT u.name, l.points FROM leaderboard l JOIN users u ON u.id=l.user_id ORDER BY l.points DESC LIMIT ?''', (top_n,))
    rows = cur.fetchall()
    conn.close()
    return [{'name': r['name'], 'points': r['points']} for r in rows]

# Weekly report generator (returns bytes of a simple PDF)
def generate_weekly_report_pdf(user_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT name,email FROM users WHERE id=?', (user_id,))
    user = cur.fetchone()
    cur.execute('SELECT COUNT(*) as total, SUM(correct) as correct FROM attempts WHERE user_id=? AND timestamp >= ?', (user_id, (datetime.now()-timedelta(days=7))))
    stats = cur.fetchone()
    weak_topics = get_weak_topics(user_id, top_n=5)
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"JEEx Weekly Report - {user['name']}", ln=True)
    pdf.ln(5)
    pdf.set_font('Arial', '', 12)
    total = stats['total'] or 0
    correct = stats['correct'] or 0
    acc = (correct/total*100) if total else 0
    pdf.cell(0,8,f"Questions attempted this week: {total}", ln=True)
    pdf.cell(0,8,f"Accuracy this week: {acc:.1f}%", ln=True)
    pdf.ln(6)
    pdf.cell(0,8, "Weak Topics (low accuracy):", ln=True)
    for wt in weak_topics:
        pdf.cell(0,6, f" - {wt['topic']}: {wt['accuracy']*100 if wt['accuracy'] is not None else 0:.1f}% over {wt['total']} attempts", ln=True)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 7. MOCK TEST GENERATOR (ADAPTIVE) ---

def adaptive_mock_test(user_id, num_questions=10):
    # Strategy: pick questions biased towards weak topics and difficulty adjusted by past performance
    weak = get_weak_topics(user_id, top_n=3)
    weak_topics = [w['topic'] for w in weak]
    conn = get_db_conn()
    cur = conn.cursor()
    selected = []

    # 40% from weak topics, 30% from medium difficulty, rest random
    n_weak = max(1, int(num_questions * 0.4))
    n_medium = max(1, int(num_questions * 0.3))

    if weak_topics:
        cur.execute(f"SELECT * FROM questions WHERE topic IN ({','.join('?'*len(weak_topics))}) ORDER BY RANDOM() LIMIT ?", (*weak_topics, n_weak))
        for r in cur.fetchall(): selected.append(r)

    cur.execute('SELECT * FROM questions WHERE difficulty BETWEEN 2 AND 3 ORDER BY RANDOM() LIMIT ?', (n_medium,))
    for r in cur.fetchall(): selected.append(r)

    # fill the rest
    remaining = num_questions - len(selected)
    if remaining > 0:
        cur.execute('SELECT * FROM questions ORDER BY RANDOM() LIMIT ?', (remaining,))
        for r in cur.fetchall(): selected.append(r)

    conn.close()
    # package test
    test_qs = [{'id': r['id'], 'prompt': r['prompt'], 'topic': r['topic'], 'difficulty': r['difficulty']} for r in selected]
    return test_qs

# Grade mock test and record attempts
def grade_and_record_test(user_id, answers):
    # answers: list of dict {question_id, user_answer, correct_bool, time_taken}
    score = 0
    for a in answers:
        record_attempt(user_id, a['question_id'], a.get('topic','unknown'), a.get('difficulty',1), int(a['correct']), a.get('time_taken', 0.0))
        if a['correct']: score += 1
    # store test
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO tests (user_id,questions_json,score,timestamp) VALUES (?,?,?,?)', (user_id, json.dumps(answers), float(score), datetime.now()))
    conn.commit()
    conn.close()
    return score

# --- 8. SMART REVISION PLANNER ---

def generate_revision_plan(user_id, days=7):
    # Simple plan: Uses weak topics to schedule focused sessions
    weak = get_weak_topics(user_id, top_n=5)
    plan = []
    if not weak:
        # general rotation
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT topic FROM questions LIMIT 10')
        topics = [r['topic'] for r in cur.fetchall()]
        conn.close()
        for i in range(days):
            plan.append({'day': i+1, 'topics': [topics[i % len(topics)]]})
        return plan

    topics = [w['topic'] for w in weak]
    for i in range(days):
        plan.append({'day': i+1, 'topics': [topics[i % len(topics)]]})
    return plan

# --- 9. DAILY PRACTICE QUESTIONS (DPQ) ---

def get_daily_practice(user_id, n=5):
    # Mix of weak topics and random
    weak = get_weak_topics(user_id, top_n=3)
    weak_topics = [w['topic'] for w in weak]
    conn = get_db_conn()
    cur = conn.cursor()
    selected = []
    if weak_topics:
        cur.execute(f"SELECT * FROM questions WHERE topic IN ({','.join('?'*len(weak_topics))}) ORDER BY RANDOM() LIMIT ?", (*weak_topics, max(1,int(n/2))))
        for r in cur.fetchall(): selected.append(r)
    remaining = n - len(selected)
    if remaining>0:
        cur.execute('SELECT * FROM questions ORDER BY RANDOM() LIMIT ?', (remaining,))
        for r in cur.fetchall(): selected.append(r)
    conn.close()
    return [{'id': r['id'], 'prompt': r['prompt'], 'topic': r['topic'], 'difficulty': r['difficulty']} for r in selected]

# --- 10. STREAMLIT UI EXTENSIONS (AUTH, DASHBOARD) ---

# Session init
if 'user' not in st.session_state:
    st.session_state.user = None

# Authentication UI in sidebar
with st.sidebar:
    st.markdown("## Account")
    if st.session_state.user is None:
        auth_mode = st.radio("Have an account?", ("Login","Sign up"))
        if auth_mode == "Sign up":
            su_name = st.text_input("Name", key='su_name')
            su_email = st.text_input("Email", key='su_email')
            su_pass = st.text_input("Password", type='password', key='su_pass')
            if st.button("Create account"):
                ok = create_user(su_name, su_email, su_pass)
                if ok:
                    st.success("Account created. Please login.")
                else:
                    st.error("Could not create account. Email may already exist.")
        else:
            le_email = st.text_input("Email", key='le_email')
            le_pass = st.text_input("Password", type='password', key='le_pass')
            if st.button("Login"):
                user = authenticate_user(le_email, le_pass)
                if user:
                    st.session_state.user = user
                    st.success(f"Welcome {user['name']}")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials")
    else:
        st.markdown(f"**Logged in as:** {st.session_state.user['name']}")
        if st.button("Logout"):
            st.session_state.user = None
            st.experimental_rerun()

        st.markdown("---")
        # User quick actions
        st.markdown("### Quick Actions")
        if st.button("My Accuracy & Weak Topics"):
            acc = get_user_accuracy(st.session_state.user['id'])
            if acc is None:
                st.info("No attempts recorded yet. Start solving to track your progress.")
            else:
                st.success(f"Overall accuracy: {acc*100:.1f}%")
                st.table(get_weak_topics(st.session_state.user['id'], top_n=6))
        if st.button("Get Weekly Report (PDF)"):
            pdf_bytes = generate_weekly_report_pdf(st.session_state.user['id'])
            st.download_button("Download Weekly Report", data=pdf_bytes, file_name="JEEx_weekly_report.pdf", mime="application/pdf")

        if st.button("Generate 10-Question Mock Test"):
            qs = adaptive_mock_test(st.session_state.user['id'], num_questions=10)
            st.session_state.current_mock = qs
            st.experimental_rerun()

        if st.button("Daily Practice Questions (DPQs)"):
            dps = get_daily_practice(st.session_state.user['id'], n=5)
            st.session_state.dpqs = dps
            st.experimental_rerun()

        st.markdown("---")
        st.markdown("### Leaderboard")
        lb = get_leaderboard(10)
        for i,u in enumerate(lb, start=1):
            st.markdown(f"{i}. **{u['name']}** — {u['points']} pts")

# --- 11. MAIN APP (keeps original chat behavior but hooks into tracking) ---

# Branding & CSS (kept minimal for brevity)
st.title("JEEx PRO - Enhanced")
st.write("Your AI Rank Booster with personal tracking, mock tests and daily practice.")

# Show DPQs if available
if 'dpqs' in st.session_state and st.session_state.dpqs:
    st.markdown("### Your Daily Practice Questions (DPQs)")
    for q in st.session_state.dpqs:
        st.markdown(f"**{q['id']}** — {q['prompt']}  _(Topic: {q['topic']}, Dif: {q['difficulty']})_")
    if st.button("Clear DPQs"):
        st.session_state.dpqs = None

# Mock test UI
if 'current_mock' in st.session_state and st.session_state.current_mock:
    st.markdown("### Mock Test (Adaptive)")
    answers = []
    for q in st.session_state.current_mock:
        st.markdown(f"**{q['id']}** — {q['prompt']} _(Topic:{q['topic']})_")
        ua = st.text_input(f"Answer for {q['id']}", key=f"ans_{q['id']}")
        # For prototype: assume any non-empty answer correct for recording demo
        if ua:
            answers.append({'question_id': q['id'], 'user_answer': ua, 'correct': True, 'time_taken': random.uniform(5,60), 'topic': q['topic'], 'difficulty': q['difficulty']})
    if st.button("Submit Mock Test"):
        if st.session_state.user is None:
            st.error("Please login to record and grade the test.")
        else:
            score = grade_and_record_test(st.session_state.user['id'], answers)
            st.success(f"Mock test submitted. Score: {score}/{len(st.session_state.current_mock)}")
            st.session_state.current_mock = None

# Simple chat input (retain existing code integration but for prototype we'll not call OpenAI here)
user_msg = st.text_area("Ask JEEx a doubt (prototype mode - local routing)")
if st.button("Send") and user_msg:
    # In production, route to OpenAI as in original app.
    st.info("This is prototype chat. In production this will call the JEEx assistant.")
    # Record a sample attempt if user provides a question and marks it correct via quick widget
    if st.session_state.user:
        # Create a faux question_id and record a 'not-graded' attempt to track engagement
        qid = f"chat_{int(time.time())}"
        record_attempt(st.session_state.user['id'], qid, 'chat', 1, False, 10.0)
        st.success("Your session has been recorded for analytics.")
    else:
        st.warning("Login to record progress and receive personalised plans.")

# Footer - Leaderboard (global)
st.markdown("---")
st.subheader("Global Leaderboard")
for i,row in enumerate(get_leaderboard(5), start=1):
    st.write(f"{i}. {row['name']} — {row['points']} pts")

st.info("Notes: This integrated prototype demonstrates core data flows for tracking, tests, DPQs, reports and gamification. For production: connect to OpenAI assistant, secure user auth, and migrate DB to managed service.")
