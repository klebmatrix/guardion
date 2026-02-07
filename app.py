import os, threading, time, io, qrcode
from flask import Flask, render_template, send_file, request, jsonify
from web3 import Web3

app = Flask(__name__)

MODULOS = {
    "MOD_01": os.environ.get("WALLET_01", "0x..."),
    "MOD_02": os.environ.get("WALLET_02", "0x..."),
    "MOD_03": os.environ.get("WALLET_03", "0x...")
}

# Configuração de Contratos (Polygon)
CONTRATOS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
}

@app.route('/')
def home():
    return render_template('index.html', modulos=MODULOS)

@app.route('/converter', methods=['POST'])
def converter():
    dados = request.get_json()
    mod = dados.get('modulo')
    carteira = MODULOS.get(mod)
    
    # Lógica de decisão do Agente
    if mod == "MOD_01":
        msg = f"🤖 MOD_01: Iniciando troca USDC ➔ WBTC (Bitcoin)"
    elif mod == "MOD_02":
        msg = f"🤖 MOD_02: Iniciando troca USDC ➔ USDT (Tether)"
    elif mod == "MOD_03":
        msg = f"🤖 MOD_03: Diversificando em várias Cryptos (Portfólio)"
    else:
        msg = "Módulo desconhecido"

    print(f"Comando executado: {msg} na carteira {carteira}")
    return jsonify({"status": "sucesso", "msg": msg})

@app.route('/qr/<path:text>')
def qr(text):
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)