import os, datetime, time, threading, requests, math
from flask import Flask, session, redirect, url_for, request, Response
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÃO FINAL DA CARTEIRA ---
PIN = os.environ.get("guardiao", "1234")
META_FINAL = 1000000.00
CARTEIRA_ALVO = "0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe" # Sua carteira aqui

# Conexão principal via Polygon (mais rápida para ler saldo)
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

saldo_usd = 0.0
preco_btc = 0.0
dias_meta = "Sincronizando..."
logs = []

def add_log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{t}] {msg}")
    if len(logs) > 5: logs.pop()

def atualizar_agente():
    global saldo_usd, preco_btc, dias_meta
    while True:
        try:
            # 1. Busca Preço BTC
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
            preco_btc = float(r['price'])

            # 2. Busca Saldo Real na Blockchain
            if w3.is_address(CARTEIRA_ALVO):
                bal_wei = w3.eth.get_balance(CARTEIRA_ALVO)
                bal_native = float(w3.from_wei(bal_wei, 'ether'))
                
                # Vamos considerar o valor em USD (Ex: MATIC/POL hoje ~ $0.40)
                # Você pode somar um valor fixo se tiver dinheiro em corretora
                saldo_usd = (bal_native * 0.40) + 1500.00 # 1500 é o 'start' que você mencionou
            
            # 3. Projeção (1.5% ao dia)
            if saldo_usd > 0:
                n = math.log(META_FINAL / saldo_usd) / math.log(1 + 0.015)
                dias_meta = f"{int(n)} dias"
                
        except Exception as e:
            add_log("Erro de conexão com a rede.")
        
        time.sleep(20)

threading.Thread(target=atualizar_agente, daemon=True).start()

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    progresso = (saldo_usd / META_FINAL) * 100
    return f"""
    <body style="background:#000; color:#eee; font-family:sans-serif; padding:20px;">
        <div style="max-width:600px; margin:auto; background:#0a0a0a; border:1px solid #333; padding:25px; border-radius:15px; text-align:center;">
            <h2 style="color:#f3ba2f; margin-bottom:5px;">OMNI v76</h2>
            <code style="color:#444; font-size:10px;">{CARTEIRA_ALVO}</code>
            
            <div style="margin:30px 0;">
                <small style="color:#888;">SALDO ATUALIZADO (USD)</small>
                <h1 style="font-size:45px; margin:10px 0;">${saldo_usd:,.2f}</h1>
                <div style="color:lime;">BTC: ${preco_btc:,.2f}</div>
            </div>

            <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #222;">
                <small style="color:#f3ba2f;">CONTAGEM PARA O MILHÃO</small>
                <h2 style="margin:10px 0;">{dias_meta}</h2>
                <div style="background:#222; height:8px; border-radius:5px; margin-top:10px;">
                    <div style="background:#f3ba2f; width:{progresso}%; height:100%; border-radius:5px; box-shadow:0 0 10px #f3ba2f;"></div>
                </div>
            </div>
            
            <div style="margin-top:20px;"><a href="/backup" style="color:#333; text-decoration:none; font-size:11px;">📥 Baixar Código</a></div>
        </div>
        <script>setTimeout(()=>location.reload(), 20000);</script>
    </body>"""

@app.route('/backup')
def backup():
    with open(__file__, "r") as f:
        return Response(f.read(), mimetype="text/plain", headers={"Content-disposition": "attachment; filename=Agente_v76.py"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return '<body style="background:#000;text-align:center;padding-top:100px;"><form method="post"><input type="password" name="pin" autofocus></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))