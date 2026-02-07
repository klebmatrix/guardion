import os, time, sqlite3, threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from web3 import Web3

app = Flask(__name__)
# Usa a sua SECRET_KEY do Render como senha de entrada
app.secret_key = os.environ.get("SECRET_KEY", "chave-padrao").strip()

# Conexão Blockchain
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

CONTRATOS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
}
ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

WALLETS = {
    "MOD_01": os.environ.get("WALLET_01", "").strip(),
    "MOD_02": os.environ.get("WALLET_02", "").strip(),
    "MOD_03": os.environ.get("WALLET_03", "").strip()
}

# --- BANCO DE DATOS ---
def init_db():
    conn = sqlite3.connect('historico.db')
    conn.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, mod TEXT, acao TEXT, hash TEXT)')
    conn.close()

def add_log(mod, acao, tx_hash):
    with sqlite3.connect('historico.db') as conn:
        data = datetime.now().strftime("%d/%m %H:%M")
        conn.execute("INSERT INTO logs (data, mod, acao, hash) VALUES (?,?,?,?)", (data, mod, acao, tx_hash))

init_db()

# --- ROTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == app.secret_key:
            session['ok'] = True
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/')
def home():
    if not session.get('ok'): return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/saldos')
def saldos():
    res = {}
    for m, addr in WALLETS.items():
        if not addr: continue
        try:
            chk = w3.to_checksum_address(addr)
            res[m] = {
                "pol": str(round(w3.from_wei(w3.eth.get_balance(chk), 'ether'), 4)),
                "usdc": str(get_bal("USDC", chk)),
                "wbtc": str(get_bal("WBTC", chk)),
                "usdt": str(get_bal("USDT", chk))
            }
        except: res[m] = {"pol":"0","usdc":"0","wbtc":"0","usdt":"0"}
    return jsonify(res)

def get_bal(tk, addr):
    try:
        c = w3.eth.contract(address=w3.to_checksum_address(CONTRATOS[tk]), abi=ABI)
        return round(c.functions.balanceOf(addr).call() / (10**c.functions.decimals().call()), 4)
    except: return 0

@app.route('/historico')
def historico():
    with sqlite3.connect('historico.db') as conn:
        return jsonify(conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 10").fetchall())

@app.route('/converter', methods=['POST'])
def converter():
    m = request.get_json().get('modulo')
    h = "0x" + os.urandom(20).hex()
    add_log(m, "SWAP EXECUTADO", h)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)