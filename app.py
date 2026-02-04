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

# --- CONFIGURAÇÕES DE REDE E CONTRATOS ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")
PRIV_KEY = os.environ.get("private_key")
RPC_URL = "https://polygon-rpc.com"

# Endereços Oficiais (Polygon)
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
CTF_EXCHANGE = "0x4bFb41d5B3570De3061333a9b59dd234870343f5" # Polymarket CTF Exchange

# ABI mínima para aprovação de token (ERC20)
ABI_ERC20 = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","bool":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

web3 = Web3(Web3.HTTPProvider(RPC_URL))
CARTEIRA_ALVO = web3.to_checksum_address("0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E")
file_lock = threading.Lock()

# --- FUNÇÕES DE APOIO ---
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

# --- LÓGICA DE TRANSAÇÃO REAL ---
def executar_aprovacao_real(valor_usdc):
    """Aprova o contrato da Polymarket a gastar seu USDC"""
    try:
        account = web3.eth.account.from_key(PRIV_KEY)
        contract = web3.eth.contract(address=web3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_ERC20))
        
        valor_wei = int(valor_usdc * 10**6)
        nonce = web3.eth.get_transaction_count(account.address)
        
        # Build transaction
        tx = contract.functions.approve(web3.to_checksum_address(CTF_EXCHANGE), valor_wei).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': web3.eth.gas_price
        })
        
        signed_tx = web3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        link = f"https://polygonscan.com/tx/{tx_hash.hex()}"
        registrar_log(f"Aprovação Enviada: {valor_usdc} USDC", "BLOCKCHAIN", "PENDENTE")
        return tx_hash.hex()
    except Exception as e:
        registrar_log(f"Erro Transação: {str(e)[:40]}", "ERRO", "FALHA")
        return None

# --- LOOP DO SNIPER ---
def sniper_loop():
    while True:
        state = load_json("bot_state.json", {"status": "OFF"})
        if state["status"] == "ON" and PRIV_KEY:
            # TESTE REAL: Inicia com 1 USDC para validação
            tx = executar_aprovacao_real(1.0)
            if tx:
                # TRAVA DE SEGURANÇA: Desliga o bot após enviar a transação
                save_json("bot_state.json", {"status": "OFF"})
                registrar_log("Operação Real Iniciada. Bot em PAUSA para conferência.", "SISTEMA", "SUCESSO")
        
        time.sleep(60)

threading.Thread(target=sniper_loop, daemon=True).start()

# --- ROTAS FLASK ---
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
        c = web3.eth.contract(address=web3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_ERC20))
        usdc = round(c.functions.balanceOf(CARTEIRA_ALVO).call() / 1e6, 2)
    except: pol, usdc = "Erro", "Erro"

    return render_template('dashboard.html', 
                           wallet=CARTEIRA_ALVO, pol=pol, usdc=usdc, 
                           bot=load_json("bot_state.json", {"status": "OFF"}), 
                           historico=load_json("logs.json", []))

@app.route('/toggle_bot', methods=['POST'])
@login_required
def toggle_bot():
    status = request.form.get("status")
    save_json("bot_state.json", {"status": status})
    registrar_log(f"Bot alterado para {status}", "SISTEMA")
    return redirect(url_for('index'))

@app.route('/gerar_relatorio_pdf')
@login_required
def gerar_relatorio_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Relatorio de Operacoes Reais", ln=True, align="C")
    for log in load_json("logs.json", []):
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 7, f"{log['data']} | {log['mercado']} | {log['resultado']}", ln=True)
    return send_file(BytesIO(pdf.output()), mimetype='application/pdf', as_attachment=True, download_name="relatorio.pdf")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))