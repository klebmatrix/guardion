import os, json, datetime
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
# Chave mestra de segurança para a sessão não cair
app.secret_key = os.environ.get("FLASK_SECRET", "OMNI_STABLE_V86")

# --- CONFIGS COM FALLBACK (Se não houver no Render, usa esses) ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")
PIN_INTERNO = os.environ.get("pin_interior", "0000")
RPC_URL = "https://polygon-rpc.com"

# ABI Mínima
ERC20_ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]

# Pasta temporária do Render para salvar estados
STATE_FILE = "/tmp/bot_state.json"

def get_balance_safe(w3, addr):
    try:
        return w3.eth.get_balance(addr) / 10**18
    except: return 0.0

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        return "PIN INCORRETO <a href='/login'>Tentar de novo</a>"
    return '<body style="background:#000;color:cyan;text-align:center;padding-top:100px;">' \
           '<h3>PAINEL OMNI</h3><form method="post"><input type="password" name="pin" autofocus></form></body>'

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    # Conexão Web3 Silenciosa
    w3 = None
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 5}))
    except: pass

    mod_html = ""
    for i in range(1, 4):
        key = os.environ.get(f"KEY_MOD_{i}")
        if key:
            try:
                acc = Account.from_key(key)
                pol = get_balance_safe(w3, acc.address) if w3 else 0.0
                mod_html += f"""
                <div style="background:#161b22; padding:15px; border-radius:10px; margin-bottom:10px; border:1px solid #30363d;">
                    <b>MOD_0{i}</b><br>
                    <small style="color:#8b949e;">{acc.address}</small><br>
                    <b style="color:lime;">POL: {pol:.2f}</b>
                </div>"""
            except Exception as e:
                mod_html += f"<div style='color:red;'>Erro na KEY_MOD_{i}</div>"

    return f"""
    <body style="background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:20px;">
        <div style="max-width:450px; margin:auto;">
            <h2 style="color:#58a6ff;">ORQUESTRADOR v86.7</h2>
            <div style="background:#1c2128; padding:15px; border-radius:10px; border:1px dashed #58a6ff; margin-bottom:20px; text-align:center;">
                <form action="/gerar" method="post">
                    <input type="password" name="pin" placeholder="PIN INTERIOR">
                    <button style="background:#58a6ff; border:none; padding:5px; cursor:pointer;">GERAR QI</button>
                </form>
                {f'<div style="color:lime; font-size:10px; margin-top:10px; word-break:break-all;">KEY: {session.pop("new_key", "")}</div>' if "new_key" in session else ""}
            </div>
            {mod_html if mod_html else "<p>Nenhuma KEY_MOD encontrada no Render.</p>"}
        </div>
    </body>"""

@app.route('/gerar', methods=['POST'])
def gerar():
    if session.get('logged_in') and request.form.get('pin') == PIN_INTERNO:
        acc = Account.create()
        session['new_key'] = acc._private_key.hex()
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))