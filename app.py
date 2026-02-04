import os, json, threading, time, requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# O Gunicorn procura exatamente por esta linha:
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

# --- CONFIGURAÇÕES ---
RPC_URL = "https://polygon-rpc.com"
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
CTF_EXCHANGE = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"
PRIV_KEY = os.environ.get("private_key")
CARTEIRA = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"

ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","bool":"bool"}],"type":"function"}]'

w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# --- FUNÇÕES AUXILIARES ---
def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r") as f: return json.load(f)
        except: pass
    return padrao

def salvar_dados(arquivo, dados):
    with open(arquivo, "w") as f: json.dump(dados, f)

def registrar_log(mensagem, acao="SISTEMA", resultado="OK"):
    logs = carregar_dados("logs.json", [])
    logs.insert(0, {"data": datetime.now().strftime("%H:%M:%S"), "mercado": mensagem, "lado": acao, "resultado": resultado})
    salvar_dados("logs.json", logs[:15])

# --- LÓGICA DE TRADE ---
def executar_trade_usdc(token_id, valor_usdc=1.0):
    try:
        registrar_log(f"Iniciando Trade de {valor_usdc} USDC", "SNIPER", "ORDEM")
        # Simulação de sucesso para validar o fluxo
        registrar_log(f"Sucesso! 1.0 USDC -> {token_id[:8]}", "TRADE", "EXECUTADO")
        salvar_dados("bot_state.json", {"status": "OFF"})
        return True
    except Exception as e:
        registrar_log(f"Erro Trade: {str(e)[:20]}", "TRADE", "FALHA")
        return False

def motor_bot():
    while True:
        status = carregar_dados("bot_state.json", {"status": "OFF"})
        if status.get("status") == "ON" and PRIV_KEY:
            try:
                account = w3.eth.account.from_key(PRIV_KEY)
                contract = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
                permissao = contract.functions.allowance(account.address, w3.to_checksum_address(CTF_EXCHANGE)).call()
                
                if permissao >= (1 * 10**6):
                    ID_TOKEN_YES = "0x2713309603378E81550930d4a002d6A6A8a832"
                    executar_trade_usdc(ID_TOKEN_YES, 1.0)
                else:
                    registrar_log("Aguardando Allowance...", "BLOCKCHAIN", "WAIT")
            except Exception as e:
                registrar_log(f"Erro Motor: {str(e)[:20]}", "MOTOR", "FALHA")
        time.sleep(60)

# Inicia o motor
threading.Thread(target=motor_bot, daemon=True).start()

# --- ROTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == os.environ.get("guardiao", "123456"):
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        bal_pol = round(w3.from_wei(w3.eth.get_balance(CARTEIRA), 'ether'), 4)
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
        bal_usdc = round(c.functions.balanceOf(CARTEIRA).call() / 1e6, 2)
    except: bal_pol, bal_usdc = "Erro", "Erro"
    return render_template('dashboard.html', wallet=CARTEIRA, pol=bal_pol, usdc=bal_usdc, 
                           bot=carregar_dados("bot_state.json", {"status": "OFF"}), 
                           historico=carregar_dados("logs.json", []))

@app.route('/toggle_bot', methods=['POST'])
def toggle_bot():
    novo = request.form.get("status")
    salvar_dados("bot_state.json", {"status": novo})
    registrar_log(f"Bot em {novo}", "USUARIO", "OK")
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)