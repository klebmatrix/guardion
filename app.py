import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN = os.environ.get("guardiao")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Endereço do Contrato USDC na Polygon
USDC_CONTRACT = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
USDC_ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

logs = []
def add_log(msg):
    agora = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{agora}] {msg}")
    if len(logs) > 20: logs.pop()

def obter_saldos():
    try:
        # Saldo POL
        pol = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
        # Saldo USDC
        contrato = w3.eth.contract(address=USDC_CONTRACT, abi=USDC_ABI)
        usdc_raw = contrato.functions.balanceOf(WALLET).call()
        usdc = usdc_raw / 10**6 # USDC tem 6 casas decimais
        return pol, usdc
    except:
        return 0.0, 0.0

# Motor de monitorização (mesmo da v46.1)
def motor_autonomo():
    add_log("🧠 MOTOR DE DECISÃO EM EXECUÇÃO")
    while True:
        try:
            # Lógica de análise aqui...
            time.sleep(15)
        except: pass

threading.Thread(target=motor_autonomo, daemon=True).start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:lime;text-align:center;padding-top:100px;font-family:monospace;"><h2>SISTEMA v46.2</h2><form method="post"><input type="password" name="pin" placeholder="PIN" autofocus><button type="submit">ENTRAR</button></form></body>'

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    
    pol, usdc = obter_saldos()
    log_render = "".join([f"<div style='border-bottom:1px solid #222;padding:5px;'>{l}</div>" for l in logs])
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:2px solid lime; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid lime; padding-bottom:10px; margin-bottom:20px;">
                <h2 style="color:lime; margin:0;">🤖 TERMINAL AUTOMÁTICO</h2>
                <div style="text-align:right;">
                    POL: <b style="color:cyan;">{pol:.4f}</b><br>
                    USDC: <b style="color:yellow;">{usdc:.2f} $</b>
                </div>
            </div>
            <div style="background:#0a0a0a; height:350px; overflow-y:auto; padding:10px; font-size:12px; color:#0f0;">
                {log_render}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)