import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_real_2026")

# --- CONFIGURAÇÕES ---
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
PRIV_KEY = os.environ.get("private_key") # Configura no Render!

# Contratos Oficiais Polymarket
CTF_EXCHANGE = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

# ABI Mínima para Transacionar
ABI_ERC20 = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

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

# --- FUNÇÃO DE TIRO (EXECUÇÃO REAL) ---
def dar_o_tiro(token_id, valor_usdc):
    if not PRIV_KEY:
        registrar_movimentacao("ERRO", "SISTEMA", "CHAVE AUSENTE", "0")
        return
    
    try:
        conta = Account.from_key(PRIV_KEY)
        valor_wei = int(valor_usdc * 10**6) # USDC tem 6 decimais
        
        # 1. Verificar Nonce
        nonce = w3.eth.get_transaction_count(WALLET)
        
        # 2. Preparar Transação (Data simplificada para o exemplo de compra)
        # O 'data' deve ser gerado de acordo com a função da Exchange da Polymarket
        tx = {
            'nonce': nonce,
            'to': CTF_EXCHANGE,
            'value': 0,
            'gas': 300000,
            'gasPrice': int(w3.eth.gas_price * 1.2), # 20% acima para rapidez
            'chainId': 137,
            'data': '0x' # Aqui vai o hex da função buy da Polymarket
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        registrar_log_tiro = f"TX: {tx_hash.hex()[:10]}"
        registrar_movimentacao("COMPRA", "POLYMARKET", "EXECUTADO", f"${valor_usdc}")
        
    except Exception as e:
        registrar_movimentacao("FALHA", "BLOCKCHAIN", str(e)[:15], f"${valor_usdc}")

# --- MOTOR DE SCAN COM GATILHO ---
def motor_sniper():
    while True:
        try:
            # Consulta API para buscar odds desajustadas
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&limit=5", timeout=10)
            if r.status_code == 200:
                eventos = r.json()
                registrar_movimentacao("SCAN", "RADAR", "BUSCANDO", "OK")
                
                # EXEMPLO DE GATILHO:
                # Se encontrar um mercado específico com probabilidade alta:
                # dar_o_tiro("ID_DO_TOKEN", 5.0) # Compra 5 USDC
            
        except Exception as e:
            registrar_movimentacao("SCAN", "API", "ERRO CONEXÃO", "-")
            
        time.sleep(20)

threading.Thread(target=motor_sniper, daemon=True).start()

# --- INTERFACE (DASHBOARD) ---
@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    # Busca Saldos Reais
    try:
        pol_bal = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        usdc_inst = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=ABI_ERC20)
        usdc_bal = round(usdc_inst.functions.balanceOf(WALLET).call() / 10**6, 2)
    except:
        pol_bal, usdc_bal = "0", "0"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td style='padding:10px;'>{l['hora']}</td><td>{l['mkt']}</td><td style='color:orange;'>{l['acao']}</td><td>{l['val']}</td><td style='color:#00ff00;'>{l['st']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#000; color:#fff; font-family:monospace; padding:20px;">
        <div style="border:1px solid orange; padding:20px;">
            <h2 style="color:orange; margin:0;">⚡ SNIPER COMMAND CENTER v6</h2>
            <hr border="0" style="border-top:1px solid #333; margin:15px 0;">
            <p>Saldos: <span style="color:cyan;">POL: {pol_bal}</span> | <span style="color:#00ff00;">USDC: {usdc_bal}</span></p>
            <table style="width:100%; text-align:left; border-collapse:collapse;">
                <tr style="color:#666;"><th>HORA</th><th>MERCADO</th><th>AÇÃO</th><th>VALOR</th><th>STATUS</th></tr>
                {rows}
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