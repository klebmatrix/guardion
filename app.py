import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÕES ---
PIN = os.environ.get("guardiao", "1234")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")

NETWORKS = {
    'BSC': 'https://bsc-dataseed.binance.org',
    'POLYGON': 'https://polygon-rpc.com'
}

logs = []
insights = []

def add_log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{t}] {msg}")
    if len(logs) > 20: logs.pop()

def add_insight(acao, motivo):
    t = datetime.datetime.now().strftime('%H:%M')
    insights.insert(0, {"hora": t, "acao": acao, "motivo": motivo})
    if len(insights) > 10: insights.pop()

def motor_omni():
    add_log("🚀 AGENTE OMNI v62 - OPERACIONAL")
    while True:
        try:
            # Percepção Básica
            btc_data = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
            preco = float(btc_data['price'])
            add_insight("VIGILÂNCIA", f"BTC em ${preco:.0f}. Agente monitorando redes.")
        except Exception as e:
            add_log(f"⚠️ Erro: {str(e)[:20]}")
        time.sleep(30)

threading.Thread(target=motor_omni, daemon=True).start()

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    log_html = "<br>".join(logs)
    ins_html = "".join([f"<li><b>{i['acao']}</b>: {i['motivo']} ({i['hora']})</li>" for i in insights])
    return f"""
    <body style="background:#000; color:lime; font-family:monospace; padding:20px;">
        <h2>🛡️ OMNI v62 - DASHBOARD</h2>
        <div style="display:flex; gap:20px;">
            <div style="flex:1; border:1px solid lime; padding:10px;">
                <h3>🧠 Insights</h3><ul>{ins_html}</ul>
            </div>
            <div style="flex:1; border:1px solid lime; padding:10px;">
                <h3>📡 Logs</h3>{log_html}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return '<body style="background:#000;color:lime;text-align:center;padding-top:100px;">' \
           '<form method="post">PIN: <input type="password" name="pin"><button>ENTRAR</button></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))