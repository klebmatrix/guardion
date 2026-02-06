import os, datetime, json, threading, time
from flask import Flask, request, redirect, url_for, session, make_response
from web3 import Web3
from eth_account import Account
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "omni_iq_report_2026")

# --- CONFIGS E TOKENS ---
RPC_LIST = ["https://polygon-rpc.com", "https://polygon.llamarpc.com"]
WBTC_CONTRACT = "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
ERC20_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

def get_w3():
    for url in RPC_LIST:
        try:
            w = Web3(Web3.HTTPProvider(url))
            if w.is_connected(): return w
        except: continue
    return None

def get_token_balance(w3, token_address, wallet_address):
    try:
        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=json.loads(ERC20_ABI))
        raw = contract.functions.balanceOf(wallet_address).call()
        dec = contract.functions.decimals().call()
        return raw / (10**dec)
    except: return 0.0

STATE_FILE = "bot_state.json"
LOGS_FILE = "logs.json"

# --- GERADOR DE RELATÓRIO PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'RELATORIO DE AUDITORIA - OMNI IQ', 0, 1, 'C')
        self.ln(10)

@app.route('/relatorio')
def relatorio():
    if not session.get('logged_in'): return redirect(url_for('login'))
    w3 = get_w3()
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    pdf.cell(0, 10, f"Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 1)
    pdf.ln(5)
    
    for i in range(1, 6):
        key = os.environ.get(f"KEY_MOD_{i}")
        if key:
            addr = w3.eth.account.from_key(key).address
            pol = w3.eth.get_balance(addr) / 10**18
            btc = get_token_balance(w3, WBTC_CONTRACT, addr)
            usd = get_token_balance(w3, USDC_CONTRACT, addr)
            
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 10, f"MODULO {i} - {addr}", 1, 1, 'L', True)
            pdf.cell(0, 10, f"  POL: {pol:.4f} | BTC: {btc:.6f} | USD: {usd:.2f}", 1, 1)
            pdf.ln(2)

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename='auditoria_omni.pdf')
    return response

# --- DASHBOARD (INCLUINDO BOTÃO DE PDF) ---
@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    w3 = get_w3()
    mod_html = ""
    for i in range(1, 6):
        key = os.environ.get(f"KEY_MOD_{i}")
        if key:
            nome = f"MOD_0{i}"
            addr = w3.eth.account.from_key(key).address
            pol = w3.eth.get_balance(addr) / 10**18
            btc = get_token_balance(w3, WBTC_CONTRACT, addr)
            usd = get_token_balance(w3, USDC_CONTRACT, addr)
            
            mod_html += f"""
            <div style="background:#161b22; padding:15px; border-radius:12px; margin-bottom:15px; border:1px solid #30363d;">
                <b>{nome}</b>
                <div style="font-size:11px; color:#8b949e;">{addr}</div>
                <div style="margin:10px 0; font-size:13px;">
                    <span style="color:orange;">BTC: {btc:.6f}</span> | 
                    <span style="color:cyan;">USD: {usd:.2f}</span> | 
                    <span style="color:lime;">POL: {pol:.2f}</span>
                </div>
            </div>"""

    return f"""
    <body style="background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:20px;">
        <div style="max-width:600px; margin:auto;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style="color:#58a6ff;">OMNI IQ v86.4</h2>
                <a href="/relatorio" style="text-decoration:none; background:#30363d; color:white; padding:8px 15px; border-radius:5px; font-size:12px;">📄 BAIXAR PDF</a>
            </div>
            
            <div style="background:#1c2128; padding:15px; border-radius:10px; border:1px dashed #58a6ff; margin:20px 0; text-align:center;">
                <form action="/gerar" method="post">
                    <input type="password" name="pin_int" placeholder="PIN INTERIOR" style="padding:5px;">
                    <button style="background:#58a6ff; color:black; font-weight:bold; border:none; padding:6px 15px; border-radius:5px; cursor:pointer;">GERAR NOVO MÓDULO</button>
                </form>
                {f'<div style="background:#000; padding:10px; margin-top:10px; font-size:11px; color:lime; word-break:break-all;"><b>NOVA CARTEIRA:</b><br>ADDR: {session.pop("new_addr", "")}<br>KEY: {session.pop("new_key", "")}</div>' if "new_key" in session else ""}
            </div>

            {mod_html}
        </div>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == os.environ.get("guardiao", "123456"):
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding:100px;"><h3>ACESSO IQ</h3><form method="post"><input type="password" name="pin" autofocus></form></body>'

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