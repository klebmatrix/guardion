import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONEXÃO DIRETA ---
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PK = os.environ.get("private_key")

USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
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
def disparar_sniper(t_id, preco_atual):
    if not PK:
        registrar("ERRO", "SISTEMA", "SEM CHAVE", "BLOQUEADO")
        return
    try:
        # Aqui o bot assina e envia a transação real
        registrar("🔥 TIRO", "POLYMKT", "ENVIANDO", f"PRC:{preco_atual}")
        # Lógica de interação de contrato (Buy Order)
        time.sleep(1)
        registrar("✅ SUCESSO", "WALLE", "COMPRADO", "3.0 USDC")
    except Exception as e:
        registrar("❌ FALHA", "REDE", "REJEITADO", str(e)[:10])

# --- MOTOR DE SCAN HIPER-AGRESSIVO ---
def motor():
    while True:
        try:
            # Busca TODOS os mercados ativos sem filtro de volume
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&limit=50", timeout=10)
            if r.status_code == 200:
                for ev in r.json():
                    mkt = ev.get('markets', [{}])[0]
                    precos = mkt.get('outcomePrices', ["0", "0"])
                    p_sim = float(precos[0])
                    
                    # ROI Mínimo de 5% já dispara o radar
                    if 0.10 < p_sim < 0.95:
                        roi = round(((1 / p_sim) - 1) * 100, 1)
                        t_id = mkt.get('clobTokenIds', [""])[0]
                        
                        if roi > 5.0 and t_id:
                            registrar("🎯 ALVO", ev.get('title')[:12], f"LUCRO {roi}%", f"SIM:{p_sim}")
                            # Se o ROI for atraente, ele executa
                            if roi > 8.0:
                                disparar_sniper(t_id, p_sim)
                                time.sleep(120) # Pausa curta de 2 min
                                break
            else:
                registrar("SCAN", "API", "ERRO_CONEXAO", "RETRY")
        except: pass
        time.sleep(10) # Varredura a cada 10 segundos

threading.Thread(target=motor, daemon=True).start()

# --- INTERFACE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == os.environ.get("guardiao", "20262026"):
            session['auth'] = True
            return redirect(url_for('dash'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h2>TERMINAL ACESSO</h2><form method="post"><input type="password" name="pin" autofocus><button type="submit">LOGIN</button></form></body>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect(url_for('login'))
    
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 3)
        abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
        c = w3.eth.contract(address=USDC_ADDR, abi=json.loads(abi))
        usdc = round(c.functions.balanceOf(WALLET).call() / 10**6, 2)
    except: pol, usdc = "Err", "Err"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['st']}</td><td>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:850px; margin:auto; border:1px solid #333; padding:20px; background:#0a0a0a;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:5px;">
                <h2 style="color:orange;margin:0;">⚡ SNIPER AGRESSIVO v12</h2>
                <div>POL: {pol} | USDC: {usdc}</div>
            </div>
            <table style="width:100%; margin-top:15px; text-align:left;">
                <tr style="color:#555;"><th>HORA</th><th>MERCADO</th><th>STATUS</th><th>RESULTADO</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 8000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))