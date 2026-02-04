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

# Endereços
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
CTF_EXCHANGE = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"

# ABI ERC20 completa para saldo e aprovação
ABI_ERC20 = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","bool":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"}]'

web3 = Web3(Web3.HTTPProvider(RPC_URL))
CARTEIRA_ALVO = web3.to_checksum_address("0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E")
file_lock = threading.Lock()

# --- UTILITÁRIOS ---
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

# --- LÓGICA DE MOVIMENTAÇÃO REAL ---
def verificar_e_aprovar(valor_usdc):
    """Verifica se já existe permissão, se não, gasta POL para aprovar."""
    try:
        account = web3.eth.account.from_key(PRIV_KEY)
        contract = web3.eth.contract(address=web3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_ERC20))
        
        valor_wei = int(valor_usdc * 10**6)
        
        # 1. Checar se já aprovamos antes (Allowance)
        permissao_atual = contract.functions.allowance(account.address, web3.to_checksum_address(CTF_EXCHANGE)).call()
        
        if permissao_atual >= valor_wei:
            return "Já Aprovado" # Não gasta POL à toa se já houver permissão

        # 2. Se não tem permissão, faz o Approve
        nonce = web3.eth.get_transaction_count(account.address)
        tx = contract.functions.approve(web3.to_checksum_address(CTF_EXCHANGE), 100 * 10**6).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': web3.eth.gas_price
        })
        signed_tx = web3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()
    except Exception as e:
        return f"Erro: {str(e)[:30]}"

# --- SNIPER LOOP ---
def sniper_loop():
    while True:
        state = load_json("bot_state.json", {"status": "OFF"})
        if state["status"] == "ON" and PRIV_KEY:
            # Tenta verificar aprovação para 1 USDC
            res = verificar_e_aprovar(1.0)
            
            if res == "Já Aprovado":
                registrar_log("Caminho Livre: USDC já aprovado para uso.", "SISTEMA", "PRONTO")
                # Próxima fase: Aqui entrará a função de COMPRA de cotas (Trade)
                # Por segurança, mantemos OFF até você validar que o erro de gastar POL parou
                save_json("bot_state.json", {"status": "OFF"})
            elif "Erro" in res:
                registrar_log(res, "ERRO", "FALHA")
            else:
                registrar_log(f"Nova Aprovação Enviada: {res[:10]}", "BLOCKCHAIN", "AGUARDAR")
        
        time.sleep(60)

threading.Thread(target=sniper_loop, daemon=True).start()

# --- ROTAS FLASK ---
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
@wraps(lambda: None) # Apenas para garantir consistência
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
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
def toggle_bot():
    status = request.form.get("status")
    save_json("bot_state.json", {"status": status})
    registrar_log(f"Bot alterado para {status}", "SISTEMA")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))