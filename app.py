import os
import json
import threading
import time
import requests
from io import BytesIO
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, send_file
from web3 import Web3
from fpdf import FPDF
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de caminhos
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("FLASK_SECRET", "chave_secreta_padrao_123")

# --- CONFIGURAÇÕES DO SISTEMA ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")
PRIV_KEY = os.environ.get("private_key")
RPC_URL = "https://polygon-rpc.com"

# Bloqueio de thread para segurança de arquivos JSON
file_lock = threading.Lock()

# --- BLOCKCHAIN SETUP ---
web3 = Web3(Web3.HTTPProvider(RPC_URL))
CARTEIRA_ALVO = web3.to_checksum_address("0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E")

# Contratos USDC (Polygon)
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

# --- PERSISTÊNCIA DE DADOS ---
BOT_STATE_FILE = "bot_state.json"
LOGS_FILE = "logs.json"

def load_bot_state():
    with file_lock:
        if os.path.exists(BOT_STATE_FILE):
            try:
                with open(BOT_STATE_FILE, "r") as f:
                    return json.load(f)
            except: pass
        return {"status": "OFF", "preference": "YES"}

def save_bot_state(state):
    with file_lock:
        with open(BOT_STATE_FILE, "w") as f:
            json.dump(state, f)

def load_logs():
    with file_lock:
        if os.path.exists(LOGS_FILE):
            try:
                with open(LOGS_FILE, "r") as f:
                    return json.load(f)
            except: pass
        return []

def save_logs(logs):
    with file_lock:
        with open(LOGS_FILE, "w") as f:
            json.dump(logs[:50], f)

def registrar_log(mensagem, lado="AUTO", resultado="OK"):
    agora = datetime.now().strftime("%d/%m %H:%M:%S")
    log = {"data": agora, "mercado": mensagem, "lado": lado, "resultado": resultado}
    logs = load_logs()
    logs.insert(0, log)
    save_logs(logs)
    return logs

# --- LOOP DO BOT ---
def sniper_loop():
    while True:
        state = load_bot_state()
        if state["status"] == "ON" and PRIV_KEY:
            try:
                # Simulação de consulta à API Polymarket
                res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                if res.status_code == 200:
                    mercados = res.json()
                    if mercados:
                        pergunta = mercados[0].get('question', 'Sem Nome')[:30]
                        decisao = state.get("preference", "YES")
                        registrar_log(f"Sniper: {pergunta}", decisao, "EXECUTADO")
            except Exception as e:
                registrar_log(f"Erro IA: {str(e)[:40]}", "ERRO", "FALHA")
        
        time.sleep(300) # Intervalo de 5 minutos

bot_thread = threading.Thread(target=sniper_loop, daemon=True)
bot_thread.start()

# --- GERAÇÃO DE PDF ---
class PDFReport(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "RELATORIO DE OPERACOES - SNIPER BOT", ln=True, align="C")
        self.ln(10)

def gerar_pdf_relatorio():
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 5, f"Wallet: {CARTEIRA_ALVO}", ln=True)
    pdf.cell(0, 5, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    pdf.ln(5)
    
    logs = load_logs()
    # Cabeçalho da tabela
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(40, 8, "Data/Hora", 1, 0, "C", True)
    pdf.cell(80, 8, "Mercado", 1, 0, "C", True)
    pdf.cell(30, 8, "Lado", 1, 0, "C", True)
    pdf.cell(30, 8, "Status", 1, 1, "C", True)
    
    for log in logs:
        pdf.cell(40, 8, str(log.get("data")), 1)
        pdf.cell(80, 8, str(log.get("mercado"))[:25], 1)
        pdf.cell(30, 8, str(log.get("lado")), 1)
        pdf.cell(30, 8, str(log.get("resultado")), 1, 1)
    
    return pdf.output()

# --- ROTAS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error="PIN incorreto.")
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    pol_bal, usdc_final = "0.0", "0.0"
    try:
        pol_bal = round(web3.from_wei(web3.eth.get_balance(CARTEIRA_ALVO), 'ether'), 4)
        c_native = web3.eth.contract(address=web3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
        c_bridged = web3.eth.contract(address=web3.to_checksum_address(USDC_BRIDGED), abi=json.loads(ABI_USDC))
        
        b1 = c_native.functions.balanceOf(CARTEIRA_ALVO).call() / 10**6
        b2 = c_bridged.functions.balanceOf(CARTEIRA_ALVO).call() / 10**6
        usdc_final = round(max(b1, b2), 2)
    except Exception as e:
        print(f"Erro Web3: {e}")

    logs = load_logs()
    return render_template('dashboard.html', 
                           wallet=CARTEIRA_ALVO, pol=pol_bal, usdc=usdc_final,
                           bot=load_bot_state(), historico=logs,
                           total_ops=len(logs))

@app.route('/toggle_bot', methods=['POST'])
@login_required
def toggle_bot():
    novo_status = request.form.get("status")
    state = load_bot_state()
    state["status"] = novo_status
    save_bot_state(state)
    registrar_log(f"Bot alterado para {novo_status}", "SISTEMA")
    return redirect(url_for('index'))

@app.route('/gerar_relatorio_pdf')
@login_required
def gerar_relatorio_pdf():
    try:
        output = gerar_pdf_relatorio()
        return send_file(BytesIO(output), mimetype='application/pdf',
                         as_attachment=True, download_name="relatorio.pdf")
    except Exception as e:
        return f"Erro: {e}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)