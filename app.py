import os
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session
from web3 import Web3
from functools import wraps

app = Flask(__name__)

# --- CONFIGURAÇÕES DO RENDER ---
PIN_SISTEMA = os.environ.get("guardiao")      # Sua senha de acesso
CHAVE_PRIVADA = os.environ.get("private_key") # Para assinar transações
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

# CARTEIRA PÚBLICA (FIXA)
CARTEIRA_ALVO = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"

# --- VALIDAÇÃO DE AMBIENTE ---
if not PIN_SISTEMA or not CHAVE_PRIVADA:
    raise RuntimeError("❌ ERRO: 'guardiao' ou 'private_key' ausentes no Render!")

# --- BLOCKCHAIN SETUP ---
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))
EXCHANGE_ADDR = "0x4bFb9e7A482025732168923a1aB1313936a79853"

bot_status = {"active": False}
historico = []

# --- SEGURANÇA ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- FUNÇÃO DE TRANSAÇÃO ---
def disparar_tiro(token_id, valor_usdc):
    try:
        amount_wei = int(float(valor_usdc) * 10**6)
        nonce = web3.eth.get_transaction_count(CARTEIRA_ALVO, 'pending')
        
        abi_buy = '[{"inputs":[{"internalType":"uint256","name":"tokenID","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"minOutput","type":"uint256"}],"name":"buy","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
        exchange = web3.eth.contract(address=EXCHANGE_ADDR, abi=abi_buy)
        
        tx = exchange.functions.buy(int(token_id), amount_wei, 0).build_transaction({
            'from': CARTEIRA_ALVO,
            'nonce': nonce,
            'gas': 400000,
            'gasPrice': int(web3.eth.gas_price * 1.3)
        })
        
        signed = web3.eth.account.sign_transaction(tx, CHAVE_PRIVADA)
        hash_tx = web3.eth.send_raw_transaction(signed.rawTransaction)
        return f"SUCESSO: {hash_tx.hex()}"
    except Exception as e:
        return f"FALHA: {str(e)}"

# --- INTERFACE HTML ---
HTML_UI = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>TERMINAL SNIPER</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; text-align: center; padding: 40px; }
        .box { border: 2px solid #0f0; padding: 20px; display: inline-block; border-radius: 10px; box-shadow: 0 0 20px #0f0; }
        button { background: #0f0; color: #000; padding: 15px 40px; border: none; font-weight: bold; cursor: pointer; border-radius: 5px; }
        .log { margin-top: 20px; text-align: left; background: #111; padding: 10px; height: 120px; overflow-y: scroll; border: 1px solid #333; }
    </style>
</head>
<body>
    <div class="box">
        <h2>⚡ SISTEMA SNIPER ONLINE ⚡</h2>
        <p>CONECTADO: {{ wallet }}</p>
        <p>POL: {{ pol }} | USDC: 14.44</p>
        <form method="post" action="/toggle">
            <button>{{ "PARAR" if status else "LIGAR E ATIRAR" }}</button>
        </form>
        <div class="log">
            {% for item in logs %}
            <div>[{{ item.hora }}] {{ item.msg }}</div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        # Compara o que você digitou com o 'guardiao' do Render
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            erro = "PIN INVÁLIDO"
    return '<h2>LOGIN SNIPER</h2><form method="post">PIN (GUARDIAO): <input type="password" name="pin"><button>ENTRAR</button></form>' + (f'<p style="color:red">{erro}</p>' if erro else '')

@app.route('/')
@login_required
def index():
    try:
        pol = round(web3.from_wei(web3.eth.get_balance(CARTEIRA_ALVO), 'ether'), 4)
    except: pol = "Erro"
    return render_template_string(HTML_UI, wallet=CARTEIRA_ALVO, pol=pol, status=bot_status["active"], logs=historico)

@app.route('/toggle', methods=['POST'])
@login_required
def toggle():
    bot_status["active"] = not bot_status["active"]
    if bot_status["active"]:
        res = disparar_tiro(123456789, 14.44) # Dispara com 14.44 USDC
        historico.insert(0, {"hora": datetime.datetime.now().strftime("%H:%M:%S"), "msg": res})
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)