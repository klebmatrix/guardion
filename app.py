import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN_SISTEMA = os.environ.get("guardiao") 
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
LOGS_FILE = "movimentacoes.json"

def registrar(acao, mkt, st, val="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mkt, "st": st, "val": val})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:10], f)

# --- MOTOR DE SCAN ---
def motor():
    while True:
        try:
            # Puxa mercados da Polymarket diretamente
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&closed=false&limit=15", timeout=15)
            if r.status_code == 200:
                for ev in r.json():
                    m = ev.get('markets', [{}])[0]
                    p = float(m.get('outcomePrices', ["0"])[0])
                    if 0.10 < p < 0.90:
                        roi = round(((1/p)-1)*100, 1)
                        if roi > 10:
                            registrar("🎯 ALVO", ev.get('title')[:15], f"LUCRO {roi}%", f"P:{p}")
            registrar("SCAN", "SISTEMA", "A VIGIAR", "LIVE")
        except: pass
        time.sleep(15)

threading.Thread(target=motor, daemon=True).start()

# --- LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if not PIN_SISTEMA:
        return 'ERRO: Configura a variavel "guardiao" no Render.'
    if request.method == 'POST' and request.form.get('pin') == PIN_SISTEMA:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>SNIPER LOGIN</h1><form method="post"><input type="password" name="pin" autofocus><button type="submit">ENTRAR</button></form></body>'

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    
    pol, usdc = "...", "..."
    try:
        # Consulta de POL (Usando o RPC oficial da Polygon para evitar bloqueios)
        rpc_data = {"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}
        r_pol = requests.post("https://polygon-rpc.com", json=rpc_data, timeout=10).json()
        pol = round(int(r_pol['result'], 16) / 10**18, 4)

        # Consulta de USDC
        token_data = {"jsonrpc":"2.0","method":"eth_call","params":[{"to":USDC_CONTRACT,"data":"0x70a08231000000000000000000000000" + WALLET[2:]},"latest"],"id":1}
        r_usdc = requests.post("https://polygon-rpc.com", json=token_data, timeout=10).json()
        usdc = round(int(r_usdc['result'], 16) / 10**6, 2)
    except: pass

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['st']}</td><td style='color:lime;'>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:1px solid #333; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="color:orange;">⚡ SNIPER TERMINAL v21</h2>
                <div style="text-align:right;">
                    <div>POL: <b style="color:cyan;">{pol}</b></div>
                    <div>USDC: <b style="color:lime;">{usdc}</b></div>
                </div>
            </div>
            <table style="width:100%; margin-top:20px; text-align:left;">
                <tr style="color:#555;"><th>HORA</th><th>MERCADO</th><th>STATUS</th><th>VALOR</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)