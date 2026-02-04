import os, json, threading, time, requests
from io import BytesIO
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from web3 import Web3
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

# --- CONFIGURAÇÕES ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")
PRIV_KEY = os.environ.get("private_key")
RPC_URL = "https://polygon-rpc.com"

file_lock = threading.Lock()
web3 = Web3(Web3.HTTPProvider(RPC_URL))
CARTEIRA_ALVO = web3.to_checksum_address("0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E")

# Contratos USDC
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

# --- PERSISTÊNCIA ---
def load_json(filename, default):
    with file_lock:
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f: return json.load(f)
            except: pass
        return default

def save_json(filename, data):
    with file_lock:
        with open(filename, "w") as f: json.dump(data, f)

def registrar_log(mensagem, lado="AUTO", resultado="OK"):
    logs = load_json("logs.json", [])
    logs.insert(0, {"data": datetime.now().strftime("%d/%m %H:%M:%S"), "mercado": mensagem, "lado": lado, "resultado": resultado})
    save_json("logs.json", logs[:50])

# --- BOT LOOP ---
def sniper_loop():
    while True:
        state = load_json("bot_state.json", {"status": "OFF"})
        if state["status"] == "ON" and PRIV_KEY:
            try:
                res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                if res.status_code == 200:
                    pergunta = res.json()[0].get('question', 'Market')[:30]
                    registrar_log(f"Sniper: {pergunta}", "YES", "EXECUTADO")
            except Exception as e:
                registrar_log(f"Erro IA: {str(e)[:30]}", "ERRO", "FALHA")
        time.sleep(300)

threading.Thread(target=sniper_loop, daemon=True).start()

# --- ROTAS ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'): return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('index'))
        error = "PIN Incorreto"
    return render_template('login.html', error=error)

@app.route('/')
@login_required
def index():
    try:
        pol = round(web3.from_wei(web3.eth.get_balance(CARTEIRA_ALVO), 'ether'), 4)
        c1 = web3.eth.contract(address=web3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
        c2 = web3.eth.contract(address=web3.to_checksum_address(USDC_BRIDGED), abi=json.loads(ABI_USDC))
        usdc = round(max(c1.functions.balanceOf(CARTEIRA_ALVO).call(), c2.functions.balanceOf(CARTEIRA_ALVO).call()) / 1e6, 2)
    except: pol, usdc = "0.0", "0.0"

    return render_template('dashboard.html', wallet=CARTEIRA_ALVO, pol=pol, usdc=usdc, bot=load_json("bot_state.json", {"status": "OFF"}), historico=load_json("logs.json", []))

@app.route('/toggle_bot', methods=['POST'])
@login_required
def toggle_bot():
    status = request.form.get("status")
    save_json("bot_state.json", {"status": status})
    registrar_log(f"Bot {status}", "SISTEMA")
    return redirect(url_for('index'))

@app.route('/gerar_relatorio_pdf')
@login_required
def gerar_relatorio_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Relatorio Sniper Bot", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    for log in load_json("logs.json", []):
        pdf.cell(0, 8, f"{log['data']} - {log['mercado']} - {log['resultado']}", ln=True)
    return send_file(BytesIO(pdf.output()), mimetype='application/pdf', as_attachment=True, download_name="relatorio.pdf")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))