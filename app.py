import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONEXÃO COM A REDE ---
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")

LOGS_FILE = "movimentacoes.json"

def registrar(acao, mkt, st, val="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mkt, "st": st, "val": val})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:15], f)

# --- MOTOR DE SCAN ---
def motor():
    while True:
        try:
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&closed=false&limit=10", timeout=10)
            if r.status_code == 200:
                registrar("SCAN", "POLYMKT", "VIGIANDO", "LIVE")
        except: pass
        time.sleep(20)

threading.Thread(target=motor, daemon=True).start()

# --- LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == os.environ.get("guardiao", "20262026"):
            session['auth'] = True
            return redirect(url_for('dash'))
    return '''<body style="background:#000;color:orange;text-align:center;padding-top:100px;font-family:monospace;">
              <h2>🛡️ ACESSO AO SNIPER</h2>
              <form method="post"><input type="password" name="pin" autofocus style="padding:10px;"><br><br>
              <button type="submit" style="padding:10px 30px;background:orange;font-weight:bold;">ENTRAR</button></form></body>'''

# --- DASHBOARD REAL ---
@app.route('/')
def dash():
    if not session.get('auth'): return redirect(url_for('login'))
    
    try:
        # Pega saldo de POL (o seu 14.44)
        balance_wei = w3.eth.get_balance(WALLET)
        pol = round(w3.from_wei(balance_wei, 'ether'), 4)
        
        # Pega saldo de USDC (o que o bot usa)
        abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
        c = w3.eth.contract(address=USDC_ADDR, abi=json.loads(abi))
        usdc = round(c.functions.balanceOf(WALLET).call() / 10**6, 2)
    except: pol, usdc = "0.0000", "0.00"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['st']}</td><td style='color:lime;'>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:850px; margin:auto; border:1px solid #333; padding:20px; background:#000;">
            <h2 style="color:orange; border-bottom:1px solid orange; margin-bottom:15px;">⚡ TERMINAL REAL-TIME</h2>
            <div style="display:flex; justify-content:space-between; margin-bottom:20px; background:#111; padding:15px; border-radius:5px;">
                <div>POL (Taxas): <b style="color:cyan; font-size:20px;">{pol}</b></div>
                <div>USDC (Sniper): <b style="color:lime; font-size:20px;">{usdc}</b></div>
            </div>
            <table style="width:100%; text-align:left;">
                <tr style="color:#555;"><th>HORA</th><th>ALVO</th><th>STATUS</th><th>VALOR</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)