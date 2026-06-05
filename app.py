from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os, json
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

DB = '/tmp/vrio.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        V INTEGER, R INTEGER, I INTEGER, O INTEGER,
        tot INTEGER, pct INTEGER,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS discussion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        name TEXT NOT NULL,
        text TEXT NOT NULL,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dim TEXT NOT NULL,
        q_index INTEGER NOT NULL,
        text TEXT NOT NULL,
        opt0 TEXT, opt1 TEXT, opt2 TEXT, opt3 TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        text TEXT NOT NULL,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ── Responses ──
@app.route('/api/response', methods=['POST'])
def save_response():
    d = request.json
    conn = get_db()
    existing = conn.execute('SELECT id FROM responses WHERE session_id=?', (d['session_id'],)).fetchone()
    if existing:
        conn.execute('UPDATE responses SET V=?,R=?,I=?,O=?,tot=?,pct=?,ts=CURRENT_TIMESTAMP WHERE session_id=?',
                     (d['V'],d['R'],d['I'],d['O'],d['tot'],d['pct'],d['session_id']))
    else:
        conn.execute('INSERT INTO responses (session_id,V,R,I,O,tot,pct) VALUES (?,?,?,?,?,?,?)',
                     (d['session_id'],d['V'],d['R'],d['I'],d['O'],d['tot'],d['pct']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/responses', methods=['GET'])
def get_responses():
    conn = get_db()
    rows = conn.execute('SELECT * FROM responses ORDER BY ts DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ── Discussion ──
@app.route('/api/discussion', methods=['GET'])
def get_discussion():
    conn = get_db()
    rows = conn.execute('SELECT * FROM discussion ORDER BY ts DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/discussion', methods=['POST'])
def post_discussion():
    d = request.json
    conn = get_db()
    conn.execute('INSERT INTO discussion (role,name,text) VALUES (?,?,?)',
                 (d['role'], d['name'], d['text']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ── Questions ──
@app.route('/api/questions', methods=['GET'])
def get_questions():
    conn = get_db()
    rows = conn.execute('SELECT * FROM questions ORDER BY dim, q_index').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/questions', methods=['POST'])
def save_questions():
    questions = request.json  # list of {dim, q_index, text, opt0..opt3}
    conn = get_db()
    conn.execute('DELETE FROM questions')
    for q in questions:
        conn.execute('INSERT INTO questions (dim,q_index,text,opt0,opt1,opt2,opt3) VALUES (?,?,?,?,?,?,?)',
                     (q['dim'], q['q_index'], q['text'], q['opt0'], q['opt1'], q['opt2'], q['opt3']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ── Feedback per student ──
@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    conn = get_db()
    rows = conn.execute('SELECT * FROM feedback ORDER BY ts DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/feedback', methods=['POST'])
def save_feedback():
    d = request.json
    conn = get_db()
    existing = conn.execute('SELECT id FROM feedback WHERE session_id=?', (d['session_id'],)).fetchone()
    if existing:
        conn.execute('UPDATE feedback SET text=?,ts=CURRENT_TIMESTAMP WHERE session_id=?',
                     (d['text'], d['session_id']))
    else:
        conn.execute('INSERT INTO feedback (session_id,text) VALUES (?,?)',
                     (d['session_id'], d['text']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ── Reset ──
@app.route('/api/reset', methods=['POST'])
def reset_data():
    conn = get_db()
    conn.execute('DELETE FROM responses')
    conn.execute('DELETE FROM discussion')
    conn.execute('DELETE FROM feedback')
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
