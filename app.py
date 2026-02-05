import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÕES ---
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
PIN = os.environ.get("guardiao")

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

# --- MONITOR DE HOME DA BINANCE (LISTAGENS E TENDÊNCIAS) ---
def monitor_binance_home():
    add_log("📡 OBSERVADOR DA HOME BINANCE ATIVO")
    while True:
        try:
            # O bot simula uma leitura da Home para ver o que está 'quente'
            res = requests.get("https://api.binance.com/api/v3/ticker/24hr")
            data = res.json()
            
            # Ordena por volume ou variação para saber o que está na 'Home'
            top_moeda = sorted(data, key=lambda x: float(x['priceChangePercent']), reverse=True)[0]
            
            simbolo = top_moeda['symbol']
            variacao = top_moeda['priceChangePercent']
            
            add_log(f"🔥 HOME TREND: {simbolo} subindo {variacao}%")
            
            # Se a moeda que você tem (POL) estiver perdendo força na Home, o bot decide agir
            if simbolo == "POLUSDT" and float(variacao) < -5:
                add_log("⚠️ POL perdendo força na Home. Preparando saída...")
                
        except Exception as e:
            add_log(f"⚠️ Erro ao ler Home: {str(e)[:20]}")
        time.sleep(40)

threading.Thread(target=monitor_binance_home, daemon=True).start()

# --- INTERFACE ---
@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    log_render = "".join([f"<div style='border-bottom:1px solid #222;padding:5px;'>{l}</div>" for l in logs[:10]])
    return f"""
    <body style="background:#000; color:#eee; font-family:monospace; padding:20px;">
        <h2 style="color:#f3ba2f;">🟡 BINANCE HOME OBSERVER</h2>
        <div style="border:1px solid #f3ba2f; padding:15px; background:#111;">
            SISTEMA: <b>ATIVO</b> | EXTENSÃO VIRTUAL: <b>CONECTADA</b>
        </div>
        <div style="margin-top:20px; font-size:12px; color:#f3ba2f;">
            {log_render}
        </div>
        <script>setTimeout(()=>location.reload(), 20000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '<h1>BINANCE AUTH</h1><form method="post"><input type="password" name="pin"><button>LOGAR</button></form>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)