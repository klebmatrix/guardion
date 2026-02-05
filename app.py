import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_real_777")

# --- CONEXÃO REAL POLYGON ---
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")

# Contratos
USDC_ADDRESS = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
CTF_ADDRESS = Web3.to_checksum_address("0x4D97Abd4C5914519d9821104593037647f02036d") # Polymarket CTF

# ABIs
USDC_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
CTF_ABI = '[{"constant":true,"inputs":[{"name":"account","type":"address"},{"name":"id","type":"uint256"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]'

LOGS_FILE = "movimentacoes.json"

def registrar_log(acao, mercado, status, valor="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mercado, "st": status, "val": valor})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:30], f)

def buscar_ativos_polymarket():
    # Esta função simula a busca por IDs de tokens específicos que você possa ter
    # Na Polymarket, cada aposta tem um ID único.
    ativos_encontrados = []
    # Exemplo: Se você tiver posições abertas, elas seriam listadas aqui via contrato CTF
    return ativos_encontrados

def buscar_saldos_reais():
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        contrato = w3.eth.contract(address=USDC_ADDRESS, abi=json.loads(USDC_ABI))
        usdc = round(contrato.functions.balanceOf(WALLET).call() / 10**6, 2)
        return pol, usdc
    except:
        return "0.00", "0.00"

# --- MOTOR DE SCAN ---
def motor_sniper():
    while True:
        try:
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&limit=5", timeout=10)
            if r.status_code == 200:
                registrar_log("SCAN", "RADAR", "BUSCANDO OPORTUNIDADE", "LIVE")
        except: pass
        time.sleep(20)

threading.Thread(target=motor_sniper, daemon=True).start()

# --- INTERFACE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == os.environ.get("guardiao", "20262026"):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return '''<body style="background:#000;color:orange;text-align:center;padding-top:100px;font-family:sans-serif;">
              <form method="post"><h2>SISTEMA SNIPER</h2><input type="password" name="pin" style="padding:10px;"><button type="submit" style="padding:10px;">ENTRAR</button></form></body>'''

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    pol, usdc = buscar_saldos_reais()
    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['acao']}</td><td style='color:#00ff00;'>{l['st']}</td><td>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:950px; margin:auto; border:1px solid #333; padding:20px; border-radius:10px;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="color:orange;">🛡️ SNIPER ASSETS TRACKER</h2>
                <div style="text-align:right;">
                    <b>POL:</b> <span style="color:cyan;">{pol}</span> | <b>USDC:</b> <span style="color:#00ff00;">{usdc}</span>
                </div>
            </div>

            <div style="margin-top:20px; display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
                <div style="background:#0a0a0a; padding:15px; border:1px solid #222;">
                    <h4 style="margin:0; color:orange;">🛒 ATIVOS NA CARTEIRA</h4>
                    <p style="font-size:12px; color:#666;">Tokens de aposta detectados:</p>
                    <div style="color:#888; font-size:13px;">[ NENHUM TOKEN DE RESULTADO ATIVO ]</div>
                </div>
                <div style="background:#0a0a0a; padding:15px; border:1px solid #222;">
                    <h4 style="margin:0; color:orange;">🔄 STATUS DO SCANNER</h4>
                    <p style="font-size:12px; color:#00ff00;">● CONECTADO À POLYGON RPC</p>
                    <p style="font-size:12px; color:#00ff00;">● MONITORANDO API POLYMARKET</p>
                </div>
            </div>

            <h4 style="color:orange; margin-top:30px;">📜 LOG DE OPERAÇÕES</h4>
            <table style="width:100%; text-align:left; border-collapse:collapse;">
                <tr style="color:#444; border-bottom:1px solid #444;"><th>HORA</th><th>MERCADO</th><th>AÇÃO</th><th>STATUS</th><th>DADOS</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))