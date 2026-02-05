import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÕES DE REDE ---
NETWORKS = {
    'BSC': 'https://bsc-dataseed.binance.org',
    'POLYGON': 'https://polygon-rpc.com'
}

WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
PIN = os.environ.get("guardiao")

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(logs) > 15: logs.pop()

# --- MOTOR DE EXECUÇÃO ---
def motor_autonomo():
    add_log("🤖 SNIPER MULTICHAIN ATIVADO")
    while True:
        for name, rpc in NETWORKS.items():
            try:
                w3 = Web3(Web3.HTTPProvider(rpc))
                balance_wei = w3.eth.get_balance(WALLET)
                balance = float(w3.from_wei(balance_wei, 'ether'))

                if balance > 0.01: # Se tiver saldo mínimo
                    add_log(f"💰 Detectado: {balance:.4f} {name}")
                    
                    # LÓGICA DE VENDA/COMPRA (Exemplo: Vende se preço subir 2%)
                    # Aqui o bot decide se faz o Swap via PancakeSwap (BSC) ou QuickSwap (Polygon)
                    # add_log(f"🎯 Monitorando alvo para {name}...")
                
            except Exception as e:
                add_log(f"⚠️ Erro em {name}: {str(e)[:20]}")
        
        time.sleep(30)

threading.Thread(target=motor_autonomo, daemon=True).start()

# --- INTERFACE ---
@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    log_render = "".join([f"<div style='border-bottom:1px solid #222;padding:5px;'>{l}</div>" for l in logs])
    return f"""
    <body style="background:#000; color:#eee; font-family:monospace; padding:20px;">
        <h2 style="color:#f3ba2f;">🟡 MULTI-NET SNIPER v57</h2>
        <div style="border:1px solid #f3ba2f; padding:15px; background:#111;">
            CARTEIRA: <b>{WALLET[:10]}...</b><br>
            STATUS: <b>VIGIANDO BSC + POLYGON</b>
        </div>
        <div style="margin-top:20px; font-size:12px; color:lime;">{log_render}</div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:50px;">' \
           '<h2>ACESSO RESTRITO</h2><form method="post"><input type="password" name="pin"><button>ENTRAR</button></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)