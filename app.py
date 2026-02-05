import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO MASTER ---
PIN = os.environ.get("guardiao")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

# --- INTELIGÊNCIA DE VOLUME (AQUI O BOT DECIDE) ---
def calcular_entrada_autonoma(saldo_total):
    # O bot analisa a volatilidade (exemplo simplificado)
    # Se a variação for alta, ele arrisca apenas 25%
    # Se a tendência for sólida, ele usa 100%
    try:
        # Simulando análise de risco
        risco_mercado = "BAIXO" # O bot definiria isso via algoritmo
        
        if risco_mercado == "ALTO":
            return saldo_total * 0.25 # Pega só um pouco
        else:
            return saldo_total * 0.95 # Pega quase tudo (deixa sobra para gás)
    except:
        return saldo_total * 0.10

def motor_autonomo_v2():
    add_log("🧠 MÓDULO DE DECISÃO DE VOLUME ATIVO")
    while True:
        try:
            bal_wei = w3.eth.get_balance(WALLET)
            saldo_atual = float(w3.from_wei(bal_wei, 'ether'))
            
            if saldo_atual > 0.1:
                # O BOT DECIDE O QUANTO PEGAR:
                valor_entrada = calcular_entrada_autonoma(saldo_atual)
                
                # Exemplo de lógica de decisão:
                # Se preço cair 2% em 1 minuto -> COMPRA valor_entrada
                add_log(f"🤖 DECISÃO: Em caso de gatilho, pegarei {valor_entrada:.4f} POL")
            
        except Exception as e:
            add_log(f"Erro: {str(e)[:20]}")
        time.sleep(20)

threading.Thread(target=motor_autonomo_v2, daemon=True).start()

# --- INTERFACE DE MONITORAMENTO ---
@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    
    bal_wei = w3.eth.get_balance(WALLET)
    saldo_exato = w3.from_wei(bal_wei, 'ether')
    
    log_render = "".join([f"<div style='border-bottom:1px solid #222;padding:5px;'>{l}</div>" for l in logs[:15]])
    
    return f"""
    <body style="background:#000; color:#0f0; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:1px solid lime; padding:20px;">
            <h2 style="color:lime;">🤖 GESTOR AUTÔNOMO v49</h2>
            <div style="display:flex; justify-content:space-between; background:#111; padding:15px; border-radius:5px;">
                <span>SALDO TOTAL: <b style="color:white;">{saldo_exato:.4f} POL</b></span>
                <span>STATUS: <b style="color:orange;">DECIDINDO ENTRADA</b></span>
            </div>
            <div style="margin-top:20px; background:#050505; height:300px; overflow-y:auto; padding:10px; font-size:12px; border:1px solid #222;">
                {log_render}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '<h1>LOGIN</h1><form method="post"><input type="password" name="pin" autofocus><button>OK</button></form>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)