import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from web3 import Web3
from functools import wraps

app = Flask(__name__)
app.secret_key = "sniper_key_2026" # Chave para as sessões

# --- CREDENCIAIS ---
USUARIO_ADMIN = "admin"
SENHA_ADMIN = "1234" # Mude isso depois!

# --- CONFIGURAÇÕES WEB3 ---
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))
WALLET_ADDRESS = "0x..." # Seu endereço

bot_status = {"active": False}
historico = []

# --- DECORATOR DE SEGURANÇA ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        if request.form['username'] != USUARIO_ADMIN or request.form['password'] != SENHA_ADMIN:
            erro = 'Credenciais Inválidas!'
        else:
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('login.html', error=erro)

@app.route('/')
@login_required
def index():
    pol = round(web3.from_wei(web3.eth.get_balance(WALLET_ADDRESS), 'ether'), 4)
    return render_template('dashboard.html', pol=pol, usdc=14.44, bot=bot_status, historico=historico)

@app.route('/toggle', methods=['POST'])
@login_required
def toggle():
    bot_status["active"] = not bot_status["active"]
    historico.insert(0, {"hora": datetime.datetime.now().strftime("%H:%M:%S"), "msg": "Alteração de Status", "tipo": "SISTEMA"})
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)