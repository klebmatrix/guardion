import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
# Isso força a troca da chave de sessão toda vez que o app reinicia
app.secret_key = os.urandom(24) 

# --- CONFIGS ---
RPC_URL = "https://polygon-rpc.com"
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
LOGS_FILE = "movimentacoes.json"

def registrar_log(acao, mercado, status):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mercado, "st": status})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:15], f)

# Motor em segundo plano
def motor_sniper():
    time.sleep(10)
    while True:
        try:
            requests.get("https://gamma-api.polymarket.com/events?active=true&limit=5", timeout=10)
            registrar_log("SCAN", "SISTEMA", "VIGIANDO")
        except: pass
        time.sleep(40)

threading.Thread(target=motor_sniper, daemon=True).start()

# --- FORÇAR TELA DE LOGIN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pin_usuario = request.form.get('pin')
        pin_correto = os.environ.get("guardiao", "20262026")
        if pin_usuario == pin_correto:
            session['auth_sniper'] = True
            return redirect(url_for('index'))
    
    return '''
    <body style="background:#000; color:orange; font-family:sans-serif; text-align:center; padding-top:100px;">
        <div style="display:inline-block; border:2px solid orange; padding:50px; border-radius:10px;">
            <h1>SISTEMA BLOQUEADO</h1>
            <p>Insira o PIN de Segurança:</p>
            <form method="post">
                <input type="password" name="pin" autofocus style="padding:10px; font-size:20px; text-align:center;"><br><br>
                <button type="submit" style="padding:10px 40px; background:orange; border:none; font-weight:bold; cursor:pointer;">ENTRAR</button>
            </form>
        </div>
    </body>
    '''

@app.route('/')
def index():
    if not session.get('auth_sniper'):
        return redirect(url_for('login'))
    
    # Busca saldos
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 3)
        abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
        c = w3.eth.contract(address=USDC_ADDR, abi=json.loads(abi))
        usdc = round(c.functions.balanceOf(WALLET).call() / 10**6, 2)
    except: pol, usdc = "Erro", "Erro"

    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: pass
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td>{l['acao']}</td><td style='color:orange;'>{l['mkt']}</td><td style='color:lime;'>{l['st']}</td></tr>" for l in logs])

    return f'''
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:1px solid #444; padding:20px;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange;">
                <h2 style="color:orange;">⚡ SNIPER TERMINAL</h2>
                <p>POL: {pol} | USDC: {usdc}</p>
            </div>
            <table style="width:100%; margin-top:20px; text-align:left;">
                <tr style="color:#666;"><th>HORA</th><th>AÇÃO</th><th>MERCADO</th><th>STATUS</th></tr>
                {rows}
            </table>
            <br><a href="/logout" style="color:red;">Sair do Sistema</a>
        </div>
        <script>setTimeout(()=>location.reload(), 20000);</script>
    </body>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))