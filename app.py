import os, datetime, time, threading
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32) # Chave de sessão ultra segura

# --- CONFIGURAÇÃO DE SEGURANÇA ---
PIN_SEGURANCA = os.environ.get("guardiao") # Certifique-se que esta variável está no Render
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(logs) > 20: logs.pop()

# --- MOTOR AUTÔNOMO (RODANDO NO FUNDO) ---
def motor_operacional():
    while True:
        try:
            # Aqui o bot continua trabalhando mesmo com o site deslogado
            time.sleep(30)
        except: pass

threading.Thread(target=motor_operacional, daemon=True).start()

# --- CONTROLE DE ACESSO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SEGURANCA:
            session['autenticado'] = True
            session.permanent = True # Sessão dura enquanto o navegador estiver aberto
            return redirect(url_for('dashboard'))
        else:
            return 'PIN INCORRETO. <a href="/login">Tentar novamente</a>'
    
    return '''
    <body style="background:#000; color:white; font-family:sans-serif; text-align:center; padding-top:100px;">
        <div style="display:inline-block; border:1px solid #333; padding:40px; border-radius:10px;">
            <h2 style="color:orange;">ACESSO RESTRITO</h2>
            <form method="post">
                <input type="password" name="pin" placeholder="Digite o PIN" autofocus 
                       style="padding:15px; width:200px; border-radius:5px; border:none; margin-bottom:10px;"><br>
                <button type="submit" style="padding:15px 30px; background:orange; border:none; cursor:pointer; font-weight:bold;">ENTRAR NO TERMINAL</button>
            </form>
        </div>
    </body>
    '''

@app.route('/')
def dashboard():
    # Se não estiver logado, bloqueia TUDO e manda pro login
    if not session.get('autenticado'):
        return redirect(url_for('login'))
    
    bal_wei = w3.eth.get_balance(WALLET)
    saldo = w3.from_wei(bal_wei, 'ether')
    log_render = "".join([f"<div style='border-bottom:1px solid #222;padding:8px;'>{l}</div>" for l in logs])
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:2px solid orange; padding:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style="color:orange;">🛡️ TERMINAL BLINDADO v51</h2>
                <a href="/logout" style="color:red; text-decoration:none;">[ SAIR ]</a>
            </div>
            <div style="background:#111; padding:20px; margin:20px 0; border-radius:5px;">
                SALDO EM CARTEIRA: <b style="color:cyan; font-size:22px;">{saldo:.4f} POL</b>
            </div>
            <div style="background:#000; height:300px; overflow-y:auto; padding:10px; border:1px solid #333; color:lime; font-size:12px;">
                {log_render}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>
    """

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)