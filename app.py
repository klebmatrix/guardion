import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session, send_file
from web3 import Web3
from fpdf import FPDF
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_2026_fixed")

# --- CONFIGS ---
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
    with open(LOGS_FILE, "w") as f: json.dump(logs[:15], f)

# --- INTERFACE HTML DIRETA ---
def tela_login():
    return '''<body style="background:#000;color:#fff;text-align:center;padding-top:100px;font-family:sans-serif;">
              <div style="display:inline-block;border:1px solid #333;padding:30px;background:#111;">
              <h2>🛡️ ACESSO GUARDIÃO</h2>
              <form method="post"><input type="password" name="pin" style="padding:10px;width:200px;"><br><br>
              <button type="submit" style="padding:10px 20px;background:orange;border:none;cursor:pointer;">ENTRAR</button></form>
              </div></body>'''

def tela_dash(logs):
    log_items = "".join([f"<li style='color:#00ff00;margin-bottom:5px;'>{l['data']} - {l['msg']}</li>" for l in logs])
    return f'''<body style="background:#0e1117;color:#fff;font-family:sans-serif;padding:20px;">
               <h1>🚀 PAINEL SNIPER OFICIAL</h1>
               <p>Wallet: <code>{WALLET}</code></p>
               <hr border="1" color="#333">
               <div style="background:#1a1c24;padding:20px;border-radius:10px;text-align:left;max-width:600px;margin:auto;">
               <h3>📜 LOGS DE ATIVIDADE:</h3>
               <ul style="list-style:none;padding:0;">{log_items}</ul>
               </div></body>'''

# --- ROTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            registrar_log("Acesso autorizado")
            return redirect(url_for('dashboard'))
    return tela_login()

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return tela_dash(carregar_logs())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)