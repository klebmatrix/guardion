import os, datetime, time, threading, requests, math
from flask import Flask, session, redirect, url_for, request, Response
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÕES ---
PIN = os.environ.get("guardiao", "1234")
META_FINAL = 1000000.00
CARTEIRA_ALVO = "0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe"

# Dados Globais
saldo_usd = 0.0
preco_btc = 0.0
dias_meta = "Sincronizando..."

def add_log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{t}] {msg}")

def motor_dados():
    global saldo_usd, preco_btc, dias_meta
    while True:
        try:
            # 1. Preço BTC (API Coindesk - Mais estável no Render)
            try:
                r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10).json()
                preco_btc = float(r['bpi']['USD']['rate_float'])
            except:
                preco_btc = 65000.0 # Valor reserva

            # 2. Saldo Blockchain (Túnel Direto Ankr)
            try:
                w3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/polygon"))
                bal_wei = w3.eth.get_balance(CARTEIRA_ALVO)
                bal_native = float(w3.from_wei(bal_wei, 'ether'))
                # Saldo = Valor na carteira + Seu aporte inicial de $1500
                saldo_usd = (bal_native * 0.40) + 1500.00
            except:
                saldo_usd = 1500.00 # Se a rede cair, assume o aporte inicial

            # 3. Projeção
            n = math.log(META_FINAL / saldo_usd) / math.log(1 + 0.015)
            dias_meta = f"{int(n)} dias"
        except:
            pass
        time.sleep(20)

threading.Thread(target=motor_dados, daemon=True).start()

# --- ROTAS (A solução para o Not Found) ---

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    progresso = (saldo_usd / META_FINAL) * 100
    
    return f"""
    <body style="background:#000; color:#eee; font-family:sans-serif; text-align:center; padding:50px 20px;">
        <div style="max-width:500px; margin:auto; background:#0a0a0a; border:1px solid #333; padding:30px; border-radius:20px;">
            <h1 style="color:#f3ba2f; margin:0;">OMNI v78</h1>
            <p style="color:#444; font-size:11px;">{CARTEIRA_ALVO}</p>
            
            <div style="margin:40px 0;">
                <h2 style="font-size:45px; margin:0;">${saldo_usd:,.2f}</h2>
                <div style="color:lime; font-weight:bold;">BTC: ${preco_btc:,.2f}</div>
            </div>

            <div style="background:#111; padding:20px; border-radius:15px; border:1px solid #222;">
                <small style="color:#888;">PREVISÃO 1 MILHÃO</small>
                <h2 style="color:#f3ba2f; margin:10px 0;">{dias_meta}</h2>
                <div style="background:#222; height:10px; border-radius:10px; overflow:hidden;">
                    <div style="background:linear-gradient(90deg, #f3ba2f, #00ff00); width:{progresso}%; height:100%;"></div>
                </div>
            </div>
            <br>
            <a href="/backup" style="color:#333; text-decoration:none; font-size:10px;">📦 BAIXAR BACKUP</a>
        </div>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return f'''
    <body style="background:#000; color:#f3ba2f; text-align:center; padding-top:100px;">
        <h3>DIGITE O PIN DO AGENTE</h3>
        <form method="post"><input type="password" name="pin" autofocus style="padding:10px;"></form>
    </body>'''

@app.route('/backup')
def backup():
    if not session.get('auth'): return "Acesso negado", 401
    with open(__file__, "r") as f:
        return Response(f.read(), mimetype="text/plain", headers={"Content-disposition": "attachment; filename=app.py"})

if __name__ == "__main__":
    # Importante: O Render define a porta automaticamente
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)