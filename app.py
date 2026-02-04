import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from web3 import Web3
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

# --- CONFIGURAÇÕES RENDER ---
PIN_SISTEMA = os.environ.get("guardiao")
CHAVE_PRIVADA = os.environ.get("private_key")

# --- BLOCKCHAIN SETUP ---
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))
CARTEIRA_ALVO = web3.to_checksum_address("0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E")

# Dados para o Dashboard
bot_data = {"status": "OFF"}
stats = {"total": 0, "yes": 0, "no": 0, "erro": 0}
historico_ops = []

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    try:
        pol_bal = round(web3.from_wei(web3.eth.get_balance(CARTEIRA_ALVO), 'ether'), 4)
    except:
        pol_bal = "0.0"
    
    return render_template('dashboard.html', 
                         wallet=CARTEIRA_ALVO, 
                         pol=pol_bal, 
                         usdc="14.44",
                         bot=bot_data,
                         total_ops=stats["total"],
                         ops_yes=stats["yes"],
                         ops_no=stats["no"],
                         ops_erro=stats["erro"],
                         historico=historico_ops)

@app.route('/toggle_bot', methods=['POST'])
@login_required
def toggle_bot():
    status_acao = request.form.get("status")
    bot_data["status"] = status_acao
    
    # Log de sistema
    historico_ops.insert(0, {
        "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "mercado": "Controle Manual",
        "lado": "SISTEMA" if status_acao == "ON" else "ERRO"
    })
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)