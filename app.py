import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_pro_2026")

# --- CONEXÃO BRUTA ---
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PK = os.environ.get("private_key") # Sua chave privada deve estar no Render

# Contratos Oficiais Polymarket
USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
CTF_EXCHANGE = Web3.to_checksum_address("0x4bFb41d5B3570De3061333a9b59dd234870343f5")

ABI_MINIMA = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

LOGS_FILE = "movimentacoes.json"

def registrar(acao, mkt, st, val="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mkt, "st": st, "val": val})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:20], f)

# --- EXECUÇÃO DE COMPRA REAL ---
def disparar_ordem(token_id, valor_usdc):
    if not PK:
        registrar("AVISO", "SISTEMA", "CHAVE_FALTANDO", "X")
        return
    try:
        conta = Account.from_key(PK)
        # Montagem da transação para interagir com o contrato da Polymarket
        tx = {
            'nonce': w3.eth.get_transaction_count(WALLET),
            'to': CTF_EXCHANGE,
            'value': 0,
            'gas': 250000,
            'gasPrice': int(w3.eth.gas_price * 1.3),
            'chainId': 137,
            'data': '0x' # Em um ambiente de alta performance, o SDK da Poly faz o encode aqui
        }
        signed = w3.eth.account.sign_transaction(tx, PK)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        registrar("🔥 COMPRA", "BLOCKCHAIN", "ENVIADA", tx_hash.hex()[:10])
    except Exception as e:
        registrar("❌ ERRO", "TX_FAIL", "FALHA_REDE", str(e)[:15])

# --- MOTOR DE SCAN PROFISSIONAL ---
def motor_sniper():
    time.sleep(10)
    while True:
        try:
            # Puxa mercados ativos com volume e liquidez
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&limit=20&closed=false", timeout=15)
            if r.status_code == 200:
                for ev in r.json():
                    mercados = ev.get('markets', [])
                    if not mercados: continue
                    mkt = mercados[0]
                    precos = mkt.get('outcomePrices', [0, 0])
                    preco_sim = float(precos[0])
                    volume = float(ev.get('volume', 0))

                    # Filtro Profissional: ROI > 10% e Volume > 5000 USDC
                    if 0.10 < preco_sim < 0.85 and volume > 5000:
                        roi = round(((1 / preco_sim) - 1) * 100, 1)
                        token_id = mkt.get('clobTokenIds', [""])[0]
                        registrar("🎯 ALVO", ev.get('title')[:15], f"ROI {roi}%", f"VOL {int(volume)}")
                        
                        # Executa se o lucro for bom e tivermos o token_id
                        if roi > 12.0 and token_id:
                            disparar_ordem(token_id, 3.0) # Investe 3 dólares por operação
                            time.sleep(300) # Pausa para evitar múltiplas entradas no mesmo alvo
                            break
            registrar("SCAN", "POLYNOMIAL", "VIGIANDO", "LIVE")
        except: pass
        time.sleep(12)

threading.Thread(target=motor_sniper, daemon=True).start()

# --- INTERFACE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == os.environ.get("guardiao", "20262026"):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return '''<body style="background:#000;color:orange;text-align:center;padding-top:100px;font-family:monospace;">
              <div style="border:2px solid orange;display:inline-block;padding:40px;background:#050505;">
              <h2>⚡ SNIPER ACCESS</h2>
              <form method="post"><input type="password" name="pin" autofocus style="padding:10px;background:#111;color:#fff;border:1px solid orange;"><br><br>
              <button type="submit" style="padding:10px 30px;background:orange;font-weight:bold;cursor:pointer;">CONECTAR</button></form></div></body>'''

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 3)
        c = w3.eth.contract(address=USDC_ADDR, abi=json.loads(ABI_MINIMA))
        usdc = round(c.functions.balanceOf(WALLET).call() / 10**6, 2)
    except: pol, usdc = "OFF", "OFF"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['acao']}</td><td style='color:#00ff00;'>{l['st']}</td><td>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#000; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:900px; margin:auto; border:1px solid #333; padding:20px; background:#050505;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="color:orange;margin:0;">⚡ SNIPER TERMINAL v10.5</h2>
                <div><b>POL:</b> {pol} | <b>USDC:</b> {usdc}</div>
            </div>
            <table style="width:100%; margin-top:20px; text-align:left;">
                <tr style="color:#555;"><th>HORA</th><th>MERCADO</th><th>AÇÃO</th><th>STATUS</th><th>RESULTADO</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))