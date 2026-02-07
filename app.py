import os, time, sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from web3 import Web3

app = Flask(__name__)
app.secret_key = str(os.environ.get("SECRET_KEY", "123")).strip()

RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

CONTRATOS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
}
ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

def init_db():
    conn = sqlite3.connect('historico.db')
    conn.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, mod TEXT, acao TEXT, hash TEXT)')
    conn.commit()
    conn.close()

init_db()

@app.route('/health')
def health():
    return jsonify({"status": "ONLINE" if w3.is_connected() else "OFFLINE"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == app.secret_key:
            session['autenticado'] = True
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/')
def home():
    if not session.get('autenticado'): return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/saldos')
def saldos():
    if not session.get('autenticado'): return jsonify({})
    res = {}
    wallets = {
        "MOD_01": str(os.environ.get("WALLET_01", "")).strip(),
        "MOD_02": str(os.environ.get("WALLET_02", "")).strip(),
        "MOD_03": str(os.environ.get("WALLET_03", "")).strip()
    }
    for m, addr in wallets.items():
        if len(addr) < 40:
            res[m] = {"pol":"0", "usdc":"0", "wbtc":"0", "usdt":"0"}
            continue
        try:
            chk = w3.to_checksum_address(addr)
            res[m] = {
                "pol": str(round(w3.from_wei(w3.eth.get_balance(chk), 'ether'), 4)),
                "usdc": str(get_bal("USDC", chk)),
                "wbtc": str(get_bal("WBTC", chk)),
                "usdt": str(get_bal("USDT", chk))
            }
        except: res[m] = {"pol":"0", "usdc":"0", "wbtc":"0", "usdt":"0"}
    return jsonify(res)

def get_bal(tk, addr):
    try:
        c = w3.eth.contract(address=w3.to_checksum_address(CONTRATOS[tk]), abi=ABI)
        raw = c.functions.balanceOf(addr).call()
        return round(raw / (10**c.functions.decimals().call()), 4)
    except: return 0

@app.route('/historico')
def historico():
    conn = sqlite3.connect('historico.db')
    rows = conn.execute("SELECT * VALUES FROM logs ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()
    return jsonify(rows or [])

@app.route('/converter', methods=['POST'])
def converter():
    m = request.get_json().get('modulo')
    tx = "0x" + os.urandom(20).hex()
    with sqlite3.connect('historico.db') as conn:
        conn.execute("INSERT INTO logs (data, mod, acao, hash) VALUES (?,?,?,?)", (datetime.now().strftime("%H:%M:%S"), m, "SWAP", tx))
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)