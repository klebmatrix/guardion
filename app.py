import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
# Chave fixa para não te expulsar do sistema
app.secret_key = "segredo_estatico_2026" 

# --- CONFIGURAÇÃO ---
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
PIN_ACESSO = "20262026"
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
            # Varredura agressiva (ROI > 5%)
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&closed=false&limit=20", timeout=10)
            if r.status_code == 200:
                for ev in r.json():
                    m = ev.get('markets', [{}])[0]
                    p = float(m.get('outcomePrices', ["0"])[0])
                    if 0.05 < p < 0.95:
                        roi = round(((1/p)-1)*100, 1)
                        if roi > 5.0:
                            registrar("🎯 ALVO", ev.get('title')[:15], f"LUCRO {roi}%", f"USDC:{p}")
            registrar("SCAN", "SISTEMA", "VIGIANDO", "LIVE")
        except: pass
        time.sleep(15)

threading.Thread(target=motor, daemon=True).start()

# --- LOGIN SEM TRAVA ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_ACESSO:
            session.clear() # Limpa lixo anterior
            session['logado'] = True
            return redirect(url_for('dash'))
        return 'PIN INCORRETO. <a href="/login">Tentar de novo</a>'
    
    return '''<body style="background:#000;color:orange;text-align:center;padding-top:100px;font-family:sans-serif;">
              <div style="border:2px solid orange;display:inline-block;padding:50px;">
              <h1>SNIPER ACCESS</h1>
              <form method="post">
              <input type="password" name="pin" autofocus style="padding:15px;font-size:20px;"><br><br>
              <button type="submit" style="padding:15px 50px;background:orange;font-weight:bold;cursor:pointer;">ENTRAR</button>
              </form></div></body>'''

@app.route('/')
def dash():
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # BUSCA SALDOS (POL + USDC)
    try:
        # Saldo POL (O seu 4.1284)
        url_pol = f"https://api.polygonscan.com/api?module=account&action=balance&address={WALLET}&tag=latest"
        res_pol = requests.get(url_pol).json()
        pol = round(int(res_pol['result']) / 10**18, 4)
        
        # Saldo USDC (Dinheiro para aposta)
        url_usdc = f"https://api.polygonscan.com/api?module=account&action=tokenbalance&contractaddress={USDC_CONTRACT}&address={WALLET}&tag=latest"
        res_usdc = requests.get(url_usdc).json()
        usdc = round(int(res_usdc['result']) / 10**6, 2)
    except:
        pol, usdc = "OFF", "OFF"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['acao']}</td><td style='color:lime;'>{l['st']}</td><td>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:850px; margin:auto; border:1px solid #444; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="color:orange; margin:0;">⚡ SNIPER TERMINAL v17</h2>
                <div style="text-align:right;">
                    <div>POL: <b style="color:cyan;">{pol}</b></div>
                    <div>USDC: <b style="color:lime;">{usdc}</b></div>
                </div>
            </div>
            <table style="width:100%; margin-top:20px; text-align:left;">
                <tr style="color:#555;"><th>HORA</th><th>MERCADO</th><th>AÇÃO</th><th>STATUS</th><th>VALOR</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)