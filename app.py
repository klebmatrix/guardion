import os, datetime, time, threading
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN = os.environ.get("guardiao")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# USDC Contrato e ABI
USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
USDC_ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

logs = []
def add_log(msg):
    agora = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{agora}] {msg}")

def pegar_saldos_exatos():
    try:
        # SALDO POL COM PRECISÃO MÁXIMA
        pol_wei = w3.eth.get_balance(WALLET)
        pol = w3.from_wei(pol_wei, 'ether')
        
        # SALDO USDC
        contrato = w3.eth.contract(address=USDC_ADDR, abi=USDC_ABI)
        usdc_raw = contrato.functions.balanceOf(WALLET).call()
        usdc = usdc_raw / 10**6
        return pol, usdc
    except:
        return 0.0, 0.0

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    
    # BUSCA OS VALORES REAIS
    saldo_pol, saldo_usdc = pegar_saldos_exatos()
    
    # Formatação forçada para 4 casas decimais para bater com a carteira
    pol_formatado = "{:.4f}".format(saldo_pol)

    return f"""
    <body style="background:#000; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:700px; margin:auto; border:2px solid orange; padding:20px; border-radius:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:10px;">
                <h2 style="color:orange; margin:0;">🛡️ SNIPER PRECISION v47</h2>
                <div style="background:lime; color:black; padding:3px 8px; border-radius:4px; font-weight:bold; font-size:12px;">LIVE</div>
            </div>
            
            <div style="margin-top:20px; display:grid; grid-template-columns: 1fr; gap:15px;">
                <div style="background:#111; padding:25px; border-left:5px solid cyan; border-radius:5px;">
                    <small style="color:cyan; text-transform:uppercase; letter-spacing:1px;">Saldo Real POL</small><br>
                    <b style="font-size:38px; color:#fff;">{pol_formatado}</b> <span style="color:cyan;">POL</span>
                </div>
                
                <div style="background:#111; padding:20px; border-left:5px solid yellow; border-radius:5px;">
                    <small style="color:yellow; text-transform:uppercase; letter-spacing:1px;">Saldo Real USDC</small><br>
                    <b style="font-size:28px; color:#fff;">$ {saldo_usdc:.2f}</b>
                </div>
            </div>

            <div style="margin-top:20px; background:#0a0a0a; border:1px solid #222; padding:15px; font-size:12px;">
                <b style="color:orange;">LOG DE MOVIMENTAÇÃO:</b>
                <div style="margin-top:10px; color:#888;">
                    [INFO] Aguardando variação para gatilho automático...<br>
                    [INFO] Monitorando carteira: {WALLET}
                </div>
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

# Mantém as funções de Login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h2>ACESSO RESTRITO</h2><form method="post"><input type="password" name="pin" autofocus><button>OK</button></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)