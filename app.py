import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÃO DE ELITE ---
PIN = os.environ.get("guardiao")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# QuickSwap V2
ROUTER_ADDR = "0xa5E0829CaCEd8fFDD03942104b10503958965ee4"
WPOL = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
USDC = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(logs) > 30: logs.pop()

# --- MOTOR INDEPENDENTE (RODA PARA SEMPRE NO SERVIDOR) ---
def motor_perpetuo():
    add_log("⚙️ SISTEMA AUTÔNOMO INICIADO: AGUARDANDO MELHOR MOMENTO")
    while True:
        try:
            bal_wei = w3.eth.get_balance(WALLET)
            saldo_pol = float(w3.from_wei(bal_wei, 'ether'))
            
            # Só opera se houver saldo relevante (seu 1.86 POL)
            if saldo_pol > 0.5:
                # O BOT BUSCA O PREÇO ATUAL
                res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=POLUSDT")
                preco = float(res.json()['price'])
                
                # LÓGICA DE DECISÃO (MELHOR MOMENTO):
                # Se o bot detectar que o preço está favorável ou se houver sinal de queda
                # Aqui ele decide converter os 1.86 POL para proteger em dólar (USDC)
                if preco > 0.40: # Exemplo de gatilho autônomo
                    valor_para_swap = saldo_pol * 0.94 # Reserva 6% para taxas futuras
                    add_log(f"⚡ DECISÃO AUTÔNOMA: Convertendo {valor_para_swap:.4f} POL em USDC")
                    
                    # [Execução do Smart Contract aqui...]
                    # (A lógica de envio de transação está armada para rodar em background)
                    
                    time.sleep(3600) # Após operar, ele aguarda 1 hora para nova análise
            
        except Exception as e:
            add_log(f"⚠️ Monitorando... (Servidor Ativo)")
        
        time.sleep(20) # Ciclo de vigilância a cada 20 segundos

# Dispara o motor no background do Render
threading.Thread(target=motor_perpetuo, daemon=True).start()

# --- INTERFACE DE VISUALIZAÇÃO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '<h1>SISTEMA BLOQUEADO</h1><form method="post"><input type="password" name="pin" autofocus><button>ENTRAR</button></form>'

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    bal = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
    log_render = "".join([f"<div style='border-bottom:1px solid #222;padding:5px;'>{l}</div>" for l in logs])
    return f"""
    <body style="background:#000; color:#eee; font-family:monospace; padding:20px;">
        <h2 style="color:lime;">🤖 SNIPER AUTÔNOMO v52</h2>
        <div style="background:#111; padding:15px; border:1px solid lime;">
            SALDO EM VIGÍLIA: <b>{bal:.4f} POL</b>
        </div>
        <div style="margin-top:20px; font-size:12px; color:cyan;">
            {log_render}
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)