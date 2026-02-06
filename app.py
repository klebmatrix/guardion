import os, datetime, time, threading, requests, math
from flask import Flask, session, redirect, url_for, request, Response
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÕES DE ELITE ---
PIN = os.environ.get("guardiao", "1234")
META_FINAL = 1000000.00
CARTEIRA_ALVO = "0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe"

# Variáveis globais
saldo_usd = 0.0
preco_btc = 0.0
dias_meta = "Iniciando Motores..."
status_conexao = "Desconectado"

def buscar_preco_btc():
    # Tenta 3 fontes diferentes para o preço do BTC
    fontes = [
        "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
        "https://api.coindesk.com/v1/bpi/currentprice.json",
        "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    ]
    for url in fontes:
        try:
            res = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            if "binance" in url: return float(res.json()['price'])
            if "coindesk" in url: return float(res.json()['bpi']['USD']['rate_float'])
            if "coinbase" in url: return float(res.json()['data']['amount'])
        except:
            continue
    return 0.0

def motor_eterno():
    global saldo_usd, preco_btc, dias_meta, status_conexao
    while True:
        try:
            # 1. Preço do Bitcoin
            preco_btc = buscar_preco_btc()
            
            # 2. Saldo Blockchain (Usando um RPC público ultra-estável)
            try:
                w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com", request_kwargs={'timeout': 10}))
                if w3.is_connected():
                    bal_wei = w3.eth.get_balance(CARTEIRA_ALVO)
                    bal_native = float(w3.from_wei(bal_wei, 'ether'))
                    # Valor simulado + real (ajuste conforme seu aporte real)
                    saldo_usd = (bal_native * 0.40) + 1500.00 
                    status_conexao = "✅ Online"
                else:
                    status_conexao = "⚠️ RPC Offline"
            except:
                status_conexao = "❌ Erro Web3"
                saldo_usd = 1500.00 # Mantém o aporte para o cálculo não zerar

            # 3. Cálculo do Milhão
            if saldo_usd > 0:
                n = math.log(META_FINAL / saldo_usd) / math.log(1 + 0.015)
                dias_meta = f"{int(n)} dias"
                
        except Exception as e:
            print(f"Erro no Motor: {e}")
        
        time.sleep(20) # Ciclo de 20 segundos

threading.Thread(target=motor_eterno, daemon=True).start()

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    progresso = min((saldo_usd / META_FINAL) * 100, 100)
    
    return f"""
    <body style="background:#000; color:#eee; font-family:sans-serif; text-align:center; padding:30px;">
        <div style="max-width:500px; margin:auto; background:#0a0a0a; border:1px solid #333; padding:40px; border-radius:30px; box-shadow: 0 0 50px rgba(243,186,47,0.1);">
            <h2 style="color:#f3ba2f; margin:0;">OMNI v80 🚀</h2>
            <div style="font-size:10px; color:#444; margin-top:5px;">{CARTEIRA_ALVO}</div>
            <div style="font-size:10px; color:{"lime" if "✅" in status_conexao else "red"};">{status_conexao}</div>

            <div style="margin:40px 0;">
                <small style="color:#666;">PATRIMÔNIO ATUAL</small>
                <h1 style="font-size:50px; margin:10px 0;">${saldo_usd:,.2f}</h1>
                <div style="color:lime; font-weight:bold; letter-spacing:1px;">BTC: ${preco_btc:,.2f}</div>
            </div>

            <div style="background:#111; padding:25px; border-radius:20px; border:1px solid #222;">
                <small style="color:#888;">DESTINO: 1 MILHÃO</small>
                <h2 style="color:#f3ba2f; margin:10px 0; font-size:32px;">{dias_meta}</h2>
                <div style="background:#222; height:12px; border-radius:10px; overflow:hidden; margin-top:15px;">
                    <div style="background:linear-gradient(90deg, #f3ba2f, #00ff00); width:{progresso}%; height:100%;"></div>
                </div>
                <div style="font-size:11px; color:#444; margin-top:10px;">Progresso: {progresso:.4f}%</div>
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 20000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return '<body style="background:#000;color:#f3ba2f;text-align:center;padding-top:100px;"><h3>PIN REQUERIDO:</h3><form method="post"><input type="password" name="pin" autofocus style="padding:10px; background:#111; color:#fff; border:1px solid #333;"></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))