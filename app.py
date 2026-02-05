import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_final_2026")

# --- CONFIGURAÇÕES REAIS ---
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PRIV_KEY = os.environ.get("private_key")

# Contratos e ABIs
USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
CTF_EXCHANGE = Web3.to_checksum_address("0x4bFb41d5B3570De3061333a9b59dd234870343f5")
ERC20_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

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

# --- FUNÇÃO DE EXECUÇÃO DE TRADE ---
def executar_compra(token_id, valor_usdc):
    if not PRIV_KEY:
        registrar_log("AVISO", "SISTEMA", "SEM CHAVE PRIVADA", "0")
        return
    try:
        conta = Account.from_key(PRIV_KEY)
        nonce = w3.eth.get_transaction_count(WALLET)
        tx = {
            'nonce': nonce,
            'to': CTF_EXCHANGE,
            'value': 0,
            'gas': 400000,
            'gasPrice': int(w3.eth.gas_price * 1.25),
            'chainId': 137,
            'data': '0x' # Em produção, aqui vai o encode da função buy()
        }
        signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        registrar_log("🔥 TIRO", "POLYMARKET", "SUCESSO", f"TX:{tx_hash.hex()[:6]}")
    except Exception as e:
        registrar_log("❌ ERRO", "BLOCKCHAIN", str(e)[:15], "FALHA")

# --- MOTOR SNIPER DE LUCRO ---
def motor_sniper():
    while True:
        try:
            # Busca mercados com liquidez real
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&limit=15&closed=false", timeout=10)
            if r.status_code == 200:
                for ev in r.json():
                    mkt = ev.get('markets', [{}])[0]
                    precos = mkt.get('outcomePrices', [0, 0])
                    preco_sim = float(precos[0]) if precos else 0
                    volume = float(ev.get('volume', 0))

                    if 0.15 < preco_sim < 0.85 and volume > 10000:
                        roi = round(((1 / preco_sim) - 1) * 100, 1)
                        if roi > 15.0:
                            token_id = mkt.get('clobTokenIds', [""])[0]
                            registrar_log("🎯 ALVO", ev.get('title')[:12], f"ROI {roi}%", f"VOL:{int(volume)}")
                            # GATILHO: Comprar 3.5 USDC (25% da sua banca de 14)
                            executar_compra(token_id, 3.5)
                            time.sleep(600) # Pausa para não repetir no mesmo alvo
                            break
            registrar_log("SCAN", "RADAR", "BUSCANDO", "LIVE")
        except: pass
        time.sleep(15)

threading.Thread(target=motor_sniper, daemon=True).start()

# --- INTERFACE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == os.environ.get("guardiao", "20262026"):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return '''<body style="background:#000;color:orange;text-align:center;padding-top:100px;font-family:monospace;">
              <form method="post" style="border:1px solid orange;display:inline-block;padding:30px;">
              <h3>SNIPER SECURITY</h3><input type="password" name="pin" autofocus><br><br>
              <button type="submit" style="background:orange;border:none;padding:5px 20px;cursor:pointer;">ENTRAR</button>
              </form></body>'''

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        usdc_contract = w3.eth.contract(address=USDC_ADDR, abi=json.loads(ERC20_ABI))
        usdc = round(usdc_contract.functions.balanceOf(WALLET).call() / 10**6, 2)
    except: pol, usdc = "Err", "Err"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['acao']}</td><td style='color:#00ff00;'>{l['st']}</td><td>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:900px; margin:auto; border:1px solid #444; padding:20px; background:#0a0a0a; border-radius:10px;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="margin:0; color:orange;">⚡ SNIPER TERMINAL v10.0</h2>
                <div style="font-size:18px;">
                    POL: <b style="color:cyan;">{pol}</b> | USDC: <b style="color:#00ff00;">{usdc}</b>
                </div>
            </div>
            <table style="width:100%; margin-top:20px; text-align:left; border-collapse:collapse;">
                <tr style="color:#666; border-bottom:1px solid #444;"><th>HORA</th><th>MERCADO</th><th>AÇÃO</th><th>STATUS</th><th>DADOS</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))