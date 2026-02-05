import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN_SISTEMA = os.environ.get("guardiao") 
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
    with open(LOGS_FILE, "w") as f: json.dump(logs[:12], f)

# --- MOTOR DE BUSCA VIA API (NÃO BLOQUEIA) ---
def motor_api():
    while True:
        try:
            # 1. Busca POL (Nativo) - Usando API Pública do Polygonscan
            # Se você tiver uma API Key, coloque-a no final: &apikey=SUA_CHAVE
            url_pol = f"https://api.polygonscan.com/api?module=account&action=balance&address={WALLET}&tag=latest"
            r1 = requests.get(url_pol, timeout=10).json()
            if r1.get('status') == '1':
                cache["pol"] = f"{int(r1['result']) / 10**18:.4f}"

            # 2. Busca USDC (Token)
            url_usdc = f"https://api.polygonscan.com/api?module=account&action=tokenbalance&contractaddress={USDC_CONTRACT}&address={WALLET}&tag=latest"
            r2 = requests.get(url_usdc, timeout=10).json()
            if r2.get('status') == '1':
                cache["usdc"] = f"{int(r2['result']) / 10**6:.2f}"
            
            registrar("SCAN", "POLYGON", "CONECTADO", "LIVE")
        except:
            registrar("ERRO", "CONEXÃO", "RETRY", "FAIL")
        
        time.sleep(20)

threading.Thread(target=motor_api, daemon=True).start()

# --- INTERFACE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if not PIN_SISTEMA: return "ERRO: Defina 'guardiao' no Render."
    if request.method == 'POST' and request.form.get('pin') == PIN_SISTEMA:
        session['auth'] = True
        return redirect(url_for('dash'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>LOGIN SNIPER</h1><form method="post"><input type="password" name="pin" autofocus><button type="submit">ENTRAR</button></form></body>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect(url_for('login'))
    
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['st']}</td><td style='color:lime;'>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:750px; margin:auto; border:1px solid #333; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px; margin-bottom:20px;">
                <h2 style="color:orange; margin:0;">🛡️ SNIPER TERMINAL v25</h2>
                <div style="text-align:right;">
                    <div>POL: <b style="color:cyan;">{cache['pol']}</b></div>
                    <div>USDC: <b style="color:lime;">{cache['usdc']}</b></div>
                </div>
            </div>
            <table style="width:100%; text-align:left; border-collapse:collapse;">
                <tr style="color:#555; border-bottom:1px solid #444;"><th>HORA</th><th>MERCADO</th><th>STATUS</th><th>VALOR</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)