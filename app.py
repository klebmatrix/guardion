import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

# --- CONFIGURAÇÕES TÉCNICAS ---
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
PRIV_KEY = os.environ.get("private_key")

USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
CTF_EXCHANGE = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"
ABI_ERC20 = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

LOGS_FILE = "movimentacoes.json"

def registrar_movimentacao(acao, mercado, status, valor="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mercado, "st": status, "val": valor})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:30], f)

# --- FUNÇÃO DE TIRO REAL ---
def dar_o_tiro(token_id, valor_usdc):
    if not PRIV_KEY:
        registrar_movimentacao("ERRO", "KEY", "AUSENTE", "0")
        return
    try:
        nonce = w3.eth.get_transaction_count(WALLET)
        tx = {
            'nonce': nonce,
            'to': CTF_EXCHANGE,
            'value': 0,
            'gas': 350000,
            'gasPrice': int(w3.eth.gas_price * 1.3),
            'chainId': 137,
            'data': '0x' # Placeholder para o smart contract
        }
        signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        registrar_movimentacao("TIRO", "BLOCKCHAIN", "SUCESSO", f"TX:{tx_hash.hex()[:6]}")
    except Exception as e:
        registrar_movimentacao("FALHA", "TRADE", "ERRO TX", "0")

# --- INTELIGÊNCIA DE MERCADO (O CORAÇÃO DO BOT) ---
def motor_sniper():
    while True:
        try:
            # Varredura focada em liquidez e probabilidade
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&limit=15", timeout=10)
            if r.status_code == 200:
                eventos = r.json()
                for ev in eventos:
                    mkt = ev.get('markets', [{}])[0]
                    precos = mkt.get('outcomePrices', [0, 0])
                    preco_sim = float(precos[0]) if precos else 0
                    volume = float(ev.get('volume', 0))
                    
                    # LÓGICA IDEAL: ROI entre 15% e 45% + Volume Alto
                    if preco_sim > 0:
                        roi = round(((1 / preco_sim) - 1) * 100, 2)
                        
                        if 15 < roi < 45 and volume > 10000:
                            titulo = ev.get('title', 'Market')[:15]
                            token_id = mkt.get('clobTokenIds', [""])[0]
                            
                            registrar_movimentacao("ALVO", titulo, f"ROI {roi}%", f"V:{int(volume)}")
                            
                            # GESTÃO DE RISCO: Usa apenas 3 USDC por operação (aprox 20% do saldo)
                            dar_o_tiro(token_id, 3.0)
                            time.sleep(600) # Pausa para evitar overtrading
                            break
            registrar_movimentacao("SCAN", "RADAR", "BUSCANDO LUCRO", "OK")
        except: pass
        time.sleep(15)

threading.Thread(target=motor_sniper, daemon=True).start()

# --- INTERFACE ---
@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        usdc_inst = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=ABI_ERC20)
        usdc = round(usdc_inst.functions.balanceOf(WALLET).call() / 10**6, 2)
    except: pol, usdc = "0.0", "0.0"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td style='padding:10px;'>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['acao']}</td><td style='color:#00ff00;'>{l['st']}</td><td>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:900px; margin:auto; border:1px solid orange; padding:20px; background:#0a0a0a; border-radius:10px;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="margin:0; color:orange;">⚡ SNIPER ELITE v7</h2>
                <div style="font-size:18px;">
                    <span style="margin-right:15px;">POL: <b style="color:cyan;">{pol}</b></span>
                    <span>USDC: <b style="color:#00ff00;">{usdc}</b></span>
                </div>
            </div>
            <table style="width:100%; text-align:left; border-collapse:collapse; margin-top:20px;">
                <thead style="background:#111; color:orange;">
                    <tr><th style="padding:10px;">HORA</th><th>MERCADO</th><th>AÇÃO</th><th>STATUS</th><th>VALOR</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        <script>setTimeout(() => {{ location.reload(); }}, 10000);</script>
    </body>
    """

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == os.environ.get("guardiao", "20262026"):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:100px;"><form method="post">PIN:<br><input type="password" name="pin" autofocus><button>ENTRAR</button></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))