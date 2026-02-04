import os
import datetime
import json
import threading
import time
import requests
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from web3 import Web3
from functools import wraps
from fpdf import FPDF
from io import BytesIO

# FORÇANDO O CAMINHO DA PASTA TEMPLATES
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

# --- CONFIGURAÇÕES RENDER ---
PIN_SISTEMA = os.environ.get("guardiao", "123456") # Default para teste local
PRIV_KEY = os.environ.get("private_key")

# --- BLOCKCHAIN SETUP ---
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))
CARTEIRA_ALVO = web3.to_checksum_address("0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E")

USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

# --- DADOS GLOBAIS DO BOT (PERSISTIDOS EM ARQUIVO) ---
BOT_STATE_FILE = "bot_state.json"
LOGS_FILE = "logs.json"

def load_bot_state():
    if os.path.exists(BOT_STATE_FILE):
        with open(BOT_STATE_FILE, "r") as f:
            return json.load(f)
    return {"status": "OFF", "preference": "YES"} # Default

def save_bot_state(state):
    with open(BOT_STATE_FILE, "w") as f:
        json.dump(state, f)

def load_logs():
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f:
            return json.load(f)
    return []

def save_logs(logs):
    with open(LOGS_FILE, "w") as f:
        json.dump(logs[:50], f) # Limita a 50 logs para não sobrecarregar

def registrar_log(mensagem, lado="AUTO", resultado="OK"):
    agora = datetime.now().strftime("%d/%m %H:%M:%S")
    log = {"data": agora, "mercado": mensagem, "lado": lado, "resultado": resultado}
    logs = load_logs()
    logs.insert(0, log)
    save_logs(logs)
    return logs

# --- LÓGICA DO BOT (EXECUTADA EM THREAD SEPARADA) ---
def sniper_loop():
    while True:
        bot_state = load_bot_state()
        if bot_state["status"] == "ON" and PRIV_KEY:
            try:
                # 1. SCANNER DE MERCADO REAL
                res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                mercado = res.json()[0]
                pergunta = mercado.get('question', 'Polymarket')[:30]
                
                # 2. IA DE DECISÃO (Exemplo simples: sempre YES)
                decisao = bot_state.get("preference", "YES")
                
                # 3. EXECUÇÃO DO TIRO (Simulado)
                registrar_log(f"Sniper: {pergunta}", decisao, "EXECUTADO")
                
            except Exception as e:
                registrar_log(f"Erro IA: {str(e)[:50]}", "ERRO", "FALHA")
        
        time.sleep(300) # Espera 5 minutos

# Inicia o loop do bot em uma thread separada
bot_thread = threading.Thread(target=sniper_loop)
bot_thread.daemon = True # Garante que a thread morra com o processo principal
bot_thread.start()

# --- FUNÇÕES DE GERAÇÃO DE PDF ---
class PDFReport(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "RELATORIO DE OPERACOES - SNIPER BOT", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

def gerar_pdf_relatorio():
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 5, f"Wallet: {CARTEIRA_ALVO}", ln=True)
    pdf.cell(0, 5, f"Data do Relatorio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    pdf.ln(5)
    
    logs = load_logs()
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(40, 8, "Data/Hora", border=1)
    pdf.cell(80, 8, "Mercado", border=1)
    pdf.cell(40, 8, "Lado", border=1)
    pdf.cell(30, 8, "Status", border=1, ln=True)
    
    pdf.set_font("helvetica", "", 9)
    for log in logs:
        pdf.cell(40, 8, log.get("data", ""), border=1)
        mercado = log.get("mercado", "")[:25]
        pdf.cell(80, 8, mercado, border=1)
        pdf.cell(40, 8, log.get("lado", ""), border=1)
        pdf.cell(30, 8, log.get("resultado", ""), border=1, ln=True)
    
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, "RESUMO", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, f"Total de Operacoes: {len(logs)}", ln=True)
    
    bot_state = load_bot_state()
    pdf.cell(0, 6, f"Status do Bot: {bot_state['status']}", ln=True)
    
    # Retorna como bytes
    return pdf.output()

# --- ROTAS FLASK ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
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
    try:
        pol_bal = round(web3.from_wei(web3.eth.get_balance(CARTEIRA_ALVO), 'ether'), 4)
        
        usdc_contract_native = web3.eth.contract(address=web3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
        usdc_contract_bridged = web3.eth.contract(address=web3.to_checksum_address(USDC_BRIDGED), abi=json.loads(ABI_USDC))
        
        usdc_bal_native = usdc_contract_native.functions.balanceOf(CARTEIRA_ALVO).call() / 10**6
        usdc_bal_bridged = usdc_contract_bridged.functions.balanceOf(CARTEIRA_ALVO).call() / 10**6
        usdc_final = max(usdc_bal_native, usdc_bal_bridged)
        usdc_final = round(usdc_final, 2)

    except Exception as e:
        print(f"Erro ao obter saldos: {e}")
        pol_bal = "0.0"
        usdc_final = "0.0"
    
    bot_state = load_bot_state()
    logs = load_logs()

    # Estatísticas para o dashboard
    total_ops = len(logs)
    ops_yes = len([l for l in logs if l.get("lado") == "YES"])
    ops_no = len([l for l in logs if l.get("lado") == "NO"])
    ops_erro = len([l for l in logs if l.get("resultado") == "FALHA"])

    return render_template('dashboard.html', 
                           wallet=CARTEIRA_ALVO, 
                           pol=pol_bal, 
                           usdc=usdc_final,
                           bot=bot_state,
                           total_ops=total_ops,
                           ops_yes=ops_yes,
                           ops_no=ops_no,
                           ops_erro=ops_erro,
                           historico=logs)

@app.route('/toggle_bot', methods=['POST'])
@login_required
def toggle_bot():
    status_acao = request.form.get("status")
    bot_state = load_bot_state()
    bot_state["status"] = status_acao
    save_bot_state(bot_state)
    
    registrar_log(f"Bot {status_acao}", "SISTEMA", "OK")
    return redirect(url_for('index'))

@app.route('/gerar_relatorio_pdf')
@login_required
def gerar_relatorio_pdf():
    pdf_output = gerar_pdf_relatorio()
    if pdf_output:
        return send_file(
            BytesIO(pdf_output),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"relatorio_sniper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
    return "Erro ao gerar PDF", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True) # debug=True para ver erros no console
