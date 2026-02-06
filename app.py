import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "central_modular_2026_pro")

# --- CONFIGURAÇÕES ---
PIN_SISTEMA = os.environ.get("guardiao", "123456")
PIN_INTERIOR = os.environ.get("pin_interior", "0000")
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))
CARTEIRA_ALVO = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"

STATE_FILE = "bot_state.json"
LOGS_FILE = "logs.json"

def load_json(f, d):
    if os.path.exists(f):
        try:
            with open(f, "r") as file: return json.load(file)
        except: return d
    return d

def save_json(f, d):
    try:
        with open(f, "w") as file: json.dump(d, file, indent=4)
    except: pass

def registrar_log(msg, mod="SYS", res="OK"):
    logs = load_json(LOGS_FILE, [])
    logs.insert(0, {"data": datetime.datetime.now().strftime("%H:%M:%S"), "mod": mod, "msg": msg, "res": res})
    save_json(LOGS_FILE, logs[:50])

# --- MOTOR DE EXECUÇÃO ---
def efetivar_transacao(priv_key, nome_mod):
    try:
        # Garante que a chave comece com 0x se necessário
        pk = priv_key if priv_key.startswith('0x') else '0x' + priv_key
        conta = web3.eth.account.from_key(pk)
        
        # Verifica saldo antes de tentar (evita gasto de gás em erro)
        balance = web3.eth.get_balance(conta.address)
        if balance < web3.to_wei(0.01, 'ether'):
            registrar_log("Saldo insuficiente (POL)", nome_mod, "AVISO")
            return

        tx = {
            'nonce': web3.eth.get_transaction_count(conta.address),
            'to': web3.to_checksum_address(CARTEIRA_ALVO),
            'value': 0, 
            'gas': 25000, 
            'gasPrice': int(web3.eth.gas_price * 1.2), # Aumenta 20% para prioridade
            'chainId': 137
        }
        signed = web3.eth.account.sign_transaction(tx, pk)
        tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
        registrar_log(f"TX: {tx_hash.hex()[:10]}", nome_mod, "SUCESSO")
    except Exception as e:
        registrar_log("Falha na Rede/Chave", nome_mod, "ERRO")

def loop_modulo(nome_mod, priv_key):
    while True:
        state = load_json(STATE_FILE, {})
        if state.get(nome_mod) == "ON":
            efetivar_transacao(priv_key, nome_mod)
            time.sleep(600) # 10 minutos entre ações
        time.sleep(10)

# Inicialização Dinâmica
MODULOS_CONFIGURADOS = {}
for i in range(1, 6): # Escaneia de 1 a 5
    key = os.environ.get(f"KEY_MOD_{i}")
    if key:
        nome = f"MODULO_{i}"
        MODULOS_CONFIGURADOS[nome] = key
        threading.Thread(target=loop_modulo, args=(nome, key), name=nome, daemon=True).start()

# --- INTERFACE DASHBOARD ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN_SISTEMA:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding-top:100px;font-family:sans-serif;">' \
           '<form method="post"><h3>ACESSO RESTRITO</h3><input type="password" name="pin" autofocus style="padding:10px;"></form></body>'

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    state = load_json(STATE_FILE, {})
    logs = load_json(LOGS_FILE, [])
    
    mod_html = ""
    for nome in MODULOS_CONFIGURADOS.keys():
        status = state.get(nome, "OFF")
        cor = "#00ff00" if status == "ON" else "#ff4b4b"
        mod_html += f"""
        <div style="background:#1a1c24; padding:20px; border-radius:15px; margin-bottom:15px; border-left: 6px solid {cor};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:18px; font-weight:bold;">{nome}</span>
                <span style="color:{cor}; font-weight:bold;">● {status}</span>
            </div>
            <form action="/toggle" method="post" style="margin-top:15px; display:flex; gap:10px;">
                <input type="hidden" name="mod_name" value="{nome}">
                <input type="password" name="pin_int" placeholder="PIN INTERIOR" style="flex:1; padding:8px; border-radius:5px; border:none;">
                <button name="action" value="ON" style="background:#00ff00; color:black; border:none; padding:8px 15px; border-radius:5px; font-weight:bold; cursor:pointer;">LIGAR</button>
                <button name="action" value="OFF" style="background:#ff4b4b; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer;">DESLIGAR</button>
            </form>
        </div>"""

    return f"""
    <body style="background:#0e1117; color:#eee; font-family:sans-serif; padding:20px;">
        <div style="max-width:700px; margin:auto;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h1 style="color:cyan; margin:0;">OMNI ORQUESTRADOR</h1>
                <span style="font-size:12px; color:#444;">v86.1</span>
            </div>
            <p style="color:#666; font-size:12px;">RPC: {RPC_URL}</p>
            <div style="margin-top:30px;">{mod_html if mod_html else "<p style='color:orange;'>Nenhuma chave (KEY_MOD_X) detectada no Render.</p>"}</div>
            <hr style="border:0.1px solid #222; margin:40px 0;">
            <h3 style="margin-bottom:15px;">CONSOLE DE LOGS</h3>
            <div style="background:#000; padding:15px; border-radius:10px; font-family:monospace; font-size:12px; border:1px solid #222;">
                {"".join([f"<div style='margin-bottom:5px; border-bottom:1px solid #111; padding-bottom:3px;'>"
                          f"<span style='color:#555;'>[{l['data']}]</span> "
                          f"<span style='color:cyan;'>{l['mod']}</span>: "
                          f"{l['msg']} -> <b style='color:{'lime' if l['res']=='SUCESSO' else 'red'};'>{l['res']}</b></div>" for l in logs])}
            </div>
        </div>
    </body>"""

@app.route('/toggle', methods=['POST'])
def toggle():
    if not session.get('logged_in'): return redirect(url_for('login'))
    mod, act, pin = request.form.get('mod_name'), request.form.get('action'), request.form.get('pin_int')
    state = load_json(STATE_FILE, {})
    if act == "ON":
        if pin == PIN_INTERIOR:
            state[mod] = "ON"
            registrar_log("OPERACIONAL", mod)
        else: registrar_log("PIN INTERNO INVÁLIDO", mod, "NEGADO")
    else:
        state[mod] = "OFF"
        registrar_log("SUSPENSO", mod)
    save_json(STATE_FILE, state)
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))