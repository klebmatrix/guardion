import os, datetime, json, threading, time, random
from flask import Flask, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "ultra_stable_2026")

# --- COMBO DE ESTABILIZAÇÃO (RPCs de Reserva) ---
RPC_LIST = [
    "https://polygon-rpc.com",
    "https://rpc-mainnet.maticvigil.com",
    "https://polygon.llamarpc.com"
]

def get_stable_web3():
    for url in RPC_LIST:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
            if w3.is_connected(): return w3
        except: continue
    return None

CARTEIRA_ALVO = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
STATE_FILE = "bot_state.json"
LOGS_FILE = "logs.json"

# --- AUXILIARES ---
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

# --- MOTOR DE EXECUÇÃO ESTABILIZADO ---
def efetivar_transacao(priv_key, nome_mod):
    w3 = get_stable_web3()
    if not w3:
        registrar_log("Rede Instável", nome_mod, "ERRO")
        return

    try:
        pk = priv_key if priv_key.startswith('0x') else '0x' + priv_key
        conta = w3.eth.account.from_key(pk)
        
        # Check de Gás Dinâmico
        gas_price = int(w3.eth.gas_price * 1.3) # 30% acima para garantir entrada
        balance = w3.eth.get_balance(conta.address)
        
        if balance < w3.to_wei(0.02, 'ether'):
            registrar_log("Combustível Baixo", nome_mod, "AVISO")
            return

        tx = {
            'nonce': w3.eth.get_transaction_count(conta.address),
            'to': w3.to_checksum_address(CARTEIRA_ALVO),
            'value': 0, 
            'gas': 28000, 
            'gasPrice': gas_price,
            'chainId': 137
        }
        
        signed = w3.eth.account.sign_transaction(tx, pk)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        registrar_log(f"Efetivado: {tx_hash.hex()[:8]}", nome_mod, "SUCESSO")
        
    except Exception as e:
        registrar_log("Conflito de Nonce/Rede", nome_mod, "RE-TENTAR")

def loop_modulo(nome_mod, priv_key):
    while True:
        state = load_json(STATE_FILE, {})
        if state.get(nome_mod) == "ON":
            # Estabilizador: Delay Aleatório entre 3 e 15 segundos para evitar 'Sync Block'
            time.sleep(random.randint(3, 15)) 
            efetivar_transacao(priv_key, nome_mod)
            
            # Descanso longo para estabilizar o consumo de CPU no Render
            time.sleep(600) 
        time.sleep(15)

# --- INICIALIZAÇÃO ---
MODULOS_CONFIGURADOS = {}
for i in range(1, 4): # Focado nos seus 3 módulos
    key = os.environ.get(f"KEY_MOD_{i}")
    if key:
        nome = f"MOD_0{i}"
        MODULOS_CONFIGURADOS[nome] = key
        threading.Thread(target=loop_modulo, args=(nome, key), name=nome, daemon=True).start()

# --- INTERFACE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == os.environ.get("guardiao", "123456"):
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding-top:100px;">' \
           '<form method="post"><h3>ACESSO OMNI</h3><input type="password" name="pin" autofocus></form></body>'

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
        <div style="background:#161b22; padding:15px; border-radius:10px; margin-bottom:10px; border:1px solid #30363d;">
            <div style="display:flex; justify-content:space-between;">
                <b>{nome}</b> <span style="color:{cor};">● {status}</span>
            </div>
            <form action="/toggle" method="post" style="margin-top:10px;">
                <input type="hidden" name="mod_name" value="{nome}">
                <input type="password" name="pin_int" placeholder="PIN" style="width:60px; background:#0d1117; color:white; border:1px solid #333;">
                <button name="action" value="ON" style="background:#238636; color:white; border:none; padding:5px 10px; border-radius:5px; cursor:pointer;">LIGAR</button>
                <button name="action" value="OFF" style="background:#da3633; color:white; border:none; padding:5px 10px; border-radius:5px; cursor:pointer;">OFF</button>
            </form>
        </div>"""

    return f"""
    <body style="background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:20px;">
        <div style="max-width:600px; margin:auto;">
            <h2 style="color:#58a6ff;">OMNI ORQUESTRADOR v86.2</h2>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">{mod_html}</div>
            <hr style="border:0.1px solid #30363d; margin:30px 0;">
            <h3>LOGS DE SISTEMA</h3>
            <div style="background:#010409; padding:15px; border-radius:10px; font-family:monospace; font-size:11px; border:1px solid #30363d; height:300px; overflow-y:auto;">
                {"".join([f"<div style='border-bottom:1px solid #161b22; padding:5px 0;'>"
                          f"<span style='color:#8b949e;'>[{l['data']}]</span> "
                          f"<b style='color:#58a6ff;'>{l['mod']}</b>: {l['msg']} -> "
                          f"<span style='color:{'#3fb950' if l['res']=='SUCESSO' else '#f85149'};'>{l['res']}</span></div>" for l in logs])}
            </div>
        </div>
    </body>"""

@app.route('/toggle', methods=['POST'])
def toggle():
    if not session.get('logged_in'): return redirect(url_for('login'))
    mod, act, pin = request.form.get('mod_name'), request.form.get('action'), request.form.get('pin_int')
    state = load_json(STATE_FILE, {})
    if act == "ON":
        if pin == os.environ.get("pin_interior", "0000"):
            state[mod] = "ON"
            registrar_log("MODO ATIVO", mod)
        else: registrar_log("PIN NEGADO", mod, "ERRO")
    else:
        state[mod] = "OFF"
        registrar_log("MODO SUSPENSO", mod)
    save_json(STATE_FILE, state)
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))