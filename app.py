import os; os.system("pip install qrcode[pil]")
import os, sys
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "diagnostico_v87")

# Configurações de Ambiente
PIN_SISTEMA = os.environ.get("guardiao", "123456")
RPC_URL = "https://polygon-rpc.com"

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        mod_html = ""
        
        # Tenta carregar as chaves com segurança
        for i in range(1, 4):
            key = os.environ.get(f"KEY_MOD_{i}")
            if key:
                acc = Account.from_key(key)
                # Fallback se a rede falhar
                try:
                    pol = w3.eth.get_balance(acc.address) / 10**18
                except:
                    pol = 0.0
                
                mod_html += f"""
                <div style="background:#161b22; padding:10px; border-radius:8px; margin-bottom:10px; border:1px solid #333;">
                    <b style="color:#58a6ff;">MOD_0{i}</b><br>
                    <small style="color:gray;">{acc.address}</small><br>
                    <b style="color:lime;">POL: {pol:.2f}</b>
                </div>"""
                
        return f"""
        <body style="background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:20px;">
            <h3>OMNI v87.2 - SISTEMA ATIVO</h3>
            {mod_html if mod_html else "<p>Nenhuma KEY_MOD_X configurada no Render.</p>"}
        </body>"""
    
    except Exception as e:
        # Se der erro, ele mostra o texto do erro na tela
        return f"<h1>ERRO DE DIAGNÓSTICO:</h1><p>{str(e)}</p>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding-top:100px;">' \
           '<h3>PAINEL OMNI</h3><form method="post"><input type="password" name="pin" autofocus></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
import os, io, base64
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account
import qrcode

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "omni_v87_qr")

PIN_SISTEMA = os.environ.get("guardiao", "123456")
PIN_INTERNO = os.environ.get("pin_interior", "0000")
RPC_URL = "https://polygon-rpc.com"

def get_qr(address):
    img = qrcode.make(address)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    mod_html = ""
    
    for i in range(1, 4):
        key = os.environ.get(f"KEY_MOD_{i}")
        if key:
            acc = Account.from_key(key)
            qr_base64 = get_qr(acc.address)
            
            mod_html += f"""
            <div style="background:#161b22; padding:15px; border-radius:12px; margin-bottom:15px; border:1px solid #30363d; text-align:center;">
                <b style="color:#58a6ff;">MÓDULO 0{i}</b><br>
                <img src="data:image/png;base64,{qr_base64}" style="width:120px; margin:10px; border:4px solid #fff; border-radius:8px;"><br>
                <small style="color:gray; font-size:9px; word-break:break-all;">{acc.address}</small>
                
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-top:10px;">
                    <div style="background:#000; padding:5px; border-radius:4px; color:lime; font-size:12px;">POL: SCAN</div>
                    <div style="background:#000; padding:5px; border-radius:4px; color:cyan; font-size:12px;">USDC: SCAN</div>
                </div>

                <form action="/swap" method="post" style="margin-top:10px; display:flex; gap:5px;">
                    <input type="password" name="pin" placeholder="PIN" style="width:50px; background:#000; color:#fff; border:1px solid #444;">
                    <button style="background:#58a6ff; border:none; padding:8px; border-radius:4px; font-weight:bold; flex:1; cursor:pointer;">SWAP TO BTC</button>
                </form>
            </div>"""

    return f"""
    <body style="background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:10px;">
        <div style="max-width:400px; margin:auto;">
            <h2 style="text-align:center; color:#58a6ff;">OMNI QR-PAY ⚡</h2>
            {mod_html}
        </div>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN_SISTEMA:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding-top:100px;"><h3>DIGITE PIN</h3><form method="post"><input type="password" name="pin" autofocus></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))