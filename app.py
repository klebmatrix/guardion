import os, threading, time, io, qrcode
from flask import Flask, render_template, send_file
from web3 import Web3

app = Flask(__name__)

# Configurações via Environment Variables do Render
RPC_URL = os.environ.get("RPC_URL", "https://polygon-rpc.com")
WALLET_01 = os.environ.get("WALLET_01", "SEU_ENDERECO_AQUI")

def agente_multi():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    print("🤖 AGENTE MULTI: Iniciado e monitorando USDC -> WBTC")
    
    while True:
        try:
            if WALLET_01 != "SEU_ENDERECO_AQUI":
                balance = w3.eth.get_balance(WALLET_01)
                eth_balance = w3.from_wei(balance, 'ether')
                
                if eth_balance > 0:
                    print(f"💰 Depósito Detectado em {WALLET_01}: {eth_balance} MATIC/USDC")
                    print("⚡ Iniciando conversão para WBTC via Uniswap...")
                    # Lógica de Swap automática aqui
                else:
                    print(f"🔎 Monitorando {WALLET_01[:6]}... aguardando depósito.")
            
            time.sleep(30)
        except Exception as e:
            print(f"⚠️ Erro no Agente: {e}")
            time.sleep(10)

# Inicia o Agente em segundo plano
threading.Thread(target=agente_multi, daemon=True).start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/qr/<path:text>')
def qr(text):
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)