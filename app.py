import os, json, threading, time, requests
from io import BytesIO
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from web3 import Web3
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

# --- CONFIGURAÇÕES BÁSICAS ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")
PRIV_KEY = os.environ.get("private_key")
RPC_URL = "https://polygon-rpc.com"

# Dados da Carteira e Tokens
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
CARTEIRA_ALVO = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
ABI_ERC20 = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

# Inicializa Web3 com timeout para não travar o site
web3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 10}))

# --- PERSISTÊNCIA SIMPLES ---
def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f: return json.load(f)
        except: pass
    return default

def save_json(filename, data):
    with open(filename, "w") as f: json.dump(data, f)

# --- ROTAS ---
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
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Valores iniciais
    pol, usdc = "Carregando...", "Carregando..."
    
    try:
        # Busca MATIC/POL
        balance = web3.eth.get_balance(CARTEIRA_ALVO)
        pol = round(web3.from_wei(balance, 'ether'), 4)
        
        # Busca USDC
        c = web3.eth.contract(address=web3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_ERC20))
        usdc_raw = c.functions.balanceOf(CARTEIRA_ALVO).call()
        usdc = round(usdc_raw / 1e6, 2)
    except Exception as e:
        print(f"Erro ao carregar saldos: {e}")
        pol, usdc = "Erro conexão", "Erro conexão"

    return render_template('dashboard.html', 
                           wallet=CARTEIRA_ALVO, pol=pol, usdc=usdc, 
                           bot=load_json("bot_state.json", {"status": "OFF"}), 
                           historico=load_json("logs.json", []))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)