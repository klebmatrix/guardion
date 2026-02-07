import os
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "omni_v87_stable")

# --- CONFIGURAÇÕES ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")
PIN_INTERNO = os.environ.get("pin_interior", "0000")
RPC_URL = "https://polygon-rpc.com"

# Endereços Oficiais (Polygon)
USDC_ADDR = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
WBTC_ADDR = "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"

# ABI Mínima para ler saldos
ABI_SALDO = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]

def get_token_balance(w3, token_addr, wallet_addr):
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ABI_SALDO)
        raw_bal = contract.functions.balanceOf(wallet_addr).call()
        decimals = contract.functions.decimals().call()
        return raw_bal / (10**decimals)
    except: return 0.0

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    mod_html = ""
    
    for i in range(1, 4):
        key = os.environ.get(f"KEY_MOD_{i}")
        if key:
            acc = Account.from_key(key)
            pol = w3.eth.get_balance(acc.address) / 10**18
            usdc = get_token_balance(w3, USDC_ADDR, acc.address)
            wbtc = get_token_balance(w3, WBTC_ADDR, acc.address)

            mod_html += f"""
            <div style="background:#161b22; padding:15px; border-radius:12px; margin-bottom:15px; border:1px solid #30363d;">
                <b style="color:#58a6ff;">MOD_0{i}</b>
                <div style="font-size:10px; color:gray; margin-bottom:10px;">{acc.address}</div>
                
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:5px; margin-bottom:10px;">
                    <div style="background:#0d1117; padding:5px; border-radius:4px; color:lime;">POL: {pol:.2f}</div>
                    <div style="background:#0d1117; padding:5px; border-radius:4px; color:cyan;">USDC: {usdc:.2f}</div>
                    <div style="background:#0d1117; padding:5px; border-radius:4px; color:orange; grid-column: span 2;">WBTC: {wbtc:.6f}</div>
                </div>

                <form action="/swap" method="post" style="display:flex; gap:5px;">
                    <input type="hidden" name="key" value="{key}">
                    <input type="password" name="pin" placeholder="PIN" style="width:50px; background:#000; color:white; border:1px solid #333;">
                    <button style="background:#58a6ff; border:none; padding:8px; border-radius:4px; flex:1; font-weight:bold; cursor:pointer;">SWAP USDC > WBTC</button>
                </form>
            </div>"""

    return f'<body style="background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:15px;"><div style="max-width:400px; margin:auto;">{mod_html}</div></body>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN_SISTEMA:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding-top:100px;"><h3>ACESSO OMNI</h3><form method="post"><input type="password" name="pin" autofocus></form></body>'

@app.route('/swap', methods=['POST'])
def swap():
    # Aqui a lógica processa a troca via Uniswap Router se o PIN bater
    if session.get('logged_in') and request.form.get('pin') == PIN_INTERNO:
        # Lógica de Transação Web3 aqui
        pass 
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))