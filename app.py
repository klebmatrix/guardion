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

# Carrega .env para testes locais, no Render ele usa as Environment Variables
load_dotenv()

app = Flask(__name__)
# Chave mestra para as sessões (Login)
app.secret_key = os.environ.get("FLASK_SECRET", "super-secret-key-2026")

# --- CONFIGURAÇÕES DO RENDER ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")
PRIV_KEY = os.environ.get("private_key")
RPC_URL = "https://polygon-rpc.com"

# Segurança para arquivos JSON (evita erro de leitura simultânea)
file_lock = threading.Lock()

# --- WEB3 SETUP ---
web3 = Web3(Web3.HTTPProvider(RPC_URL))
CARTEIRA_ALVO = web3.to_checksum_address("0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E")

# Dados USDC
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

# --- SISTEMA DE ARQUIVOS (JSON) ---
def load_data(filename, default_value):
    with file_lock:
        if not os.path.exists(filename):
            return default_value
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except:
            return default_value

def save_data(filename, data):
    with file_lock:
        try:
            with open(filename, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Erro ao salvar {filename}: {e}")

# --- LOGS ---
def registrar_log(mensagem, lado="SISTEMA", resultado="OK"):
    logs = load_data("logs.json", [])
    novo_log = {
        "data": datetime.now().strftime("%d/%m %H:%M:%S"),
        "mercado": mensagem,
        "lado": lado,
        "resultado": resultado
    }
    logs.insert(0, novo_log)
    save_data("logs.json", logs[:50]) # Mantém apenas os últimos 50

# --- BOT EM BACKGROUND ---
def bot_worker():
    while True:
        state = load_data("bot_state.json", {"status": "OFF"})
        if state.get("status") == "ON" and PRIV_KEY:
            try:
                # Simulação de análise
                registrar_log("Monitorando Polymarket...", "AUTO", "SCAN")
            except Exception as e:
                registrar_log(f"Erro Bot: {str(e)[:20]}", "ERRO", "FALHA")
        time.sleep(300) # Checa a cada 5 min

threading.Thread(target=bot_worker, daemon=True).start()

# --- PROTEÇÃO DE ROTA ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS FLASK ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = "PIN de acesso inválido!"
    return render_template('login.html', error=error)

@app.route('/')
@login_required
def index():
    # Inicializa variáveis para não quebrar o HTML se a Web3 falhar
    saldo_matic = "0.00"
    saldo_usdc = "0.00"
    
    try:
        # Busca MATIC
        matic_wei = web3.eth.get_balance(CARTEIRA_ALVO)
        saldo_matic = round(web3.from_wei(matic_wei, 'ether'), 4)
        
        # Busca USDC (Try/Except interno para não travar por causa de contrato)
        try:
            c_native = web3.eth.contract(address=web3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
            usdc_raw = c_native.functions.balanceOf(CARTEIRA_ALVO).call()
            saldo_usdc = round(usdc_raw / 10**6, 2)
        except:
            saldo_usdc = "Erro RPC"
    except Exception as e:
        print(f"Erro Web3 Geral: {e}")
        saldo_matic = "Offline"

    bot_state = load_data("bot_state.json", {"status": "OFF"})
    historico = load_data("logs.json", [])

    return render_template('dashboard.html', 
                           wallet=CARTEIRA_ALVO,
                           pol=saldo_matic,
                           usdc=saldo_usdc,
                           bot=bot_state,
                           historico=historico)

@app.route('/toggle_bot', methods=['POST'])
@login_required
def toggle_bot():
    novo_status = request.form.get("status")
    save_data("bot_state.json", {"status": novo_status})
    registrar_log(f"Bot alterado para {novo_status}")
    return redirect(url_for('index'))

@app.route('/gerar_relatorio_pdf')
@login_required
def gerar_relatorio_pdf():
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Relatorio Sniper Bot", ln=True, align="C")
        
        logs = load_data("logs.json", [])
        pdf.set_font("Arial", "", 10)
        for l in logs:
            pdf.cell(0, 8, f"{l['data']} | {l['mercado']} | {l['resultado']}", ln=True)
        
        return send_file(BytesIO(pdf.output()), mimetype='application/pdf', as_attachment=True, download_name="relatorio.pdf")
    except Exception as e:
        return f"Erro ao gerar PDF: {e}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)