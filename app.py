import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session, send_file
from web3 import Web3
from fpdf import FPDF
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

# --- CONFIGURAÇÕES ---
PIN_SISTEMA = os.environ.get("guardiao", "20262026")
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
LOGS_FILE = "logs.json"

def carregar_logs():
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def registrar_log(msg):
    logs = carregar_logs()
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs.insert(0, {"data": agora, "msg": msg})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:20], f)

# Rota de Login (HTML Embutido)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:100px;">' \
           '<form method="post"><h2>DIGITE O PIN:</h2><input type="password" name="pin" style="padding:10px;">' \
           '<button type="submit" style="padding:10px;">ENTRAR</button></form></body>'

# Dashboard (HTML Embutido)
@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    logs = carregar_logs()
    log_html = "".join([f"<li>{l['data']} - {l['msg']}</li>" for l in logs])
    return f"""
    <body style="background:#0e1117; color:white; font-family:sans-serif; padding:20px; text-align:center;">
        <h1 style="color:orange;">🚀 SNIPER GUARDIÃO</h1>
        <p>Wallet: <code>{WALLET}</code></p>
        <div style="background:#1a1c24; padding:20px; border-radius:10px; border:1px solid #333; display:inline-block;">
            <h3>LOGS RECENTES:</h3>
            <ul style="text-align:left;">{log_html}</ul>
        </div>
    </body>
    """

if __name__ == "__main__":
    # O Render exige que o app rode na porta definida pela variável de ambiente PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)