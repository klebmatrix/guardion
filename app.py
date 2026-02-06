import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request, Response

app = Flask(__name__)
app.secret_key = os.urandom(32)

PIN = os.environ.get("guardiao", "1234")
logs = []
# Variáveis de Estado (Memória do Agente)
ALERTA_PRECO = 0
ESTADO_MERCADO = "AGUARDANDO"

def add_log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{t}] {msg}")
    if len(logs) > 12: logs.pop()

# --- NÚCLEO DE INTELIGÊNCIA ---
def motor_de_decisao():
    global ESTADO_MERCADO
    while True:
        try:
            # API Pública da Binance (Sempre On e Grátis)
            btc = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
            eth = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT").json()
            preco_btc = float(btc['price'])
            preco_eth = float(eth['price'])
            
            ESTADO_MERCADO = f"BTC: ${preco_btc:,.0f} | ETH: ${preco_eth:,.0f}"
            
            if ALERTA_PRECO > 0 and preco_btc >= ALERTA_PRECO:
                add_log(f"🚨 ALERTA ATINGIDO: BTC em ${preco_btc:,.0f}")
        except:
            pass
        time.sleep(15)

threading.Thread(target=motor_de_decisao, daemon=True).start()

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    return f"""
    <body style="background:#000; color:#eee; font-family:'Courier New', monospace; padding:20px;">
        <div style="max-width:1000px; margin:auto; border:1px solid #333; padding:25px; border-radius:15px; background:#0a0a0a;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h1 style="color:#f3ba2f; margin:0;">🦾 OMNI v71</h1>
                <div style="text-align:right; color:lime;">{ESTADO_MERCADO}</div>
            </div>
            
            <hr style="border:0.5px solid #222; margin:20px 0;">

            <div style="display:grid; grid-template-columns: 1.5fr 1fr; gap:25px;">
                <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #444;">
                    <h3 style="color:#00d4ff; margin-top:0;">⌨️ TERMINAL DE EXECUÇÃO</h3>
                    <form action="/executar" method="post">
                        <input name="comando" autofocus placeholder="Ex: 'alertar 100000' ou 'vender'" 
                               style="width:100%; padding:15px; background:#000; color:lime; border:1px solid #333; font-size:16px; margin-bottom:15px; outline:none;">
                        <button style="width:100%; padding:12px; background:#f3ba2f; color:#000; border:none; font-weight:bold; cursor:pointer; border-radius:5px;">ENVIAR ORDEM</button>
                    </form>
                    <p style="font-size:11px; color:#666; margin-top:10px;">Dica: Digite 'ajuda' para ver comandos disponíveis.</p>
                </div>

                <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #444;">
                    <h3 style="color:#f3ba2f; margin-top:0;">📡 LOGS</h3>
                    <div style="height:180px; overflow-y:auto; font-size:12px; background:#050505; padding:10px; border-radius:5px;">{"<br>".join(logs)}</div>
                    <br>
                    <a href="/backup" style="display:block; text-align:center; padding:10px; border:1px dashed #666; color:#888; text-decoration:none; border-radius:5px;">📥 BAIXAR BACKUP AGORA</a>
                </div>
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

@app.route('/executar', methods=['POST'])
def executar():
    global ALERTA_PRECO
    cmd = request.form.get('comando').lower()
    if "alertar" in cmd:
        try:
            ALERTA_PRECO = float(cmd.split()[-1])
            add_log(f"🎯 Novo Alerta de Preço em ${ALERTA_PRECO:,.2f}")
        except:
            add_log("❌ Erro: Use 'alertar 95000'")
    elif "limpar" in cmd:
        logs.clear()
        add_log("🧹 Logs limpos.")
    else:
        add_log(f"❓ Comando não reconhecido: {cmd}")
    return redirect(url_for('index'))

@app.route('/backup')
def backup():
    if not session.get('auth'): return "Unauthorized", 401
    with open(__file__, "r") as f:
        return Response(f.read(), mimetype="text/plain", headers={"Content-disposition": "attachment; filename=Agente_v71.py"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return '<body style="background:#000; color:lime; text-align:center; padding-top:100px;"><h2>ACESSO RESTRITO</h2><form method="post"><input type="password" name="pin" autofocus style="padding:10px;"></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))