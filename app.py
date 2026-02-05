import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO DE COMBATE ---
PIN = os.environ.get("guardiao")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# QuickSwap V2 Router e Endereços de Tokens
QUICK_ROUTER = Web3.to_checksum_address("0xa5E0829CaCEd8fFDD03942104b10503958965ee4")
WPOL = Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")
USDC = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")

# ABI Mínima para Swap
ABI_ROUTER = [{"name":"swapExactETHForTokens","type":"function","inputs":[{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"payable"}]

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(logs) > 20: logs.pop()

# --- MOTOR DE EXECUÇÃO AUTÔNOMA ---
def motor_autonomo():
    add_log("🤖 CÉREBRO ATIVO: Monitorando Mercado...")
    while True:
        try:
            # 1. Checa Saldo
            bal_wei = w3.eth.get_balance(WALLET)
            saldo_pol = float(w3.from_wei(bal_wei, 'ether'))
            
            # 2. O Bot decide o volume (Sempre deixando reserva para o gás)
            if saldo_pol > 0.5:
                valor_entrada = saldo_pol * 0.92 # Pega 92% para garantir o gás
                
                # 3. LÓGICA AUTÔNOMA DE GATILHO (Preço/Variação)
                # Aqui o bot decide se o preço está bom para entrar
                res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=POLUSDT")
                preco = float(res.json()['price'])
                
                # Exemplo: Se o bot identificar oportunidade (preço abaixo de um teto técnico)
                if preco < 0.45: # AJUSTE ESTA LÓGICA SE DESEJAR
                    add_log(f"🎯 OPORTUNIDADE: Preço {preco}. Iniciando SWAP REAL...")
                    
                    contract = w3.eth.contract(address=QUICK_ROUTER, abi=ABI_ROUTER)
                    quantidade_wei = w3.to_wei(valor_entrada, 'ether')
                    
                    tx = contract.functions.swapExactETHForTokens(
                        0, [WPOL, USDC], WALLET, int(time.time()) + 600
                    ).build_transaction({
                        'from': WALLET,
                        'value': quantidade_wei,
                        'gas': 250000,
                        'gasPrice': w3.eth.gas_price,
                        'nonce': w3.eth.get_transaction_count(WALLET),
                        'chainId': 137
                    })
                    
                    # ASSINATURA E ENVIO REAL
                    signed_tx = w3.eth.account.sign_transaction(tx, PVT_KEY)
                    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    
                    add_log(f"✅ SUCESSO! TX: {w3.to_hex(tx_hash)[:15]}")
                    time.sleep(1200) # Pausa 20 min para evitar loops
            
        except Exception as e:
            add_log(f"⚠️ Erro: {str(e)[:40]}")
        
        time.sleep(15)

# Inicia o motor em segundo plano
threading.Thread(target=motor_autonomo, daemon=True).start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '<h1>AUTONOMOUS ACCESS</h1><form method="post"><input type="password" name="pin" autofocus><button>OK</button></form>'

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    bal = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
    log_render = "".join([f"<div style='border-bottom:1px solid #333;padding:5px;'>{l}</div>" for l in logs])
    return f"""
    <body style="background:#000; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:1px solid lime; padding:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style="color:lime; margin:0;">🤖 SNIPER AUTÔNOMO v50</h2>
                <b style="font-size:20px;">{bal:.4f} POL</b>
            </div>
            <div style="margin-top:20px; background:#050505; height:350px; overflow-y:auto; padding:10px; border:1px solid #222; color:lime;">
                {log_render}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)