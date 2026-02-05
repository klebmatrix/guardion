import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24) # Reseta a sessão toda vez para forçar o login

# --- CONFIGURAÇÕES DIRETAS ---
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
PIN_MEU = os.environ.get("guardiao", "20262026")
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

# --- MOTOR DE BUSCA LEVE (NÃO TRAVA O RENDER) ---
def motor_real():
    while True:
        try:
            # Busca direta na API da Polymarket (Sem frescura)
            res = requests.get("https://gamma-api.polymarket.com/events?active=true&closed=false&limit=20", timeout=10)
            if res.status_code == 200:
                dados = res.json()
                for item in dados:
                    mkt = item.get('markets', [{}])[0]
                    price = float(mkt.get('outcomePrices', ["0"])[0])
                    
                    if 0.10 < price < 0.90:
                        roi = round(((1 / price) - 1) * 100, 1)
                        # FILTRO REAL: Se o lucro for maior que 10%, ele registra
                        if roi > 10:
                            registrar("🎯 ALVO", item.get('title')[:15], f"LUCRO {roi}%", f"R$ {price}")
            registrar("SCAN", "SISTEMA", "VIGIANDO", "LIVE")
        except Exception as e:
            pass
        time.sleep(20)

threading.Thread(target=motor_real, daemon=True).start()

# --- INTERFACE DE ACESSO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_MEU:
            session['logado'] = True
            return redirect(url_for('dashboard'))
        else:
            return 'PIN INCORRETO. <a href="/login">Tentar novamente</a>'
    
    return '''
    <body style="background:#000; color:orange; font-family:monospace; text-align:center; padding-top:100px;">
        <div style="border:2px solid orange; display:inline-block; padding:50px;">
            <h1>SISTEMA DE ACESSO</h1>
            <form method="post">
                PIN: <input type="password" name="pin" autofocus style="font-size:20px;"><br><br>
                <button type="submit" style="padding:10px 20px; background:orange; cursor:pointer; font-weight:bold;">ENTRAR NO SNIPER</button>
            </form>
        </div>
    </body>
    '''

@app.route('/')
def dashboard():
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # Busca Saldo Real via API de Explorer (Mais leve que Web3)
    try:
        url_bal = f"https://api.polygonscan.com/api?module=account&action=balance&address={WALLET}&tag=latest"
        r_bal = requests.get(url_bal).json()
        pol = round(int(r_bal['result']) / 10**18, 2)
    except: pol = "Erro"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #333;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['acao']}</td><td style='color:lime;'>{l['st']}</td><td>{l['val']}</td></tr>" for l in logs])

    return f'''
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:1px solid #444; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange;">
                <h2 style="color:orange;">⚡ SNIPER REAL-TIME</h2>
                <p>POL: <b>{pol}</b> | WALLET: <b>...{WALLET[-6:]}</b></p>
            </div>
            <table style="width:100%; margin-top:20px; text-align:left;">
                <tr style="color:#666;"><th>HORA</th><th>ALVO</th><th>AÇÃO</th><th>STATUS</th><th>VALOR</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>
    '''

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))