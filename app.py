import os, json, threading, time
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_2026")

# --- CONFIGURAÇÕES ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")
CARTEIRA = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"

# --- FUNÇÕES DE ARQUIVO (Sem erros de dependência) ---
def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r") as f:
                return json.load(f)
        except:
            pass
    return padrao

def salvar_dados(arquivo, dados):
    try:
        with open(arquivo, "w") as f:
            json.dump(dados, f)
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")

def registrar_log(mensagem, acao="SISTEMA", resultado="OK"):
    logs = carregar_dados("logs.json", [])
    novo_log = {
        "data": datetime.now().strftime("%H:%M:%S"),
        "mercado": mensagem,
        "lado": acao,
        "resultado": resultado
    }
    logs.insert(0, novo_log)
    salvar_dados("logs.json", logs[:15])

# --- MOTOR EM BACKGROUND ---
def motor_bot():
    while True:
        status_atual = carregar_dados("bot_state.json", {"status": "OFF"})
        if status_atual.get("status") == "ON":
            # Aqui simulamos a atividade para o histórico
            registrar_log("Monitorando Polymarket...", "SCAN", "ATIVO")
        time.sleep(60) # Loga a cada 1 minuto enquanto ligado

# Inicia a thread do bot
threading.Thread(target=motor_bot, daemon=True).start()

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
    
    bot_info = carregar_dados("bot_state.json", {"status": "OFF"})
    historico_info = carregar_dados("logs.json", [])
    
    return render_template('dashboard.html', 
                           wallet=CARTEIRA, 
                           pol="4.0", 
                           usdc="14.44", 
                           bot=bot_info, 
                           historico=historico_info)

@app.route('/toggle_bot', methods=['POST'])
def toggle_bot():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    novo_status = request.form.get("status")
    # Salva o novo estado
    salvar_dados("bot_state.json", {"status": novo_status})
    
    # Registra a mudança no log
    registrar_log(f"Bot alterado para {novo_status}", "USUÁRIO", "OK")
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)'	