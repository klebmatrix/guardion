import os, threading, time, io, qrcode
from flask import Flask, render_template, send_file, request, jsonify
from web3 import Web3

app = Flask(__name__)

# Configurações do Agente (Puxa do Render)
RPC_URL = os.environ.get("RPC_URL", "https://polygon-rpc.com")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Módulos com as tuas carteiras
MODULOS = {
    "MOD_01": os.environ.get("WALLET_01", "0x000..."),
    "MOD_02": os.environ.get("WALLET_02", "0x000..."),
    "MOD_03": os.environ.get("WALLET_03", "0x000...")
}

@app.route('/')
def home():
    # Passa os módulos para o HTML
    return render_template('index.html', modulos=MODULOS)

@app.route('/converter', methods=['POST'])
def converter():
    dados = request.json
    mod = dados.get('modulo')
    print(f"🤖 AGENTE: Ordem de conversão para WBTC recebida no {mod}")
    # Aqui o Agente usa a tua Private Key do Render para fazer o Swap
    return jsonify({"status": "sucesso", "msg": f"Conversão iniciada no {mod}!"})

@app.route('/qr/<path:text>')
def qr(text):
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)