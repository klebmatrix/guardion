import os, datetime, json, threading, time, requests, math
from flask import Flask, render_template, request, redirect, url_for, session, Response
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_ultra_safe")

# --- CONFIGURAÇÕES DE AMBIENTE (RENDER) ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")   # PIN de entrada no site
PIN_INTERIOR = os.environ.get("pin_interior", "0000") # Trava para ligar o bot
PRIV_KEY = os.environ.get("private_key")
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))
CARTEIRA_ALVO = web3.to_checksum_address("0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E")

BOT_STATE_FILE = "bot_state.json"
LOGS_FILE = "logs.json"

# --- PERSISTÊNCIA ---
def load_json(f, d):
    if os.path.exists(f):
        try:
            with open(f, "r") as file: return json.load(file)
        except: return d
    return d

def save_json(f, d):
    with open(f, "w") as file: json.dump(d, file, indent=4)

def registrar_log(msg, lado="AUTO", res="OK"):
    logs = load_json(LOGS_FILE, [])
    logs.insert(0, {"data": datetime.datetime.now().strftime("%H:%M:%S"), "mercado": msg, "lado": lado, "resultado": res})
    save_json(LOGS_FILE, logs[:50])

# --- MOTOR DE TRANSAÇÃO ---
def efetivar_transacao():
    if not PRIV_KEY: return
    try:
        conta = web3.eth.account.from_key(PRIV_KEY)
        tx = {
            'nonce': web3.eth.get_transaction_count(conta.address),
            'to': CARTEIRA_ALVO,
            'value': web3.to_wei(0, 'ether'),
            'gas': 25000,
            'gasPrice': web3.eth.gas_price,
            'chainId': 137
        }
        signed_tx = web3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        registrar_log(f"TX: {tx_hash.hex()[:10]}", "EXEC", "SUCESSO")
    except Exception as e:
        registrar_log("Falha na Rede", "EXEC", "ERRO")

def sniper_loop():
    while True:
        state = load_json(BOT_STATE_FILE, {"status": "OFF"})
        if state["status"] == "ON" and PRIV_KEY:
            efetivar_transacao()
            time.sleep(600)
        time.sleep(10)

if not any(t.name == "SniperBotThread" for t in threading.enumerate()):
    threading.Thread(target=sniper_loop, name="SniperBotThread", daemon=True).start()

# --- ROTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN_SISTEMA:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding:100px;"><form method="post"><h2>LOGIN</h2><input type="password" name="pin" autofocus></form></body>'

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    state = load_json(BOT_STATE_FILE, {"status": "OFF"})
    logs = load_json(LOGS_FILE, [])
    status_color = "#00ff00" if state['status'] == 'ON' else "#ff0000"
    
    return f"""
    <body style="background:#0e1117; color:white; font-family:sans-serif; padding:20px;">
        <div style="max-width:800px; margin:auto; background:#1a1c24; padding:30px; border-radius:15px; border-top: 5px solid {status_color};">
            <h1>Sniper Console</h1>
            <p>Bot Status: <b style="color:{status_color};">{state['status']}</b></p>
            <hr style="border:0.2px solid #333;">
            
            <div style="margin:30px 0; background:#111; padding:20px; border-radius:10px;">
                <h3>Controle de Ativação</h3>
                <form action="/toggle" method="post">
                    <input type="password" name="pin_int" placeholder="PIN INTERIOR" style="padding:10px; border-radius:5px; border:none; margin-bottom:10px;"><br>
                    <button name="action" value="ON" style="background:#00ff00; padding:12px 25px; cursor:pointer; font-weight:bold;">ATIVAR BOT</button>
                    <button name="action" value="OFF" style="background:#ff0000; padding:12px 25px; cursor:pointer; color:white;">DESATIVAR</button>
                </form>
                <small style="color:#555;">* PIN INTERIOR é necessário apenas para LIGAR o bot.</small>
            </div>

            <table style="width:100%; text-align:left; border-collapse:collapse;">
                <tr style="background:#333;"><th style="padding:10px;">Hora</th><th style="padding:10px;">Ação</th><th style="padding:10px;">Status</th></tr>
                {"".join([f"<tr><td style='padding:8px;border-bottom:1px solid #222;'>{l['data']}</td><td style='padding:8px;border-bottom:1px solid #222;'>{l['mercado']}</td><td style='padding:8px;border-bottom:1px solid #222;'>{l['resultado']}</td></tr>" for l in logs])}
            </table>
        </div>
    </body>"""

@app.route('/toggle', methods=['POST'])
def toggle():
    if not session.get('logged_in'): return redirect(url_for('login'))
    action = request.form.get('action')
    input_pin = request.form.get('pin_int')

    if action == "ON":
        if input_pin == PIN_INTERIOR:
            save_json(BOT_STATE_FILE, {"status": "ON"})
            registrar_log("BOT LIGADO (PIN OK)", "SISTEMA")
        else:
            registrar_log("Tentativa de ligar (PIN INCORRETO)", "SEGURANÇA", "NEGADO")
    else:
        save_json(BOT_STATE_FILE, {"status": "OFF"})
        registrar_log("Bot desligado manualmente", "SISTEMA")
        
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))