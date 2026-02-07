import os, threading, time, io, qrcode
from flask import Flask, render_template, send_file
from web3 import Web3

app = Flask(__name__)

# Configuração dos Agentes (Defina as carteiras no painel do Render)
MODULOS = {
    "MOD_01": os.environ.get("WALLET_01", "0x000...1"),
    "MOD_02": os.environ.get("WALLET_02", "0x000...2"),
    "MOD_03": os.environ.get("WALLET_03", "0x000...3")
}

def agente_multi_monitor():
    w3 = Web3(Web3.HTTPProvider(os.environ.get("RPC_URL", "https://polygon-rpc.com")))
    print("🤖 AGENTES 1, 2 e 3 INICIADOS")
    
    while True:
        for mod, addr in MODULOS.items():
            try:
                if "0x" in addr:
                    # Aqui o agente checa o saldo para converter USDC > WBTC
                    balance = w3.eth.get_balance(addr)
                    if balance > 0:
                        print(f"💰 {mod} detectou saldo! Iniciando conversão...")
            except:
                pass
        time.sleep(20)

threading.Thread(target=agente_multi_monitor, daemon=True).start()

@app.route('/')
def home():
    return render_template('index.html', modulos=MODULOS)

@app.route('/qr/<path:text>')
def qr(text):
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)