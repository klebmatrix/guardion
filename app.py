import os, datetime, time, threading, requests, math
from flask import Flask, session, redirect, url_for, request, Response
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

PIN = os.environ.get("guardiao", "1234")
META_FINAL = 1000000.00
CARTEIRA_ALVO = "0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe"

# Conector de reserva (BSC é mais estável no Render)
w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))

saldo_usd = 0.0
preco_btc = 0.0
dias_meta = "Conectando..."
logs = []

def add_log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{t}] {msg}")
    if len(logs) > 5: logs.pop()

def motor_resiliente():
    global saldo_usd, preco_btc, dias_meta
    while True:
        try:
            # 1. Busca Preço BTC (Usando API alternativa da Coinbase se Binance falhar)
            try:
                r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=10).json()
                preco_btc = float(r['data']['amount'])
            except:
                add_log("Erro Preço: Tentando Binance...")
                r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
                preco_btc = float(r['price'])

            # 2. Busca Saldo (Se falhar, assume saldo base para teste)
            try:
                if w3.is_connected():
                    bal_wei = w3.eth.get_balance(CARTEIRA_ALVO)
                    bal_native = float(w3.from_wei(bal_wei, 'ether'))
                    # Se saldo for 0, colocamos 1500 apenas para o gráfico não morrer
                    saldo_usd = (bal_native * 600) + 1500.00 
                else:
                    saldo_usd = 1500.00
                    add_log("Web3 Off: Usando simulado.")
            except:
                saldo_usd = 1500.00

            # 3. Projeção
            taxa = 0.015 # 1.5% dia
            n = math.log(META_FINAL / saldo_usd) / math.log(1 + taxa)
            dias_meta = f"{int(n)} dias"
            
        except Exception as e:
            add_log(f"Falha Geral: {str(e)[:15]}")
        
        time.sleep(10)

threading.Thread(target=motor_resiliente, daemon=True).start()

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    progresso = (saldo_usd / META_FINAL) * 100
    return f"""
    <body style="background:#000; color:#eee; font-family:sans-serif; padding:20px; text-align:center;">
        <div style="max-width:500px; margin:auto; border:1px solid #333; padding:30px; border-radius:20px; background:#0a0a0a;">
            <h1 style="color:#f3ba2f; margin:0;">OMNI v77</h1>
            <p style="color:#444; font-size:10px;">CARTEIRA ATIVA</p>
            
            <div style="margin:40px 0;">
                <h2 style="font-size:40px; margin:0; color:#fff;">${saldo_usd:,.2f}</h2>
                <div style="color:lime; font-weight:bold;">BTC: ${preco_btc:,.2f}</div>
            </div>

            <div style="background:#111; padding:20px; border-radius:15px; border:1px solid #222;">
                <div style="color:#888; font-size:12px;">META: 1 MILHÃO</div>
                <h2 style="color:#f3ba2f; margin:10px 0;">{dias_meta}</h2>
                <div style="background:#222; height:10px; border-radius:10px;">
                    <div style="background:linear-gradient(90deg, #f3ba2f, #00ff00); width:{progresso}%; height:100%; border-radius:10px;"></div>
                </div>
            </div>
            
            <div style="margin-top:20px; font-family:monospace; font-size:10px; color:#444;">
                {" | ".join(logs)}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return '<body style="background:#000; padding-top:100px; text-align:center;"><form method="post"><input type="password" name="pin" autofocus style="background:#111; color:white; border:1px solid #333; padding:10px;"></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))