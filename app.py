import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_final_2026")

# --- DADOS TÉCNICOS ---
RPC_URL = "https://polygon-rpc.com"
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
LOGS_FILE = "movimentacoes.json"

def registrar_log(acao, mercado, status, valor="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mercado, "st": status, "val": valor})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:20], f)

# --- MOTOR SNIPER (EM SEGUNDO PLANO) ---
def motor_sniper():
    time.sleep(15) # Dá tempo para o servidor subir antes de iniciar o scan
    while True:
        try:
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&limit=10", timeout=10)
            if r.status_code == 200:
                registrar_log("SCAN", "RADAR", "BUSCANDO", "OK")
        except: pass
        time.sleep(30)

threading.Thread(target=motor_sniper, daemon=True).start()

# --- ROTAS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # O PIN deve ser configurado no Render como 'guardiao'
        if request.form.get('pin') == os.environ.get("guardiao", "20262026"):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return '''
    <body style="background:#000; color:orange; font-family:sans-serif; text-align:center; padding-top:100px;">
        <div style="display:inline-block; border:2px solid orange; padding:40px; border-radius:15px; background:#0a0a0a;">
            <h2 style="margin-bottom:20px;">🛡️ SNIPER TERMINAL</h2>
            <form method="post">
                <input type="password" name="pin" placeholder="Digite o PIN" autofocus 
                       style="padding:12px; width:200px; border-radius:5px; border:1px solid orange; background:#111; color:white;">
                <br><br>
                <button type="submit" style="padding:12px 30px; background:orange; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">ACESSAR</button>
            </form>
        </div>
    </body>'''

@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Busca saldos reais via Web3
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 3)
        abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
        c = w3.eth.contract(address=USDC_ADDR, abi=json.loads(abi))
        usdc = round(c.functions.balanceOf(WALLET).call() / 10**6, 2)
    except: pol, usdc = "0.000", "0.00"

    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: pass
    
    rows = "".join([f"<tr style='border-bottom:1px solid #333;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['acao']}</td><td style='color:#00ff00;'>{l['st']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:850px; margin:auto; border:1px solid #444; padding:20px; background:#0a0a0a; border-radius:10px;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="margin:0; color:orange;">⚡ DASHBOARD SNIPER</h2>
                <div style="text-align:right;">POL: {pol} | USDC: {usdc}</div>
            </div>
            <table style="width:100%; margin-top:20px; text-align:left;">
                <tr style="color:#777;"><th>HORA</th><th>ALVO</th><th>AÇÃO</th><th>STATUS</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))