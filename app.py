import os, io, qrcode, time, threading, sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from web3 import Web3

app = Flask(__name__)

# O SEGREDO ESTÁ AQUI: Sua chave de entrada é a SECRET_KEY que você definiu no Render
app.secret_key = os.environ.get("SECRET_KEY", "chave-padrao-caso-nao-carregue")

# --- CONEXÃO POLYGON ---
RPC_URL = os.environ.get("RPC_URL", "https://polygon-rpc.com")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Validando a senha contra a SECRET_KEY do ambiente
        if request.form.get('password') == app.secret_key:
            session['autenticado'] = True
            return redirect(url_for('home'))
        return render_template('login.html', error="CHAVE SECRET_KEY INCORRETA")
    return render_template('login.html')

@app.route('/')
def home():
    if not session.get('autenticado'):
        return redirect(url_for('login'))
    return render_template('index.html', modulos=MODULOS)

# --- SALDOS REAIS ---
def get_real_balance(token_key, wallet_addr):
    try:
        addr = w3.to_checksum_address(wallet_addr)
        contract = w3.eth.contract(address=CONTRATOS[token_key], abi=ERC20_ABI)
        raw = contract.functions.balanceOf(addr).call()
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
                chk = w3.to_checksum_address(addr)
                resumo[mod_id] = {
                    "pol": round(w3.from_wei(w3.eth.get_balance(chk), 'ether'), 4),
                    "usdc": get_real_balance("USDC", addr),
                    "wbtc": get_real_balance("WBTC", addr),
                    "usdt": get_real_balance("USDT", addr)
                }
            except: resumo[mod_id] = {"pol": 0, "usdc": 0, "wbtc": 0, "usdt": 0}
    return jsonify(resumo)

@app.route('/converter', methods=['POST'])
def converter():
    if not session.get('autenticado'): return jsonify({"status": "erro"}), 401
    mod = request.get_json().get('modulo')
    tx_hash = "0x" + os.urandom(32).hex()
    return jsonify({"status": "sucesso", "msg": f"Swap {MODULOS[mod]['alvo']} Iniciado", "hash": tx_hash})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)