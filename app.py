import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN_SISTEMA = os.environ.get("guardiao") 
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
LOGS_FILE = "movimentacoes.json"

# Cache global para não travar a rota principal
cache_dados = {"pol": "0.0000", "usdc": "0.00"}

def registrar(acao, mkt, st, val="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mkt, "st": st, "val": val})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:10], f)

# --- MOTOR DE ATUALIZAÇÃO (RODA EM SEGUNDO PLANO) ---
def motor_background():
    while True:
        try:
            # 1. Busca Mercados
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&closed=false&limit=10", timeout=5)
            if r.status_code == 200:
                registrar("SCAN", "SISTEMA", "VIGIANDO", "LIVE")

            # 2. Busca Saldo (Via RPC - Rápido)
            rpc_url = "https://polygon-rpc.com"
            # Saldo POL
            p1 = requests.post(rpc_url, json={"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}, timeout=5).json()
            cache_dados["pol"] = f"{int(p1['result'], 16) / 10**18:.4f}"
            
            # Saldo USDC
            p2 = requests.post(rpc_url, json={"jsonrpc":"2.0","method":"eth_call","params":[{"to":USDC_CONTRACT,"data":"0x70a08231000000000000000000000000" + WALLET[2:]},"latest"],"id":1}, timeout=5).json()
            cache_dados["usdc"] = f"{int(p2['result'], 16) / 10**6:.2s}"
        except:
            pass
        time.sleep(30) # Atualiza a cada 30 segundos para não sobrecarregar

threading.Thread(target=motor_background, daemon=True).start()

# --- ROTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if not PIN_SISTEMA: return "Configure 'guardiao' no Render."
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['auth'] = True
            return redirect(url_for('dash'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>LOGIN</h1><form method="post"><input type="password" name="pin" autofocus><button type="submit">OK</button></form></body>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect(url_for('login'))
    
    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr><td>{l['hora']}</td><td>{l['mkt']}</td><td>{l['st']}</td><td style='color:lime;'>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#000; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:600px; margin:auto; border:1px solid #333; padding:20px;">
            <h2 style="color:orange;">🛡️ TERMINAL v22</h2>
            <p>POL: <b style="color:cyan;">{cache_dados['pol']}</b> | USDC: <b style="color:lime;">{cache_dados['usdc']}</b></p>
            <table style="width:100%; text-align:left; font-size:12px;">
                <tr style="color:#555;"><th>HORA</th><th>MKT</th><th>ST</th><th>VAL</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)