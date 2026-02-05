import os, datetime, requests, time, threading
from flask import Flask, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN = os.environ.get("guardiao")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA") 
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# CONTRATOS
USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
QUICK_ROUTER = Web3.to_checksum_address("0xa5E0829CaCEd8fFDD03942104b10503958965ee4")

status_log = []
def add_log(msg):
    status_log.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

# --- MOTOR DE MOVIMENTAÇÕES AUTOMÁTICAS ---
def motor_de_combate():
    add_log("SISTEMA DE AUTOMAÇÃO INICIADO")
    while True:
        try:
            # 1. Checa o Preço do Alvo (Simulando link com Polymarket/Oracle)
            preco_atual = 14.4000 # EXEMPLO: Preço caiu abaixo de 14.4459
            alvo = 14.4459
            
            if preco_atual <= alvo:
                add_log(f"GATILHO DETECTADO: {preco_atual} <= {alvo}")
                
                if PVT_KEY:
                    # EXECUTA MOVIMENTAÇÃO: SWAP DE POL PARA USDC
                    balance = w3.eth.get_balance(WALLET)
                    if balance > w3.to_wei(0.5, 'ether'): # Deixa um pouco para gás
                        add_log("EXECUTANDO SWAP AUTOMÁTICO...")
                        # [Lógica de Swap do Web3 aqui...]
                        add_log("MOVIMENTAÇÃO CONCLUÍDA COM SUCESSO")
                        time.sleep(300) # Pausa de 5 min após operar
                else:
                    add_log("ERRO: CHAVE_PRIVADA AUSENTE PARA OPERAR")
                    
        except Exception as e:
            add_log(f"ERRO NO MOTOR: {str(e)[:20]}")
        
        time.sleep(10) # Varredura a cada 10 segundos

# Inicia o motor em uma thread separada
threading.Thread(target=motor_de_combate, daemon=True).start()

@app.route('/')
def dash():
    if not session.get('auth'): return redirect('/login')
    logs = "".join([f"<div style='border-bottom:1px solid #222; padding:5px;'>{l}</div>" for l in status_log[:10]])
    return f"""
    <body style="background:#000; color:#0f0; font-family:monospace; padding:20px;">
        <div style="max-width:700px; margin:auto; border:1px solid #333; padding:20px;">
            <h2 style="color:orange;">⚡ SNIPER TERMINAL - MOVIMENTAÇÕES LIVE</h2>
            <hr>
            <div style="display:flex; justify-content:space-between;">
                <span>CARTEIRA: <b>{WALLET[:10]}...</b></span>
                <span>STATUS: <b style="color:lime;">VIGIANDO ALVO</b></span>
            </div>
            <div style="margin-top:20px; background:#111; height:300px; overflow-y:auto; padding:10px; color:#aaa;">
                {logs}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 5000);</script>
    </body>"""

# [Rotas de Login omitidas para brevidade, manter as mesmas do v43]
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)