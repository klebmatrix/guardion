import os
import json
from flask import Flask, render_template, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
# Se a variável FLASK_SECRET não existir no Render, ele usa a padrão abaixo
app.secret_key = os.environ.get("FLASK_SECRET", "segredo_temporario_123")

# --- CONFIGURAÇÕES ---
# Garante que o app não quebre se as variáveis de ambiente estiverem vazias
PIN_SISTEMA = os.environ.get("guardiao", "123456")
RPC_URL = "https://polygon-rpc.com"
CARTEIRA = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"

# Inicializa Web3 com um timeout curto para não travar o boot do servidor
try:
    web3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 5}))
except:
    web3 = None

# --- ROTAS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # Se o PIN digitado for igual ao configurado
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = "PIN de Acesso Incorreto"
    return render_template('login.html', error=error)

@app.route('/')
def index():
    # Se não estiver logado, manda para o login
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    saldo_pol = "0.0"
    saldo_usdc = "0.0"
    
    # Tenta buscar saldos, mas se a rede falhar, o site abre mesmo assim
    if web3 and web3.is_connected():
        try:
            balance = web3.eth.get_balance(CARTEIRA)
            saldo_pol = round(web3.from_wei(balance, 'ether'), 4)
            # USDC Simulado para este teste inicial de estabilidade
            saldo_usdc = "14.44" 
        except:
            saldo_pol = "Erro RPC"

    return render_template('dashboard.html', 
                           wallet=CARTEIRA, 
                           pol=saldo_pol, 
                           usdc=saldo_usdc, 
                           bot={"status": "OFF"}, 
                           historico=[])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    # O Render exige que o app rode na porta definida pela variável PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)