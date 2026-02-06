import os, datetime, json, threading, time, random
from flask import Flask, request, redirect, url_for, session, make_response
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "omni_qi_ultra_v85")

# --- CONFIGURAÇÕES ---
RPC_URL = "https://polygon-rpc.com"
WBTC_CONTRACT = "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]')

STATE_FILE = "bot_state.json"
LOGS_FILE = "logs.json"

def get_w3():
    try:
        w = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 10}))
        return w if w.is_connected() else None
    except: return None

def get_token_balance(w3, token_address, wallet_address):
    try:
        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        return contract.functions.balanceOf(wallet_address).call() / (10**contract.functions.decimals().call())
    except: return 0.0

def load_j(f, d):
    if os.path.exists(f):
        try:
            with open(f, "r") as file: return json.load(file)
        except: return d
    return d

# --- INTERFACE ---
@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    w3 = get_w3()
    state = load_j(STATE_FILE, {})
    
    mod_html = ""
    for i in range(1, 4):
        key = os.environ.get(f"KEY_MOD_{i}")
        if key:
            nome = f"MOD_0{i}"
            addr = Account.from_key(key).address
            status = state.get(nome, "OFF")
            cor = "#00ff00" if status == "ON" else "#ff4b4b"
            
            # Busca saldos se o W3 estiver ativo
            pol, btc, usd = 0, 0, 0
            if w3:
                pol = w3.eth.get_balance(addr) / 10**18
                btc = get_token_balance(w3, WBTC_CONTRACT, addr)
                usd = get_token_balance(w3, USDC_CONTRACT, addr)

            mod_html += f"""
            <div style="background:#161b22; padding:15px; border-radius:12px; margin-bottom:15px; border:1px solid #30363d; border-left: 5px solid {cor};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b>{nome}</b> <span style="color:{cor}; font-size:12px;">● {status}</span>
                </div>
                <div style="font-size:11px; color:#8b949e; margin:5px 0;">{addr[:12]}...{addr[-10:]}</div>
                <div style="display:flex; gap:10px; font-size:12px; margin:10px 0;">
                    <span style="color:orange;">BTC: {btc:.6f}</span>
                    <span style="color:cyan;">USD: {usd:.2f}</span>
                    <span style="color:lime;">POL: {pol:.2f}</span>
                </div>
                <form action="/toggle" method="post" style="display:flex; gap:5px;">
                    <input type="hidden" name="mod_name" value="{nome}">
                    <input type="password" name="pin_int" placeholder="PIN" style="width:50px; background:#0d1117; color:white; border:1px solid #333; padding:5px;">
                    <button name="act" value="ON" style="background:#238636; color:white; border:none; border-radius:4px; flex:1; cursor:pointer;">LIGAR</button>
                    <button name="act" value="OFF" style="background:#da3633; color:white; border:none; border-radius:4px; flex:1; cursor:pointer;">DESLIGAR</button>
                </form>
            </div>"""

    return f"""
    <body style="background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:20px;">
        <div style="max-width:500px; margin:auto;">
            <h2 style="color:#58a6ff; text-align:center;">OMNI ORQUESTRADOR QI</h2>
            
            <div style="background:#1c2128; padding:20px; border-radius:12px; border:1px dashed #58a6ff; margin-bottom:25px; text-align:center;">
                <h4 style="margin:0 0 10px 0; color:#58a6ff;">GERADOR DE INTELIGÊNCIA (QI)</h4>
                <form action="/gerar" method="post">
                    <input type="password" name="pin_int" placeholder="PIN INTERIOR" style="padding:8px; border-radius:5px; border:1px solid #333; background:#0d1117; color:white;">
                    <button style="background:#58a6ff; color:black; font-weight:bold; border:none; padding:8px 15px; border-radius:5px; cursor:pointer;">GERAR NOVA KEY</button>
                </form>
                {f'<div style="background:#000; padding:15px; margin-top:15px; font-size:11px; color:lime; border:1px solid #238636; word-break:break-all;"><b>NOVA CARTEIRA GERADA:</b><br><br>ENDEREÇO: {session.get("new_addr")}<br>CHAVE PRIVADA: {session.get("new_key")}<br><br><small style="color:orange;">Copiou? Ela sumirá ao recarregar.</small></div>' if "new_key" in session else ""}
            </div>

            {mod_html}

            <p style="text-align:center; font-size:10px; color:#444;">Refresh Automático: 30s</p>
        </div>
        <script>setTimeout(() => {{ if(!document.querySelector('input[type="password"]:focus')) {{ location.reload(); }} }}, 30000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == os.environ.get("guardiao", "123456"):
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding-top:100px;font-family:sans-serif;"><h3>ACESSO OMNI</h3><form method="post"><input type="password" name="pin" autofocus style="padding:10px;"></form></body>'

@app.route('/toggle', methods=['POST'])
def toggle():
    if not session.get('logged_in'): return redirect(url_for('login'))
    mod, act, pin = request.form.get('mod_name'), request.form.get('act'), request.form.get('pin_int')
    
    if pin == os.environ.get("pin_interior", "0000"):
        state = load_j(STATE_FILE, {})
        state[mod] = act
        with open(STATE_FILE, "w") as f: json.dump(state, f)
    return redirect(url_for('dashboard'))

@app.route('/gerar', methods=['POST'])
def gerar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.form.get('pin_int') == os.environ.get("pin_interior", "0000"):
        acc = Account.create()
        session['new_addr'] = acc.address
        session['new_key'] = acc._private_key.hex()
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))