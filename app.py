import os, datetime, time, threading
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO DE GUERRA ---
PIN = os.environ.get("guardiao")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Endereços para a Troca (QuickSwap V2)
ROUTER_ADDR = Web3.to_checksum_address("0xa5E0829CaCEd8fFDD03942104b10503958965ee4")
WETH_ADDR = Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270") # WMatic
USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")

# ABI para Swap
ABI_ROUTER = [{"name":"swapExactETHForTokens","type":"function","inputs":[{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"payable"}]

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def motor_executivo():
    add_log("🚀 MOTOR AUTOMÁTICO ATIVADO - MODO SNIPER")
    while True:
        try:
            # 1. PEGA O PREÇO ATUAL (Exemplo de gatilho real)
            preco_alvo = 14.4459
            preco_mercado = 14.4000 # Isso viria de uma API de oráculo
            
            if preco_mercado <= preco_alvo:
                add_log(f"🎯 ALVO ATINGIDO! Mercado: {preco_mercado}")
                
                # 2. CHECA SALDO
                bal_wei = w3.eth.get_balance(WALLET)
                if bal_wei > w3.to_wei(0.5, 'ether'): # Só opera se tiver mais de 0.5 POL
                    add_log("💰 EXECUTANDO TROCA AUTOMÁTICA...")
                    
                    contract = w3.eth.contract(address=ROUTER_ADDR, abi=ABI_ROUTER)
                    # Troca 2.0 POL por USDC (ajuste conforme necessário)
                    quantidade = w3.to_wei(2.0, 'ether')
                    
                    tx = contract.functions.swapExactETHForTokens(
                        0, [WETH_ADDR, USDC_ADDR], WALLET, int(time.time()) + 600
                    ).build_transaction({
                        'from': WALLET, 'value': quantidade, 'gas': 250000,
                        'gasPrice': w3.eth.gas_price, 'nonce': w3.eth.get_transaction_count(WALLET),
                        'chainId': 137
                    })
                    
                    signed = w3.eth.account.sign_transaction(tx, PVT_KEY)
                    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
                    add_log(f"✅ SUCESSO! TX: {w3.to_hex(tx_hash)[:15]}")
                    time.sleep(600) # Pausa 10 min após transação
                else:
                    add_log("⚠️ SALDO INSUFICIENTE PARA TAXAS")
            
        except Exception as e:
            add_log(f"❌ ERRO: {str(e)[:30]}")
        
        time.sleep(5) # Varredura rápida (cada 5 seg)

# Inicia o robô no fundo
threading.Thread(target=motor_executivo, daemon=True).start()

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect('/login')
    log_list = "".join([f"<div style='border-bottom:1px solid #222; padding:4px;'>{l}</div>" for l in logs[:15]])
    return f"""
    <body style="background:#000; color:#0f0; font-family:monospace; padding:20px;">
        <div style="max-width:750px; margin:auto; border:1px solid orange; padding:20px;">
            <h2 style="color:orange;">⚡ TERMINAL FULL AUTO v44</h2>
            <div style="background:#111; padding:10px; border-left:4px solid lime;">
                <b>ESTADO:</b> OPERACIONAL | <b>ALVO:</b> 14.4459
            </div>
            <div style="margin-top:20px; height:400px; overflow-y:auto; background:#050505; padding:10px; font-size:12px;">
                {log_list}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 5000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect('/')
    return '<h1>LOGIN</h1><form method="post"><input type="password" name="pin" autofocus><button>OK</button></form>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)