import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN_SISTEMA = os.environ.get("guardiao") 
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
LOGS_FILE = "movimentacoes.json"

# Cache global para exibição instantânea
cache = {"pol": "Sincronizando...", "usdc": "Sincronizando..."}

def registrar(acao, mkt, st, val="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mkt, "st": st, "val": val})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:12], f)

# --- MOTOR DE CONEXÃO ROBUSTA ---
def motor_resiliente():
    # Lista de Nodes (Se um cair, o outro assume)
    rpcs = [
        "https://polygon-rpc.com",
        "https://rpc-mainnet.maticvigil.com",
        "https://rpc.ankr.com/polygon",
        "https://1rpc.io/matic"
    ]
    
    while True:
        for node in rpcs:
            try:
                # 1. Busca Saldo POL
                p1 = requests.post(node, json={"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}, timeout=5).json()
                if 'result' in p1:
                    cache["pol"] = f"{int(p1['result'], 16) / 10**18:.4f}"
                
                # 2. Busca Saldo USDC
                data_hex = "0x70a08231000000000000000000000000" + WALLET[2:]
                p2 = requests.post(node, json={"jsonrpc":"2.0","method":"eth_call","params":[{"to":USDC_CONTRACT,"data":data_hex},"latest"],"id":1}, timeout=5).json()
                if 'result' in p2:
                    cache["usdc"] = f"{int(p2['result'], 16) / 10**6:.2f}"
                
                # Se chegou aqui, a conexão foi um sucesso
                break 
            except:
                continue # Tenta o próximo node se este falhar
        
        registrar("SCAN", "SISTEMA", "VIGIANDO", "LIVE")
        time.sleep(15)

threading.Thread(target=motor_resiliente, daemon=True).start()

# --- INTERFACE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if not PIN_SISTEMA: return "ERRO: Variavel 'guardiao' obrigatoria no Render."
    if request.method == 'POST' and request.form.get('pin') == PIN_SISTEMA:
        session['auth'] = True
        return redirect(url_for('dash'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;font-family:monospace;"><h1>🛡️ SNIPER v24</h1><form method="post"><input type="password" name="pin" maxlength="8" autofocus style="padding:10px;font-size:20px;"><br><br><button type="submit" style="padding:10px 40px;background:orange;font-weight:bold;">ENTRAR</button></form></body>'

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
                <h2 style="color:orange; margin:0;">🛡️ SNIPER TERMINAL</h2>
                <div style="text-align:right;">
                    <div>POL: <b style="color:cyan;">{cache['pol']}</b></div>
                    <div>USDC: <b style="color:lime;">{cache['usdc']}</b></div>
                </div>
            </div>
            <table style="width:100%; text-align:left; border-collapse:collapse;">
                <tr style="color:#555; border-bottom:1px solid #444;"><th>HORA</th><th>ALVO</th><th>STATUS</th><th>RESULTADO</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 8000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)