import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONEXÃO ---
PIN = os.environ.get("guardiao")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(logs) > 20: logs.pop()

# --- MOTOR DE MONITORAMENTO ---
def motor_de_combate():
    add_log("🤖 MOTOR DE DECISÃO INICIADO")
    while True:
        try:
            # Pega o saldo real para confirmar que o bot está lendo a carteira
            bal_wei = w3.eth.get_balance(WALLET)
            saldo_atual = float(w3.from_wei(bal_wei, 'ether'))
            
            # Aqui ele ficaria vigiando o preço para mover seus 14.2096
            # add_log(f"Vigiando... Saldo em conta: {saldo_atual:.4f} POL")
            
        except Exception as e:
            add_log(f"Erro no motor: {str(e)[:20]}")
        time.sleep(30)

threading.Thread(target=motor_de_combate, daemon=True).start()

# --- ROTAS (CORRIGIDAS) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '''
    <body style="background:#000;color:orange;text-align:center;padding-top:100px;font-family:monospace;">
        <h2>ENTRADA DO TERMINAL</h2>
        <form method="post">
            <input type="password" name="pin" autofocus style="padding:10px;background:#111;color:white;border:1px solid orange;">
            <button style="padding:10px;background:orange;cursor:pointer;">ACESSAR</button>
        </form>
    </body>
    '''

@app.route('/')
def dashboard():
    if not session.get('auth'): 
        return redirect(url_for('login'))
    
    # Busca saldo com precisão total
    bal_wei = w3.eth.get_balance(WALLET)
    saldo_exato = w3.from_wei(bal_wei, 'ether')
    
    log_render = "".join([f"<div style='border-bottom:1px solid #222;padding:5px;'>{l}</div>" for l in logs])
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:2px solid orange; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid orange; padding-bottom:10px; margin-bottom:20px;">
                <h2 style="color:orange; margin:0;">🛡️ SNIPER LIVE v48</h2>
                <div style="text-align:right;">
                    SALDO REAL:<br>
                    <b style="color:cyan; font-size:24px;">{saldo_exato:.4f} POL</b>
                </div>
            </div>
            <div style="background:#0a0a0a; height:350px; overflow-y:auto; padding:10px; font-size:12px; color:#0f0; border:1px solid #111;">
                {log_render}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)