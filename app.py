import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÕES DE ELITE ---
PIN = os.environ.get("guardiao", "1234")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")

NETWORKS = {
    'BSC': 'https://bsc-dataseed.binance.org',
    'POLYGON': 'https://polygon-rpc.com'
}

# --- MEMÓRIA DO AGENTE ---
logs = []
insights = []

def add_log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{t}] {msg}")
    if len(logs) > 15: logs.pop()

def add_insight(acao, motivo):
    t = datetime.datetime.now().strftime('%H:%M %d/%m')
    insights.insert(0, {"hora": t, "acao": acao, "motivo": motivo})
    if len(insights) > 10: insights.pop()

# --- MOTOR DE INTELIGÊNCIA ---
def motor_agente():
    add_log("🧠 AGENTE v61 INICIALIZADO")
    while True:
        try:
            # 1. PERCEPÇÃO: Binance Home + Kalshi (Simulado via API)
            price_data = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
            btc_price = float(price_data['price'])
            
            # 2. VARREDURA MULTICHAIN
            for name, rpc in NETWORKS.items():
                w3 = Web3(Web3.HTTPProvider(rpc))
                bal = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
                
                if bal > 0.001:
                    add_log(f"💰 Ativo em {name}: {bal:.4f}")
                    # Lógica de Decisão do Agente
                    if btc_price > 50000: # Exemplo de gatilho
                        # acao = executar_trade(name, w3)
                        add_insight(f"VIGILÂNCIA {name}", f"BTC a ${btc_price:.0f}. Mantendo posição por tendência de alta.")
            
        except Exception as e:
            add_log(f"⚠️ Erro de leitura: {str(e)[:20]}")
        
        time.sleep(45)

threading.Thread(target=motor_agente, daemon=True).start()

# --- INTERFACE DO DASHBOARD ---
@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    
    insight_html = "".join([f"<div style='margin-bottom:10px; border-left:3px solid #f3ba2f; padding-left:10px;'>"
                            f"<small>{i['hora']}</small><br><b>{i['acao']}</b><br><i>{i['motivo']}</i></div>" for i in insights])
    
    log_html = "".join([f"<div style='font-size:12px; color:#888;'>{l}</div>" for l in logs])

    return f"""
    <body style="background:#0a0a0a; color:#eee; font-family:sans-serif; padding:20px;">
        <h2 style="color:#f3ba2f;">🧠 AGENTE DE ELITE v61</h2>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
            <div style="background:#151515; padding:15px; border-radius:10px;">
                <h3>📝 Relatório de Insights</h3>
                {insight_html if insights else "Aguardando primeira decisão..."}
            </div>
            <div style="background:#151515; padding:15px; border-radius:10px;">
                <h3>📡 Logs do Sistema</h3>
                {log_html}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:100px;">' \
           '<h2>ACESSO RESTRITO</h2><form method="post"><input type="password" name="pin"><button>ENTRAR</button></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))