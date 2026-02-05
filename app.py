import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# CONFIGURAÇÕES
PIN_SISTEMA = os.environ.get("guardiao")
# Se você não colocar nada no Render, ele vai tentar esse link direto:
RPC_URL = os.environ.get("RPC_URL", "https://polygon.llamarpc.com") 
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
LOGS_FILE = "movimentacoes.json"

cache = {"pol": "0.0000", "usdc": "0.00"}

def registrar(acao, mkt, st, val="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mkt, "st": st, "val": val})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:10], f)

def motor():
    while True:
        try:
            # Puxa POL (Seu 4.1284)
            r1 = requests.post(RPC_URL, json={"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}, timeout=15).json()
            if 'result' in r1:
                cache["pol"] = f"{int(r1['result'], 16) / 10**18:.4f}"

            # Puxa USDC
            data_hex = "0x70a08231000000000000000000000000" + WALLET[2:]
            r2 = requests.post(RPC_URL, json={"jsonrpc":"2.0","method":"eth_call","params":[{"to":USDC_CONTRACT,"data":data_hex},"latest"],"id":1}, timeout=15).json()
            if 'result' in r2:
                cache["usdc"] = f"{int(r2['result'], 16) / 10**6:.2f}"
            
            registrar("SCAN", "REDE", "SINCRO", "OK")
        except Exception as e:
            registrar("ERRO", "RPC", "FALHA_CONEXAO", "RETRY")
        time.sleep(20)

threading.Thread(target=motor, daemon=True).start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN_SISTEMA:
        session['auth'] = True
        return redirect(url_for('dash'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>ACESSO TERMINAL</h1><form method="post"><input type="password" name="pin" autofocus><button type="submit">OK</button></form></body>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect(url_for('login'))
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td>{l['mkt']}</td><td>{l['st']}</td><td style='color:lime;'>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:600px; margin:auto; border:1px solid #444; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange;">
                <h2 style="color:orange;">⚡ SNIPER TERMINAL v28</h2>
                <div style="text-align:right;">
                    <div>POL: <b style="color:cyan;">{cache['pol']}</b></div>
                    <div>USDC: <b style="color:lime;">{cache['usdc']}</b></div>
                </div>
            </div>
            <table style="width:100%; margin-top:20px; text-align:left;">
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)