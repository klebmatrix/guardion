import os, io, qrcode, time, threading, sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# --- CONFIGURAÇÃO WEB3 (POLYGON) ---
RPC_URL = os.environ.get("RPC_URL", "https://polygon-rpc.com")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Apenas a Senha do Render
ADMIN_PASS = os.environ.get("USER_PASS", "1234")

CONTRATOS = {
    "USDC": w3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"),
    "WBTC": w3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"),
    "USDT": w3.to_checksum_address("0xc2132D05D31c914a87C6611C10748AEb04B58e8F")
}
ERC20_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

MODULOS = {
    "MOD_01": {"addr": os.environ.get("WALLET_01"), "alvo": "WBTC"},
    "MOD_02": {"addr": os.environ.get("WALLET_02"), "alvo": "USDT"},
    "MOD_03": {"addr": os.environ.get("WALLET_03"), "alvo": "MULTI"}
}

# --- CONTROLE DE ACESSO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Verifica apenas a senha enviada pelo formulário
        if request.form.get('password') == ADMIN_PASS:
            session['autenticado'] = True
            return redirect(url_for('home'))
        return render_template('login.html', error="Chave de Acesso Inválida")
    return render_template('login.html')

@app.route('/')
def home():
    if not session.get('autenticado'):
        return redirect(url_for('login'))
    return render_template('index.html', modulos=MODULOS)

# --- FUNÇÕES DE SALDO ---
def get_balance(key, addr):
    try:
        check_addr = w3.to_checksum_address(addr)
        contract = w3.eth.contract(address=CONTRATOS[key], abi=ERC20_ABI)
        raw = contract.functions.balanceOf(check_addr).call()
        dec = contract.functions.decimals().call()
        return round(raw / (10**dec), 6)
    except: return 0.0

@app.route('/saldos')
def obter_saldos():
    if not session.get('autenticado'): return jsonify({}), 401
    resumo = {}
    for mod_id, dados in MODULOS.items():
        addr = dados['addr']
        if addr and "0x" in addr:
            try:
                check_addr = w3.to_checksum_address(addr)
                resumo[mod_id] = {
                    "pol": round(w3.from_wei(w3.eth.get_balance(check_addr), 'ether'), 4),
                    "usdc": get_balance("USDC", addr),
                    "wbtc": get_balance("WBTC", addr),
                    "usdt": get_balance("USDT", addr)
                }
            except: resumo[mod_id] = {"pol": 0, "usdc": 0, "wbtc": 0, "usdt": 0}
    return jsonify(resumo)

# ... Mantenha as rotas /converter, /historico e o motor_agente aqui abaixo ...
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)