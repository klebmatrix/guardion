import os, datetime, json, threading, time
from flask import Flask, request, redirect, url_for, session, make_response
from web3 import Web3
from eth_account import Account
try:
    from fpdf import FPDF
except ImportError:
    pass # Evita queda se fpdf não carregar

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "safe_iq_2026")

# --- CONFIGS ---
RPC_URL = "https://polygon-rpc.com"
WBTC_CONTRACT = "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]')

def get_w3():
    try:
        w = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 10}))
        return w if w.is_connected() else None
    except: return None

def get_token_balance(w3, token_address, wallet_address):
    try:
        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        raw = contract.functions.balanceOf(wallet_address).call()
        dec = contract.functions.decimals().call()
        return raw / (10**dec)
    except: return 0.0

# --- INTERFACE ---
@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    w3 = get_w3()
    if not w3: return "Erro: Falha na conexão com a Rede Polygon (RPC)."
    
    mod_html = ""
    for i in range(1, 4):
        key = os.environ.get(f"KEY_MOD_{i}")
        if key:
            try:
                addr = Account.from_key(key).address
                pol = w3.eth.get_balance(addr) / 10**18
                btc = get_token_balance(w3, WBTC_CONTRACT, addr)
                usd = get_token_balance(w3, USDC_CONTRACT, addr)
                
                mod_html += f"""
                <div style="background:#161b22; padding:15px; border-radius:12px; margin-bottom:15px; border:1px solid #30363d;">
                    <b>MODULO {i}</b><br>
                    <small style="color:#8b949e;">{addr}</small>
                    <div style="margin-top:10px; font-weight:bold;">
                        <span style="color:orange;">BTC: {btc:.6f}</span> | 
                        <span style="color:cyan;">USD: {usd:.2f}</span> | 
                        <span style="color:lime;">POL: {pol:.2f}</span>
                    </div>
                </div>"""
            except: continue

    return f"""
    <body style="background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:20px;">
        <div style="max-width:600px; margin:auto;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style="color:#58a6ff;">OMNI IQ</h2>
                <a href="/relatorio" style="background:#30363d; color:white; padding:8px; border-radius:5px; text-decoration:none; font-size:12px;">BAIXAR PDF</a>
            </div>
            <div style="background:#1c2128; padding:15px; border-radius:10px; border:1px dashed #58a6ff; margin:20px 0; text-align:center;">
                <form action="/gerar" method="post">
                    <input type="password" name="pin_int" placeholder="PIN INTERIOR" style="padding:5px;">
                    <button type="submit" style="background:#58a6ff; border:none; padding:6px; cursor:pointer; font-weight:bold;">GERAR CARTEIRA</button>
                </form>
                {f'<div style="background:#000; padding:10px; margin-top:10px; font-size:10px; color:lime; word-break:break-all;">KEY: {session.pop("new_key", "")}</div>' if "new_key" in session else ""}
            </div>
            {mod_html}
        </div>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    pin_correto = os.environ.get("guardiao", "123456")
    if request.method == 'POST' and request.form.get('pin') == pin_correto:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding:100px;"><form method="post"><h3>PIN</h3><input type="password" name="pin" autofocus></form></body>'

@app.route('/gerar', methods=['POST'])
def gerar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.form.get('pin_int') == os.environ.get("pin_interior", "0000"):
        acc = Account.create()
        session['new_key'] = acc._private_key.hex()
    return redirect(url_for('dashboard'))

@app.route('/relatorio')
def relatorio():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Relatório de Auditoria OMNI", ln=1, align='C')
        pdf.cell(200, 10, txt=f"Data: {datetime.datetime.now()}", ln=2, align='L')
        
        response = make_response(pdf.output(dest='S').encode('latin-1'))
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'attachment', filename='auditoria.pdf')
        return response
    except Exception as e:
        return f"Erro ao gerar PDF: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))