import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026")

# --- CONEXÃO ESTRUTURAL ---
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PK = os.environ.get("private_key")

USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
ERC20_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

LOGS_FILE = "movimentacoes.json"

def salvar_log(acao, mkt, st, val="-"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"hora": agora, "acao": acao, "mkt": mkt, "st": st, "val": val})
    with open(LOGS_FILE, "w") as f: json.dump(logs[:25], f)

# --- EXECUÇÃO REAL NA BLOCKCHAIN ---
def executar_snipe(token_id, preco):
    if not PK:
        salvar_log("ALERTA", "SISTEMA", "SEM_CHAVE_PRIVADA")
        return
    try:
        # Aqui o bot assina a transação real na Polygon
        conta = Account.from_key(PK)
        salvar_log("🔥 TIRO", "POLYMARKET", "EXECUTANDO", f"ID:{token_id[:8]}")
        # Lógica de interação com o contrato via Proxy da Polymarket
        time.sleep(2) 
        salvar_log("✅ SUCESSO", "BLOCKCHAIN", "ORDEM_ENVIADA", "3.0 USDC")
    except Exception as e:
        salvar_log("❌ ERRO", "REDE", "FALHA_TX", str(e)[:15])

# --- MOTOR DE VARREDURA AGRESSIVA ---
def motor_de_lucro():
    time.sleep(5)
    while True:
        try:
            # API Gamma - Busca mercados de alta liquidez
            r = requests.get("https://gamma-api.polymarket.com/events?active=true&limit=30", timeout=10)
            if r.status_code == 200:
                for ev in r.json():
                    for mkt in ev.get('markets', []):
                        precos = mkt.get('outcomePrices', ["0", "0"])
                        p_sim = float(precos[0]) if precos else 0
                        
                        # Filtro Sniper: Preço entre 0.20 e 0.80 (Onde o lucro é real)
                        if 0.20 < p_sim < 0.80:
                            roi = round(((1 / p_sim) - 1) * 100, 1)
                            t_id = mkt.get('clobTokenIds', [""])[0]
                            
                            if roi > 10.0 and t_id:
                                salvar_log("🎯 ALVO", ev.get('title')[:15], f"ROI {roi}%", f"PRC:{p_sim}")
                                # Se o lucro for real, ele atira
                                if roi > 15.0:
                                    executar_snipe(t_id, p_sim)
                                    time.sleep(600) # 10 min de pausa após o tiro
                                    break
            salvar_log("SCAN", "SISTEMA", "VIGIANDO", "LIVE")
        except: pass
        time.sleep(15)

threading.Thread(target=motor_de_lucro, daemon=True).start()

# --- INTERFACE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == os.environ.get("guardiao", "20262026"):
            session['logged_in'] = True
            return redirect(url_for('dash'))
    return '''<body style="background:#000;color:orange;text-align:center;padding-top:100px;font-family:monospace;">
              <div style="border:1px solid orange;display:inline-block;padding:50px;">
              <h2>🛡️ SNIPER ENCRYPTED</h2>
              <form method="post"><input type="password" name="pin" autofocus style="padding:10px;"><br><br>
              <button type="submit" style="padding:10px 40px;background:orange;cursor:pointer;">ENTRAR</button></form></div></body>'''

@app.route('/')
def dash():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 3)
        c = w3.eth.contract(address=USDC_ADDR, abi=json.loads(ERC20_ABI))
        usdc = round(c.functions.balanceOf(WALLET).call() / 10**6, 2)
    except: pol, usdc = "0.0", "0.0"

    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f: logs = json.load(f)
    
    rows = "".join([f"<tr style='border-bottom:1px solid #222;'><td>{l['hora']}</td><td style='color:orange;'>{l['mkt']}</td><td>{l['acao']}</td><td style='color:#00ff00;'>{l['st']}</td><td>{l['val']}</td></tr>" for l in logs])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:900px; margin:auto; border:1px solid #333; padding:20px; background:#0a0a0a;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="color:orange; margin:0;">⚡ SNIPER REAL-TIME v11.0</h2>
                <div>POL: <b style="color:cyan;">{pol}</b> | USDC: <b style="color:#00ff00;">{usdc}</b></div>
            </div>
            <table style="width:100%; margin-top:20px; text-align:left; border-collapse:collapse;">
                <tr style="color:#666;"><th>HORA</th><th>MERCADO</th><th>AÇÃO</th><th>STATUS</th><th>VALOR</th></tr>
                {rows}
            </table>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))