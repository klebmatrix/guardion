import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN_SISTEMA = os.environ.get("guardiao") 
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
LOGS_FILE = "movimentacoes.json"

# Cache para não travar a tela
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

# --- MOTOR DE RESGATE DE SALDO ---
def motor_resgate():
    # RPC da Cloudflare (Geralmente não bloqueia o Render)
    rpc_url = "https://polygon-rpc.com"
    
    while True:
        try:
            # Busca POL (O seu 4.1284)
            payload_pol = {"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}
            r1 = requests.post(rpc_url, json=payload_pol, timeout=10).json()
            if 'result' in r1:
                saldo_pol = int(r1['result'], 16) / 10**18
                cache["pol"] = f"{saldo_pol:.4f}"

            # Busca USDC (Banca)
            # 0x70a08231 é o seletor para 'balanceOf(address)'
            data_hex = "0x70a08231000000000000000000000000" + WALLET[2:]
            payload_usdc = {"jsonrpc":"2.0","method":"eth_call","params":[{"to":USDC_CONTRACT,"data":data_hex},"latest"],"id":1}
            r2 = requests.post(rpc_url, json=payload_usdc, timeout=10).json()
            if 'result' in r2:
                saldo_usdc = int(r2['result'], 16) / 10**6
                cache["usdc"] = f"{saldo_usdc:.2f}"
            
            registrar("SCAN", "REDE", "SINCRO", "OK")
        except:
            registrar("SCAN", "REDE", "ERRO", "BUSCANDO")
        
        time.sleep(20)

threading.Thread(target=motor_resgate, daemon=True).start()

# --- LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if not PIN_SISTEMA: return "ERRO: Variavel 'guardiao' no Render vazia."
    if request.method == 'POST' and request.form.get('pin') == PIN_SISTEMA:
        session['auth'] = True
        return redirect(url_for('dash'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>🛡️ ACESSO SNIPER</h1><form method="post"><input type="password" name="pin" autofocus><br><br><button type="submit">ENTRAR</button></form></body>'

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
        <div style="max-width:700px; margin:auto; border:1px solid #444; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="color:orange; margin:0;">⚡ SNIPER TERMINAL v26</h2>
                <div style="text-align:right;">
                    <div>POL (TAXA): <b style="color:cyan;">{cache['pol']}</b></div>
                    <div>USDC (BANCA): <b style="color:lime;">{cache['usdc']}</b></div>
                </div>
            </div>
            <table style="width:100%; text-align:left; margin-top:20px;">
                <tr style="color:#555;"><th>HORA</th><th>ALVO</th><th>STATUS</th><th>VALOR</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)