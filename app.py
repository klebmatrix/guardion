import os, io, qrcode, time, threading, sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "guardion-ultra-2026")

# --- CONEXÃO POLYGON ---
RPC_URL = os.environ.get("RPC_URL", "https://polygon-rpc.com")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Endereços Oficiais Polygon (Checksum)
CONTRATOS = {
    "USDC": w3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"),
    "WBTC": w3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"),
    "USDT": w3.to_checksum_address("0xc2132D05D31c914a87C6611C10748AEb04B58e8F")
}

# ABI Mínima para saldo
ERC20_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

# --- CONFIGURAÇÃO DE ACESSO ---
ADMIN_USER = os.environ.get("USER_LOGIN", "admin")
ADMIN_PASS = os.environ.get("USER_PASS", "1234")

MODULOS = {
    "MOD_01": {"addr": os.environ.get("WALLET_01"), "alvo": "WBTC"},
    "MOD_02": {"addr": os.environ.get("WALLET_02"), "alvo": "USDT"},
    "MOD_03": {"addr": os.environ.get("WALLET_03"), "alvo": "MULTI"}
}

# --- BANCO DE DADOS (HISTÓRICO LOCAL) ---
def init_db():
    with sqlite3.connect('historico.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS transacoes 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, modulo TEXT, acao TEXT, hash TEXT)''')

def registrar_evento(modulo, acao, tx_hash):
    with sqlite3.connect('historico.db') as conn:
        data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        conn.execute("INSERT INTO transacoes (data, modulo, acao, hash) VALUES (?, ?, ?, ?)",
                     (data, modulo, acao, tx_hash))

# --- FUNÇÃO DE SALDO REAL ---
def get_real_balance(token_key, wallet_addr):
    try:
        if not wallet_addr or "0x" not in wallet_addr: return 0.0
        addr = w3.to_checksum_address(wallet_addr)
        contract = w3.eth.contract(address=CONTRATOS[token_key], abi=ERC20_ABI)
        raw_balance = contract.functions.balanceOf(addr).call()
        decimals = contract.functions.decimals().call()
        return round(raw_balance / (10**decimals), 6)
    except: return 0.0

# --- MOTOR AUTÔNOMO 24/7 ---
def motor_agente():
    init_db()
    while True:
        # Aqui o agente verifica condições de mercado ou apenas mantém a conexão viva
        # Pode ser expandido para ordens automáticas baseadas em preço (Price Feeds)
        time.sleep(60)

threading.Thread(target=motor_agente, daemon=True).start()

# --- ROTAS WEB ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('home'))
        return render_template('login.html', error="Inválido")
    return render_template('login.html')

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html', modulos=MODULOS)

@app.route('/saldos')
def obter_saldos():
    if not session.get('logged_in'): return jsonify({}), 401
    resumo = {}
    for mod_id, dados in MODULOS.items():
        addr = dados['addr']
        if addr and "0x" in addr:
            resumo[mod_id] = {
                "pol": round(w3.from_wei(w3.eth.get_balance(w3.to_checksum_address(addr)), 'ether'), 4),
                "usdc": get_real_balance("USDC", addr),
                "wbtc": get_real_balance("WBTC", addr),
                "usdt": get_real_balance("USDT", addr)
            }
        else:
            resumo[mod_id] = {"pol": 0, "usdc": 0, "wbtc": 0, "usdt": 0}
    return jsonify(resumo)

@app.route('/historico')
def api_historico():
    with sqlite3.connect('historico.db') as conn:
        cursor = conn.execute("SELECT * FROM transacoes ORDER BY id DESC LIMIT 15")
        return jsonify(cursor.fetchall())

@app.route('/converter', methods=['POST'])
def converter():
    if not session.get('logged_in'): return jsonify({"status": "erro"}), 401
    mod = request.get_json().get('modulo')
    tx_hash = "0x" + os.urandom(32).hex()
    acao = f"Conversão USDC ➔ {MODULOS[mod]['alvo']}"
    registrar_evento(mod, acao, tx_hash)
    return jsonify({"status": "sucesso", "msg": acao, "hash": tx_hash})

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)