import os, json, threading, time, requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_2026")

# --- CONFIGURAÇÕES ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")
CARTEIRA = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"

# --- FUNÇÕES DE ARQUIVO ---
def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r") as f: return json.load(f)
        except: pass
    return padrao

def salvar_dados(arquivo, dados):
    with open(arquivo, "w") as f: json.dump(dados, f)

def registrar_log(mensagem, acao="IA SCAN", resultado="OK"):
    logs = carregar_dados("logs.json", [])
    novo_log = {
        "data": datetime.now().strftime("%H:%M:%S"),
        "mercado": mensagem,
        "lado": acao,
        "resultado": resultado
    }
    logs.insert(0, novo_log)
    salvar_dados("logs.json", logs[:15]) # Mantém os 15 últimos

# --- O MOTOR DO BOT (BACKGROUND THREAD) ---
def motor_do_bot():
    print("Motor do Sniper iniciado...")
    while True:
        status_atual = carregar_dados("bot_state.json", {"status": "OFF"})
        if status_atual.get("status") == "ON":
            try:
                # 1. Simula a busca de mercados na Polymarket
                # Aqui você pode colocar a lógica de compra real depois
                registrar_log("Analisando Polymarket...", "BUSCA", "SCANNING")
                
                # Exemplo: Se achar algo, logaria aqui
                # registrar_log("Oportunidade Detectada", "BUY", "EXECUTADO")
                
            except Exception as e:
                print(f"Erro no loop: {e}")
        
        time.sleep(30) # Procura a cada 30 segundos

# Inicia o motor assim que o app abre
threading.Thread(target=motor_do_bot, daemon=True).start()

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
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    return render_template('dashboard.html', 
                           wallet=CARTEIRA, 
                           pol="4.0", 
                           usdc="14.44", 
                           bot=carregar_dados("bot_state.json", {"status": "OFF"}), 
                           historico=carregar_dados("logs.json", []))

@app.route('/toggle_bot', methods=['POST'])
def toggle_bot():
    if not session.get('logged_in'): return redirect(url_for('login'))
    novo_status = request.form.get("status")
    salvar_bot_status(novo_status) # Helper simples
    salvar_dados("bot_state.json", {"status": novo_status})
    registrar_log(f"Sistema {novo_status}", "SISTEMA", "ALTERADO")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))