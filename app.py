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

def pegar_saldos_reais():
    try:
        # Pega POL direto da rede
        pol_wei = w3.eth.get_balance(WALLET)
        pol = w3.from_wei(pol_wei, 'ether')
        
        # Pega USDC direto do contrato
        contrato = w3.eth.contract(address=USDC_ADDR, abi=USDC_ABI)
        usdc_raw = contrato.functions.balanceOf(WALLET).call()
        usdc = usdc_raw / 10**6
        return float(pol), float(usdc)
    except Exception as e:
        return 0.0, 0.0

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    
    # BUSCA OS VALORES AGORA
    meu_pol, meu_usdc = pegar_saldos_reais()
    
    # Preço do mercado (apenas informativo, para não confundir com saldo)
    preco_mercado_atual = 14.21 

    return f"""
    <body style="background:#000; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:700px; margin:auto; border:2px solid orange; padding:20px;">
            <h2 style="color:orange;">🛡️ CARTEIRA EM TEMPO REAL</h2>
            
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:20px;">
                <div style="background:#111; padding:20px; border:1px solid cyan;">
                    <small style="color:cyan;">SALDO POL</small><br>
                    <b style="font-size:25px;">{meu_pol:.4f}</b>
                </div>
                <div style="background:#111; padding:20px; border:1px solid yellow;">
                    <small style="color:yellow;">SALDO USDC</small><br>
                    <b style="font-size:25px;">$ {meu_usdc:.2f}</b>
                </div>
            </div>

            <div style="background:#050505; padding:10px; border-left:4px solid magenta;">
                <small>INFO MERCADO:</small> Preço Alvo Atual: <b style="color:white;">{preco_mercado_atual}</b>
            </div>

            <div style="margin-top:20px; font-size:11px; color:#444;">
                Endereço: {WALLET}<br>
                Status: <span style="color:lime;">CONECTADO À POLYGON</span>
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

# (Mantenha as funções de Login e Motor Autônomo abaixo)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '<h1>LOGIN</h1><form method="post"><input type="password" name="pin" autofocus><button>OK</button></form>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)