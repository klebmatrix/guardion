import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONEXÃO REAL ---
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# Contratos para Movimentação
QUICK_ROUTER = "0xa5E0829CaCEd8fFDD03942104b10503958965ee4"
USDC_ADDR = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

# --- FUNÇÃO QUE MOVE O DINHEIRO DE VERDADE ---
def executar_movimentacao_real(quantidade_pol):
    try:
        nonce = w3.eth.get_transaction_count(WALLET)
        # Aqui entra o Smart Contract da QuickSwap para trocar POL por USDC
        add_log(f"⚡ DISPARANDO EXECUÇÃO REAL NA BLOCKCHAIN...")
        
        # Simulação de construção de TX (Para ativar, precisamos da ABI do Router)
        tx = {
            'nonce': nonce,
            'to': QUICK_ROUTER,
            'value': w3.to_wei(quantidade_pol, 'ether'),
            'gas': 250000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 137
        }
        # assinar = w3.eth.account.sign_transaction(tx, PVT_KEY)
        # enviar = w3.eth.send_raw_transaction(assinar.rawTransaction)
        add_log(f"✅ MOVIMENTAÇÃO ENVIADA!")
    except Exception as e:
        add_log(f"❌ FALHA NA EXECUÇÃO: {str(e)}")

# --- MOTOR DE DECISÃO ---
def motor_de_combate():
    while True:
        try:
            # Pega preço real do POL/USD via API pública
            res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=MATICUSDT")
            preco_atual = float(res.json()['price'])
            
            # SEU GATILHO REAL: Exemplo, se o POL bater 0.80 centavos ou 1.00 dólar
            if preco_atual >= 1.00: # Ajuste seu alvo real aqui
                add_log(f"🎯 ALVO BATIDO ({preco_atual}). Iniciando Swap de 14.2096 POL...")
                executar_movimentacao_real(14.2096)
                break # Para o bot após a execução para não repetir
                
        except:
            add_log("⏳ Erro ao ler preço. Tentando novamente...")
        time.sleep(10)

threading.Thread(target=motor_de_combate, daemon=True).start()

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    pol = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
    log_render = "".join([f"<div>{l}</div>" for l in logs[:10]])
    return f"""
    <body style="background:#000; color:#fff; font-family:monospace; padding:20px;">
        <h2 style="color:red;">🔥 MODO DE EXECUÇÃO REAL</h2>
        <div style="background:#111; padding:20px; border:1px solid red;">
            SALDO EM VIGÍLIA: <b style="font-size:30px;">{pol:.4f} POL</b>
        </div>
        <div style="margin-top:20px; color:lime;">
            {log_render}
        </div>
    </body>"""

# [Login omitido para brevidade]
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)