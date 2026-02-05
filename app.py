import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO DE SEGURANÇA ESTRITA ---
# AGORA BUSCA EXCLUSIVAMENTE DO RENDER. SEM PADRÃO NO CÓDIGO.
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
    with open(LOGS_FILE, "w") as f: json.dump(logs[:15], f)

# --- MOTOR DE SCAN ---
def motor():
    while True:
        try:
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&closed=false&limit=15", timeout=10)
            if r.status_code == 200:
                for ev in r.json():
                    m = ev.get('markets', [{}])[0]
                    p = float(m.get('outcomePrices', ["0"])[0])
                    if 0.10 < p < 0.90:
                        roi = round(((1/p)-1)*100, 1)
                        if roi > 8: # Filtro agressivo
                            registrar("🎯 ALVO", ev.get('title')[:15], f"LUCRO {roi}%", f"P:{p}")
            registrar("SCAN", "SISTEMA", "BUSCANDO", "LIVE")
        except: pass
        time.sleep(20)

threading.Thread(target=motor, daemon=True).start()

# --- LOGIN VINCULADO AO RENDER ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se a variável 'guardiao' não estiver configurada no Render, o sistema avisa
    if not PIN_SISTEMA:
        return '<body style="background:red;color:white;text-align:center;padding:50px;"><h2>ERRO CRÍTICO</h2>A variável "guardiao" não foi encontrada no painel do Render. Configure-a para acessar.</body>'

    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session.clear()
            session['auth'] = True
            return redirect(url_for('dashboard'))
        return 'ACESSO NEGADO. <a href="/login">Tente novamente</a>'
    
    return '''
    <body style="background:#000; color:orange; font-family:monospace; text-align:center; padding-top:100px;">
        <div style="border:2px solid orange; display:inline-block; padding:50px;">
            <h1>🛡️ SNIPER TERMINAL</h1>
            <p>Insira os 8 dígitos configurados no Render</p>
            <form method="post">
                <input type="password" name="pin" maxlength="8" autofocus 
                       style="font-size:24px; padding:10px; width:220px; text-align:center; background:#111; color:orange; border:1px solid orange;"><br><br>
                <button type="submit" style="padding:12px 40px; background:orange; color:black; font-weight:bold; cursor:pointer; border:none;">ENTRAR</button>
            </form>
        </div>
    </body>'''

@app.route('/')
def dashboard():
    if not session.get('auth'):
        return redirect(url_for('login'))
    
    try:
        # Pega POL (Seu 4.1284)
        r_pol = requests.get(f"https://api.polygonscan.com/api?module=account&action=balance&address={WALLET}&tag=latest").json()
        pol = round(int(r_pol['result']) / 10**18, 4)
        
        # Pega USDC (Seu dinheiro de aposta)
        url_u = f"https://api.polygonscan.com/api?module=account&action=tokenbalance&contractaddress={USDC_CONTRACT}&address={WALLET}&tag=latest"
        r_u = requests.get(url_u).json()
        usdc = round(int(r_u.get('result', 0)) / 10**6, 2)
    except:
        pol, usdc = "OFF", "OFF"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['st']}</td><td style='color:lime;'>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:850px; margin:auto; border:1px solid #444; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="color:orange; margin:0;">⚡ SNIPER TERMINAL v19</h2>
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