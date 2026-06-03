from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os, json
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

DB = os.environ.get('DB_PATH', '/var/data/vrio.db')

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
    conn.commit()
    conn.close()

init_db()

# ── Serve frontend ──
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ── Save response ──
@app.route('/api/response', methods=['POST'])
def save_response():
    d = request.json
    conn = get_db()
    # upsert by session_id
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

# ── Get all responses (admin) ──
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
