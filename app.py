import os, json
from flask import Flask, render_template, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

PIN_SISTEMA = os.environ.get("guardiao", "123456")
CARTEIRA = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
RPC_URL = "https://polygon-rpc.com"

# --- PERSISTÊNCIA SIMPLES PARA O STATUS DO BOT ---
def get_bot_status():
    if os.path.exists("bot_state.json"):
        try:
            with open("bot_state.json", "r") as f:
                return json.load(f)
        except: pass
    return {"status": "OFF"}

def save_bot_status(status):
    with open("bot_state.json", "w") as f:
        json.dump({"status": status}, f)

# --- ROTAS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('index'))
        error = "PIN Incorreto"
    return render_template('login.html', error=error)

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Busca de saldo simplificada
    pol = "14.44" # Valor mockado para estabilidade inicial
    usdc = "4.0"
    
    return render_template('dashboard.html', 
                           wallet=CARTEIRA, 
                           pol=pol, 
                           usdc=usdc, 
                           bot=get_bot_status(), 
                           historico=[])

# ESTA É A ROTA QUE ESTAVA FALTANDO E CAUSAVA O "NOT FOUND"
@app.route('/toggle_bot', methods=['POST'])
def toggle_bot():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    novo_status = request.form.get("status")
    save_bot_status(novo_status)
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)