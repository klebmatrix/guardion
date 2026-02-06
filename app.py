import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request

app = Flask(__name__)
app.secret_key = "guardiao_ultra_secret_99"

# Configuração simples para garantir que o site abra
PIN = os.environ.get("guardiao", "1234")

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(logs) > 20: logs.pop()

def motor():
    while True:
        add_log("📡 Oráculo Kalshi/Binance em prontidão...")
        time.sleep(60)

threading.Thread(target=motor, daemon=True).start()

@app.route('/')
def home():
    if not session.get('auth'):
        return redirect(url_for('login'))
    
    log_html = "".join([f"<li>{l}</li>" for l in logs])
    return f"""
    <body style="background:#000;color:lime;font-family:monospace;padding:20px;">
        <h2>🛡️ GUARDIÃO V59 - ONLINE</h2>
        <hr>
        <ul>{log_html}</ul>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>
    """

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN:
            session['auth'] = True
            return redirect(url_for('home'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;">' \
           '<form method="post">PIN: <input type="password" name="pin"><button>LOGAR</button></form></body>'

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)