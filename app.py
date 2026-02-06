
import os, datetime, time, threading, requests, math, cloudscraper
from flask import Flask, session, redirect, url_for, request, Response

app = Flask(__name__)
app.secret_key = os.urandom(32)

PIN = os.environ.get("guardiao", "1234")
META_FINAL = 1000000.00
CARTEIRA_ALVO = "0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe"

saldo_usd = 0.0
preco_btc = 0.0
dias_meta = "Sincronizando..."
status_rede = "Conectando..."

def motor_bypass():
    global saldo_usd, preco_btc, dias_meta, status_rede
    scraper = cloudscraper.create_scraper() # Disfarça o Agente como um navegador real
    
    while True:
        try:
            # 1. Busca Preço BTC via Bypass
            try:
                r = scraper.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10).json()
                preco_btc = float(r['price'])
            except:
                preco_btc = 98000.0 # Valor reserva se tudo falhar

            # 2. Busca Saldo via API de Explorador (Mais leve que Web3 para o Render)
            try:
                # Usando a API pública do Polygonscan (não precisa de chave para consultas simples)
                url_bal = f"https://api.polygonscan.com/api?module=account&action=balance&address={CARTEIRA_ALVO}&tag=latest"
                res_bal = scraper.get(url_bal, timeout=10).json()
                
                if res_bal.get('status') == '1':
                    wei = int(res_bal['result'])
                    bal_native = wei / 10**18
                    # Saldo = (Moedas * Preço médio $0.40) + Seu aporte inicial
                    saldo_usd = (bal_native * 0.40) + 1500.00
                    status_rede = "✅ ONLINE (Bypass)"
                else:
                    saldo_usd = 1500.00
                    status_rede = "⚠️ API BUSY"
            except:
                saldo_usd = 1500.00
                status_rede = "❌ RESTRITO"

            # 3. Projeção
            n = math.log(META_FINAL / saldo_usd) / math.log(1 + 0.015)
            dias_meta = f"{int(n)} dias"
            
        except Exception as e:
            status_rede = "🔌 RECONECTANDO..."
        
        time.sleep(15)

threading.Thread(target=motor_bypass, daemon=True).start()

# --- MANTÉM O RESTANTE DAS ROTAS IGUAL (INDEX, LOGIN) ---
@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    progresso = min((saldo_usd / META_FINAL) * 100, 100)
    return f"""
    <body style="background:#000; color:#eee; font-family:sans-serif; text-align:center; padding:30px;">
        <div style="max-width:500px; margin:auto; background:#0a0a0a; border:1px solid #333; padding:40px; border-radius:30px;">
            <h2 style="color:#f3ba2f; margin:0;">OMNI v81 🔥</h2>
            <div style="font-size:10px; color:lime; margin-top:10px;">{status_rede}</div>
            <div style="margin:40px 0;">
                <small style="color:#666;">PATRIMÔNIO ATUAL</small>
                <h1 style="font-size:50px; margin:10px 0;">${saldo_usd:,.2f}</h1>
                <div style="color:lime; font-weight:bold;">BTC: ${preco_btc:,.2f}</div>
            </div>
            <div style="background:#111; padding:25px; border-radius:20px; border:1px solid #222;">
                <small style="color:#888;">DESTINO: 1 MILHÃO</small>
                <h2 style="color:#f3ba2f; margin:10px 0;">{dias_meta}</h2>
                <div style="background:#222; height:12px; border-radius:10px; overflow:hidden; margin-top:15px;">
                    <div style="background:linear-gradient(90deg, #f3ba2f, #00ff00); width:{progresso}%; height:100%;"></div>
                </div>
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return '<body style="background:#000;color:#f3ba2f;text-align:center;padding-top:100px;"><form method="post"><input type="password" name="pin" autofocus></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))