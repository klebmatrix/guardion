import os, io, qrcode
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "guardion-master-key-2026")

# --- CONFIGURAÇÃO BLOCKCHAIN (POLYGON) ---
RPC_URL = os.environ.get("RPC_URL", "https://polygon-rpc.com")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# ABI Mínima para Tokens (USDC, WBTC, USDT)
ERC20_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

CONTRATOS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
}

# --- CONFIGURAÇÃO DE ACESSO ---
ADMIN_USER = os.environ.get("USER_LOGIN", "guardiao")
ADMIN_PASS = os.environ.get("USER_PASS", "1234")

MODULOS = {
    "MOD_01": os.environ.get("WALLET_01"), # ESTRATÉGIA: USDC -> WBTC
    "MOD_02": os.environ.get("WALLET_02"), # ESTRATÉGIA: USDC -> USDT
    "MOD_03": os.environ.get("WALLET_03")  # ESTRATÉGIA: MULTI CRYPTO
}

# --- FUNÇÕES DE APOIO ---
def get_token_balance(token_key, wallet_addr):
    try:
        if not wallet_addr or "0x" not in wallet_addr: return 0.0
        contract = w3.eth.contract(address=CONTRATOS[token_key], abi=ERC20_ABI)
        raw_balance = contract.functions.balanceOf(wallet_addr).call()
        decimals = contract.functions.decimals().call()
        return round(raw_balance / (10**decimals), 6)
    except: return 0.0

# --- ROTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('home'))
        return render_template('login.html', error="Acesso Negado!")
    return render_template('login.html')

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html', modulos=MODULOS)

@app.route('/saldos')
def obter_saldos():
    if not session.get('logged_in'): return jsonify({}), 401
    resumo = {}
    for mod, addr in MODULOS.items():
        resumo[mod] = {
            "pol": round(w3.from_wei(w3.eth.get_balance(addr), 'ether'), 4) if addr else 0,
            "usdc": get_token_balance("USDC", addr),
            "wbtc": get_token_balance("WBTC", addr),
            "usdt": get_token_balance("USDT", addr)
        }
    return jsonify(resumo)

@app.route('/converter', methods=['POST'])
def converter():
    if not session.get('logged_in'): return jsonify({"status": "erro"}), 401
    
    dados = request.get_json()
    mod = dados.get('modulo')
    
    # Lógica de ordens do Kleber
    if mod == "MOD_01":
        msg = "ORDEM: Todo USDC em conta sendo convertido para WBTC (Bitcoin)."
    elif mod == "MOD_02":
        msg = "ORDEM: Todo USDC em conta sendo convertido para USDT (Tether)."
    elif mod == "MOD_03":
        msg = "ORDEM: Diversificação Multi-Crypto iniciada (Cesta de Ativos)."
    else:
        return jsonify({"status": "erro", "msg": "Módulo Inválido"})

    tx_hash = "0x" + os.urandom(32).hex() # Simulando o Hash da transação real
    
    return jsonify({
        "status": "sucesso",
        "msg": msg,
        "hash": tx_hash
    })

@app.route('/qr/<path:text>')
def qr(text):
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)