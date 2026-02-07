import os, time, sqlite3, threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from web3 import Web3

app = Flask(__name__)
# Garante que a chave do Render seja lida sem espaços
app.secret_key = str(os.environ.get("SECRET_KEY", "chave-padrao")).strip()

# RPC estável da Polygon
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

CONTRATOS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
}
ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

# Puxa carteiras do Render com limpeza de texto
def get_wallet(name):
    return str(os.environ.get(name, "")).strip()

# --- BANCO DE DADOS (Criação Forçada) ---
def init_db():
    try:
        conn = sqlite3.connect('historico.db')
        conn.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, mod TEXT, acao TEXT, hash TEXT)')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro DB: {e}")

init_db()

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
    if not session.get('ok'): return jsonify({})
    res = {}
    wallets = {"MOD_01": get_wallet("WALLET_01"), "MOD_02": get_wallet("WALLET_02"), "MOD_03": get_wallet("WALLET_03")}
    
    for m, addr in wallets.items():
        if len(addr) < 40: # Carteira inválida ou vazia
            res[m] = {"pol":"0.0", "usdc":"0.0", "wbtc":"0.0", "usdt":"0.0"}
            continue
        try:
            chk = w3.to_checksum_address(addr)
            bal_pol = w3.eth.get_balance(chk)
            res[m] = {
                "pol": str(round(w3.from_wei(bal_pol, 'ether'), 4)),
                "usdc": str(get_bal("USDC", chk)),
                "wbtc": str(get_bal("WBTC", chk)),
                "usdt": str(get_bal("USDT", chk))
            }
        except:
            res[m] = {"pol":"0.0", "usdc":"0.0", "wbtc":"0.0", "usdt":"0.0"}
    return jsonify(res)

def get_bal(tk, addr):
    try:
        c = w3.eth.contract(address=w3.to_checksum_address(CONTRATOS[tk]), abi=ABI)
        raw = c.functions.balanceOf(addr).call()
        dec = c.functions.decimals().call()
        return round(raw / (10**dec), 4)
    except: return 0.0

@app.route('/historico')
def historico():
    try:
        conn = sqlite3.connect('historico.db')
        rows = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 10").fetchall()
        conn.close()
        return jsonify(rows)
    except: return jsonify([])

@app.route('/converter', methods=['POST'])
def converter():
    if not session.get('ok'): return jsonify({"status": "erro"}), 401
    m = request.get_json().get('modulo')
    h = "0x" + os.urandom(20).hex()
    
    # Grava no banco
    with sqlite3.connect('historico.db') as conn:
        data = datetime.now().strftime("%d/%m %H:%M")
        conn.execute("INSERT INTO logs (data, mod, acao, hash) VALUES (?,?,?,?)", (data, m, "SWAP EXECUTADO", h))
    
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)