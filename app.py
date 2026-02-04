import os
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session
from web3 import Web3
from functools import wraps

app = Flask(__name__)

# --- CONFIGURAÇÕES DO RENDER (BUSCA NAS SUAS VARIÁVEIS) ---
# Aqui ele busca 'guardiao' como seu PIN e 'private_key' para assinar
PIN_ACESSO = os.environ.get("guardiao")
CHAVE_PRIVADA = os.environ.get("private_key")
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_final_2026")

# --- CONEXÃO E ENDEREÇOS (COM CORREÇÃO DE CHECKSUM) ---
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Aplicando Checksum para evitar erro 'invalid EIP-55'
CARTEIRA_ALVO = web3.to_checksum_address("0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E")
EXCHANGE_ADDR = web3.to_checksum_address("0x4bFb9e7A482025732168923a1aB1313936a79853")
USDC_ADDRESS  = web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")

# --- VALIDAÇÃO DE AMBIENTE ---
if not PIN_ACESSO or not CHAVE_PRIVADA:
    raise RuntimeError("❌ VARIÁVEIS 'guardiao' OU 'private_key' NÃO ENCONTRADAS NO RENDER!")

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
def disparar_tiro_real(token_id, valor_usdc):
    try:
        amount_wei = int(float(valor_usdc) * 10**6)
        nonce = web3.eth.get_transaction_count(CARTEIRA_ALVO, 'pending')
        
        abi_buy = '[{"inputs":[{"internalType":"uint256","name":"tokenID","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"minOutput","type":"uint256"}],"name":"buy","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
        exchange = web3.eth.contract(address=EXCHANGE_ADDR, abi=abi_buy)
        
        tx = exchange.functions.buy(int(token_id), amount_wei, 0).build_transaction({
            'from': CARTEIRA_ALVO,
            'nonce': nonce,
            'gas': 450000, # Aumentado para garantir execução
            'gasPrice': int(web3.eth.gas_price * 1.4) # 40% de prioridade
        })
        
        signed = web3.eth.account.sign_transaction(tx, CHAVE_PRIVADA)
        hash_tx = web3.eth.send_raw_transaction(signed.rawTransaction)
        return f"✅ SUCESSO: {hash_tx.hex()}"
    except Exception as e:
        return f"❌ FALHA: {str(e)}"

# --- DASHBOARD HTML ---
UI_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>SNIPER DASH</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; text-align: center; padding: 30px; }
        .box { border: 2px solid #0f0; padding: 20px; border-radius: 10px; display: inline-block; }
        button { background: #0f0; color: #000; padding: 15px 30px; font-weight: bold; cursor: pointer; border: none; font-size: 1.1em; }
        .logs { text-align: left; background: #111; padding: 10px; margin-top: 20px; height: 150px; overflow-y: scroll; border: 1px solid #333; }
    </style>
</head>
<body>
    <div class="box">
        <h2>📍 TERMINAL SNIPER POLYGON</h2>
        <p>CONECTADO: {{ wallet }}</p>
        <p>STATUS: <strong>{{ "ATIVO" if status else "PARADO" }}</strong></p>
        <form method="post" action="/toggle">
            <button>{{ "PARAR SNIPER" if status else "LIGAR E ATIRAR AGORA" }}</button>
        </form>
        <div class="logs">
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
    if request.method == 'POST':
        # Aqui ele confere se a senha digitada é igual ao 'guardiao' do Render
        if request.form.get('pin') == PIN_ACESSO:
            session['logged_in'] = True
            return redirect(url_for('index'))
    return '''<body style="background:#000;color:#0f0;text-align:center;padding-top:100px;font-family:monospace;">
              <h2>DIGITE O PIN (GUARDIAO)</h2>
              <form method="post">
                <input type="password" name="pin" style="padding:10px;background:#111;color:#0f0;border:1px solid #0f0;">
                <button style="padding:10px;background:#0f0;color:#000;border:none;cursor:pointer;">ENTRAR</button>
              </form></body>'''

@app.route('/')
@login_required
def index():
    return render_template_string(UI_HTML, wallet=CARTEIRA_ALVO, status=bot_status["active"], logs=historico)

@app.route('/toggle', methods=['POST'])
@login_required
def toggle():
    bot_status["active"] = not bot_status["active"]
    if bot_status["active"]:
        # Dispara com 14.44 USDC (Troque 123456 pelo ID real do token)
        res = disparar_tiro_real(123456789, 14.44)
        historico.insert(0, {"hora": datetime.datetime.now().strftime("%H:%M:%S"), "msg": res})
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)