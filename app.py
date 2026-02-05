import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN_SISTEMA = os.environ.get("guardiao") 
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
LOGS_FILE = "movimentacoes.json"

# Cache com valores iniciais para evitar o 0.0000 eterno
cache_dados = {"pol": "Carregando...", "usdc": "Carregando..."}

def registrar(acao, mkt, st, val="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mkt, "st": st, "val": val})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:10], f)

def motor_background():
    while True:
        try:
            rpc_url = "https://polygon-rpc.com"
            
            # Busca POL (4.1284)
            p1 = requests.post(rpc_url, json={"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}, timeout=10).json()
            if 'result' in p1:
                cache_dados["pol"] = f"{int(p1['result'], 16) / 10**18:.4f}"
            
            # Busca USDC
            p2 = requests.post(rpc_url, json={"jsonrpc":"2.0","method":"eth_call","params":[{"to":USDC_CONTRACT,"data":"0x70a08231000000000000000000000000" + WALLET[2:]},"latest"],"id":1}, timeout=10).json()
            if 'result' in p2:
                cache_dados["usdc"] = f"{int(p2['result'], 16) / 10**6:.2f}"
            
            # Registro de atividade
            registrar("SCAN", "SISTEMA", "VIGIANDO", "LIVE")
        except Exception as e:
            print(f"Erro no motor: {e}")
        
        time.sleep(20) # Atualiza a cada 20 segundos

threading.Thread(target=motor_background, daemon=True).start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not PIN_SISTEMA: return "ERRO: Defina a variavel 'guardiao' no Render."
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
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td>{l['mkt']}</td><td>{l['st']}</td><td style='color:lime;'>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:700px; margin:auto; border:1px solid #444; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px; margin-bottom:15px;">
                <h2 style="color:orange; margin:0;">⚡ SNIPER TERMINAL v23</h2>
                <div style="text-align:right;">
                    <div>POL: <b style="color:cyan;">{cache_dados['pol']}</b></div>
                    <div>USDC: <b style="color:lime;">{cache_dados['usdc']}</b></div>
                </div>
            </div>
            <table style="width:100%; text-align:left; border-collapse:collapse;">
                <tr style="color:#555; border-bottom:1px solid #333;"><th>HORA</th><th>MERCADO</th><th>STATUS</th><th>VALOR</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)