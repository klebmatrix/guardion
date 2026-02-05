import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

# --- CONFIGURAÇÕES BLOCKCHAIN ---
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Dados da Carteira
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
PRIV_KEY = os.environ.get("private_key") # DEVE estar no Render

# Contratos (Polymarket CTF Exchange)
POLY_EXCHANGE = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"
USDC_TOKEN = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

LOGS_FILE = "logs.json"

def registrar_log(msg, mercado="SISTEMA", status="INFO"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    logs.insert(0, {"data": agora, "msg": msg, "mercado": mercado, "status": status})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:30], f)

# --- FUNÇÃO DE EXECUÇÃO REAL ---
def executar_compra_real(token_id, valor_usdc):
    if not PRIV_KEY:
        registrar_log("Chave Privada Ausente!", "ERRO", "FALHA")
        return
    
    try:
        conta = Account.from_key(PRIV_KEY)
        # 1. Preparar a transação (Exemplo simplificado de interação com a Exchange)
        # Nota: A Polymarket usa ordens assinadas ou interações via CTF Exchange
        registrar_log(f"Iniciando compra de {valor_usdc} USDC", "POLY", "PROCESSANDO")
        
        nonce = w3.eth.get_transaction_count(WALLET)
        tx = {
            'nonce': nonce,
            'to': POLY_EXCHANGE,
            'value': 0,
            'gas': 250000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 137,
            'data': '0x' # Aqui entraria o bytecode da função buy(token_id, amount)
        }
        
        # Assinar e Enviar
        signed_tx = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        registrar_log(f"ORDEM ENVIADA! TX: {tx_hash.hex()[:10]}...", "POLY", "SUCESSO")
        
    except Exception as e:
        registrar_log(f"Erro na execução: {str(e)[:30]}", "BLOCKCHAIN", "FALHA")

# --- MOTOR DE SCAN COM GATILHO ---
def motor_sniper():
    while True:
        try:
            # 1. Varrer Polymarket por oportunidades (Odds < 0.90 por exemplo)
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&limit=5")
            if r.status_code == 200:
                eventos = r.json()
                for ev in eventos:
                    # LÓGICA DE GATILHO REAL:
                    # Se encontrarmos uma oportunidade específica (exemplo fictício de ID):
                    # executar_compra_real("TOKEN_ID_AQUI", 10) 
                    pass
                registrar_log("Monitorando Odds e Liquidez", "RADAR", "BUSCANDO")
        except:
            pass
        time.sleep(20)

threading.Thread(target=motor_sniper, daemon=True).start()

# --- INTERFACE ---
@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    log_rows = "".join([f"<tr><td style='padding:8px;'>{l['data']}</td><td>{l['mercado']}</td><td>{l['msg']}</td><td style='color:#00ff00;'>{l['status']}</td></tr>" for l in logs])
    
    return f"""
    <body style="background:#000; color:#fff; font-family:sans-serif; padding:20px;">
        <h1 style="color:orange;">🛡️ TERMINAL DE EXECUÇÃO REAL</h1>
        <div style="background:#111; padding:15px; border:1px solid orange; border-radius:5px; margin-bottom:20px;">
            <p>SISTEMA: <b>OPERACIONAL</b> | CARTEIRA: <code>{WALLET}</code></p>
            <p style="color:cyan;">Aguardando sinal de entrada nos mercados...</p>
        </div>
        <table style="width:100%; text-align:left; background:#111;">
            <tr style="color:orange;"><th>HORA</th><th>MERCADO</th><th>MOVIMENTAÇÃO</th><th>STATUS</th></tr>
            {log_rows}
        </table>
    </body>
    """

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == os.environ.get("guardiao", "20262026"):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:100px;"><form method="post"><input type="password" name="pin"><button>ENTRAR</button></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))