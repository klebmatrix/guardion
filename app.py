import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "FORCA_BRUTA_2026"

# --- CONFIGURAÇÃO BRUTA ---
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
LOGS_FILE = "movimentacoes.json"
PIN_ACESSO = "20262026" # PIN FIXO PARA NÃO TER ERRO

def registrar(acao, mkt, st, val="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mkt, "st": st, "val": val})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:15], f)

# --- MOTOR DE SCAN ULTRA-AGRESSIVO ---
def motor_agressivo():
    while True:
        try:
            # Headers para não ser bloqueado pela Polymarket
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&closed=false&limit=30", headers=headers, timeout=10)
            
            if r.status_code == 200:
                for ev in r.json():
                    mkt = ev.get('markets', [{}])[0]
                    p_sim = float(mkt.get('outcomePrices', ["0", "0"])[0])
                    
                    if 0.01 < p_sim < 0.99:
                        roi = round(((1/p_sim)-1)*100, 1)
                        # ROI de 2% já dispara o alvo para você ver o bot trabalhar
                        if roi > 2.0:
                            registrar("🎯 ALVO", ev.get('title')[:15], f"LUCRO {roi}%", f"USDC:{p_sim}")
                            # Aqui entraria a execução real com a Private Key
            registrar("SCAN", "SISTEMA", "BUSCANDO OPORTUNIDADE", "LIVE")
        except: pass
        time.sleep(10) # Varredura rápida

threading.Thread(target=motor_agressivo, daemon=True).start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_ACESSO:
            session['logado'] = True
            return redirect(url_for('dash'))
    return '''<body style="background:#000;color:orange;text-align:center;padding-top:100px;font-family:sans-serif;">
              <h1>SISTEMA OPERACIONAL</h1>
              <form method="post"><input type="password" name="pin" autofocus style="padding:15px;font-size:20px;"><br><br>
              <button type="submit" style="padding:15px 50px;background:orange;font-weight:bold;cursor:pointer;">ENTRAR</button></form></body>'''

@app.route('/')
def dash():
    if not session.get('logado'): return redirect(url_for('login'))
    
    # BUSCA SALDO VIA API EXPLORER (MUITO MAIS RÁPIDO)
    try:
        # Saldo de POL (Nativo)
        r_pol = requests.get(f"https://api.polygonscan.com/api?module=account&action=balance&address={WALLET}&tag=latest").json()
        pol = round(int(r_pol['result']) / 10**18, 4)
        
        # Saldo de USDC (Token)
        url_usdc = f"https://api.polygonscan.com/api?module=account&action=tokenbalance&contractaddress={USDC_CONTRACT}&address={WALLET}&tag=latest"
        r_usdc = requests.get(url_usdc).json()
        usdc = round(int(r_usdc['result']) / 10**6, 2)
    except:
        pol, usdc = "Erro", "Erro"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['st']}</td><td style='color:lime;'>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:850px; margin:auto; border:1px solid #444; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="color:orange; margin:0;">⚡ SNIPER TERMINAL v16</h2>
                <div style="text-align:right;">
                    <div>POL (TAXA): <b style="color:cyan;">{pol}</b></div>
                    <div>USDC (BANCA): <b style="color:lime;">{usdc}</b></div>
                </div>
            </div>
            <table style="width:100%; margin-top:20px; text-align:left; border-collapse:collapse;">
                <tr style="color:#555;"><th>HORA</th><th>ALVO</th><th>STATUS</th><th>VALOR</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 5000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)