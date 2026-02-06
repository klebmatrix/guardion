import os, datetime, time, threading, requests, math
from flask import Flask, session, redirect, url_for, request, Response
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÕES DE CONEXÃO REAL ---
PIN = os.environ.get("guardiao", "1234")
META_FINAL = 1000000.00
# Insira sua carteira pública aqui (exemplo abaixo)
CARTEIRA = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE" 
# RPC Público (Polygon é estável e rápido para leitura)
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# Variáveis globais dinâmicas
saldo_real_usd = 0.0
dias_restantes = "Calculando..."
preco_btc_atual = 0.0

def add_log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{t}] {msg}")

def motor_de_tempo_real():
    global saldo_real_usd, dias_restantes, preco_btc_atual
    while True:
        try:
            # 1. Busca Preço do BTC (Binance)
            res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
            preco_btc_atual = float(res['price'])
            
            # 2. Busca Saldo Real (Exemplo: Saldo em MATIC/POL convertido para USD)
            # Para simplificar, pegamos o saldo nativo, mas você pode adicionar tokens específicos
            balance_wei = w3.eth.get_balance(CARTEIRA)
            balance_native = w3.from_wei(balance_wei, 'ether')
            
            # Simulação de conversão (Exemplo: assumindo que o saldo na carteira + investimentos somam X)
            # Aqui você pode personalizar para ler o valor exato dos seus ativos
            saldo_real_usd = float(balance_native) * 0.50 + 1500.00 # Exemplo de composição
            
            # 3. Cálculo de Destino (Baseado em 1.5% de rendimento médio)
            taxa_diaria = 0.015 # 1.5%
            if saldo_real_usd > 0 and saldo_real_usd < META_FINAL:
                n = math.log(META_FINAL / saldo_real_usd) / math.log(1 + taxa_diaria)
                dias_restantes = f"{int(n)} dias"
            elif saldo_real_usd >= META_FINAL:
                dias_restantes = "Meta Atingida! 🏆"
            
        except Exception as e:
            add_log(f"Erro na leitura: {e}")
        
        time.sleep(20) # Atualiza a cada 20 segundos

threading.Thread(target=motor_de_tempo_real, daemon=True).start()

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    
    progresso = (saldo_real_usd / META_FINAL) * 100
    
    return f"""
    <body style="background:#000; color:#eee; font-family:sans-serif; padding:20px;">
        <div style="max-width:800px; margin:auto; background:#0a0a0a; border:1px solid #222; padding:30px; border-radius:20px;">
            <div style="text-align:center; margin-bottom:30px;">
                <h1 style="color:#f3ba2f; margin:0;">💎 TRACKER REAL-TIME</h1>
                <small style="color:#555;">Monitorando: {CARTEIRA[:10]}...</small>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
                <div style="background:#111; padding:20px; border-radius:12px; border:1px solid #333;">
                    <span style="color:#888; font-size:12px;">SALDO ATUALIZADO</span>
                    <h2 style="color:lime;">${saldo_real_usd:,.2f}</h2>
                    <small style="color:#444;">BTC: ${preco_btc_atual:,.0f}</small>
                </div>
                <div style="background:#111; padding:20px; border-radius:12px; border:1px solid #f3ba2f;">
                    <span style="color:#888; font-size:12px;">CONTAGEM REGRESSIVA</span>
                    <h2 style="color:#f3ba2f;">{dias_restantes}</h2>
                    <small style="color:#444;">Alvo: $1.000.000,00</small>
                </div>
            </div>

            <div style="margin-top:30px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:12px;">
                    <span>Progresso do Milhão</span>
                    <span>{progresso:.4f}%</span>
                </div>
                <div style="background:#222; height:12px; border-radius:10px;">
                    <div style="background:linear-gradient(90deg, #f3ba2f, #00ff00); width:{progresso}%; height:100%; border-radius:10px;"></div>
                </div>
            </div>

            <div style="text-align:center; margin-top:40px;">
                <a href="/backup" style="color:#333; text-decoration:none; font-size:12px;">📥 Baixar Script v74</a>
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 20000);</script>
    </body>"""

@app.route('/backup')
def backup():
    with open(__file__, "r") as f:
        return Response(f.read(), mimetype="text/plain", headers={"Content-disposition": "attachment; filename=Agente_v74.py"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return '<body style="background:#000; color:#f3ba2f; text-align:center; padding-top:100px;"><h3>🔐 ACESSO PRIVADO</h3><form method="post"><input type="password" name="pin" autofocus></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))