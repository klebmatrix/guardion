from flask import Flask, render_template, send_file
import threading
import time
import os
import qrcode
import io
from web3 import Web3

app = Flask(__name__)

# --- CONFIGURAÇÃO DO AGENTE MULTI ---
# No Render, configure essas variáveis na aba 'Environment'
RPC_URL = os.environ.get("RPC_URL", "https://polygon-rpc.com")
CARTEIRAS_MODULOS = {
    "MOD_01": os.environ.get("WALLET_01"),
    "MOD_02": os.environ.get("WALLET_02"),
    "MOD_03": os.environ.get("WALLET_03")
}

def agente_multi_logic():
    """O Agente Multi monitora todas as carteiras em loop"""
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    print("🤖 AGENTE MULTI-MÓDULO: ONLINE")

    while True:
        for modulo, address in CARTEIRAS_MODULOS.items():
            if not address: continue # Pula se a carteira não estiver configurada
            
            try:
                balance = w3.eth.get_balance(address)
                balance_eth = w3.from_wei(balance, 'ether')
                
                if balance_eth > 0:
                    print(f"💰 {modulo}: Depósito de {balance_eth} MATIC detectado!")
                    # Aqui o Agente Multi executa a troca automática
                else:
                    print(f"🔎 {modulo}: Monitorando {address[:6]}... (Vazio)")
            except Exception as e:
                print(f"⚠️ Erro no {modulo}: {e}")
        
        time.sleep(30) # Espera 30 segundos antes da próxima varredura

# Inicia o Agente Multi em background
threading.Thread(target=agente_multi_logic, daemon=True).start()

# --- ROTAS DO SITE ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr/<path:data>')
def generate_qr(data):
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)