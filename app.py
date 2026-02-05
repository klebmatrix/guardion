import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
# Chave secreta fixa para evitar deslogar toda hora que o server reinicia
app.secret_key = "guardiao_key_segura_123" 

# --- CONFIGURAÇÃO ---
PIN = os.environ.get("guardiao", "1234") # Fallback para 1234 se a env falhar
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(logs) > 20: logs.pop()

# --- MOTOR DE DECISÃO ---
def motor():
    add_log("🤖 MOTOR ATIVO (AGUARDANDO GATILHO)")
    while True:
        try:
            # Lógica simplificada para evitar erro 500 no boot
            time.sleep(30)
        except:
            pass

threading.Thread(target=motor, daemon=True).start()

# --- ROTAS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN:
            session['auth'] = True
            return redirect(url_for('dashboard'))
        return 'PIN INCORRETO. <a href="/login">Tentar de novo</a>'
    
    return '''
    <body style="background:#000;color:orange;text-align:center;padding-top:100px;font-family:monospace;">
        <form method="post">
            <h2>TERMINAL RESTRITO</h2>
            <input type="password" name="pin" autofocus style="padding:10px;"><br><br>
            <button style="padding:10px 20px;">ENTRAR</button>
        </form>
    </body>
    '''

@app.route('/')
def dashboard():
    if not session.get('auth'):
        return redirect(url_for('login'))
    
    try:
        bal = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
        saldo_str = f"{bal:.4f} POL"
    except:
        saldo_str = "Erro na Rede"

    log_html = "".join([f"<div style='border-bottom:1px solid #222;'>{l}</div>" for l in logs])
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:600px; margin:auto; border:1px solid orange; padding:20px;">
            <h3>🛡️ STATUS DO SISTEMA</h3>
            <p>CARTEIRA: <b>{WALLET[:10]}...</b></p>
            <p>SALDO: <b style="color:cyan;">{saldo_str}</b></p>
            <hr>
            <div style="height:200px; overflow-y:auto; color:lime; font-size:12px;">{log_html}</div>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>
    """

if __name__ == "__main__":
    # Render usa a porta 10000 por padrão
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)