import os
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "stable_iq_final_2026")

# Memória para manter os módulos ligados/desligados enquanto o servidor rodar
MEMORIA_ESTADOS = {}

# Configurações de PIN
PIN_SISTEMA = os.environ.get("guardiao", "123456")
PIN_INTERNO = os.environ.get("pin_interior", "0000")
RPC_URL = "https://polygon-rpc.com"

def get_balance(addr):
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 5}))
        return w3.eth.get_balance(addr) / 10**18
    except: return 0.0

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN_SISTEMA:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding-top:100px;"><h3>ACESSO OMNI</h3><form method="post"><input type="password" name="pin" autofocus></form></body>'

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    mod_html = ""
    # Processa os 3 módulos principais
    for i in range(1, 4):
        key = os.environ.get(f"KEY_MOD_{i}")
        if key:
            try:
                acc = Account.from_key(key)
                nome = f"MOD_0{i}"
                
                # Se for a primeira vez, já entra como ATIVO (ON)
                if nome not in MEMORIA_ESTADOS:
                    MEMORIA_ESTADOS[nome] = "ON"
                
                status = MEMORIA_ESTADOS[nome]
                cor = "#00ff00" if status == "ON" else "#ff4b4b"
                saldo = get_balance(acc.address)

                mod_html += f"""
                <div style="background:#161b22; padding:15px; border-radius:10px; margin-bottom:12px; border:1px solid #30363d; border-left: 6px solid {cor};">
                    <div style="display:flex; justify-content:space-between;">
                        <b>{nome}</b> <span style="color:{cor};">● {status}</span>
                    </div>
                    <div style="font-size:10px; color:#8b949e;">{acc.address}</div>
                    <div style="color:lime; font-weight:bold; margin:10px 0;">POL: {saldo:.2f}</div>
                    <form action="/toggle" method="post">
                        <input type="hidden" name="mod_name" value="{nome}">
                        <input type="password" name="pin_int" placeholder="PIN" style="width:40px; background:#000; color:#fff; border:1px solid #333;">
                        <button name="act" value="ON" style="background:green; color:white; border:none; padding:5px; cursor:pointer;">LIGAR</button>
                        <button name="act" value="OFF" style="background:red; color:white; border:none; padding:5px; cursor:pointer;">DESLIGAR</button>
                    </form>
                </div>"""
            except: continue

    return f"""
    <body style="background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:15px;">
        <div style="max-width:400px; margin:auto;">
            <h3 style="color:#58a6ff; text-align:center;">OMNI QI ATIVO</h3>
            
            <div style="background:#1c2128; padding:15px; border-radius:10px; border:1px dashed #58a6ff; margin-bottom:20px; text-align:center;">
                <form action="/gerar" method="post">
                    <input type="password" name="pin_int" placeholder="PIN INTERIOR" style="width:100px;">
                    <button style="background:#58a6ff; border:none; padding:5px; cursor:pointer;">GERAR KEY</button>
                </form>
                {f'<div style="color:lime; font-size:10px; margin-top:10px; word-break:break-all;">KEY: {session.pop("new_key", "")}</div>' if "new_key" in session else ""}
            </div>
            {mod_html}
        </div>
    </body>"""

@app.route('/toggle', methods=['POST'])
def toggle():
    if session.get('logged_in') and request.form.get('pin_int') == PIN_INTERNO:
        MEMORIA_ESTADOS[request.form.get('mod_name')] = request.form.get('act')
    return redirect(url_for('dashboard'))

@app.route('/gerar', methods=['POST'])
def gerar():
    if session.get('logged_in') and request.form.get('pin_int') == PIN_INTERNO:
        acc = Account.create()
        session['new_key'] = acc._private_key.hex()
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))